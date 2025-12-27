"""
Models para o sistema de Campanhas de Marketing.
"""

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class CampaignType(models.TextChoices):
    BRANDING = 'branding', 'Branding e Posicionamento'
    SALES = 'sales', 'Campanha de Vendas'
    LAUNCH = 'launch', 'Lançamento de Produto/Serviço'
    EDUCATION = 'education', 'Educação de Mercado'
    ENGAGEMENT = 'engagement', 'Engajamento'
    LEAD_GENERATION = 'lead_generation', 'Geração de Leads'
    PORTFOLIO = 'portfolio', 'Portfólio/Showcase'


class CampaignStatus(models.TextChoices):
    DRAFT = 'draft', 'Rascunho'
    PENDING_APPROVAL = 'pending_approval', 'Aguardando Aprovação'
    APPROVED = 'approved', 'Aprovado'
    ACTIVE = 'active', 'Ativo'
    COMPLETED = 'completed', 'Concluído'
    PAUSED = 'paused', 'Pausado'


class CampaignStructure(models.TextChoices):
    AIDA = 'aida', 'AIDA (Atenção-Interesse-Desejo-Ação)'
    PAS = 'pas', 'PAS (Problem-Agitate-Solve)'
    FUNIL = 'funil', 'Funil de Conteúdo'
    BAB = 'bab', 'Before-After-Bridge'
    STORYTELLING = 'storytelling', 'Jornada do Herói'
    SIMPLE = 'simple', 'Sequência Simples'


class Campaign(models.Model):
    """
    Campanha publicitária completa.
    Uma campanha é uma sequência organizada de posts para atingir objetivo específico.
    """
    
    # Relacionamento
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='campaigns'
    )
    
    # Informações Básicas
    name = models.CharField(
        max_length=200,
        help_text="Nome da campanha"
    )
    type = models.CharField(
        max_length=50,
        choices=CampaignType.choices,
        help_text="Tipo de campanha"
    )
    objective = models.TextField(
        help_text="Objetivo macro da campanha (detalhado pelo usuário)"
    )
    main_message = models.TextField(
        help_text="Mensagem principal a comunicar",
        blank=True,
        default=""
    )
    
    # Estrutura e Configuração
    structure = models.CharField(
        max_length=50,
        choices=CampaignStructure.choices,
        default=CampaignStructure.SIMPLE,
        help_text="Framework narrativo da campanha"
    )
    duration_days = models.IntegerField(
        default=14,
        help_text="Duração total da campanha em dias"
    )
    post_count = models.IntegerField(
        default=8,
        help_text="Quantidade total de posts"
    )
    post_frequency = models.IntegerField(
        default=3,
        help_text="Posts por semana"
    )
    
    # Datas
    start_date = models.DateField(
        null=True,
        blank=True,
        help_text="Data de início (opcional)"
    )
    end_date = models.DateField(
        null=True,
        blank=True,
        help_text="Data de término (opcional)"
    )
    
    # Configurações Visuais
    visual_styles = models.JSONField(
        default=list,
        blank=True,
        help_text="Lista de estilos visuais escolhidos (ex: ['minimal', 'corporate'])"
    )
    content_mix = models.JSONField(
        default=dict,
        blank=True,
        help_text="Mix de tipos de conteúdo (ex: {'feed': 0.5, 'reel': 0.3, 'story': 0.2})"
    )
    
    # Contexto Adicional
    briefing_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Dados completos do briefing (cases, depoimentos, materiais, etc)"
    )
    generation_context = models.JSONField(
        default=dict,
        blank=True,
        help_text="Contexto usado na geração (para reprodução/debug)"
    )
    
    # Status e Aprovação
    status = models.CharField(
        max_length=20,
        choices=CampaignStatus.choices,
        default=CampaignStatus.DRAFT
    )
    
    # Geração Automática
    is_auto_generated = models.BooleanField(
        default=False,
        help_text="Indica se foi gerada automaticamente (modo rápido)"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'campaigns'
        verbose_name = 'Campanha'
        verbose_name_plural = 'Campanhas'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['type']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.get_type_display()}"
    
    @property
    def posts_approved_count(self):
        """Retorna quantidade de posts aprovados."""
        return self.campaign_posts.filter(is_approved=True).count()
    
    @property
    def is_fully_approved(self):
        """Verifica se todos os posts foram aprovados."""
        total = self.campaign_posts.count()
        if total == 0:
            return False
        return self.posts_approved_count == total


