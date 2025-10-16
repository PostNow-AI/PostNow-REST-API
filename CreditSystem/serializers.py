from rest_framework import serializers

from .models import (
    AIModel,
    AIModelPreferences,
    CreditPackage,
    CreditTransaction,
    SubscriptionPlan,
    UserCredits,
    UserSubscription,
)


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    interval_display = serializers.CharField(read_only=True)

    class Meta:
        model = SubscriptionPlan
        fields = ['id', 'name', 'description', 'price', 'interval', 'interval_display',
                  'stripe_price_id', 'is_active', 'benefits']
        read_only_fields = ['id', 'interval_display']

    def to_representation(self, instance):
        """Convert price to float for JSON serialization"""
        data = super().to_representation(instance)
        if 'price' in data:
            data['price'] = float(instance.price)
        return data


class UserSubscriptionSerializer(serializers.ModelSerializer):
    plan = SubscriptionPlanSerializer(read_only=True)
    status_display = serializers.CharField(read_only=True)

    class Meta:
        model = UserSubscription
        fields = ['id', 'user', 'plan', 'start_date', 'end_date', 'status',
                  'status_display', 'stripe_subscription_id']
        read_only_fields = ['id', 'status_display']


class CreditPackageSerializer(serializers.ModelSerializer):
    """Serializer para pacotes de créditos"""

    class Meta:
        model = CreditPackage
        fields = ['id', 'name', 'credits', 'price', 'is_active']
        read_only_fields = ['id']

    def to_representation(self, instance):
        """Converte a representação para garantir tipos corretos"""
        data = super().to_representation(instance)
        # Garante que credits e price sejam sempre números
        if 'credits' in data:
            data['credits'] = float(instance.credits)
        if 'price' in data:
            data['price'] = float(instance.price)
        return data


class UserCreditsSerializer(serializers.ModelSerializer):
    """Serializer para saldo de créditos do usuário"""
    username = serializers.CharField(source='user.username', read_only=True)
    has_credits = serializers.BooleanField(read_only=True)

    class Meta:
        model = UserCredits
        fields = ['id', 'username', 'balance', 'has_credits', 'last_updated']
        read_only_fields = ['id', 'username', 'has_credits', 'last_updated']

    def to_representation(self, instance):
        """Converte a representação para garantir tipos corretos"""
        data = super().to_representation(instance)
        # Garante que balance seja sempre um número
        if 'balance' in data:
            data['balance'] = float(instance.balance)
        return data


class CreditTransactionSerializer(serializers.ModelSerializer):
    """Serializer para transações de créditos"""
    username = serializers.CharField(source='user.username', read_only=True)
    transaction_type_display = serializers.CharField(
        source='get_transaction_type_display',
        read_only=True
    )

    class Meta:
        model = CreditTransaction
        fields = [
            'id', 'username', 'amount', 'transaction_type',
            'transaction_type_display', 'ai_model', 'description',
            'created_at'
        ]
        read_only_fields = ['id', 'username',
                            'transaction_type_display', 'created_at']

    def to_representation(self, instance):
        """Converte a representação para garantir tipos corretos"""
        data = super().to_representation(instance)
        # Garante que amount seja sempre um número
        if 'amount' in data:
            data['amount'] = float(instance.amount)
        return data


class AIModelSerializer(serializers.ModelSerializer):
    """Serializer para modelos de IA"""

    class Meta:
        model = AIModel
        fields = ['id', 'name', 'provider', 'cost_per_token', 'is_active']
        read_only_fields = ['id']

    def to_representation(self, instance):
        """Converte a representação para garantir tipos corretos"""
        data = super().to_representation(instance)
        # Garante que cost_per_token seja sempre um número
        if 'cost_per_token' in data:
            data['cost_per_token'] = float(instance.cost_per_token)
        return data


class PurchaseCreditsSerializer(serializers.Serializer):
    """Serializer para compra de créditos"""
    package_id = serializers.IntegerField()

    def validate_package_id(self, value):
        try:
            package = CreditPackage.objects.get(id=value, is_active=True)
            return value  # Return the ID value, not the object
        except CreditPackage.DoesNotExist:
            raise serializers.ValidationError(
                "Pacote de créditos não encontrado ou inativo")


class CreditUsageSerializer(serializers.Serializer):
    """Serializer para uso de créditos"""
    ai_model = serializers.CharField(max_length=50)
    estimated_tokens = serializers.IntegerField(min_value=1)
    description = serializers.CharField(max_length=500)

    def validate_ai_model(self, value):
        try:
            AIModel.objects.get(name=value, is_active=True)
            return value
        except AIModel.DoesNotExist:
            raise serializers.ValidationError(
                "Modelo de IA não encontrado ou inativo")
        return value


class StripeCheckoutSerializer(serializers.Serializer):
    """Serializer para checkout do Stripe"""
    package_id = serializers.IntegerField()
    success_url = serializers.URLField()
    cancel_url = serializers.URLField()

    def validate_package_id(self, value):
        try:
            CreditPackage.objects.get(id=value, is_active=True)
            return value  # Return the ID value, not the object
        except CreditPackage.DoesNotExist:
            raise serializers.ValidationError(
                "Pacote de créditos não encontrado ou inativo")


class AIModelPreferencesSerializer(serializers.ModelSerializer):
    """Serializer para preferências de modelos de IA do usuário"""

    class Meta:
        model = AIModelPreferences
        fields = [
            'id', 'preferred_provider', 'budget_preference', 'max_cost_per_operation',
            'preferred_models', 'auto_select_cheapest', 'allow_fallback',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def to_representation(self, instance):
        """Converte a representação para garantir tipos corretos"""
        data = super().to_representation(instance)
        # Garante que max_cost_per_operation seja sempre um número
        if 'max_cost_per_operation' in data:
            data['max_cost_per_operation'] = float(
                instance.max_cost_per_operation)
        return data


class ModelRecommendationSerializer(serializers.Serializer):
    """Serializer para recomendações de modelos"""
    operation_type = serializers.CharField(
        max_length=50,
        default='text_generation',
        help_text="Tipo de operação: text_generation, creative, analysis, etc."
    )
    estimated_tokens = serializers.IntegerField(
        min_value=1,
        default=1000,
        help_text="Número estimado de tokens para a operação"
    )
