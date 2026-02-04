from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from ..models import (
    CreditTransaction,
    UserCredits,
    UserSubscription,
    UserSubscriptionStatus,
)

User = get_user_model()


class CreditService:
    """
    Service para gerenciar operações de créditos dos usuários com sistema misto de assinatura + créditos
    """

    @staticmethod
    def set_user_credits(user, amount):
        """
        Sets the user's credit balance to a specific amount.

        Args:
            user: The user instance
            amount: The amount to set (integer or float)

        Returns:
            None

        Raises:
            ValidationError: If amount is invalid or user has no credit record
        """
        from ..models import UserCredits  # Assuming UserCredit is the model for credits

        try:
            # Get or create the user's credit record
            user_credit, created = UserCredits.objects.get_or_create(
                user=user,
                defaults={'balance': 0}
            )

            # Validate amount
            if amount < 0:
                raise ValidationError("Credit amount cannot be negative")

            # Set the balance
            user_credit.balance = amount
            user_credit.save()

            print(f"[CREDIT DEBUG] Set credits to {amount} for user {user.id}")

        except Exception as e:
            raise ValidationError(f"Error setting user credits: {str(e)}")

    @staticmethod
    def validate_user_subscription(user) -> bool:
        """
        Valida se o usuário possui uma assinatura ativa

        Args:
            user: Usuário a ser validado

        Returns:
            bool: True se possui assinatura ativa, False caso contrário
        """
        try:
            # Verifica se há assinatura ativa
            active_subscription = UserSubscription.objects.filter(
                user=user,
                status='active'
            ).first()

            if not active_subscription:
                return False

            # Para assinaturas com data de fim (não lifetime), verifica se não expirou
            if active_subscription.end_date and active_subscription.end_date < timezone.now():
                # Marca como expirada
                active_subscription.status = 'expired'
                active_subscription.save()
                return False

            # Atualiza o status do usuário
            status, created = UserSubscriptionStatus.objects.get_or_create(
                user=user,
                defaults={
                    'has_active_subscription': True,
                    'current_subscription': active_subscription
                }
            )

            if not created:
                status.has_active_subscription = True
                status.current_subscription = active_subscription
                status.save()

            return True

        except Exception:
            return False

    @staticmethod
    def check_and_reset_monthly_credits(user):
        """
        Verifica e redefine os créditos baseado no ciclo do plano de assinatura

        Args:
            user: Usuário a ter os créditos verificados

        Note:
            - Monthly/Lifetime: Reset todo mês
            - Quarterly: Reset a cada 3 meses  
            - Semester: Reset a cada 6 meses
            - Yearly: Reset a cada 12 meses
        """
        try:
            # Avoid recursion by getting the credits directly
            credits, created = UserCredits.objects.get_or_create(
                user=user,
                defaults={'balance': Decimal('0.00')}
            )

            # Obtém a assinatura ativa
            active_subscription = UserSubscription.objects.filter(
                user=user,
                status='active'
            ).first()

            if not active_subscription:
                return  # Sem assinatura, não há créditos mensais

            current_time = timezone.now()

            # Verifica se precisa resetar (primeiro do mês ou nunca resetou)
            should_reset = False

            if not credits.last_credit_reset:
                should_reset = True
            else:
                # Verifica se precisa resetar baseado no intervalo do plano
                last_reset = credits.last_credit_reset
                should_reset = CreditService._should_reset_based_on_plan_interval(
                    active_subscription.plan.interval,
                    last_reset,
                    current_time
                )

            if should_reset:
                # Reset dos créditos mensais
                monthly_credits = active_subscription.plan.monthly_credits

                # Remove créditos mensais não utilizados do mês anterior
                unused_monthly = credits.monthly_credits_allocated - credits.monthly_credits_used
                if unused_monthly > 0:
                    credits.balance -= unused_monthly

                # Adiciona novos créditos mensais
                credits.balance += monthly_credits
                credits.monthly_credits_allocated = monthly_credits
                credits.monthly_credits_used = Decimal('0.00')
                credits.last_credit_reset = current_time
                credits.save()

                # Registra a transação de alocação mensal
                CreditTransaction.objects.create(
                    user=user,
                    amount=monthly_credits,
                    transaction_type='monthly_allocation',
                    description=f"Alocação mensal de créditos - {active_subscription.plan.name}"
                )

        except Exception as e:
            print(f"Erro ao resetar créditos mensais: {str(e)}")

    @staticmethod
    def _should_reset_based_on_plan_interval(plan_interval, last_reset, current_time):
        """
        Determina se os créditos devem ser resetados baseado no intervalo do plano

        Args:
            plan_interval: Intervalo do plano ('monthly', 'quarterly', 'semester', 'yearly', 'lifetime')
            last_reset: Data do último reset
            current_time: Tempo atual

        Returns:
            bool: True se deve resetar, False caso contrário
        """
        if plan_interval == 'monthly' or plan_interval == 'lifetime':
            # Reset mensal
            return (current_time.year != last_reset.year or
                    current_time.month != last_reset.month)

        elif plan_interval == 'quarterly':
            # Reset a cada 3 meses
            months_diff = (current_time.year - last_reset.year) * \
                12 + (current_time.month - last_reset.month)
            return months_diff >= 3

        elif plan_interval == 'semester':
            # Reset a cada 6 meses
            months_diff = (current_time.year - last_reset.year) * \
                12 + (current_time.month - last_reset.month)
            return months_diff >= 6

        elif plan_interval == 'yearly':
            # Reset anual - verifica se passou um ano completo
            months_diff = (current_time.year - last_reset.year) * \
                12 + (current_time.month - last_reset.month)
            return months_diff >= 12

        # Default: reset mensal para casos não cobertos
        return (current_time.year != last_reset.year or
                current_time.month != last_reset.month)

    @staticmethod
    def get_or_create_user_credits(user):
        """
        Obtém ou cria o registro de créditos para um usuário
        """
        credits, created = UserCredits.objects.get_or_create(
            user=user,
            defaults={'balance': Decimal('0.00')}
        )

        return credits

    @staticmethod
    def get_user_balance(user):
        """
        Obtém o saldo atual de créditos do usuário
        """
        credits = CreditService.get_or_create_user_credits(user)
        return float(credits.balance)

    @staticmethod
    def has_sufficient_credits(user, required_amount):
        """
        Verifica se o usuário possui créditos suficientes E assinatura ativa
        """
        # Primeiro valida se tem assinatura ativa
        if not CreditService.validate_user_subscription(user):
            return False

        # Check and reset monthly credits if needed
        CreditService.check_and_reset_monthly_credits(user)

        balance = CreditService.get_user_balance(user)
        return balance >= Decimal(str(required_amount))

    @staticmethod
    @transaction.atomic
    def add_credits(user, amount, transaction_type='purchase',
                    ai_model=None, description='', stripe_payment_intent_id=None):
        """
        Adiciona créditos ao usuário de forma atômica

        Args:
            user: Usuário que receberá os créditos
            amount: Quantidade de créditos a adicionar
            transaction_type: Tipo da transação
            ai_model: Modelo de IA relacionado (se aplicável)
            description: Descrição da transação
            stripe_payment_intent_id: ID do pagamento Stripe (se aplicável)
        """
        if amount <= 0:
            raise ValidationError(
                "A quantidade de créditos deve ser maior que zero")

        # Obtém ou cria o registro de créditos
        user_credits = CreditService.get_or_create_user_credits(user)

        # Adiciona os créditos
        user_credits.balance += Decimal(str(amount))
        user_credits.save()

        # Registra a transação
        CreditTransaction.objects.create(
            user=user,
            amount=amount,
            transaction_type=transaction_type,
            ai_model=ai_model,
            description=description,
            stripe_payment_intent_id=stripe_payment_intent_id
        )

        return float(user_credits.balance)

    @staticmethod
    @transaction.atomic
    def deduct_credits_for_operation(user, operation_type: str, ai_model='', description=''):
        """
        Deduz créditos do usuário para uma operação específica usando preços fixos

        Args:
            user: Usuário que terá os créditos deduzidos
            operation_type: Tipo da operação ('text_generation' ou 'image_generation')
            ai_model: Modelo de IA utilizado (opcional)
            description: Descrição do uso

        Returns:
            bool: True se a dedução foi bem-sucedida, False caso contrário
        """
        # Valida a operação primeiro
        if not CreditService.validate_operation(user, operation_type):
            return False

        # Obtém o custo fixo
        amount = CreditService.get_operation_cost(operation_type)

        # Obtém o registro de créditos
        user_credits = CreditService.get_or_create_user_credits(user)

        # Deduz os créditos
        user_credits.balance -= amount

        # Atualiza uso mensal se for crédito mensal
        if user_credits.monthly_credits_allocated > 0:
            remaining_monthly = user_credits.monthly_credits_allocated - \
                user_credits.monthly_credits_used
            if remaining_monthly >= amount:
                user_credits.monthly_credits_used += amount

        user_credits.save()

        # Registra a transação
        CreditTransaction.objects.create(
            user=user,
            amount=-amount,  # Valor negativo para indicar dedução
            transaction_type='usage',
            operation_type=operation_type,
            ai_model=ai_model,
            description=description or f"Uso de {operation_type.replace('_', ' ')}"
        )

        return True

    @staticmethod
    @transaction.atomic
    def deduct_credits(user, amount, ai_model, description=''):
        """
        DEPRECATED: Use deduct_credits_for_operation() com tipos fixos.
        Mantido para compatibilidade com código existente.

        Deduz créditos do usuário de forma atômica

        Args:
            user: Usuário que terá os créditos deduzidos
            amount: Quantidade de créditos a deduzir
            ai_model: Modelo de IA utilizado
            description: Descrição do uso

        Returns:
            bool: True se a dedução foi bem-sucedida, False caso contrário
        """
        # Tenta determinar o tipo de operação baseado no modelo ou descrição
        operation_type = 'text_generation'  # Default
        if ('image' in ai_model.lower() or 'imagen' in ai_model.lower() or
                'image' in description.lower()):
            operation_type = 'image_generation'

        return CreditService.deduct_credits_for_operation(user, operation_type, ai_model, description)

    @staticmethod
    def validate_operation(user, operation_type: str) -> bool:
        """
        Valida se o usuário pode realizar uma operação específica

        Args:
            user: Usuário
            operation_type: Tipo da operação ('text_generation' ou 'image_generation')

        Returns:
            bool: True se pode realizar a operação, False caso contrário
        """
        # Primeiro valida assinatura
        if not CreditService.validate_user_subscription(user):
            raise ValidationError("Usuário não possui assinatura ativa")

        # Obtém o custo fixo da operação
        cost = CreditTransaction.get_fixed_price(operation_type)
        if cost == Decimal('0.00'):
            raise ValidationError(
                f"Tipo de operação '{operation_type}' não suportado")

        # Verifica se tem créditos suficientes
        return CreditService.has_sufficient_credits(user, cost)

    @staticmethod
    def get_operation_cost(operation_type: str) -> Decimal:
        """
        Retorna o custo fixo de uma operação

        Args:
            operation_type: Tipo da operação

        Returns:
            Decimal: Custo em créditos
        """
        return CreditTransaction.get_fixed_price(operation_type)

    @staticmethod
    def calculate_usage_cost(ai_model_name, estimated_tokens):
        """
        DEPRECATED: Mantido para compatibilidade. Use get_operation_cost() com tipos fixos.

        Calcula o custo estimado de uso de um modelo de IA

        Args:
            ai_model_name: Nome do modelo de IA
            estimated_tokens: Número estimado de tokens

        Returns:
            Decimal: Custo estimado em créditos
        """
        # Para compatibilidade, retorna preços fixos baseados no tipo de modelo
        if 'image' in ai_model_name.lower() or 'imagen' in ai_model_name.lower():
            return float(CreditTransaction.get_fixed_price('image_generation'))
        else:
            return float(CreditTransaction.get_fixed_price('text_generation'))

    @staticmethod
    def get_user_transactions(user, limit=None):
        """
        Obtém o histórico de transações do usuário

        Args:
            user: Usuário
            limit: Limite de transações a retornar

        Returns:
            QuerySet: Transações do usuário
        """
        transactions = CreditTransaction.objects.filter(user=user)
        if limit:
            transactions = transactions[:limit]
        return transactions

    @staticmethod
    def get_monthly_credit_status(user):
        """
        Obtém status dos créditos mensais do usuário

        Args:
            user: Usuário

        Returns:
            dict: Status dos créditos mensais
        """
        # Check and reset monthly credits first
        CreditService.check_and_reset_monthly_credits(user)

        # Then get the credits (avoiding recursion)
        credits, created = UserCredits.objects.get_or_create(
            user=user,
            defaults={'balance': Decimal('0.00')}
        )

        return {
            'monthly_allocated': float(credits.balance),
            'monthly_used': float(credits.monthly_credits_used),
            'monthly_remaining': float(credits.balance),
            'last_reset': credits.last_credit_reset.isoformat() if credits.last_credit_reset else None,
            'usage_percentage': float(
                (credits.monthly_credits_used /
                 credits.monthly_credits_allocated * 100)
                if credits.monthly_credits_allocated > 0 else 0
            )
        }

    @staticmethod
    def get_credit_usage_summary(user):
        """
        Obtém um resumo do uso de créditos do usuário

        Args:
            user: Usuário

        Returns:
            dict: Resumo do uso de créditos
        """
        transactions = CreditTransaction.objects.filter(user=user)

        total_purchased = sum(
            t.amount for t in transactions
            if t.transaction_type in ['purchase', 'monthly_allocation'] and t.amount > 0
        )

        total_used = abs(sum(
            t.amount for t in transactions
            if t.transaction_type == 'usage' and t.amount < 0
        ))

        current_balance = CreditService.get_user_balance(user)
        monthly_status = CreditService.get_monthly_credit_status(user)
        has_subscription = CreditService.validate_user_subscription(user)

        return {
            'total_purchased': float(total_purchased),
            'total_used': float(total_used),
            'current_balance': float(current_balance),
            'usage_percentage': float((total_used / total_purchased * 100) if total_purchased > 0 else 0),
            'has_active_subscription': has_subscription,
            'monthly_status': monthly_status,
            'fixed_prices': {
                'image_generation': float(CreditTransaction.get_fixed_price('image_generation')),
                'text_generation': float(CreditTransaction.get_fixed_price('text_generation'))
            }
        }

    @staticmethod
    def check_payment_status(user):
        """
        Verifica se usuário tem pagamentos pendentes
        
        Args:
            user: Usuário a ser verificado
        
        Returns:
            dict: Status do pagamento com detalhes
        """
        pending_sub = UserSubscription.objects.filter(
            user=user,
            payment_requires_action=True
        ).first()
        
        if pending_sub:
            time_pending = None
            if pending_sub.payment_pending_since:
                time_pending = timezone.now() - pending_sub.payment_pending_since
            
            return {
                'has_pending_payment': True,
                'subscription_id': pending_sub.id,
                'plan_name': pending_sub.plan.name,
                'status': pending_sub.status,
                'pending_since': pending_sub.payment_pending_since,
                'time_pending_minutes': int(time_pending.total_seconds() / 60) if time_pending else None,
                'last_error': pending_sub.last_payment_error,
                'can_use_system': False,
                'required_action': 'complete_payment'
            }
        
        return {
            'has_pending_payment': False,
            'can_use_system': True
        }
