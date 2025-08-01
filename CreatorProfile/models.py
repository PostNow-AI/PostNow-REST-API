from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class CreatorProfile(models.Model):
    """
    Creator Profile model based on specification documents.
    Handles user qualification data for content creation personalization.
    """

    # PLATFORM CHOICES
    PLATFORM_CHOICES = [
        ('instagram', 'Instagram'),
        ('linkedin', 'LinkedIn'),
        ('youtube', 'YouTube'),
        ('tiktok', 'TikTok'),
        ('twitter', 'Twitter/X'),
    ]

    # EXPERIENCE LEVEL CHOICES
    EXPERIENCE_CHOICES = [
        ('beginner', 'Iniciante'),
        ('intermediate', 'Intermediário'),
        ('advanced', 'Avançado'),
    ]

    # PRIMARY GOAL CHOICES
    GOAL_CHOICES = [
        ('authority', 'Construir Autoridade'),
        ('leads', 'Gerar Leads'),
        ('education', 'Educar Audiência'),
        ('networking', 'Fazer Networking'),
        ('other', 'Outros'),
    ]

    # TIME AVAILABLE CHOICES
    TIME_CHOICES = [
        ('1-5', '1-5 horas'),
        ('6-15', '6-15 horas'),
        ('16+', '16+ horas'),
    ]

    # COMMUNICATION TONE CHOICES
    TONE_CHOICES = [
        ('formal', 'Formal'),
        ('casual', 'Casual'),
        ('educational', 'Educacional'),
        ('inspirational', 'Inspiracional'),
    ]

    # CONTENT DURATION CHOICES
    DURATION_CHOICES = [
        ('short', 'Conteúdo Curto'),
        ('medium', 'Conteúdo Médio'),
        ('long', 'Conteúdo Longo'),
    ]

    # COMPLEXITY LEVEL CHOICES
    COMPLEXITY_CHOICES = [
        ('basic', 'Básico'),
        ('intermediate', 'Intermediário'),
        ('advanced', 'Avançado'),
    ]

    # FREQUENCY CHOICES
    FREQUENCY_CHOICES = [
        ('daily', 'Diária'),
        ('weekly', 'Semanal'),
        ('monthly', 'Mensal'),
    ]

    # REVENUE STAGE CHOICES
    REVENUE_CHOICES = [
        ('starting', 'Começando'),
        ('growing', 'Crescendo'),
        ('scaling', 'Escalando'),
    ]

    # TEAM SIZE CHOICES
    TEAM_CHOICES = [
        ('solo', 'Solo'),
        ('small_team', 'Pequena Equipe'),
        ('company', 'Empresa'),
    ]

    # === REQUIRED FIELDS (7 total - 20% completeness) ===
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='creator_profile')

    # Campo 3: Plataforma principal - OBRIGATÓRIO
    main_platform = models.CharField(
        max_length=20,
        choices=PLATFORM_CHOICES,
        verbose_name="Plataforma Principal"
    )

    # Campo 4: Nicho de atuação - OBRIGATÓRIO
    niche = models.CharField(
        max_length=200,
        verbose_name="Nicho de Atuação",
        help_text="Ex: Marketing jurídico, Consultoria empresarial"
    )

    # Campo 5: Nível de experiência - OBRIGATÓRIO
    experience_level = models.CharField(
        max_length=20,
        choices=EXPERIENCE_CHOICES,
        verbose_name="Nível de Experiência"
    )

    # Campo 6: Objetivo principal - OBRIGATÓRIO
    primary_goal = models.CharField(
        max_length=20,
        choices=GOAL_CHOICES,
        verbose_name="Objetivo Principal"
    )

    # Campo 7: Tempo disponível - OBRIGATÓRIO
    time_available = models.CharField(
        max_length=10,
        choices=TIME_CHOICES,
        verbose_name="Tempo Disponível por Semana"
    )

    # === IMPORTANT FIELDS (Level 2 - Optional) ===

    # Contexto Profissional
    specific_profession = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="Profissão Específica",
        help_text="Ex: Advogado tributarista, Coach executivo"
    )

    target_audience = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="Público-alvo",
        help_text="Ex: Pequenas empresas, Pessoas físicas"
    )

    communication_tone = models.CharField(
        max_length=20,
        choices=TONE_CHOICES,
        blank=True,
        null=True,
        verbose_name="Tom de Comunicação"
    )

    expertise_areas = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Áreas de Expertise",
        help_text="Lista de áreas de especialização"
    )

    # Preferências de Conteúdo
    preferred_duration = models.CharField(
        max_length=20,
        choices=DURATION_CHOICES,
        blank=True,
        null=True,
        verbose_name="Duração Preferida"
    )

    complexity_level = models.CharField(
        max_length=20,
        choices=COMPLEXITY_CHOICES,
        blank=True,
        null=True,
        verbose_name="Nível de Complexidade"
    )

    theme_diversity = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        blank=True,
        null=True,
        verbose_name="Diversidade de Temas",
        help_text="Escala 0-10 (foco vs. variedade)"
    )

    publication_frequency = models.CharField(
        max_length=20,
        choices=FREQUENCY_CHOICES,
        blank=True,
        null=True,
        verbose_name="Frequência de Publicação"
    )

    # === OPTIONAL FIELDS (Level 3 - Maximum refinement) ===

    # Redes Sociais
    instagram_username = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Instagram Username"
    )

    linkedin_url = models.URLField(
        blank=True,
        null=True,
        verbose_name="LinkedIn Profile URL"
    )

    twitter_username = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Twitter/X Username"
    )

    tiktok_username = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="TikTok Username"
    )

    # Contexto de Negócio
    revenue_stage = models.CharField(
        max_length=20,
        choices=REVENUE_CHOICES,
        blank=True,
        null=True,
        verbose_name="Estágio de Receita"
    )

    team_size = models.CharField(
        max_length=20,
        choices=TEAM_CHOICES,
        blank=True,
        null=True,
        verbose_name="Tamanho da Equipe"
    )

    revenue_goal = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Meta de Receita",
        help_text="Ex: R$ 50k/mês"
    )

    authority_goal = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Meta de Autoridade",
        help_text="Ex: 1000+ conexões qualificadas"
    )

    leads_goal = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Meta de Leads",
        help_text="Ex: 2-3 leads/mês via conteúdo"
    )

    # Recursos Disponíveis
    has_designer = models.BooleanField(
        default=False,
        verbose_name="Tem Designer"
    )

    current_tools = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Ferramentas Atuais",
        help_text="Lista de ferramentas utilizadas"
    )

    tools_budget = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Orçamento para Ferramentas",
        help_text="Ex: R$ 200-500/mês"
    )

    preferred_hours = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Horários Preferenciais",
        help_text="Lista de horários preferenciais"
    )

    # === COMPLETION TRACKING ===

    # Controle de completude
    onboarding_completed = models.BooleanField(
        default=False,
        verbose_name="Onboarding Completado",
        help_text="Indica se os campos obrigatórios foram preenchidos"
    )

    completeness_percentage = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Percentual de Completude"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    onboarding_completed_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Data de Conclusão do Onboarding"
    )

    class Meta:
        verbose_name = "Perfil do Criador"
        verbose_name_plural = "Perfis dos Criadores"

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.niche}"

    def calculate_completeness(self):
        """
        Calculate profile completeness percentage based on filled fields.
        Counts all relevant profile fields dynamically.
        """
        filled_fields = 0

        # Helper function to check if field has meaningful value
        def is_field_filled(field_value):
            if field_value is None:
                return False
            if isinstance(field_value, str):
                return bool(field_value.strip())
            if isinstance(field_value, list):
                return len(field_value) > 0
            if isinstance(field_value, bool):
                return True  # Boolean fields are always considered "filled"
            return bool(field_value)

        # All profile fields (excluding metadata fields)
        profile_fields = [
            # Required fields
            self.main_platform,
            self.niche,
            self.experience_level,
            self.primary_goal,
            self.time_available,

            # Important fields
            self.specific_profession,
            self.target_audience,
            self.communication_tone,
            self.expertise_areas,
            self.preferred_duration,
            self.complexity_level,
            self.theme_diversity,
            self.publication_frequency,

            # Optional fields
            self.instagram_username,
            self.linkedin_url,
            self.twitter_username,
            self.tiktok_username,
            self.revenue_stage,
            self.team_size,
            self.revenue_goal,
            self.authority_goal,
            self.leads_goal,
            self.has_designer,
            self.current_tools,
            self.tools_budget,
            self.preferred_hours,
        ]

        # Count filled fields
        filled_fields = sum(
            1 for field in profile_fields if is_field_filled(field))

        # Add user fields (assuming name and email are always filled for authenticated users)
        if self.user_id:
            filled_fields += 2  # user.first_name/last_name and user.email

        total_fields = len(profile_fields) + 2  # +2 for user fields

        # Calculate percentage
        percentage = min(int((filled_fields / total_fields) * 100), 100)
        return percentage

    def save(self, *args, **kwargs):
        """Override save to automatically calculate completeness and onboarding status."""
        # Calculate completeness percentage
        self.completeness_percentage = self.calculate_completeness()

        # Check if onboarding is completed (all required fields filled)
        required_fields_filled = all([
            self.main_platform,
            self.niche,
            self.experience_level,
            self.primary_goal,
            self.time_available,
        ])

        if required_fields_filled and not self.onboarding_completed:
            self.onboarding_completed = True
            if not self.onboarding_completed_at:
                from django.utils import timezone
                self.onboarding_completed_at = timezone.now()

        super().save(*args, **kwargs)


