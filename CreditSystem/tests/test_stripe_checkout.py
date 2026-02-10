"""
Testes de integração para o sistema de checkout Stripe.

Estes testes verificam:
- Criação de sessão de checkout
- Validação de planos
- Tratamento de erros
- Fluxo de upgrade
"""

from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from CreditSystem.models import SubscriptionPlan, UserSubscription

User = get_user_model()


def create_test_user(email, password="testpass123"):
    """Helper para criar usuário de teste com username gerado"""
    username = email.split("@")[0]
    return User.objects.create_user(
        username=username,
        email=email,
        password=password
    )


def get_or_create_plan(interval, **kwargs):
    """Helper para criar ou obter um plano existente"""
    defaults = {
        "name": f"Plano {interval}",
        "description": f"Plano {interval} de teste",
        "price": Decimal("49.90"),
        "stripe_price_id": f"price_live_{interval}_123",  # Não usar price_test_
        "monthly_credits": Decimal("100.00"),
        "is_active": True,
    }
    defaults.update(kwargs)
    plan, _ = SubscriptionPlan.objects.get_or_create(
        interval=interval,
        defaults=defaults
    )
    # Atualizar campos se o plano já existia
    for key, value in defaults.items():
        setattr(plan, key, value)
    plan.save()
    return plan


class StripeCheckoutTestCase(TestCase):
    """Testes para criação de checkout session"""

    def setUp(self):
        """Configuração inicial dos testes"""
        self.client = APIClient()
        self.user = create_test_user("checkout_test@example.com")
        self.plan_monthly = get_or_create_plan(
            "monthly",
            name="Mensal Teste",
            price=Decimal("49.90"),
        )
        self.plan_yearly = get_or_create_plan(
            "yearly",
            name="Anual Teste",
            price=Decimal("359.00"),
        )
        self.checkout_url = "/api/v1/credits/checkout/"

    def test_checkout_requires_authentication(self):
        """Teste: checkout requer autenticação"""
        response = self.client.post(
            self.checkout_url,
            {"plan_id": self.plan_monthly.id},
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_checkout_requires_plan_id(self):
        """Teste: checkout requer plan_id"""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            self.checkout_url,
            {},
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.json()["success"])

    def test_checkout_invalid_plan_returns_404(self):
        """Teste: plano inválido retorna 404"""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            self.checkout_url,
            {"plan_id": 99999},
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.json()["success"])

    def test_checkout_plan_without_stripe_id_returns_503(self):
        """Teste: plano sem stripe_price_id retorna 503"""
        # Temporariamente remover o stripe_price_id
        original_stripe_id = self.plan_monthly.stripe_price_id
        self.plan_monthly.stripe_price_id = ""
        self.plan_monthly.save()

        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            self.checkout_url,
            {"plan_id": self.plan_monthly.id},
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)

        # Restaurar
        self.plan_monthly.stripe_price_id = original_stripe_id
        self.plan_monthly.save()

    @patch("CreditSystem.views.stripe.checkout.Session.create")
    @patch("AuditSystem.services.AuditService.log_subscription_operation")
    def test_checkout_success(self, mock_audit, mock_stripe_create):
        """Teste: checkout criado com sucesso"""
        mock_stripe_create.return_value = MagicMock(
            url="https://checkout.stripe.com/test_session"
        )
        mock_audit.return_value = None  # Evita problemas de transação

        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            self.checkout_url,
            {"plan_id": self.plan_monthly.id},
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json()["success"])
        self.assertIn("checkout_url", response.json())

    @patch("CreditSystem.views.stripe.checkout.Session.create")
    @patch("AuditSystem.services.AuditService.log_subscription_operation")
    def test_checkout_includes_trial_period(self, mock_audit, mock_stripe_create):
        """Teste: checkout inclui período de trial"""
        mock_stripe_create.return_value = MagicMock(
            url="https://checkout.stripe.com/test"
        )
        mock_audit.return_value = None

        self.client.force_authenticate(user=self.user)
        self.client.post(
            self.checkout_url,
            {"plan_id": self.plan_monthly.id},
            format="json"
        )

        # Verificar que foi chamado com subscription_data
        call_kwargs = mock_stripe_create.call_args.kwargs
        self.assertIn("subscription_data", call_kwargs)
        self.assertIn("trial_period_days", call_kwargs["subscription_data"])