class CampaignPost(models.Model):
    """
    Post individual dentro de uma campanha.
    Relaciona uma campanha com um Post do IdeaBank (reutilização).
    """
    
    campaign = models.ForeignKey(
        Campaign,
        on_delete=models.CASCADE,
        related_name='campaign_posts'
    )
    post = models.ForeignKey(
        'IdeaBank.Post',
        on_delete=models.CASCADE,
        related_name='campaigns'
    )
    
    # Posição e Agendamento
    sequence_order = models.IntegerField(
        help_text="Ordem sequencial na campanha (1, 2, 3...)"
    )
    scheduled_date = models.DateField(
        help_text="Data planejada de publicação"
    )
    scheduled_time = models.TimeField(
        default='09:00:00',
        help_text="Horário planejado"
    )
    
    # Contexto da Campanha
    phase = models.CharField(
        max_length=50,
        blank=True,
        help_text="Fase da campanha (ex: 'awareness', 'interest', 'desire', 'action' para AIDA)"
    )
    theme = models.CharField(
        max_length=200,
        blank=True,
        help_text="Tema específico deste post na campanha"
    )
    
    # Estilo Visual
    visual_style = models.CharField(
        max_length=50,
        blank=True,
        help_text="Estilo visual aplicado neste post"
    )
    
    # Status de Aprovação
    is_approved = models.BooleanField(
        default=False,
        help_text="Post foi aprovado pelo usuário"
    )
    approved_at = models.DateTimeField(
        null=True,
        blank=True
    )
    
    # Publicação
    is_published = models.BooleanField(
        default=False,
        help_text="Post foi publicado"
    )
    published_at = models.DateTimeField(
        null=True,
        blank=True
    )
    instagram_media_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="ID do post no Instagram (se publicado)"
    )
    instagram_container_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="ID do container/rascunho no Instagram"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'campaign_posts'
        verbose_name = 'Post de Campanha'
        verbose_name_plural = 'Posts de Campanhas'
        ordering = ['campaign', 'sequence_order']
        unique_together = ['campaign', 'sequence_order']
        indexes = [
            models.Index(fields=['campaign', 'sequence_order']),
            models.Index(fields=['is_approved']),
            models.Index(fields=['scheduled_date']),
        ]
    
    def __str__(self):
        return f"{self.campaign.name} - Post {self.sequence_order}"
    
    def approve(self):
        """Aprova o post."""
        self.is_approved = True
        self.approved_at = timezone.now()
        self.save()


class CampaignDraft(models.Model):
    """
    Rascunho de campanha em criação (auto-save).
    Permite usuário pausar e continuar depois sem perder progresso.
    """
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='campaign_drafts'
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        default='in_progress',
        choices=[
            ('in_progress', 'Em Progresso'),
            ('completed', 'Concluída'),
            ('abandoned', 'Abandonada'),
        ]
    )
    
    # Fase Atual
    current_phase = models.CharField(
        max_length=50,
        help_text="Fase atual do wizard (briefing, structure, styles, generation, approval)"
    )
    
    # Estado Salvo (Progressive)
    briefing_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Dados do briefing (objetivo, mensagem, casos, etc)"
    )
    structure_chosen = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Estrutura narrativa escolhida"
    )
    styles_chosen = models.JSONField(
        default=list,
        blank=True,
        help_text="Estilos visuais selecionados"
    )
    duration_days = models.IntegerField(
        null=True,
        blank=True
    )
    post_count = models.IntegerField(
        null=True,
        blank=True
    )
    
    # Posts gerados (se já avançou até geração)
    posts_data = models.JSONField(
        default=list,
        blank=True,
        help_text="Dados dos posts já gerados (se aplicável)"
    )
    
    # Campanha final (se completou)
    completed_campaign = models.ForeignKey(
        Campaign,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='draft_origin'
    )
    
    # Tracking
    total_time_spent = models.IntegerField(
        default=0,
        help_text="Tempo total gasto em segundos"
    )
    interaction_count = models.IntegerField(
        default=0,
        help_text="Número de interações/cliques"
    )
    hesitation_count = models.IntegerField(
        default=0,
        help_text="Número de hesitações detectadas"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'campaign_drafts'
        verbose_name = 'Rascunho de Campanha'
        verbose_name_plural = 'Rascunhos de Campanhas'
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['user', '-updated_at']),
            models.Index(fields=['status']),
            models.Index(fields=['current_phase']),
        ]
    
    def __str__(self):
        return f"Draft de {self.user.username} - {self.current_phase}"