class UserBehavior(models.Model):
    """
    Track user behavioral data for personalization (Level 2).
    Based on specification for behavioral profiling.
    """

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='behavior_profile')

    # Click Patterns
    ideas_selected = models.JSONField(
        default=list,
        verbose_name="Ideias Selecionadas",
        help_text="Lista de IDs das ideias selecionadas pelo usuário"
    )

    ideas_rejected = models.JSONField(
        default=list,
        verbose_name="Ideias Rejeitadas",
        help_text="Lista de IDs das ideias rejeitadas pelo usuário"
    )

    avg_time_per_idea = models.FloatField(
        default=0.0,
        verbose_name="Tempo Médio por Ideia",
        help_text="Tempo médio em segundos analisando cada ideia"
    )

    # Preferences (inferred from behavior)
    preferred_topics = models.JSONField(
        default=list,
        verbose_name="Tópicos Preferidos",
        help_text="Lista de tópicos preferidos baseados no comportamento"
    )

    preferred_complexity = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        default=5,
        verbose_name="Complexidade Preferida",
        help_text="Escala 1-10 baseada no comportamento"
    )

    preferred_length = models.CharField(
        max_length=20,
        choices=[('short', 'Curto'), ('medium', 'Médio'), ('long', 'Longo')],
        default='medium',
        verbose_name="Comprimento Preferido"
    )

    # Usage Patterns
    peak_hours = models.JSONField(
        default=list,
        verbose_name="Horários de Pico",
        help_text="Horários de maior uso baseados no comportamento"
    )

    usage_frequency = models.CharField(
        max_length=20,
        choices=[('daily', 'Diário'), ('weekly', 'Semanal'),
                 ('monthly', 'Mensal')],
        default='weekly',
        verbose_name="Frequência de Uso"
    )

    avg_session_duration = models.FloatField(
        default=0.0,
        verbose_name="Duração Média da Sessão",
        help_text="Duração média da sessão em minutos"
    )

    # Metadata
    total_interactions = models.IntegerField(
        default=0,
        verbose_name="Total de Interações"
    )

    last_activity = models.DateTimeField(
        auto_now=True,
        verbose_name="Última Atividade"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Comportamento do Usuário"
        verbose_name_plural = "Comportamentos dos Usuários"

    def __str__(self):
        return f"Comportamento - {self.user.get_full_name()}"