class SubscriptionUpgradeTestCase(TestCase):
    """Testes para upgrade de assinatura"""

    def setUp(self):
        """Configuração inicial"""
        self.client = APIClient()
        self.user = create_test_user("upgrade_test@example.com")
        self.plan_monthly = get_or_create_plan("monthly")
        self.plan_yearly = get_or_create_plan("yearly")
        self.checkout_url = "/api/v1/credits/checkout/"

    def test_same_plan_returns_already_subscribed(self):
        """Teste: tentar assinar mesmo plano retorna já assinado"""
        # Limpar assinaturas existentes
        UserSubscription.objects.filter(user=self.user).delete()

        # Criar assinatura existente
        UserSubscription.objects.create(
            user=self.user,
            plan=self.plan_monthly,
            status="active"
        )

        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            self.checkout_url,
            {"plan_id": self.plan_monthly.id},
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json()["success"])
        self.assertTrue(response.json().get("already_on_plan"))

    def test_different_plan_requires_upgrade_flag(self):
        """Teste: trocar de plano requer flag upgrade=true"""
        # Limpar assinaturas existentes
        UserSubscription.objects.filter(user=self.user).delete()

        UserSubscription.objects.create(
            user=self.user,
            plan=self.plan_monthly,
            status="active"
        )

        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            self.checkout_url,
            {"plan_id": self.plan_yearly.id},
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertTrue(response.json().get("upgrade_available"))


class SubscriptionCurrentTestCase(TestCase):
    """Testes para endpoint de assinatura atual"""

    def setUp(self):
        """Configuração inicial"""
        self.client = APIClient()
        self.user = create_test_user("current_test@example.com")
        self.plan = get_or_create_plan("monthly")
        self.current_url = "/api/v1/credits/subscription/current/"

    def test_no_subscription_returns_404(self):
        """Teste: sem assinatura retorna 404"""
        # Limpar assinaturas
        UserSubscription.objects.filter(user=self.user).delete()

        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.current_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_active_subscription_returns_data(self):
        """Teste: assinatura ativa retorna dados"""
        # Limpar assinaturas
        UserSubscription.objects.filter(user=self.user).delete()

        subscription = UserSubscription.objects.create(
            user=self.user,
            plan=self.plan,
            status="active"
        )

        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.current_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["id"], subscription.id)
        self.assertEqual(response.json()["status"], "active")

    def test_cancelled_subscription_not_returned(self):
        """Teste: assinatura cancelada não é retornada como atual"""
        # Limpar assinaturas
        UserSubscription.objects.filter(user=self.user).delete()

        UserSubscription.objects.create(
            user=self.user,
            plan=self.plan,
            status="cancelled"
        )

        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.current_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class SubscriptionPlansListTestCase(TestCase):
    """Testes para listagem de planos"""

    def setUp(self):
        """Configuração inicial"""
        self.client = APIClient()
        self.plans_url = "/api/v1/credits/plans/"

    def test_list_plans_is_public(self):
        """Teste: listagem de planos é pública"""
        get_or_create_plan("monthly")

        response = self.client.get(self.plans_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_only_active_plans_returned(self):
        """Teste: apenas planos ativos são retornados"""
        # Criar plano inativo com interval diferente
        plan = get_or_create_plan("semester", is_active=False)

        response = self.client.get(self.plans_url)
        plans = response.json()

        # Verificar que o plano inativo não está na lista
        plan_ids = [p["id"] for p in plans]
        self.assertNotIn(plan.id, plan_ids)
