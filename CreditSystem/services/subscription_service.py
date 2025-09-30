import stripe
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone

from ..models import SubscriptionPlan, UserSubscription


class SubscriptionService:
    """
    Service para integração com o Stripe para assinaturas
    """

    def __init__(self):
        """Inicializa o service com a chave do Stripe"""
        stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', None)
        if not stripe.api_key:
            raise ValidationError("STRIPE_SECRET_KEY não configurada")

    def process_webhook(self, payload, sig_header):
        """
        Processa webhook do Stripe para eventos de assinatura

        Args:
            payload: Payload do webhook
            sig_header: Header de assinatura

        Returns:
            dict: Dados processados do webhook
        """
        webhook_secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET', None)
        if not webhook_secret:
            raise ValidationError("STRIPE_WEBHOOK_SECRET não configurada")

        try:
            # Verifica a assinatura do webhook
            event = stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )
        except ValueError as e:
            raise ValidationError(f"Payload inválido: {str(e)}")
        except stripe.error.SignatureVerificationError as e:
            raise ValidationError(f"Assinatura inválida: {str(e)}")

        # Processa o evento
        if event['type'] == 'customer.subscription.created':
            return self._handle_subscription_created(event['data']['object'])
        elif event['type'] == 'customer.subscription.deleted':
            return self._handle_subscription_deleted(event['data']['object'])
        elif event['type'] == 'customer.subscription.updated':
            return self._handle_subscription_updated(event['data']['object'])
        elif event['type'] == 'invoice.payment_succeeded':
            return self._handle_payment_succeeded(event['data']['object'])
        elif event['type'] == 'invoice.payment_failed':
            return self._handle_payment_failed(event['data']['object'])

        return {'status': 'ignored', 'event_type': event['type']}

    def _handle_subscription_created(self, subscription):
        """
        Processa criação de assinatura

        Args:
            subscription: Dados da assinatura do Stripe

        Returns:
            dict: Resultado do processamento
        """
        try:
            stripe_subscription_id = subscription['id']
            user_id = None
            plan_id = None

            # Tenta obter metadados da assinatura
            metadata = subscription.get('metadata', {})
            user_id = metadata.get('user_id')
            plan_id = metadata.get('plan_id')

            # Se metadados não estão disponíveis, tenta buscar por price_id
            if not user_id or not plan_id:
                price_id = None
                if subscription.get('items', {}).get('data'):
                    price_id = subscription['items']['data'][0]['price']['id']

                if price_id:
                    try:
                        plan = SubscriptionPlan.objects.get(
                            stripe_price_id=price_id, is_active=True)
                        plan_id = str(plan.id)

                        # Busca usuário pelo customer
                        customer_id = subscription.get('customer')
                        if customer_id:
                            user_id = self._get_user_id_from_customer(
                                customer_id)
                    except SubscriptionPlan.DoesNotExist:
                        raise ValidationError(
                            f'Plano não encontrado para price_id: {price_id}')

            if not user_id or not plan_id:
                raise ValidationError(
                    'Não foi possível determinar usuário ou plano da assinatura')

            # Busca usuário e plano
            User = get_user_model()
            user = User.objects.get(id=user_id)
            plan = SubscriptionPlan.objects.get(id=plan_id, is_active=True)

            # Verifica se assinatura já existe
            existing_sub = UserSubscription.objects.filter(
                stripe_subscription_id=stripe_subscription_id
            ).first()
            if existing_sub:
                return {
                    'status': 'success',
                    'message': 'Assinatura já registrada',
                    'subscription_id': existing_sub.id
                }

            # Cancela assinaturas ativas existentes
            UserSubscription.objects.filter(
                user=user, status='active'
            ).update(status='cancelled', end_date=timezone.now())

            # Calcula data de fim
            end_date = self._calculate_end_date(plan.interval)

            # Cria nova assinatura
            user_subscription = UserSubscription.objects.create(
                user=user,
                plan=plan,
                start_date=timezone.now(),
                end_date=end_date,
                status='active',
                stripe_subscription_id=stripe_subscription_id
            )

            return {
                'status': 'success',
                'message': 'Assinatura criada com sucesso',
                'subscription_id': user_subscription.id,
                'user_id': user.id,
                'plan_name': plan.name
            }

        except User.DoesNotExist:
            raise ValidationError(f'Usuário não encontrado: {user_id}')
        except SubscriptionPlan.DoesNotExist:
            raise ValidationError(f'Plano não encontrado: {plan_id}')
        except Exception as e:
            raise ValidationError(f'Erro ao criar assinatura: {str(e)}')

    def _handle_subscription_deleted(self, subscription):
        """
        Processa cancelamento de assinatura

        Args:
            subscription: Dados da assinatura do Stripe

        Returns:
            dict: Resultado do processamento
        """
        try:
            stripe_subscription_id = subscription['id']

            user_subscription = UserSubscription.objects.filter(
                stripe_subscription_id=stripe_subscription_id,
                status='active'
            ).first()

            if user_subscription:
                user_subscription.status = 'cancelled'
                user_subscription.end_date = timezone.now()
                user_subscription.save()

                return {
                    'status': 'success',
                    'message': 'Assinatura cancelada com sucesso',
                    'subscription_id': user_subscription.id
                }
            else:
                return {
                    'status': 'success',
                    'message': 'Assinatura não encontrada ou já cancelada'
                }

        except Exception as e:
            raise ValidationError(f'Erro ao cancelar assinatura: {str(e)}')

    def _handle_subscription_updated(self, subscription):
        """
        Processa atualização de assinatura

        Args:
            subscription: Dados da assinatura do Stripe

        Returns:
            dict: Resultado do processamento
        """
        try:
            stripe_subscription_id = subscription['id']
            stripe_status = subscription['status']

            user_subscription = UserSubscription.objects.filter(
                stripe_subscription_id=stripe_subscription_id
            ).first()

            if user_subscription:
                # Mapear status do Stripe para nosso modelo
                if stripe_status == 'active':
                    user_subscription.status = 'active'
                elif stripe_status in ['canceled', 'incomplete_expired']:
                    user_subscription.status = 'cancelled'
                    if not user_subscription.end_date:
                        user_subscription.end_date = timezone.now()

                user_subscription.save()

                return {
                    'status': 'success',
                    'message': 'Assinatura atualizada com sucesso',
                    'subscription_id': user_subscription.id,
                    'new_status': user_subscription.status
                }
            else:
                return {
                    'status': 'ignored',
                    'message': 'Assinatura não encontrada'
                }

        except Exception as e:
            raise ValidationError(f'Erro ao atualizar assinatura: {str(e)}')

    def _handle_payment_succeeded(self, invoice):
        """
        Processa pagamento de fatura bem-sucedido

        Args:
            invoice: Dados da fatura

        Returns:
            dict: Resultado do processamento
        """
        # Para assinaturas recorrentes, pode ser útil registrar pagamentos bem-sucedidos
        subscription_id = invoice.get('subscription')
        if subscription_id:
            return {
                'status': 'success',
                'message': 'Pagamento de assinatura processado',
                'stripe_subscription_id': subscription_id
            }
        return {'status': 'ignored', 'message': 'Fatura não relacionada a assinatura'}

    def _handle_payment_failed(self, invoice):
        """
        Processa falha no pagamento de fatura

        Args:
            invoice: Dados da fatura

        Returns:
            dict: Resultado do processamento
        """
        subscription_id = invoice.get('subscription')
        if subscription_id:
            # Pode marcar assinatura como com problemas de pagamento
            return {
                'status': 'warning',
                'message': 'Falha no pagamento da assinatura',
                'stripe_subscription_id': subscription_id
            }
        return {'status': 'ignored', 'message': 'Fatura não relacionada a assinatura'}

    def _get_user_id_from_customer(self, customer_id):
        """
        Busca user_id pelo customer_id do Stripe

        Args:
            customer_id: ID do customer no Stripe

        Returns:
            str: ID do usuário

        Raises:
            ValidationError: Se usuário não for encontrado
        """
        try:
            customer = stripe.Customer.retrieve(customer_id)
            customer_email = customer.get('email')

            if not customer_email:
                raise ValidationError(
                    f'Customer {customer_id} não tem email associado')

            User = get_user_model()
            user = User.objects.get(email=customer_email)
            return str(user.id)

        except User.DoesNotExist:
            raise ValidationError(
                f'Usuário não encontrado com email: {customer_email}')
        except stripe.error.StripeError as e:
            raise ValidationError(
                f'Erro ao buscar customer no Stripe: {str(e)}')

    def _calculate_end_date(self, interval):
        """
        Calcula data de fim baseada no intervalo

        Args:
            interval: Intervalo da assinatura

        Returns:
            datetime or None: Data de fim (None para lifetime)
        """
        if interval == 'monthly':
            return timezone.now() + timezone.timedelta(days=30)
        elif interval == 'quarterly':
            return timezone.now() + timezone.timedelta(days=90)
        elif interval == 'semester':
            return timezone.now() + timezone.timedelta(days=180)
        elif interval == 'yearly':
            return timezone.now() + timezone.timedelta(days=365)
        # Lifetime: retorna None
        return None