class VisualStyle(models.Model):
    """
    Estilos visuais disponíveis para campanhas.
    Biblioteca curada de estilos que podem ser aplicados nas imagens.
    """
    
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Nome do estilo (ex: 'Minimal Clean', 'Corporate Blue')"
    )
    slug = models.SlugField(
        unique=True,
        help_text="Slug para identificação (ex: 'minimal_clean')"
    )
    
    category = models.CharField(
        max_length=50,
        choices=[
            ('minimal', 'Minimalista'),
            ('bold', 'Bold & Colorful'),
            ('corporate', 'Corporativo'),
            ('creative', 'Criativo/Artístico'),
            ('modern', 'Moderno'),
            ('professional', 'Profissional'),
        ],
        help_text="Categoria do estilo"
    )
    
    description = models.TextField(
        help_text="Descrição do estilo"
    )
    
    tags = models.JSONField(
        default=list,
        blank=True,
        help_text="Tags para busca (ex: ['profissional', 'moderno', 'clean'])"
    )
    
    # Performance por Nicho
    success_rate_by_niche = models.JSONField(
        default=dict,
        blank=True,
        help_text="Taxa de sucesso por nicho (ex: {'legal': 0.84, 'health': 0.76})"
    )
    global_success_rate = models.FloatField(
        default=0.75,
        help_text="Taxa de sucesso geral (0.0 a 1.0)"
    )
    
    # Configuração Técnica (para geração de imagem)
    image_prompt_modifiers = models.JSONField(
        default=list,
        blank=True,
        help_text="Modificadores do prompt de imagem (ex: ['high contrast', 'minimalist'])"
    )
    
    # Exemplo Visual
    preview_image_url = models.URLField(
        blank=True,
        null=True,
        help_text="URL de exemplo visual do estilo"
    )
    
    # Melhor Para
    best_for_campaign_types = models.JSONField(
        default=list,
        blank=True,
        help_text="Tipos de campanha ideais (ex: ['branding', 'education'])"
    )
    best_for_niches = models.JSONField(
        default=list,
        blank=True,
        help_text="Nichos ideais (ex: ['legal', 'consulting'])"
    )
    
    # Status
    is_active = models.BooleanField(
        default=True,
        help_text="Estilo está ativo e disponível"
    )
    
    # Ordenação (para curadoria)
    sort_order = models.IntegerField(
        default=0,
        help_text="Ordem de exibição (menor = aparece primeiro)"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'visual_styles'
        verbose_name = 'Estilo Visual'
        verbose_name_plural = 'Estilos Visuais'
        ordering = ['sort_order', 'name']
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['is_active']),
            models.Index(fields=['sort_order']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.category})"


class CampaignTemplate(models.Model):
    """
    Template salvo de campanha bem-sucedida.
    Permite usuário reutilizar estruturas que funcionaram.
    """
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='campaign_templates'
    )
    
    name = models.CharField(
        max_length=200,
        help_text="Nome do template"
    )
    description = models.TextField(
        blank=True,
        help_text="Descrição opcional"
    )
    
    # Configuração Completa
    campaign_type = models.CharField(max_length=50, choices=CampaignType.choices)
    structure = models.CharField(max_length=50, choices=CampaignStructure.choices)
    duration_days = models.IntegerField()
    post_count = models.IntegerField()
    post_frequency = models.IntegerField()
    
    visual_styles = models.JSONField(default=list)
    content_mix = models.JSONField(default=dict)
    
    # Distribuição de Fases (se aplicável - AIDA/PAS/Funil)
    phase_distribution = models.JSONField(
        default=dict,
        blank=True,
        help_text="Distribuição personalizada de fases (ex: {'awareness': 0.3, 'interest': 0.25, ...})"
    )
    
    # Mapeamento de Estilos (se usuário configurou manualmente)
    style_mapping = models.JSONField(
        default=dict,
        blank=True,
        help_text="Mapeamento de estilos por post (ex: {'1': 'minimal', '2': 'corporate'})"
    )
    
    # Métricas Históricas
    created_from_campaign = models.ForeignKey(
        Campaign,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='templates_generated'
    )
    success_rate = models.FloatField(
        default=0.0,
        help_text="Taxa de aprovação da campanha original (0.0 a 1.0)"
    )
    times_used = models.IntegerField(
        default=0,
        help_text="Quantas vezes este template foi usado"
    )
    avg_approval_rate = models.FloatField(
        default=0.0,
        help_text="Taxa média de aprovação quando template é usado"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'campaign_templates'
        verbose_name = 'Template de Campanha'
        verbose_name_plural = 'Templates de Campanhas'
        ordering = ['-times_used', '-created_at']
        indexes = [
            models.Index(fields=['user', '-times_used']),
            models.Index(fields=['campaign_type']),
        ]
    
    def __str__(self):
        return f"{self.name} (usado {self.times_used}x)"
    
    def increment_usage(self):
        """Incrementa contador de uso."""
        self.times_used += 1
        self.save(update_fields=['times_used'])


class CampaignJourneyEvent(models.Model):
    """
    Eventos da jornada do usuário criando campanha.
    Para análise de abandono e otimização de UX.
    """
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    campaign_draft = models.ForeignKey(
        CampaignDraft,
        on_delete=models.CASCADE,
        related_name='journey_events',
        null=True,
        blank=True
    )
    
    # Evento
    event_type = models.CharField(
        max_length=50,
        choices=[
            ('phase_entered', 'Entrou em Fase'),
            ('phase_completed', 'Completou Fase'),
            ('interaction', 'Interação'),
            ('hesitation', 'Hesitação'),
            ('error', 'Erro'),
        ]
    )
    phase = models.CharField(
        max_length=50,
        blank=True,
        help_text="Fase relacionada ao evento"
    )
    interaction_type = models.CharField(
        max_length=50,
        blank=True,
        help_text="Tipo de interação (click, edit, regenerate, etc)"
    )
    
    # Dados do Evento
    details = models.JSONField(
        default=dict,
        blank=True
    )
    duration = models.IntegerField(
        null=True,
        blank=True,
        help_text="Duração em segundos (para hesitações)"
    )
    
    # Metadata
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'campaign_journey_events'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['campaign_draft', 'timestamp']),
            models.Index(fields=['event_type']),
        ]
