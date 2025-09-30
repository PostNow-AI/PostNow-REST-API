from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models

User = get_user_model()


class SubscriptionPlan(models.Model):
    INTERVAL_CHOICES = [
        ('monthly', 'Mensal'),
        ('quarterly', 'Trimestral'),
        ('semester', 'Semestral'),
        ('yearly', 'Anual'),
        ('lifetime', 'Vitalício'),
    ]
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, default="")
    interval = models.CharField(
        max_length=20, choices=INTERVAL_CHOICES, unique=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    stripe_price_id = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.get_interval_display()})"

    @property
    def interval_display(self):
        return dict(self.INTERVAL_CHOICES).get(self.interval, self.interval)


class UserSubscription(models.Model):
    STATUS_CHOICES = [
        ('active', 'Ativo'),
        ('cancelled', 'Cancelado'),
        ('expired', 'Expirado'),
    ]

    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(blank=True, null=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='active')
    stripe_subscription_id = models.CharField(
        max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.user} - {self.plan} ({self.status})"

    @property
    def status_display(self):
        return dict(self.STATUS_CHOICES).get(self.status, self.status)


class CreditPackage(models.Model):
    """
    Modelo para pacotes de créditos disponíveis para compra
    """
    name = models.CharField(max_length=100, verbose_name="Nome do Pacote")
    credits = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Quantidade de Créditos"
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Preço em Reais"
    )
    stripe_price_id = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="ID do Preço no Stripe"
    )
    is_active = models.BooleanField(default=True, verbose_name="Ativo")
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Data de Criação")
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name="Data de Atualização")

    class Meta:
        verbose_name = "Pacote de Créditos"
        verbose_name_plural = "Pacotes de Créditos"
        ordering = ['price']

    def __str__(self):
        return f"{self.name} - R$ {self.price} ({self.credits} créditos)"


class UserCredits(models.Model):
    """
    Modelo para saldo de créditos do usuário
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='credits',
        verbose_name="Usuário"
    )
    balance = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Saldo de Créditos"
    )
    last_updated = models.DateTimeField(
        auto_now=True, verbose_name="Última Atualização")

    class Meta:
        verbose_name = "Créditos do Usuário"
        verbose_name_plural = "Créditos dos Usuários"

    def __str__(self):
        return f"{self.user.username} - {self.balance} créditos"

    @property
    def has_credits(self):
        """Verifica se o usuário possui créditos disponíveis"""
        return self.balance > Decimal('0.00')


class CreditTransaction(models.Model):
    """
    Modelo para histórico de transações de créditos
    """
    TRANSACTION_TYPES = [
        ('purchase', 'Compra'),
        ('usage', 'Uso'),
        ('refund', 'Reembolso'),
        ('bonus', 'Bônus'),
        ('adjustment', 'Ajuste'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='credit_transactions',
        verbose_name="Usuário"
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Quantidade de Créditos"
    )
    transaction_type = models.CharField(
        max_length=20,
        choices=TRANSACTION_TYPES,
        verbose_name="Tipo de Transação"
    )
    ai_model = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name="Modelo de IA Utilizado"
    )
    description = models.TextField(verbose_name="Descrição")
    stripe_payment_intent_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="ID do Pagamento Stripe"
    )
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Data de Criação")

    class Meta:
        verbose_name = "Transação de Créditos"
        verbose_name_plural = "Transações de Créditos"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['transaction_type', 'created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.get_transaction_type_display()} - {self.amount} créditos"

    @classmethod
    def get_user_balance(cls, user):
        """Calcula o saldo atual de créditos do usuário"""
        from django.db.models import Sum

        purchases = cls.objects.filter(
            user=user,
            transaction_type__in=['purchase', 'bonus', 'refund', 'adjustment']
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        usage = cls.objects.filter(
            user=user,
            transaction_type='usage'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        return purchases - abs(usage)  # Usage amounts are typically negative


class AIModelPreferences(models.Model):
    """
    Modelo para preferências de IA do usuário
    """
    PROVIDER_CHOICES = [
        ('google', 'Google (Gemini)'),
        ('openai', 'OpenAI (GPT)'),
        ('anthropic', 'Anthropic (Claude)'),
        ('auto', 'Automático (Melhor custo-benefício)'),
    ]

    BUDGET_PREFERENCES = [
        ('economy', 'Economia (Sempre o mais barato)'),
        ('balanced', 'Balanceado (Custo-benefício)'),
        ('performance', 'Performance (Qualidade máxima)'),
        ('custom', 'Personalizado'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='ai_preferences',
        verbose_name="Usuário"
    )

    preferred_provider = models.CharField(
        max_length=20,
        choices=PROVIDER_CHOICES,
        default='auto',
        verbose_name="Provedor Preferido"
    )

    budget_preference = models.CharField(
        max_length=20,
        choices=BUDGET_PREFERENCES,
        default='balanced',
        verbose_name="Preferência de Orçamento"
    )

    max_cost_per_operation = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('500.00'),
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Custo Máximo por Operação (em créditos)"
    )

    preferred_models = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Modelos Preferidos por Categoria",
        help_text="{'text_generation': 'gpt-4o-mini', 'creative': 'claude-3-sonnet'}"
    )

    auto_select_cheapest = models.BooleanField(
        default=True,
        verbose_name="Selecionar Automaticamente o Mais Barato"
    )

    allow_fallback = models.BooleanField(
        default=True,
        verbose_name="Permitir Fallback para Modelos Alternativos"
    )

    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Data de Criação")
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name="Última Atualização")

    class Meta:
        verbose_name = "Preferências de IA"
        verbose_name_plural = "Preferências de IA"

    def __str__(self):
        return f"{self.user.username} - {self.get_preferred_provider_display()}"

    def get_preferred_model_for_operation(self, operation_type: str = 'text_generation') -> str:
        """Retorna o modelo preferido para um tipo específico de operação"""
        if self.preferred_models and operation_type in self.preferred_models:
            return self.preferred_models[operation_type]

        # Fallback baseado no provedor preferido e orçamento
        if self.preferred_provider == 'google':
            return 'gemini-2.5-flash' if self.budget_preference == 'economy' else 'gemini-2.5-pro'
        elif self.preferred_provider == 'openai':
            return 'gpt-4o-mini' if self.budget_preference == 'economy' else 'gpt-4o'
        elif self.preferred_provider == 'anthropic':
            return 'claude-3-haiku' if self.budget_preference == 'economy' else 'claude-3-sonnet'
        else:  # auto
            return 'gemini-1.5-flash'  # Default mais econômico


class AIModel(models.Model):
    """
    Modelo para configuração dos modelos de IA disponíveis
    """
    name = models.CharField(max_length=100, unique=True,
                            verbose_name="Nome do Modelo")
    provider = models.CharField(max_length=100, verbose_name="Provedor")
    cost_per_token = models.DecimalField(
        max_digits=10,
        decimal_places=6,
        validators=[MinValueValidator(Decimal('0.000001'))],
        verbose_name="Custo por Token"
    )
    # Image generation costs - per image generated
    cost_per_image = models.DecimalField(
        max_digits=10,
        decimal_places=6,
        default=Decimal('0.00'),
        verbose_name="Custo por Imagem"
    )
    supports_image_generation = models.BooleanField(
        default=False,
        verbose_name="Suporte para Geração de Imagem"
    )
    is_active = models.BooleanField(default=True, verbose_name="Ativo")
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Data de Criação")

    class Meta:
        verbose_name = "Modelo de IA"
        verbose_name_plural = "Modelos de IA"
        ordering = ['provider', 'name']

    def __str__(self):
        return f"{self.provider} - {self.name}"
