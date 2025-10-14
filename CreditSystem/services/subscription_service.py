import stripe
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone

from ..models import SubscriptionPlan, UserSubscription
from .credit_service import CreditService


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

        # Log do evento recebido para debug
        if event.get('data', {}).get('object', {}).get('mode'):
            print(f"[WEBHOOK DEBUG] Modo: {event['data']['object']['mode']}")

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
        elif event['type'] == 'checkout.session.completed':
            return self._handle_checkout_session_completed(event['data']['object'])
        elif event['type'] == 'payment_intent.succeeded':
            return self._handle_payment_intent_succeeded(event['data']['object'])

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

            # Determina o status baseado no status do Stripe
            stripe_status = subscription.get('status', 'active')
            local_status = 'active'

            # Se está em trial, ainda considera como ativa (usuário tem acesso)
            if stripe_status in ['trialing', 'active']:
                local_status = 'active'
            elif stripe_status in ['incomplete', 'incomplete_expired', 'past_due']:
                local_status = 'cancelled'

            # Cria nova assinatura
            user_subscription = UserSubscription.objects.create(
                user=user,
                plan=plan,
                start_date=timezone.now(),
                end_date=end_date,
                status=local_status,
                stripe_subscription_id=stripe_subscription_id
            )

            # Trigger credit reset for new subscription
            try:
                CreditService.check_and_reset_monthly_credits(user)
                print(
                    f"[WEBHOOK DEBUG] Credits reset triggered for user {user.id} with new subscription")
            except Exception as e:
                print(
                    f"[WEBHOOK DEBUG] Error resetting credits for user {user.id}: {str(e)}")

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
                previous_status = user_subscription.status
                if stripe_status in ['trialing', 'active']:
                    user_subscription.status = 'active'
                elif stripe_status in ['canceled', 'incomplete_expired', 'past_due', 'unpaid']:
                    user_subscription.status = 'cancelled'
                    if not user_subscription.end_date:
                        user_subscription.end_date = timezone.now()

                user_subscription.save()

                # Trigger credit reset if subscription became active
                if previous_status != 'active' and user_subscription.status == 'active':
                    try:
                        CreditService.check_and_reset_monthly_credits(
                            user_subscription.user)
                        print(
                            f"[WEBHOOK DEBUG] Credits reset triggered for user {user_subscription.user.id} - subscription reactivated")
                    except Exception as e:
                        print(
                            f"[WEBHOOK DEBUG] Error resetting credits for user {user_subscription.user.id}: {str(e)}")

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
            # Trigger credit reset for subscription renewal
            try:
                user_subscription = UserSubscription.objects.filter(
                    stripe_subscription_id=subscription_id,
                    status='active'
                ).first()

                if user_subscription:
                    CreditService.check_and_reset_monthly_credits(
                        user_subscription.user)
                    print(
                        f"[WEBHOOK DEBUG] Credits reset triggered for user {user_subscription.user.id} - subscription payment succeeded")
            except Exception as e:
                print(
                    f"[WEBHOOK DEBUG] Error resetting credits for subscription {subscription_id}: {str(e)}")

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

    def _handle_checkout_session_completed(self, session):
        """
        Processa checkout session completada (para pagamentos únicos como lifetime)

        Args:
            session: Dados da sessão de checkout

        Returns:
            dict: Resultado do processamento
        """
        try:
            # Verifica se é modo 'payment' (lifetime) ou 'subscription'
            mode = session.get('mode')

            if mode == 'payment':
                # É um pagamento único (lifetime)
                return self._handle_lifetime_purchase(session)
            elif mode == 'subscription':
                # É uma assinatura recorrente - será processada em customer.subscription.created
                return {
                    'status': 'success',
                    'message': 'Checkout de assinatura completado - aguardando criação da assinatura'
                }
            else:
                return {
                    'status': 'ignored',
                    'message': f'Modo de checkout não reconhecido: {mode}'
                }

        except Exception as e:
            raise ValidationError(
                f'Erro ao processar checkout session: {str(e)}')

    def _handle_payment_intent_succeeded(self, payment_intent):
        """
        Processa payment intent bem-sucedido (backup para lifetime purchases)

        Args:
            payment_intent: Dados do payment intent

        Returns:
            dict: Resultado do processamento
        """
        try:
            # Verifica se temos charges associadas
            charges = payment_intent.get('charges', {}).get('data', [])
            if charges:

                # Se temos metadados no payment intent, processa como lifetime
                metadata = payment_intent.get('metadata', {})
                if metadata.get('user_id') and metadata.get('plan_id'):
                    return self._create_lifetime_subscription_from_metadata(metadata)

            return {
                'status': 'ignored',
                'message': 'Payment intent sem metadados de assinatura'
            }

        except Exception as e:
            raise ValidationError(
                f'Erro ao processar payment intent: {str(e)}')

    def _handle_lifetime_purchase(self, session):
        """
        Processa compra de assinatura lifetime

        Args:
            session: Dados da sessão de checkout

        Returns:
            dict: Resultado do processamento
        """
        try:
            user_id = None
            plan_id = None

            # Tenta obter metadados da sessão
            metadata = session.get('metadata', {})
            user_id = metadata.get('user_id')
            plan_id = metadata.get('plan_id')

            # Se metadados não estão disponíveis, tenta buscar por customer e line items
            if not user_id or not plan_id:
                customer_id = session.get('customer')
                line_items = session.get('line_items', {}).get('data', [])

                if customer_id:
                    user_id = self._get_user_id_from_customer(customer_id)

                if line_items:
                    price_id = line_items[0].get('price', {}).get('id')
                    if price_id:
                        try:
                            plan = SubscriptionPlan.objects.get(
                                stripe_price_id=price_id, is_active=True)
                            plan_id = str(plan.id)
                        except SubscriptionPlan.DoesNotExist:
                            raise ValidationError(
                                f'Plano não encontrado para price_id: {price_id}')

            # Se ainda não temos os dados, tenta buscar pela customer_email
            if not user_id:
                customer_details = session.get('customer_details', {})
                customer_email = customer_details.get('email')
                if customer_email:
                    User = get_user_model()
                    try:
                        user = User.objects.get(email=customer_email)
                        user_id = str(user.id)
                    except User.DoesNotExist:
                        raise ValidationError(
                            f'Usuário não encontrado com email: {customer_email}')

            if not user_id or not plan_id:
                raise ValidationError(
                    'Não foi possível determinar usuário ou plano da compra lifetime')

            return self._create_lifetime_subscription_from_metadata({
                'user_id': user_id,
                'plan_id': plan_id
            })

        except Exception as e:
            raise ValidationError(
                f'Erro ao processar compra lifetime: {str(e)}')

    def _create_lifetime_subscription_from_metadata(self, metadata):
        """
        Cria assinatura lifetime a partir dos metadados

        Args:
            metadata: Metadados com user_id e plan_id

        Returns:
            dict: Resultado do processamento
        """
        try:
            user_id = metadata.get('user_id')
            plan_id = metadata.get('plan_id')

            # Busca usuário e plano
            User = get_user_model()
            user = User.objects.get(id=user_id)
            plan = SubscriptionPlan.objects.get(id=plan_id, is_active=True)

            # Verifica se é realmente um plano lifetime
            if plan.interval != 'lifetime':
                return {
                    'status': 'warning',
                    'message': f'Tentativa de criar assinatura lifetime para plano {plan.interval}'
                }

            # Verifica se usuário já tem uma assinatura lifetime ativa
            existing_lifetime = UserSubscription.objects.filter(
                user=user,
                plan__interval='lifetime',
                status='active'
            ).first()

            if existing_lifetime:
                return {
                    'status': 'success',
                    'message': 'Usuário já possui assinatura lifetime ativa',
                    'subscription_id': existing_lifetime.id
                }

            # Cancela assinaturas ativas existentes (lifetime substitui tudo)
            UserSubscription.objects.filter(
                user=user, status='active'
            ).update(status='cancelled', end_date=timezone.now())

            # Cria nova assinatura lifetime
            user_subscription = UserSubscription.objects.create(
                user=user,
                plan=plan,
                start_date=timezone.now(),
                end_date=None,  # Lifetime não tem data de fim
                status='active',
                stripe_subscription_id=None  # Lifetime não tem subscription_id
            )

            # Trigger credit reset for new lifetime subscription
            try:
                CreditService.check_and_reset_monthly_credits(user)
                print(
                    f"[WEBHOOK DEBUG] Credits reset triggered for user {user.id} with new lifetime subscription")
            except Exception as e:
                print(
                    f"[WEBHOOK DEBUG] Error resetting credits for lifetime user {user.id}: {str(e)}")

            return {
                'status': 'success',
                'message': 'Assinatura lifetime criada com sucesso',
                'subscription_id': user_subscription.id,
                'user_id': user.id,
                'plan_name': plan.name
            }

        except User.DoesNotExist:
            raise ValidationError(f'Usuário não encontrado: {user_id}')
        except SubscriptionPlan.DoesNotExist:
            raise ValidationError(f'Plano não encontrado: {plan_id}')
        except Exception as e:
            raise ValidationError(
                f'Erro ao criar assinatura lifetime: {str(e)}')

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
