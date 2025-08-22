import stripe
from django.conf import settings
from django.core.exceptions import ValidationError

from ..models import CreditPackage
from .credit_service import CreditService


class StripeService:
    """
    Service para integração com o Stripe para pagamentos
    """

    def __init__(self):
        """Inicializa o service com a chave do Stripe"""
        stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', None)
        if not stripe.api_key:
            raise ValidationError("STRIPE_SECRET_KEY não configurada")

    def create_checkout_session(self, package_id, success_url, cancel_url, user_email=None):
        """
        Cria uma sessão de checkout do Stripe

        Args:
            package_id: ID do pacote de créditos
            success_url: URL de sucesso
            cancel_url: URL de cancelamento
            user_email: Email do usuário (opcional)

        Returns:
            dict: Dados da sessão de checkout
        """
        try:
            package = CreditPackage.objects.get(id=package_id, is_active=True)
        except CreditPackage.DoesNotExist:
            raise ValidationError("Pacote de créditos não encontrado")

        # Configuração da sessão de checkout
        checkout_data = {
            'payment_method_types': ['card'],
            'line_items': [{
                'price_data': {
                    'currency': 'brl',
                    'product_data': {
                        'name': package.name,
                        'description': f'{package.credits} créditos para uso de IA'
                    },
                    # Converte para centavos
                    'unit_amount': int(float(package.price) * 100),
                },
                'quantity': 1,
            }],
            'mode': 'payment',
            'success_url': success_url,
            'cancel_url': cancel_url,
            'metadata': {
                'package_id': package_id,
                'credits': str(package.credits),
                'package_name': package.name
            }
        }

        # Adiciona email do usuário se fornecido
        if user_email:
            checkout_data['customer_email'] = user_email

        try:
            session = stripe.checkout.Session.create(**checkout_data)
            return {
                'session_id': session.id,
                'checkout_url': session.url,
                'package': {
                    'id': package.id,
                    'name': package.name,
                    'credits': package.credits,
                    'price': package.price
                }
            }
        except stripe.error.StripeError as e:
            raise ValidationError(
                f"Erro ao criar sessão de checkout: {str(e)}")

    def process_webhook(self, payload, sig_header):
        """
        Processa webhook do Stripe para confirmar pagamentos

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
        if event['type'] == 'checkout.session.completed':
            return self._handle_checkout_completed(event['data']['object'])
        elif event['type'] == 'payment_intent.succeeded':
            return self._handle_payment_succeeded(event['data']['object'])
        elif event['type'] == 'payment_intent.payment_failed':
            return self._handle_payment_failed(event['data']['object'])

        return {'status': 'ignored', 'event_type': event['type']}

    def _handle_checkout_completed(self, session):
        """
        Processa sessão de checkout completada

        Args:
            session: Dados da sessão do Stripe

        Returns:
            dict: Resultado do processamento
        """
        try:
            # Obtém os metadados da sessão
            metadata = session.get('metadata', {})
            package_id = metadata.get('package_id')
            credits = metadata.get('credits')
            customer_email = session.get('customer_details', {}).get('email')

            if not all([package_id, credits, customer_email]):
                raise ValidationError("Metadados incompletos na sessão")

            # Busca o usuário pelo email
            from django.contrib.auth import get_user_model
            User = get_user_model()

            try:
                user = User.objects.get(email=customer_email)
            except User.DoesNotExist:
                raise ValidationError(
                    f"Usuário não encontrado: {customer_email}")

            # Adiciona os créditos ao usuário
            amount = float(credits)
            new_balance = CreditService.add_credits(
                user=user,
                amount=amount,
                transaction_type='purchase',
                description=f"Compra de {credits} créditos via Stripe",
                stripe_payment_intent_id=session.get('payment_intent')
            )

            return {
                'status': 'success',
                'user_id': user.id,
                'credits_added': amount,
                'new_balance': new_balance,
                'session_id': session.id
            }

        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'session_id': session.id
            }

    def _handle_payment_succeeded(self, payment_intent):
        """
        Processa pagamento bem-sucedido

        Args:
            payment_intent: Dados do pagamento

        Returns:
            dict: Resultado do processamento
        """
        # Esta função pode ser usada para casos onde o webhook de checkout
        # não é suficiente ou para pagamentos recorrentes
        return {
            'status': 'success',
            'payment_intent_id': payment_intent.id,
            'amount': payment_intent.amount / 100  # Stripe usa centavos
        }

    def _handle_payment_failed(self, payment_intent):
        """
        Processa pagamento falhado

        Args:
            payment_intent: Dados do pagamento

        Returns:
            dict: Resultado do processamento
        """
        return {
            'status': 'failed',
            'payment_intent_id': payment_intent.id,
            'error': payment_intent.last_payment_error.get('message', 'Erro desconhecido') if payment_intent.last_payment_error else 'Erro desconhecido'
        }

    def get_payment_intent_status(self, payment_intent_id):
        """
        Obtém o status de um pagamento

        Args:
            payment_intent_id: ID do pagamento

        Returns:
            dict: Status do pagamento
        """
        try:
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            return {
                'id': payment_intent.id,
                'status': payment_intent.status,
                'amount': payment_intent.amount / 100,
                'currency': payment_intent.currency,
                'created': payment_intent.created
            }
        except stripe.error.StripeError as e:
            raise ValidationError(
                f"Erro ao obter status do pagamento: {str(e)}")
