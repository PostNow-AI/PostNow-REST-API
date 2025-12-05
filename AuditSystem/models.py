from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class AuditLog(models.Model):
    """Comprehensive audit log for all system operations"""

    # Operation categories
    OPERATION_CHOICES = [
        ('auth', 'Autenticação'),
        ('account', 'Gerenciamento de Conta'),
        ('profile', 'Perfil do Criador'),
        ('post', 'Operações de Post'),
        ('context', 'Geração de Contexto'),
        ('content', 'Geração de Conteúdo'),
        ('image', 'Geração de Imagem'),
        ('credit', 'Sistema de Créditos'),
        ('subscription', 'Sistema de Assinatura'),
        ('email', 'Operações de Email'),
        ('system', 'Operações do Sistema'),
    ]

    # Specific actions within categories
    ACTION_CHOICES = [
        # Authentication
        ('login', 'Login do Usuário'),
        ('logout', 'Logout do Usuário'),
        ('login_failed', 'Login Falhou'),

        # Account Management
        ('account_created', 'Conta Criada'),
        ('account_updated', 'Conta Atualizada'),
        ('account_deleted', 'Conta Excluída'),

        # Creator Profile
        ('profile_created', 'Perfil Criado'),
        ('profile_updated', 'Perfil Atualizado'),
        ('profile_deleted', 'Perfil Excluído'),

        # Post Operations
        ('post_created', 'Post Criado'),
        ('post_updated', 'Post Atualizado'),
        ('post_deleted', 'Post Excluído'),

        # Content Generation
        ('content_generated', 'Conteúdo Gerado'),
        ('image_generated', 'Imagem Gerada'),
        ('content_generation_failed', 'Geração de Conteúdo Falhou'),

        ('image_generation_failed', 'Geração de Imagem Falhou'),

        ('daily_generation_started', 'Geração Diária Iniciada'),
        ('daily_generation_completed', 'Geração Diária Concluída'),

        # Weekly Context Generation
        ('weekly_generation_started', 'Geração Semanal Iniciada'),
        ('weekly_generation_completed', 'Geração Semanal Concluída'),
        ('context_generated', 'Contexto Gerado'),
        ('context_generation_failed', 'Geração de Contexto Falhou'),
        ('weekly_context_email_sent', 'Email de Contexto Semanal Enviado'),
        ('weekly_context_email_failed', 'Falha no Email de Contexto Semanal'),

        # Credit System
        ('credit_purchased', 'Crédito Comprado'),
        ('credit_used', 'Crédito Usado'),
        ('credit_refunded', 'Crédito Reembolsado'),

        # Subscription System
        ('subscription_created', 'Assinatura Criada'),
        ('subscription_updated', 'Assinatura Atualizada'),
        ('subscription_cancelled', 'Assinatura Cancelada'),
        ('subscription_renewed', 'Assinatura Renovada'),
        ('subscription_expired', 'Assinatura Expirada'),

        # Email Operations
        ('email_sent', 'Email Enviado'),
        ('email_failed', 'Email Falhou'),
        ('email_bounced', 'Email Rejeitado'),

        # System Operations
        ('system_error', 'Erro do Sistema'),
        ('maintenance', 'Operação de Manutenção'),
    ]

    # Status for operations
    STATUS_CHOICES = [
        ('success', 'Sucesso'),
        ('failure', 'Falha'),
        ('pending', 'Pendente'),
        ('error', 'Erro'),
    ]

    # Core fields
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                             related_name='audit_logs', help_text="Usuário que realizou a ação")
    operation_category = models.CharField(max_length=20, choices=OPERATION_CHOICES,
                                          help_text="Categoria da operação")
    action = models.CharField(max_length=50, choices=ACTION_CHOICES,
                              help_text="Ação específica realizada")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='success',
                              help_text="Resultado da operação")

    # Contextual information
    resource_type = models.CharField(max_length=100, blank=True,
                                     help_text="Tipo de recurso afetado (ex.: 'Post', 'Profile')")
    resource_id = models.CharField(max_length=100, blank=True,
                                   help_text="ID do recurso afetado")
    ip_address = models.GenericIPAddressField(null=True, blank=True,
                                              help_text="Endereço IP da requisição")
    user_agent = models.TextField(blank=True, help_text="String do user agent")

    # Detailed information
    details = models.JSONField(default=dict, blank=True,
                               help_text="Detalhes adicionais sobre a operação")
    error_message = models.TextField(
        blank=True, help_text="Mensagem de erro se a operação falhou")

    # Metadata
    timestamp = models.DateTimeField(
        default=timezone.now, help_text="Quando a operação ocorreu")
    duration_ms = models.PositiveIntegerField(null=True, blank=True,
                                              help_text="Duração da operação em milissegundos")
    request_id = models.CharField(max_length=100, blank=True,
                                  help_text="Identificador único da requisição para rastreamento")

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['operation_category', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
            models.Index(fields=['status', 'timestamp']),
            models.Index(fields=['resource_type', 'resource_id']),
        ]

    def __str__(self):
        user_info = f"Usuário {self.user.username}" if self.user else "Anônimo"
        return f"{user_info} - {self.get_action_display()} - {self.status} em {self.timestamp}"


