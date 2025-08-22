from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models

User = get_user_model()


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
    is_active = models.BooleanField(default=True, verbose_name="Ativo")
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Data de Criação")

    class Meta:
        verbose_name = "Modelo de IA"
        verbose_name_plural = "Modelos de IA"
        ordering = ['provider', 'name']

    def __str__(self):
        return f"{self.provider} - {self.name}"
