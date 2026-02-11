"""
Service para gerenciar checkout de assinaturas.

Este service encapsula a lógica de criação de checkout sessions do Stripe,
permitindo melhor testabilidade e manutenção.
"""

import os
from dataclasses import dataclass
from typing import Optional

import stripe
from django.conf import settings
from django.db import transaction

from AuditSystem.services import AuditService
from CreditSystem.models import SubscriptionPlan, UserSubscription
from CreditSystem.services.credit_service import CreditService


@dataclass
class CheckoutResult:
    """Resultado de uma operação de checkout"""
    success: bool
    message: str
    data: Optional[dict] = None
    status_code: int = 200


class SubscriptionCheckoutService:
    """
    Service para gerenciar checkout de assinaturas Stripe.

    Responsabilidades:
    - Validar plano e usuário
    - Verificar assinatura existente
    - Criar sessão de checkout
    - Gerenciar upgrades
    """

    def __init__(self, user, plan_id: int):
        self.user = user
        self.plan_id = plan_id
        self.plan: Optional[SubscriptionPlan] = None
        self.existing_subscription: Optional[UserSubscription] = None

        # Configurar Stripe
        stripe.api_key = settings.STRIPE_SECRET_KEY

    def validate_plan(self) -> CheckoutResult:
        """Valida se o plano existe e está ativo"""
        if not self.plan_id:
            self._log_error("missing_plan_id", "Missing plan_id parameter")
            return CheckoutResult(
                success=False,
                message="plan_id é obrigatório",
                status_code=400
            )

        try:
            self.plan = SubscriptionPlan.objects.get(id=self.plan_id, is_active=True)
        except SubscriptionPlan.DoesNotExist:
            self._log_error("plan_not_found", f"Plan {self.plan_id} not found")
            return CheckoutResult(
                success=False,
                message="Plano não encontrado ou inativo",
                status_code=404
            )

        if not self.plan.stripe_price_id:
            self._log_error("plan_unavailable", f"Plan {self.plan.name} has no Stripe ID")
            return CheckoutResult(
                success=False,
                message="Este plano está temporariamente indisponível.",
                status_code=503
            )

        return CheckoutResult(success=True, message="Plano válido")

    def check_existing_subscription(self) -> Optional[CheckoutResult]:
        """Verifica se usuário já tem assinatura ativa (com lock para evitar race condition)"""
        with transaction.atomic():
            self.existing_subscription = UserSubscription.objects.select_for_update().filter(
                user=self.user,
                status="active"
            ).select_related("plan").first()

        if not self.existing_subscription:
            return None  # Pode prosseguir com checkout normal

        # Mesmo plano
        if self.existing_subscription.plan_id == self.plan.id:
            return CheckoutResult(
                success=True,
                message="Você já está neste plano",
                data={"already_on_plan": True, "plan": self.existing_subscription.plan.name}
            )

        # Plano lifetime não pode ser alterado
        if self.existing_subscription.plan.interval == "lifetime":
            return CheckoutResult(
                success=False,
                message="Você já possui um plano vitalício ativo.",
                data={"lifetime_active": True},
                status_code=400
            )

        return None

    def create_checkout_session(self) -> CheckoutResult:
        """Cria sessão de checkout no Stripe"""
        frontend_url = getattr(settings, 'FRONTEND_URL', os.getenv("FRONTEND_URL", "http://localhost:3000"))

        try:
            # Configurar dados da assinatura
            subscription_data = None
            if self.plan.interval != "lifetime":
                subscription_data = {
                    "metadata": {
                        "user_id": str(self.user.id),
                        "plan_id": str(self.plan.id),
                    },
                    "trial_period_days": settings.SUBSCRIPTION_TRIAL_DAYS,
                }

            checkout_session = stripe.checkout.Session.create(
                customer_email=self.user.email,
                payment_method_types=["card"],
                line_items=[{
                    "price": self.plan.stripe_price_id,
                    "quantity": 1,
                }],
                allow_promotion_codes=True,
                mode="subscription" if self.plan.interval != "lifetime" else "payment",
                success_url=f"{frontend_url}/subscription/success?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=f"{frontend_url}/subscription/cancel",
                metadata={
                    "user_id": str(self.user.id),
                    "plan_id": str(self.plan.id),
                },
                subscription_data=subscription_data,
            )

            self._log_success("checkout_created", checkout_session.id)

            return CheckoutResult(
                success=True,
                message="Checkout criado",
                data={"checkout_url": checkout_session.url}
            )

        except stripe.error.StripeError as e:
            self._log_error("stripe_error", str(e))
            return CheckoutResult(
                success=False,
                message=f"Erro no Stripe: {str(e)}",
                status_code=400
            )
        except Exception as e:
            self._log_error("unexpected_error", str(e))
            return CheckoutResult(
                success=False,
                message=f"Erro interno: {str(e)}",
                status_code=500
            )

    def handle_upgrade(self, upgrade_requested: bool) -> CheckoutResult:
        """Gerencia upgrade de assinatura existente"""
        if not upgrade_requested:
            return CheckoutResult(
                success=False,
                message='Você já possui uma assinatura ativa. Envie "upgrade": true para alterar.',
                data={
                    "upgrade_available": True,
                    "current_plan": self.existing_subscription.plan.name,
                    "requested_plan": self.plan.name,
                },
                status_code=409
            )

        # Target é lifetime? Requer cancelamento manual
        if self.plan.interval == "lifetime":
            return CheckoutResult(
                success=False,
                message="Para migrar para o plano vitalício, cancele a assinatura atual primeiro.",
                data={"requires_manual_action": True},
                status_code=400
            )

        # Tentar upgrade via Stripe
        if not self.existing_subscription.stripe_subscription_id:
            return CheckoutResult(
                success=False,
                message="Assinatura local ativa. Cancele antes de criar um novo checkout.",
                data={"requires_cancellation": True},
                status_code=409
            )

        return self._perform_stripe_upgrade()

    def _perform_stripe_upgrade(self) -> CheckoutResult:
        """Executa upgrade via API do Stripe"""
        try:
            stripe_sub = stripe.Subscription.retrieve(
                self.existing_subscription.stripe_subscription_id
            )

            # Encontrar item da assinatura
            items = stripe_sub.get("items", {}).get("data", [])
            sub_item_id = self._find_subscription_item(items)

            if not sub_item_id:
                return CheckoutResult(
                    success=False,
                    message="Não foi possível localizar o item da assinatura.",
                    status_code=500
                )

            # Executar upgrade
            stripe.Subscription.modify(
                self.existing_subscription.stripe_subscription_id,
                cancel_at_period_end=False,
                proration_behavior="create_prorations",
                items=[{
                    "id": sub_item_id,
                    "price": self.plan.stripe_price_id,
                    "quantity": 1,
                }],
                metadata={
                    "user_id": str(self.user.id),
                    "upgraded_from_plan": self.existing_subscription.plan.interval,
                    "upgraded_to_plan": self.plan.interval,
                },
            )

            # Atualizar localmente
            previous_plan = self.existing_subscription.plan
            self.existing_subscription.plan = self.plan
            self.existing_subscription.save(update_fields=["plan"])

            # Reset de créditos
            try:
                CreditService.check_and_reset_monthly_credits(self.user)
            except Exception:
                pass  # Não bloquear upgrade por erro de créditos

            self._log_success("plan_upgraded", previous_plan.name)

            return CheckoutResult(
                success=True,
                message="Upgrade de assinatura realizado com sucesso.",
                data={
                    "upgraded": True,
                    "previous_plan": previous_plan.name,
                    "new_plan": self.plan.name,
                }
            )

        except stripe.error.StripeError as e:
            self._log_error("stripe_upgrade_error", str(e))
            return CheckoutResult(
                success=False,
                message=f"Erro no Stripe ao realizar upgrade: {str(e)}",
                status_code=400
            )

    def _find_subscription_item(self, items: list) -> Optional[str]:
        """Encontra o item da assinatura atual.

        Retorna None se não encontrar - não usa fallback cego para evitar
        modificar item incorreto em assinaturas com múltiplos itens.
        """
        for item in items:
            if item.get("price", {}).get("id") == self.existing_subscription.plan.stripe_price_id:
                return item.get("id")

        # Se só há um item, é seguro usá-lo
        if len(items) == 1:
            return items[0].get("id")

        # Múltiplos itens e nenhum match - não arriscar
        return None

    def _log_error(self, error_type: str, message: str):
        """Log de erro via AuditService"""
        AuditService.log_subscription_operation(
            user=self.user,
            action="subscription_created",
            status="failure",
            error_message=message,
            details={"error_type": error_type, "plan_id": self.plan_id}
        )

    def _log_success(self, action: str, detail: str):
        """Log de sucesso via AuditService"""
        AuditService.log_subscription_operation(
            user=self.user,
            action="subscription_created",
            status="success",
            details={
                "action": action,
                "plan_name": self.plan.name if self.plan else None,
                "detail": detail,
            }
        )
