from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction

from ..models import AIModel, CreditTransaction, UserCredits

User = get_user_model()


class CreditService:
    """
    Service para gerenciar operações de créditos dos usuários
    """

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
        Verifica se o usuário possui créditos suficientes
        """
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
    def deduct_credits(user, amount, ai_model, description=''):
        """
        Deduz créditos do usuário de forma atômica

        Args:
            user: Usuário que terá os créditos deduzidos
            amount: Quantidade de créditos a deduzir
            ai_model: Modelo de IA utilizado
            description: Descrição do uso

        Returns:
            bool: True se a dedução foi bem-sucedida, False caso contrário
        """
        if amount <= 0:
            raise ValidationError(
                "A quantidade de créditos deve ser maior que zero")

        # Verifica se há créditos suficientes
        if not CreditService.has_sufficient_credits(user, amount):
            return False

        # Obtém o registro de créditos
        user_credits = CreditService.get_or_create_user_credits(user)

        # Deduz os créditos
        user_credits.balance -= Decimal(str(amount))
        user_credits.save()

        # Registra a transação
        CreditTransaction.objects.create(
            user=user,
            amount=-amount,  # Valor negativo para indicar dedução
            transaction_type='usage',
            ai_model=ai_model,
            description=description
        )

        return True

    @staticmethod
    def calculate_usage_cost(ai_model_name, estimated_tokens):
        """
        Calcula o custo estimado de uso de um modelo de IA

        Args:
            ai_model_name: Nome do modelo de IA
            estimated_tokens: Número estimado de tokens

        Returns:
            Decimal: Custo estimado em créditos
        """
        try:
            ai_model = AIModel.objects.get(name=ai_model_name, is_active=True)
            cost = ai_model.cost_per_token * Decimal(str(estimated_tokens))
            # Arredonda para 6 casas decimais e converte para float
            return float(cost.quantize(Decimal('0.000001')))
        except AIModel.DoesNotExist:
            raise ValidationError(
                f"Modelo de IA '{ai_model_name}' não encontrado")

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
            if t.transaction_type == 'purchase' and t.amount > 0
        )

        total_used = abs(sum(
            t.amount for t in transactions
            if t.transaction_type == 'usage' and t.amount < 0
        ))

        current_balance = CreditService.get_user_balance(user)

        return {
            'total_purchased': float(total_purchased),
            'total_used': float(total_used),
            'current_balance': float(current_balance),
            'usage_percentage': float((total_used / total_purchased * 100) if total_purchased > 0 else 0)
        }
