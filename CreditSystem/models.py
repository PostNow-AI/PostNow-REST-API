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
        ('legacy', 'Plano Legado'),
    ]
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, default="")
    benefits = models.JSONField(default=list, blank=True)

    # e.g. ["Benefit 1", "Benefit 2", "Benefit 3"]
    interval = models.CharField(
        max_length=20, choices=INTERVAL_CHOICES, unique=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    stripe_price_id = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    # Credit system integration
    monthly_credits = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('30.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Créditos Mensais",
        help_text="Quantidade de créditos renovados a cada mês"
    )
    allow_credit_purchase = models.BooleanField(
        default=False,
        verbose_name="Permitir Compra de Créditos Extras",
        help_text="Se o usuário pode comprar créditos adicionais além do limite mensal"
    )

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
        ('pending_payment', 'Pagamento Pendente'),
    ]

    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(blank=True, null=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='active')
    stripe_subscription_id = models.CharField(
        max_length=100, blank=True, null=True)
    
    # Payment validation fields
    payment_requires_action = models.BooleanField(
        default=False,
        verbose_name="Pagamento Requer Ação",
        help_text="Indica se o pagamento está aguardando confirmação bancária (3D Secure, etc)"
    )
    payment_pending_since = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Pagamento Pendente Desde",
        help_text="Data/hora desde quando o pagamento está pendente"
    )
    last_payment_error = models.TextField(
        blank=True,
        null=True,
        verbose_name="Último Erro de Pagamento",
        help_text="Detalhes do último erro de pagamento"
    )

    def __str__(self):
        return f"{self.user} - {self.plan} ({self.status})"

    @property
    def status_display(self):
        return dict(self.STATUS_CHOICES).get(self.status, self.status)
    
    @property
    def has_valid_payment(self):
        """Verifica se o pagamento está válido (não requer ação)"""
        return not self.payment_requires_action and self.status == 'active'


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

    # Monthly credit allocation tracking
    monthly_credits_allocated = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Créditos Mensais Alocados",
        help_text="Créditos alocados no ciclo mensal atual"
    )
    monthly_credits_used = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Créditos Mensais Utilizados",
        help_text="Créditos utilizados no ciclo mensal atual"
    )
    last_credit_reset = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Último Reset de Créditos",
        help_text="Data do último reset dos créditos mensais"
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
        ('monthly_allocation', 'Alocação Mensal'),
        ('monthly_reset', 'Reset Mensal'),
    ]

    OPERATION_TYPES = [
        ('text_generation', 'Geração de Texto'),
        ('image_generation', 'Geração de Imagem'),
        ('other', 'Outro'),
    ]

    # Fixed pricing constants
    FIXED_PRICES = {
        'image_generation': Decimal('0.23'),
        'text_generation': Decimal('0.02'),
    }

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
    operation_type = models.CharField(
        max_length=20,
        choices=OPERATION_TYPES,
        null=True,
        blank=True,
        verbose_name="Tipo de Operação",
        help_text="Tipo específico da operação (geração de texto/imagem)"
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
    def get_fixed_price(cls, operation_type: str) -> Decimal:
        """Retorna o preço fixo para um tipo de operação"""
        return cls.FIXED_PRICES.get(operation_type, Decimal('0.00'))

    @classmethod
    def get_user_balance(cls, user):
        """Calcula o saldo atual de créditos do usuário"""
        from django.db.models import Sum

        purchases = cls.objects.filter(
            user=user,
            transaction_type__in=['purchase', 'bonus',
                                  'refund', 'adjustment', 'monthly_allocation']
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


class UserSubscriptionStatus(models.Model):
    """
    Modelo para rastrear o status atual da assinatura e créditos do usuário
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='subscription_status',
        verbose_name="Usuário"
    )
    has_active_subscription = models.BooleanField(
        default=False,
        verbose_name="Possui Assinatura Ativa"
    )
    current_subscription = models.ForeignKey(
        UserSubscription,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Assinatura Atual"
    )
    last_subscription_check = models.DateTimeField(
        auto_now=True,
        verbose_name="Última Verificação de Assinatura"
    )

    class Meta:
        verbose_name = "Status de Assinatura do Usuário"
        verbose_name_plural = "Status de Assinaturas dos Usuários"

    def __str__(self):
        return f"{self.user.username} - {'Ativo' if self.has_active_subscription else 'Inativo'}"


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