class DailyReport(models.Model):
    """Stores generated daily audit reports"""

    report_date = models.DateField(unique=True, help_text="Data do relatório")
    total_operations = models.PositiveIntegerField(default=0,
                                                   help_text="Número total de operações registradas")
    successful_operations = models.PositiveIntegerField(default=0,
                                                        help_text="Número de operações bem-sucedidas")
    failed_operations = models.PositiveIntegerField(default=0,
                                                    help_text="Número de operações com falha")

    # Operation counts by category
    auth_operations = models.PositiveIntegerField(
        default=0, help_text="Operações de autenticação")
    account_operations = models.PositiveIntegerField(
        default=0, help_text="Operações de conta")
    profile_operations = models.PositiveIntegerField(
        default=0, help_text="Operações de perfil")
    post_operations = models.PositiveIntegerField(
        default=0, help_text="Operações de post")
    content_operations = models.PositiveIntegerField(
        default=0, help_text="Operações de geração de conteúdo")
    credit_operations = models.PositiveIntegerField(
        default=0, help_text="Operações de crédito")
    subscription_operations = models.PositiveIntegerField(
        default=0, help_text="Operações de assinatura")
    email_operations = models.PositiveIntegerField(
        default=0, help_text="Operações de email")
    system_operations = models.PositiveIntegerField(
        default=0, help_text="Operações do sistema")

    # Content generation specific metrics
    content_generation_attempts = models.PositiveIntegerField(
        default=0,
        help_text="Tentativas de geração de conteúdo")
    content_generation_successes = models.PositiveIntegerField(
        default=0,
        help_text="Gerações de conteúdo bem-sucedidas")
    content_generation_failures = models.PositiveIntegerField(
        default=0,
        help_text="Gerações de conteúdo com falha")
    total_users_active = models.PositiveIntegerField(
        default=0,
        help_text="Número total de usuários ativos")
    automatic_expected_posts_amount = models.PositiveIntegerField(
        default=0,
        help_text="Número esperado de posts automáticos")
    actual_automatic_posts_amount = models.PositiveIntegerField(
        default=0,
        help_text="Número real de posts automáticos gerados")
    # Error summary
    top_errors = models.JSONField(default=list, blank=True,
                                  help_text="Erros mais comuns encontrados")

    # Report metadata
    generated_at = models.DateTimeField(default=timezone.now,
                                        help_text="Quando o relatório foi gerado")
    report_data = models.JSONField(default=dict, blank=True,
                                   help_text="Dados completos do relatório para geração de email")

    class Meta:
        ordering = ['-report_date']

    def __str__(self):
        return f"Relatório Diário para {self.report_date} - {self.total_operations} operações"
