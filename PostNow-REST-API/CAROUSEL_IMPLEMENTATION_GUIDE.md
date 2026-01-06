# 🎠 Guia de Implementação: Carrosséis para Instagram

> **Status:** Planejamento e Especificação  
> **Data Início:** Janeiro 2025  
> **Base:** Sistema de Posts Diários (DailyIdeasService)  
> **Objetivo:** Criar sistema de geração automática de carrosséis de alta performance para Instagram

---

## 📋 Índice

1. [Contexto e Decisão](#contexto-e-decisão)
2. [Pesquisa e Fundamentos](#pesquisa-e-fundamentos)
3. [Especificações Técnicas](#especificações-técnicas)
4. [Arquitetura Proposta](#arquitetura-proposta)
5. [Sistema Base (Referência)](#sistema-base-referência)
6. [Implementação por Fases](#implementação-por-fases)
7. [Métricas e KPIs](#métricas-e-kpis)
8. [Referências](#referências)

---

## 🎯 Contexto e Decisão

### Por que Carrosséis?

**Dados de Mercado (2024/2025):**
- Taxa de engajamento: **2.33%** vs. 1.74% de posts únicos
- Algoritmo Instagram reexibe carrosséis com slides não visualizados
- Usuários passam **3-5× mais tempo** consumindo carrosséis
- Maior taxa de salvamento (conteúdo "revisitável")

### Decisão de Arquitetura

**Usar como base:** `IdeaBank/services/daily_ideas_service.py`

**Motivo:** Sistema de Posts Diários já implementa:
- ✅ Análise Semântica em 3 etapas (98% de qualidade)
- ✅ Adaptação à marca do cliente
- ✅ Integração com CreatorProfile completo
- ✅ Weekly Context (tendências atuais)
- ✅ Logo da empresa incluída
- ✅ Upload S3 e validação de créditos

---

## 📚 Pesquisa e Fundamentos

### 1. Mecânicas de Engajamento

#### Swipe-Through (Deslizar para o lado)

**É a melhor interação?** ✅ SIM

- Principal forma nativa de interação
- Mantém usuário engajado por mais tempo
- Algoritmo favorece conteúdo com maior tempo de permanência
- Múltiplas exposições (Instagram reexibe slides não vistos)

#### Gatilhos Psicológicos

```yaml
Gap de Curiosidade:
  - "E o melhor vem agora..."
  - "O #3 vai te surpreender"
  
Progressão Visual:
  - Números (1/8, 2/8, ...)
  - Barras de progresso
  - Cores em gradiente
  
Recompensa Prometida:
  - "No último slide: bônus exclusivo"
  - "Deslize até o fim para descobrir"
  
FOMO (Fear of Missing Out):
  - "Não pare no slide 3!"
  - "A maioria desiste aqui..."
```

### 2. Elementos que Aumentam Swipe

#### A. Primeira Imagem (Capa) - CRÍTICA

**Checklist:**
- [ ] Título forte e direto (máx. 6 palavras)
- [ ] Cria curiosidade/gap de informação
- [ ] Promessa clara de valor
- [ ] Contraste visual alto
- [ ] NÃO revela tudo

**Exemplos Comprovados:**
```
✅ "5 erros que estão matando seu engajamento"
✅ "Você está fazendo isso errado"
✅ "O segredo que ninguém conta sobre..."
✅ "Antes de postar, leia isto"

❌ "Dicas de marketing digital"
❌ "Aprenda sobre redes sociais"
```

#### B. Indicadores Visuais

**Elementos Obrigatórios:**
1. **Setas Direcionais:** → (aumenta swipe em 15-20%)
2. **Numeração:** "1/8", "2/8"...
3. **Frases Cortadas:** "E o mais importante é..." [continua →]
4. **Barra de Progresso:** Visual ou textual
5. **Mudança Gradual de Cor:** Cria sensação de progressão

#### C. CTAs Específicos

**No Design:**
- "Deslize para descobrir →"
- "Arraste para ver o resultado →"
- "Continue para o melhor →"

**Nos Slides Intermediários:**
- "Ainda não acabou! →"
- "Espera, tem mais →"
- "O próximo é meu favorito →"

### 3. Tipos de Narrativa (Ordenados por Performance)

| Tipo | Completion Rate | Uso Ideal |
|------|-----------------|-----------|
| Tutorial Passo-a-Passo | 85% | Educacional, how-to |
| Mitos vs. Verdades | 80% | Autoridade, desmistificação |
| Antes e Depois | 75% | Transformação, resultados |
| Checklist/Lista | 70% | Ação imediata, organização |
| Infográfico | 68% | Dados, estatísticas |
| Storytelling | 65% | Conexão emocional |
| Comparison | 63% | Decisão de compra |
| Quotes/Frases | 60% | Inspiracional (alto save) |
| Behind the Scenes | 58% | Humanização |
| Quiz/Teste | 90% | Interação (comentários) |

### 4. Consistência Visual

#### Sistema de Design Obrigatório

```yaml
Layout:
  margin_interna: 80-100px  # Safe zone
  grid: 12x12
  alinhamento: centro ou esquerda
  
Tipografia:
  titulo: 48-72px (Bold/Black)
  subtitulo: 32-40px (SemiBold)
  corpo: 24-28px (Regular)
  cta: 28-36px (Bold)
  min_legivel: 24px
  
Cores:
  paleta: 3-4 cores consistentes
  contraste_minimo: 4.5:1 (WCAG AA)
  contraste_ideal: 7:1 (WCAG AAA)
  
Elementos:
  mesma_familia_tipografica: true
  mesmo_estilo_icones: true
  mesmo_grid: true
```

#### Padrões de Cores

**Opção 1: Degradê Progressivo**
```
Slide 1: Cor Brand (100%)
Slide 2: Brand (80%) + Secundária (20%)
...
Slide 8: Secundária (100%)
```

**Opção 2: Alternância de Contraste**
```
Slides ímpares: Fundo escuro + texto claro
Slides pares: Fundo claro + texto escuro
```

**Opção 3: Monocromático** (Recomendado para começar)
```
Todos: Fundo neutro
Destaques: Cor da marca
```

---

## 🔧 Especificações Técnicas

### Formatos Instagram

```yaml
Carrossel Feed:
  proporcao_recomendada: "4:5"  # Vertical
  pixels: "1080x1350"
  proporcao_alternativa: "1:1"  # Quadrado
  pixels_alternativa: "1080x1080"
  formato: ["JPG", "PNG"]
  tamanho_max: "30MB"
  slides_min: 2
  slides_max: 10
  slides_ideal: 6-8  # Sweet spot de engajamento
```

### Logo - Especificações

#### Estratégia de Uso

**Recomendação:** Logo em primeiro e último slide

```yaml
Logo Grande (Capa/CTA):
  largura: 120-180px
  posicao: ["centro_superior", "inferior_esquerdo"]
  percentual_imagem: 10-15%
  opacidade: 100%

Logo Pequena (Watermark - opcional):
  largura: 60-80px
  posicao: ["canto_inferior_direito", "canto_inferior_esquerdo"]
  percentual_imagem: 5-8%
  opacidade: 80-100%
  
Safe Zone:
  margem_minima: 60px
  evitar_area: "superior" # Pode ser cortada no feed
```

#### Tratamento Visual

```python
# Fundo Claro
logo_versao = "escura"
fundo_logo = "branco_suave"  # opcional
sombra = "sutil"  # se necessário

# Fundo Escuro
logo_versao = "clara/branca"
brilho = "glow_suave"
sombra = None

# Fundo Fotográfico
backdrop = "retangulo_semi_transparente"
ou = "versao_com_contorno"
contraste_minimo = 4.5
```

### Número de Slides

**Dados de Pesquisa:**
```
2-5 slides: Taxa de conclusão 70-80%
6-8 slides: Taxa de conclusão 50-60% ⭐ SWEET SPOT
9-10 slides: Taxa de conclusão 30-40%

Decisão: 6-8 slides por padrão
```

---

## 🏗️ Arquitetura Proposta

### Novos Modelos

```python
# Adicionar em IdeaBank/models.py

class CarouselPost(models.Model):
    """
    Post em formato carrossel (múltiplas imagens).
    Extends funcionalidade de Post para suportar slides.
    """
    
    post = models.OneToOneField(
        'Post',
        on_delete=models.CASCADE,
        related_name='carousel'
    )
    
    # Configuração do Carrossel
    slide_count = models.IntegerField(
        default=7,
        help_text="Número de slides (recomendado: 6-8)"
    )
    
    narrative_type = models.CharField(
        max_length=50,
        choices=[
            ('list', 'Lista/Checklist'),  # MVP: Apenas este tipo
            ('tutorial', 'Tutorial Passo-a-Passo'),  # Fase 4
            ('story', 'Storytelling'),  # Fase 4
            ('comparison', 'Comparação'),  # Fase 4
            ('before_after', 'Antes e Depois'),  # Fase 4
            ('myths', 'Mitos vs. Verdades'),  # Fase 4
            ('infographic', 'Infográfico'),  # Fase 4
            ('quiz', 'Quiz/Teste'),  # Fase 4
        ],
        default='list'
    )
    
    # Elementos Visuais
    visual_consistency_applied = models.BooleanField(
        default=True,
        help_text="Sistema aplicou consistência visual entre slides"
    )
    
    logo_placement = models.CharField(
        max_length=20,
        choices=[
            ('first_last', 'Primeiro e Último Slide'),
            ('all_minimal', 'Todos os Slides (Watermark)'),
            ('first_only', 'Apenas Primeiro Slide'),
            ('none', 'Sem Logo'),
        ],
        default='first_last'
    )
    
    swipe_triggers = models.JSONField(
        default=list,
        help_text="Elementos usados: ['arrows', 'numbering', 'cliffhangers', 'progress_bar']"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class CarouselSlide(models.Model):
    """
    Slide individual do carrossel.
    """
    
    carousel = models.ForeignKey(
        CarouselPost,
        on_delete=models.CASCADE,
        related_name='slides'
    )
    
    sequence_order = models.IntegerField(
        help_text="Ordem do slide (1, 2, 3...)"
    )
    
    # Conteúdo
    title = models.CharField(
        max_length=100,
        blank=True,
        help_text="Título do slide"
    )
    
    content = models.TextField(
        blank=True,
        help_text="Texto do slide"
    )
    
    image_url = models.URLField(
        max_length=500,
        blank=True,
        help_text="URL da imagem no S3"
    )
    
    image_description = models.TextField(
        blank=True,
        help_text="Prompt usado para gerar a imagem"
    )
    
    # Elementos de Swipe
    has_arrow = models.BooleanField(default=True)
    has_numbering = models.BooleanField(default=True)
    has_cliffhanger = models.BooleanField(default=False)
    
    # Visual
    background_color = models.CharField(
        max_length=7,
        blank=True,
        help_text="Cor de fundo (hex)"
    )
    
    class Meta:
        ordering = ['sequence_order']
        unique_together = ['carousel', 'sequence_order']


class CarouselGenerationSource(models.Model):
    """
    Rastreia origem da geração do carrossel.
    CRÍTICO para análise de dados na Fase 4.
    """
    
    carousel = models.OneToOneField(
        CarouselPost,
        on_delete=models.CASCADE,
        related_name='generation_source'
    )
    
    # Tipo de origem (MVP: 3 tipos)
    source_type = models.CharField(
        max_length=50,
        choices=[
            ('manual', 'Input Manual do Usuário'),  # MVP
            ('from_post', 'Expandido de Post Existente'),  # MVP
            ('weekly_context', 'Weekly Context/Oportunidade'),  # MVP
            ('from_campaign', 'Parte de Campanha'),  # Futuro
            ('from_idea', 'Do IdeaBank'),  # Futuro
            ('from_analytics', 'Sugestão baseada em Analytics'),  # Fase 4
            ('from_calendar', 'Calendário de Conteúdo'),  # Futuro
        ]
    )
    
    # Referências (opcional, depende do tipo)
    source_post_id = models.IntegerField(null=True, blank=True)
    source_campaign_id = models.IntegerField(null=True, blank=True)
    source_opportunity_id = models.CharField(max_length=100, blank=True)
    
    # Metadata
    original_theme = models.TextField()
    user_modifications = models.JSONField(default=dict)
    
    created_at = models.DateTimeField(auto_now_add=True)


class CarouselMetrics(models.Model):
    """
    ⚠️ CRÍTICO PARA FASE 4!
    Métricas detalhadas de performance do carrossel.
    Sistema de coleta de dados para ML.
    """
    
    carousel = models.OneToOneField(
        CarouselPost,
        on_delete=models.CASCADE,
        related_name='metrics'
    )
    
    # Métricas Básicas
    impressions = models.IntegerField(
        default=0,
        help_text="Total de visualizações"
    )
    
    reach = models.IntegerField(
        default=0,
        help_text="Usuários únicos alcançados"
    )
    
    # Métricas de Swipe ⭐ CRÍTICO
    views_per_slide = models.JSONField(
        default=dict,
        help_text="Views por slide: {'1': 1000, '2': 850, '3': 720, ...}"
    )
    
    swipe_through_rate = models.FloatField(
        default=0.0,
        help_text="(views_last_slide / views_first_slide) × 100"
    )
    
    completion_rate = models.FloatField(
        default=0.0,
        help_text="% de usuários que viram todos os slides"
    )
    
    avg_time_spent = models.IntegerField(
        default=0,
        help_text="Tempo médio gasto no carrossel (segundos)"
    )
    
    # Drop-off Analysis ⭐ CRÍTICO PARA ML
    drop_off_slide = models.IntegerField(
        null=True,
        help_text="Slide onde maioria dos usuários parou"
    )
    
    drop_off_percentage = models.FloatField(
        default=0.0,
        help_text="% de usuários que abandonaram no slide crítico"
    )
    
    # Engajamento
    likes = models.IntegerField(default=0)
    comments = models.IntegerField(default=0)
    saves = models.IntegerField(default=0)
    shares = models.IntegerField(default=0)
    
    engagement_rate = models.FloatField(
        default=0.0,
        help_text="((likes + comments + saves + shares) / impressions) × 100"
    )
    
    # Contexto Temporal ⭐ CRÍTICO PARA ML
    posted_at = models.DateTimeField(
        null=True,
        help_text="Quando foi publicado"
    )
    
    day_of_week = models.CharField(
        max_length=10,
        blank=True,
        help_text="Dia da semana (segunda, terca, ...)"
    )
    
    hour_of_day = models.IntegerField(
        null=True,
        help_text="Hora de publicação (0-23)"
    )
    
    # Origem (para comparação) ⭐ CRÍTICO PARA ML
    generation_source = models.CharField(
        max_length=50,
        blank=True,
        help_text="Cópia do source_type para análise rápida"
    )
    
    # Metadata
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def calculate_swipe_through(self):
        """Calcula swipe-through rate baseado em views por slide."""
        if not self.views_per_slide:
            return 0.0
        
        slides = sorted([int(k) for k in self.views_per_slide.keys()])
        if len(slides) < 2:
            return 0.0
        
        first_views = self.views_per_slide[str(slides[0])]
        last_views = self.views_per_slide[str(slides[-1])]
        
        if first_views == 0:
            return 0.0
        
        return (last_views / first_views) * 100
    
    def identify_drop_off_slide(self):
        """Identifica slide com maior drop-off."""
        if not self.views_per_slide:
            return None
        
        slides = sorted([int(k) for k in self.views_per_slide.keys()])
        max_drop = 0
        drop_slide = None
        
        for i in range(len(slides) - 1):
            current = self.views_per_slide[str(slides[i])]
            next_slide = self.views_per_slide[str(slides[i + 1])]
            
            if current > 0:
                drop = ((current - next_slide) / current) * 100
                if drop > max_drop:
                    max_drop = drop
                    drop_slide = slides[i + 1]
        
        return drop_slide, max_drop
```

### Novo Service: CarouselGenerationService

```python
# Criar em IdeaBank/services/carousel_generation_service.py

class CarouselGenerationService:
    """
    Service para geração de carrosséis usando base do DailyIdeasService.
    
    MVP: 3 Origens de Conteúdo
    1. Input Manual
    2. Expandir Posts Diários (reusa análise semântica)
    3. Weekly Context (oportunidades)
    
    Fluxo Geral:
    1. Análise semântica do tema (3 etapas - reuso DailyIdeasService)
    2. Estruturação de slides (7 slides padrão, narrativa: list)
    3. Geração de texto para cada slide
    4. Geração de imagens harmônicas (reusa DailyIdeasService)
    5. Aplicação de elementos de swipe (setas + numeração)
    6. Logo estratégica (primeiro + último slide)
    7. Criação de CarouselMetrics (CRÍTICO para Fase 4)
    """
    
    def __init__(self):
        self.daily_ideas_service = DailyIdeasService()
        self.prompt_service = AIPromptService()
        self.ai_service = AiService()
        self.s3_service = S3Service()
        self.weekly_context_service = WeeklyContextService()
    
    # ============================================================================
    # ORIGEM 1: INPUT MANUAL (MVP - Sprint 1)
    # ============================================================================
    
    def generate_from_manual_input(
        self,
        user: User,
        theme: str,
        options: Dict = None
    ) -> CarouselPost:
        """
        Origem 1: Usuário digita tema manualmente.
        
        Args:
            user: Usuário que está criando
            theme: Tema/assunto do carrossel (ex: "5 dicas de Instagram")
            options: Configurações opcionais
                - slide_count: int (padrão: 7)
                - logo_placement: str (padrão: 'first_last')
        
        Returns:
            CarouselPost com todos os slides gerados
        
        Example:
            >>> carousel = service.generate_from_manual_input(
            ...     user=user,
            ...     theme="5 estratégias para aumentar engajamento",
            ...     options={'slide_count': 7}
            ... )
        """
        
        options = options or {}
        slide_count = options.get('slide_count', 7)
        logo_placement = options.get('logo_placement', 'first_last')
        
        # 1. Análise Semântica (reusa DailyIdeasService)
        semantic_analysis = self._perform_semantic_analysis(user, theme)
        
        # 2. Estruturar Narrativa (MVP: apenas 'list')
        slides_structure = self._structure_list_narrative(
            theme, slide_count, semantic_analysis
        )
        
        # 3. Gerar Texto dos Slides
        slides_content = self._generate_slides_text(
            user, slides_structure, semantic_analysis
        )
        
        # 4. Gerar Imagens Harmônicas
        slides_with_images = self._generate_harmonic_images(
            user, slides_content, logo_placement
        )
        
        # 5. Criar CarouselPost no banco + Métricas
        carousel_post = self._save_carousel_to_db(
            user=user,
            theme=theme,
            narrative_type='list',
            slides=slides_with_images,
            logo_placement=logo_placement,
            source_type='manual',
            source_data={'original_theme': theme}
        )
        
        return carousel_post
    
    # ============================================================================
    # ORIGEM 2: EXPANDIR POSTS DIÁRIOS (MVP - Sprint 2) ⭐ MÁXIMO VALOR
    # ============================================================================
    
    def generate_from_daily_post(
        self,
        user: User,
        post_id: int,
        expand_strategy: str = 'auto'
    ) -> CarouselPost:
        """
        Origem 2: Expandir post diário existente para carrossel.
        REUSA análise semântica já feita (98% qualidade).
        
        Args:
            user: Usuário
            post_id: ID do post diário a expandir
            expand_strategy: Estratégia de expansão
                - 'auto': Sistema decide automaticamente
                - 'detailed_list': Lista → Carrossel detalhado
                - 'tutorial': Conceito → Passo-a-passo
                - 'before_after': Resultado → Jornada
        
        Returns:
            CarouselPost expandido do post original
        
        Example:
            >>> # Post diário: "5 erros que matam engajamento"
            >>> carousel = service.generate_from_daily_post(
            ...     user=user,
            ...     post_id=12345,
            ...     expand_strategy='detailed_list'
            ... )
            >>> # Resultado: 7 slides (1 capa + 5 erros + 1 recap)
        """
        
        # 1. Buscar post diário
        post = Post.objects.get(id=post_id, user=user)
        
        # Validar se é expansível
        if not self._is_post_expandable(post):
            raise ValueError(
                f"Post '{post.name}' não tem estrutura expansível. "
                "Procure por posts com listas, tutoriais ou transformações."
            )
        
        # 2. REUSAR análise semântica do post original
        # (Economia de créditos + mantém qualidade 98%!)
        semantic_analysis = self._extract_semantic_from_post_idea(post)
        
        # 3. Determinar estratégia de expansão
        if expand_strategy == 'auto':
            expand_strategy = self._infer_expansion_strategy(post)
        
        # 4. Estruturar slides baseado na estratégia
        slides_structure = self._expand_post_to_slides(
            post, 
            expand_strategy,
            semantic_analysis
        )
        
        # 5. Gerar conteúdo expandido para cada slide
        slides_content = self._generate_expanded_slides_text(
            user,
            post,
            slides_structure,
            semantic_analysis
        )
        
        # 6. Gerar imagens (REUSA DailyIdeasService!)
        slides_with_images = self._generate_images_with_daily_quality(
            user,
            slides_content,
            semantic_analysis,  # Reaproveitamento!
            logo_placement='first_last'
        )
        
        # 7. Criar carrossel
        carousel = self._save_carousel_to_db(
            user=user,
            theme=f"Expandido: {post.name}",
            narrative_type='list',  # MVP: sempre list
            slides=slides_with_images,
            logo_placement='first_last',
            source_type='from_post',
            source_data={
                'source_post_id': post_id,
                'original_theme': post.name,
                'expand_strategy': expand_strategy,
                'original_engagement': post.engagement_rate if hasattr(post, 'engagement_rate') else None
            }
        )
        
        return carousel
    
    def _is_post_expandable(self, post: Post) -> bool:
        """
        Verifica se post tem estrutura expansível.
        
        Padrões expansíveis:
        - Listas: "5 dicas", "7 erros", "10 estratégias"
        - Tutoriais: "Como fazer", "Como criar", "Como aumentar"
        - Transformações: "Antes e depois", "De X para Y"
        """
        
        content = f"{post.name} {post.content}".lower()
        
        expandable_patterns = [
            r'\d+ (dicas|erros|estratégias|passos|formas|maneiras|razões)',
            r'como (fazer|criar|aumentar|diminuir|melhorar|conseguir)',
            r'(antes|depois|transformação|evolução)',
            r'(mitos|verdades|fatos) sobre',
            r'guia (completo|definitivo) (de|para)',
        ]
        
        for pattern in expandable_patterns:
            if re.search(pattern, content):
                return True
        
        return False
    
    def _infer_expansion_strategy(self, post: Post) -> str:
        """
        Infere melhor estratégia de expansão baseado no conteúdo.
        """
        
        content = f"{post.name} {post.content}".lower()
        
        # Lista/Enumeração
        if re.search(r'\d+ (dicas|erros|estratégias)', content):
            return 'detailed_list'
        
        # Tutorial/Como Fazer
        if re.search(r'como (fazer|criar|aumentar)', content):
            return 'tutorial'
        
        # Transformação
        if re.search(r'(antes|depois|de \w+ para)', content):
            return 'before_after'
        
        # Fallback
        return 'detailed_list'
    
    # ============================================================================
    # ORIGEM 3: WEEKLY CONTEXT (MVP - Sprint 3)
    # ============================================================================
    
    def generate_from_opportunity(
        self,
        user: User,
        opportunity_id: str,
        angle: str = None
    ) -> CarouselPost:
        """
        Origem 3: Criar carrossel baseado em oportunidade do Weekly Context.
        
        Args:
            user: Usuário
            opportunity_id: ID da oportunidade (ex: 'dia-das-maes-2025')
            angle: Ângulo/abordagem escolhida pelo usuário
                   (ex: 'Presentes que toda mãe ama')
        
        Returns:
            CarouselPost sobre a oportunidade
        
        Example:
            >>> # Weekly Context detectou: Dia das Mães em 21 dias
            >>> carousel = service.generate_from_opportunity(
            ...     user=user,
            ...     opportunity_id='dia-das-maes-2025',
            ...     angle='7 presentes que toda mãe ama'
            ... )
        """
        
        # 1. Buscar oportunidade
        opportunity = self.weekly_context_service.get_opportunity_by_id(
            opportunity_id
        )
        
        if not opportunity:
            raise ValueError(f"Oportunidade '{opportunity_id}' não encontrada")
        
        # 2. Construir tema baseado na oportunidade
        if angle:
            theme = angle
        else:
            # Gerar tema automaticamente
            theme = self._generate_theme_from_opportunity(
                opportunity, 
                user
            )
        
        # 3. Enriquecer contexto com dados da oportunidade
        context_enrichment = {
            'opportunity_title': opportunity['title'],
            'opportunity_date': opportunity['date'],
            'keywords': opportunity['keywords'],
            'category': opportunity['category']
        }
        
        # 4. Análise Semântica (com contexto enriquecido)
        semantic_analysis = self._perform_semantic_analysis(
            user, 
            theme,
            context_enrichment
        )
        
        # 5. Estruturar narrativa
        slides_structure = self._structure_list_narrative(
            theme, 7, semantic_analysis
        )
        
        # 6. Gerar texto
        slides_content = self._generate_slides_text(
            user, slides_structure, semantic_analysis
        )
        
        # 7. Gerar imagens
        slides_with_images = self._generate_harmonic_images(
            user, slides_content, 'first_last'
        )
        
        # 8. Criar carrossel
        carousel = self._save_carousel_to_db(
            user=user,
            theme=theme,
            narrative_type='list',
            slides=slides_with_images,
            logo_placement='first_last',
            source_type='weekly_context',
            source_data={
                'source_opportunity_id': opportunity_id,
                'opportunity_title': opportunity['title'],
                'opportunity_date': opportunity['date'],
                'chosen_angle': angle
            }
        )
        
        return carousel
    
    # ============================================================================
    # MÉTODOS AUXILIARES (Reuso DailyIdeasService)
    # ============================================================================
    
    def _perform_semantic_analysis(
        self, 
        user: User, 
        theme: str,
        context_enrichment: Dict = None
    ) -> Dict:
        """
        Reusa análise semântica em 3 etapas do DailyIdeasService.
        ESTE É O DIFERENCIAL (98% qualidade).
        """
        
        # Construir contexto
        full_context = theme
        if context_enrichment:
            full_context += f"\nContexto adicional: {context_enrichment}"
        
        # Passo 1: Análise Semântica
        semantic_prompt = self.prompt_service.semantic_analysis_prompt(full_context)
        semantic_result = self.ai_service.generate_text(semantic_prompt, user)
        semantic_loaded = json.loads(semantic_result)
        
        # Passo 2: Adaptação à Marca
        adapted_prompt = self.prompt_service.adapted_semantic_analysis_prompt(
            semantic_loaded
        )
        adapted_result = self.ai_service.generate_text(adapted_prompt, user)
        adapted_loaded = json.loads(adapted_result)
        
        return adapted_loaded
    
    def _generate_harmonic_images(
        self,
        user: User,
        slides_content: List[Dict],
        logo_placement: str
    ) -> List[Dict]:
        """
        Gera imagens mantendo harmonia visual.
        Reusa _generate_image_for_feed_post do DailyIdeasService.
        """
        
        # Buscar logo do usuário
        creator_profile = CreatorProfile.objects.filter(user=user).first()
        user_logo = creator_profile.logo if creator_profile else None
        
        slides_with_images = []
        
        for i, slide in enumerate(slides_content):
            sequence = i + 1
            is_first = sequence == 1
            is_last = sequence == len(slides_content)
            
            # Decidir se inclui logo
            include_logo = False
            if logo_placement == 'first_last' and (is_first or is_last):
                include_logo = True
            elif logo_placement == 'all_minimal':
                include_logo = True
            elif logo_placement == 'first_only' and is_first:
                include_logo = True
            
            # Gerar imagem (reusa DailyIdeasService!)
            image_url = self._generate_image_for_slide(
                user,
                slide['content'],
                slide.get('semantic_analysis'),
                user_logo if include_logo else None
            )
            
            slide['image_url'] = image_url
            slides_with_images.append(slide)
        
        return slides_with_images
    
    def _save_carousel_to_db(
        self,
        user: User,
        theme: str,
        narrative_type: str,
        slides: List[Dict],
        logo_placement: str,
        source_type: str,
        source_data: Dict
    ) -> CarouselPost:
        """
        Salva carrossel no banco + cria registros de origem e métricas.
        """
        
        # 1. Criar Post base
        post = Post.objects.create(
            user=user,
            name=theme,
            content=f"Carrossel com {len(slides)} slides",
            post_type='feed',
            is_carousel=True
        )
        
        # 2. Criar CarouselPost
        carousel = CarouselPost.objects.create(
            post=post,
            slide_count=len(slides),
            narrative_type=narrative_type,
            logo_placement=logo_placement,
            swipe_triggers=['arrows', 'numbering']
        )
        
        # 3. Criar Slides
        for slide_data in slides:
            CarouselSlide.objects.create(
                carousel=carousel,
                sequence_order=slide_data['sequence'],
                title=slide_data.get('title', ''),
                content=slide_data['content'],
                image_url=slide_data['image_url'],
                image_description=slide_data.get('image_description', ''),
                has_arrow=True,
                has_numbering=True,
                has_cliffhanger=slide_data.get('has_cliffhanger', False)
            )
        
        # 4. Criar registro de origem (CRÍTICO para Fase 4)
        CarouselGenerationSource.objects.create(
            carousel=carousel,
            source_type=source_type,
            source_post_id=source_data.get('source_post_id'),
            source_campaign_id=source_data.get('source_campaign_id'),
            source_opportunity_id=source_data.get('source_opportunity_id', ''),
            original_theme=theme,
            user_modifications={}
        )
        
        # 5. Criar registro de métricas (CRÍTICO para Fase 4)
        CarouselMetrics.objects.create(
            carousel=carousel,
            generation_source=source_type,
            day_of_week=timezone.now().strftime('%A').lower(),
            hour_of_day=timezone.now().hour
        )
        
        return carousel
```

**Ver implementação completa dos prompts em:** `CAROUSEL_PROMPTS.md`

---

## 📦 Sistema Base (Referência)

### Arquivos Existentes para Reusar

```yaml
Base Principal:
  - IdeaBank/services/daily_ideas_service.py
    Método: _generate_image_for_feed_post() (linhas 390-451)
    Reusa: Análise semântica em 3 etapas
    
  - IdeaBank/services/prompt_service.py
    Método: semantic_analysis_prompt()
    Método: adapted_semantic_analysis_prompt()
    Método: image_generation_prompt()
    
  - services/ai_service.py
    Método: generate_text()
    Método: generate_image() (linha 141+)
    
  - services/s3_service.py
    Método: upload_image()

CreatorProfile:
  - CreatorProfile/models.py
    Campo: logo (TextField, base64)
    Campos: color_1, color_2, color_3, color_4, color_5
    Campo: voice_tone, brand_personality, etc.

Validação e Créditos:
  - CreditSystem/services/ (validação automática)
  - Analytics/services/image_pregen_policy.py
```

### Fluxo de Análise Semântica Existente

```python
# DailyIdeasService._generate_image_for_feed_post()
# Linhas 390-451

# 1. Buscar logo
user_logo = CreatorProfile.objects.filter(user=user).first().logo

# 2. Análise Semântica (IA Call #1)
semantic_prompt = self.prompt_service.semantic_analysis_prompt(post_content)
semantic_result = self.ai_service.generate_text(semantic_prompt, user)

# 3. Adaptação à Marca (IA Call #2)
adapted_prompt = self.prompt_service.adapted_semantic_analysis_prompt(semantic_loaded)
adapted_result = self.ai_service.generate_text(adapted_prompt, user)

# 4. Prompt de Imagem
semantic_analysis = adapted_loaded.get("analise_semantica", {})
image_prompt = self.prompt_service.image_generation_prompt(semantic_analysis)

# 5. Gerar Imagem (IA Call #3)
image_result = self.ai_service.generate_image(
    image_prompt,
    user_logo,
    user,
    types.GenerateContentConfig(
        temperature=0.7,
        top_p=0.9,
        response_modalities=["IMAGE"],
        image_config=types.ImageConfig(aspect_ratio="4:5")
    )
)

# 6. Upload S3
image_url = self.s3_service.upload_image(user, image_result)
```

**Este fluxo será reusado para cada slide do carrossel!**

---

## 🚀 Implementação por Fases

> **ESTRATÉGIA:** Fase 1 (MVP) → Coleta de Dados (1-2 meses) → Fase 4 (ML/Analytics)  
> **DECISÃO:** Pular Fases 2-3 para implementação data-driven na Fase 4

---

### 🎯 Fase 1: MVP Carrossel (2-3 sprints) ⭐ PRIORIDADE MÁXIMA

**Objetivo:** MVP lean com 3 origens de conteúdo + logging robusto de métricas

#### Sprint 1-2: Funcionalidade Base + Origens 1-2

**Entregáveis Core:**
- [ ] Modelo `CarouselPost` e `CarouselSlide`
- [ ] Modelo `CarouselMetrics` ⚠️ **CRÍTICO PARA FASE 4**
- [ ] Modelo `CarouselGenerationSource` (rastreamento de origem)
- [ ] `CarouselGenerationService` base
- [ ] Tipo de narrativa: `list` (lista/checklist) - ÚNICO no MVP
- [ ] 7 slides como padrão
- [ ] Logo em primeiro e último slide
- [ ] Elementos básicos de swipe (setas + numeração)
- [ ] Reuso 100% do `DailyIdeasService` (análise semântica 3 etapas)

**Origens de Conteúdo (Prioridade):**
1. ✅ **Input Manual** (Sprint 1)
   - Endpoint: `POST /api/v1/carousel/generate/`
   - Interface: Formulário simples com campo tema
   - Usuário digita tema → Sistema gera carrossel
   
2. ✅ **Expandir Posts Diários** (Sprint 2) ⭐ **MÁXIMO VALOR**
   - Endpoint: `POST /api/v1/carousel/expand-post/`
   - Interface: Botão "Expandir para Carrossel" em posts diários
   - Algoritmo de sugestão: Detecta posts "expansíveis"
   - **Reusa análise semântica já feita** (economia de créditos!)
   - Estratégias: `detailed_list`, `tutorial`, `before_after`

#### Sprint 3: Origem 3 + Métricas + Integração Instagram

**Entregáveis:**
3. ✅ **Weekly Context** (Sprint 3)
   - Endpoint: `POST /api/v1/carousel/from-opportunity/`
   - Interface: Card de oportunidade + botão "Criar Carrossel"
   - Integração: `WeeklyContextService` (já existe)
   - Uso: Datas comemorativas, tendências, eventos

**Logging e Métricas ⚠️ CRÍTICO:**
- [ ] `CarouselMetrics` implementado
- [ ] Integração com Instagram Graph API (métricas por slide)
- [ ] Dashboard básico de métricas (frontend)
- [ ] Export de dados para análise (CSV/JSON)
- [ ] Tracking de:
  - `views_per_slide` (JSON: {1: 1000, 2: 850, ...})
  - `swipe_through_rate`
  - `completion_rate`
  - `drop_off_slide` (onde usuário parou)
  - `engagement` (likes, comments, saves, shares)
  - `posted_at`, `day_of_week`, `hour_of_day`
  - `generation_source` (qual origem funcionou melhor)

**Validação MVP:**
```python
# Teste Origem 1: Input Manual
carousel = CarouselGenerationService().generate_from_manual_input(
    user=user,
    theme="5 dicas para aumentar engajamento no Instagram",
    options={'slide_count': 7}
)
assert carousel.slides.count() == 7
assert carousel.generation_source.source_type == 'manual'

# Teste Origem 2: Posts Diários
post_diario = Post.objects.get(id=12345)
carousel = CarouselGenerationService().generate_from_daily_post(
    user=user,
    post_id=12345,
    expand_strategy='detailed_list'
)
assert carousel.slides.count() == 7
assert carousel.generation_source.source_type == 'from_post'
assert carousel.generation_source.source_post_id == 12345

# Teste Origem 3: Weekly Context
carousel = CarouselGenerationService().generate_from_opportunity(
    user=user,
    opportunity_id='dia-das-maes-2025',
    angle='Presentes que toda mãe ama'
)
assert carousel.generation_source.source_type == 'weekly_context'

# Teste Métricas (CRÍTICO)
assert CarouselMetrics.objects.filter(carousel=carousel).exists()
assert carousel.metrics.views_per_slide is not None
```

---

### 📊 Período de Coleta de Dados (1-2 meses)

**Objetivo:** Coletar dados reais antes de desenvolver features adicionais

**O que acontece:**
- ✅ Usuários usam MVP em produção
- ✅ Sistema coleta métricas automaticamente
- ✅ Equipe analisa padrões semanalmente
- ✅ Identifica o que realmente funciona

**Análises a Fazer:**
```python
# Análise 1: Qual origem performa melhor?
origem_performance = {
    'manual': {'avg_engagement': 2.1%, 'completion_rate': 45%},
    'from_post': {'avg_engagement': 6.2%, 'completion_rate': 58%},  # ⭐ MELHOR
    'weekly_context': {'avg_engagement': 3.8%, 'completion_rate': 52%}
}

# Análise 2: Quantos slides é ideal?
slide_count_performance = {
    5: {'completion_rate': 72%},
    6: {'completion_rate': 65%},  # ⭐ SWEET SPOT
    7: {'completion_rate': 52%},
    8: {'completion_rate': 41%},
}

# Análise 3: Onde acontece o drop-off?
drop_off_analysis = {
    'slide_4': 40%,  # ⚠️ CRÍTICO - maioria para aqui
    'slide_5': 25%,
    'slide_6': 20%,
}

# Análise 4: Quais temas engajam mais?
theme_performance = {
    'storytelling': +42%,  # Acima da média
    'antes_depois': +38%,
    'erros_comuns': +35%,
    'dicas_genericas': -15%,  # Abaixo da média
}

# Análise 5: Melhor horário/dia
timing_analysis = {
    'best_days': ['terça', 'quinta'],
    'best_hours': [19, 20, 21],
    'worst_hours': [2, 3, 4, 14, 15]
}
```

**Decisões Data-Driven para Fase 4:**
- ✅ Ajustar slide count padrão (ex: de 7 para 6)
- ✅ Identificar narrativas mais eficazes
- ✅ Detectar padrões de drop-off
- ✅ Priorizar temas que funcionam
- ✅ Sugerir horários ideais
- ✅ Treinar modelo de ML

---

### 🤖 Fase 4: ML e Otimização Inteligente (3-4 sprints) ⭐ PRÓXIMA FASE

> **Quando começar:** Após 1-2 meses de coleta de dados (mínimo 100 carrosséis publicados)

**Objetivo:** Sistema inteligente que otimiza baseado em dados reais

#### Sprint 1: Análise e Modelos

**Entregáveis:**
- [ ] Análise exploratória completa dos dados
- [ ] Identificação de padrões e correlações
- [ ] Definição de modelos de ML (classificação, regressão)
- [ ] Pipeline de treinamento

**Insights Esperados:**
```python
insights_from_data = {
    # Descoberta 1: Origem mais eficaz
    "origem_ideal": "from_post (6.2% engagement vs. 2.1% manual)",
    
    # Descoberta 2: Slide count ótimo
    "slide_count_ideal": 6,  # Não 7!
    
    # Descoberta 3: Drop-off crítico
    "drop_off_pattern": "Slide 4 é crítico - precisa gancho forte",
    
    # Descoberta 4: Temas campeões
    "temas_top": ["storytelling", "antes_depois", "erros_comuns"],
    
    # Descoberta 5: Timing
    "melhor_horario": "19h-21h (terça/quinta)",
    
    # Descoberta 6: Narrativas (inferidas dos temas)
    "narrativas_eficazes": ["tutorial", "before_after", "myths"]
}
```

#### Sprint 2-3: Features Inteligentes

**Entregáveis:**

1. **ML: Sugestão de Origem Ideal**
```python
def suggest_best_origin(user, theme):
    """
    ML decide qual origem usar para maximizar engajamento.
    """
    # Análise do tema + histórico do usuário
    if ml_model.predict_best_source(theme, user.profile) == 'from_post':
        # Buscar post relacionado
        related_post = find_related_daily_post(user, theme)
        if related_post:
            return {
                'recommended': 'expand_post',
                'post_id': related_post.id,
                'reason': 'Post sobre tema similar teve 8.2% engagement',
                'confidence': 0.87
            }
    
    return {'recommended': 'manual', 'confidence': 0.65}
```

2. **ML: Inferir Narrativa Ideal** (Substitui templates manuais!)
```python
def infer_best_narrative(theme, content_analysis):
    """
    ML escolhe narrativa com base em dados históricos.
    NÃO precisa de templates manuais - ML descobriu padrões!
    """
    
    # Análise do tema
    features = extract_theme_features(theme)
    
    # ML prediz narrativa com melhor performance
    narrative = ml_model.predict_narrative(features)
    
    # Exemplos de decisões baseadas em dados:
    if "passo a passo" in theme or "como fazer" in theme:
        return "tutorial"  # Dados: 85% completion rate
    
    if "antes" in theme and "depois" in theme:
        return "before_after"  # Dados: 38% acima da média
    
    if detecta_lista(theme):
        return "list"  # Dados: 70% completion
    
    # Fallback: narrativa com melhor performance geral
    return "storytelling"  # Dados: 42% acima da média
```

3. **ML: Otimizar Slide Count**
```python
def optimize_slide_count(theme, narrative):
    """
    ML sugere número ideal de slides baseado em dados.
    """
    # Dados mostraram que 6 > 7 para maioria dos casos
    base_count = 6  # Não mais 7!
    
    # Ajustes baseados em narrativa
    if narrative == 'tutorial':
        return base_count + 1  # Tutoriais precisam mais detalhes
    
    return base_count
```

4. **ML: Auto-Otimização de Slide 4** (Drop-off Crítico)
```python
def auto_optimize_critical_slides(carousel_draft):
    """
    ML adiciona elementos de retenção em slides críticos.
    """
    # Dados identificaram slide 4 como ponto de drop-off
    slide_4 = carousel_draft.slides[3]
    
    # Adicionar cliffhanger automático
    cliffhangers = [
        "E o melhor vem agora...",
        "Espera! Ainda não acabou →",
        "O próximo é meu favorito →",
        "Você não vai querer perder o próximo"
    ]
    
    slide_4.add_cliffhanger(random.choice(cliffhangers))
    slide_4.has_cliffhanger = True
```

5. **ML: Sugestões Proativas**
```python
def generate_smart_suggestions(user):
    """
    Sistema sugere carrosséis com alta probabilidade de sucesso.
    """
    suggestions = []
    
    # Análise 1: Posts diários com potencial
    for post in user.recent_posts:
        if ml_model.predict_carousel_potential(post) > 0.8:
            suggestions.append({
                'type': 'expand_post',
                'post_id': post.id,
                'reason': f'Post teve {post.engagement_rate}% engagement',
                'expected_improvement': '+45% engagement ao expandir',
                'confidence': 0.89
            })
    
    # Análise 2: Oportunidades do Weekly Context
    for opp in weekly_context.opportunities:
        if ml_model.is_relevant_for_user(opp, user):
            suggestions.append({
                'type': 'opportunity',
                'opportunity_id': opp.id,
                'reason': f'{opp.title} relevante para seu nicho',
                'expected_engagement': '5.8%',
                'confidence': 0.76
            })
    
    # Análise 3: Temas em alta no nicho do usuário
    trending = ml_model.detect_trending_topics(user.niche)
    for topic in trending:
        suggestions.append({
            'type': 'trending',
            'theme': topic.theme,
            'reason': f'Trending +{topic.growth}% esta semana',
            'expected_engagement': '4.2%',
            'confidence': 0.71
        })
    
    return sorted(suggestions, key=lambda x: x['confidence'], reverse=True)
```

6. **ML: Múltiplas Narrativas** (Implementação inteligente)
```python
# Agora que temos dados, implementar narrativas de forma inteligente:
NARRATIVE_TEMPLATES = {
    'tutorial': {
        'priority': 1,  # Dados: 85% completion
        'slide_structure': [...],
        'swipe_elements': ['numbered_steps', 'progress_bar']
    },
    'before_after': {
        'priority': 2,  # Dados: +38% engagement
        'slide_structure': [...],
        'swipe_elements': ['comparison_arrows', 'transformation_indicator']
    },
    'list': {
        'priority': 3,  # Dados: 70% completion (já implementado no MVP)
        'slide_structure': [...],
        'swipe_elements': ['arrows', 'numbering']
    },
    'myths': {
        'priority': 4,  # Dados: 80% completion
        'slide_structure': [...],
        'swipe_elements': ['myth_buster_icon', 'true_false_indicator']
    }
}
# Implementar apenas narrativas que dados mostraram serem eficazes!
```

#### Sprint 4: A/B Testing e Dashboard

**Entregáveis:**
- [ ] A/B testing automático de variantes
- [ ] Dashboard avançado de analytics
- [ ] Recomendações em tempo real
- [ ] Sistema de aprendizado contínuo
- [ ] API de sugestões inteligentes

**Features Avançadas:**
```python
# A/B Testing Automático
def create_ab_test_variants(carousel):
    """
    Gera variantes do carrossel para testar.
    """
    variants = [
        carousel,  # Original
        carousel.with_different_slide_count(6),  # Teste: menos slides
        carousel.with_cliffhangers_removed(),    # Teste: sem cliffhangers
        carousel.with_different_narrative()      # Teste: outra narrativa
    ]
    return variants

# Dashboard de Recomendações
recommendations = {
    'for_you': [
        "Expandir post 'Storytelling' para carrossel (89% confiança)",
        "Criar carrossel sobre 'Dia das Mães' (em 21 dias)",
        "Reduzir slides de 7 para 6 (seus dados mostram +15% completion)"
    ],
    'best_time_to_post': "Terça, 19h-21h (+32% engagement vs. média)",
    'trending_themes': ["storytelling", "antes_depois", "erros_comuns"]
}
```

---

### 🎯 Comparação: Fases 1→2→3→4 vs. Fases 1→4

| Aspecto | Tradicional (1→2→3→4) | Nossa Estratégia (1→4) |
|---------|----------------------|------------------------|
| **Tempo até ML** | 6-8 meses | ⭐ 3-4 meses |
| **Features baseadas em** | Achismo/Suposições | ⭐ Dados reais |
| **Risco de desperdício** | Alto (features não usadas) | ⭐ Baixo (data-driven) |
| **Múltiplas narrativas** | Manual (8 templates) | ⭐ ML infere automaticamente |
| **Otimização** | Tardia, reativa | ⭐ Cedo, proativa |
| **Dívida técnica** | Alta (refactor de Fases 2-3) | ⭐ Baixa |
| **Foco da equipe** | Disperso | ⭐ Concentrado |
| **ROI** | Incerto | ⭐ Validado com dados |

---

### ⚠️ CRÍTICO: Requisitos para Fase 4 Funcionar

**Fase 1 DEVE ter:**
1. ✅ Logging completo de métricas (`CarouselMetrics`)
2. ✅ Integração com Instagram API (métricas por slide)
3. ✅ Rastreamento de origem (`CarouselGenerationSource`)
4. ✅ Mínimo 100 carrosséis publicados
5. ✅ Dados de pelo menos 1-2 meses

**Sem esses dados, Fase 4 não pode ser implementada!**

---

## 📊 Métricas e KPIs

### KPIs de Carrossel

```yaml
Métricas Primárias:
  swipe_through_rate:
    formula: "(views_last_slide / views_first_slide) × 100"
    benchmark_bom: "> 50%"
    benchmark_excelente: "> 60%"
  
  completion_rate:
    formula: "(users_completed / users_started) × 100"
    benchmark_bom: "> 40%"
    benchmark_excelente: "> 55%"

Métricas Secundárias:
  avg_time_per_carousel:
    benchmark: "> 15 segundos"
  
  save_rate:
    formula: "(saves / impressions) × 100"
    benchmark: "> 3%"
  
  engagement_rate:
    formula: "((likes + comments + saves + shares) / impressions) × 100"
    benchmark: "> 2.5%"

Métricas de Qualidade:
  consistency_score:
    descricao: "Avaliação de consistência visual (0-100)"
    benchmark: "> 85"
  
  narrative_flow_score:
    descricao: "Coesão narrativa entre slides (0-100)"
    benchmark: "> 80"
```

### Como Medir (Instagram Insights)

```python
# Dados disponíveis via Instagram API
instagram_metrics = {
    'impressions': int,         # Visualizações totais
    'reach': int,              # Usuários únicos
    'engagement': int,         # Likes + comments + saves + shares
    'saves': int,              # Salvamentos
    'carousel_album_impressions': int,  # Por slide
    'carousel_album_reach': int,        # Por slide
    'carousel_album_engagement': int    # Por slide
}

# Calcular swipe-through
def calculate_swipe_through(carousel_metrics):
    first_slide_impressions = carousel_metrics['slides'][0]['impressions']
    last_slide_impressions = carousel_metrics['slides'][-1]['impressions']
    
    return (last_slide_impressions / first_slide_impressions) * 100
```

---

## 📚 Referências

### Pesquisa de Mercado

- Taxa de engajamento carrosséis: 2.33% vs. 1.74% posts únicos
- Sweet spot: 6-8 slides (50-60% completion rate)
- Algoritmo reexibe carrosséis não visualizados completamente
- Fonte: Instagram Insights & Social Media Examiner (2024)

### Documentação Técnica Instagram

- [Instagram Graph API - Carousel Albums](https://developers.facebook.com/docs/instagram-api/reference/ig-media/)
- [Instagram Content Publishing - Best Practices](https://developers.facebook.com/docs/instagram-api/guides/content-publishing)

### Código Base PostNow

```
PostNow-REST-API/
├── IdeaBank/services/daily_ideas_service.py (linhas 390-451)
├── services/ai_service.py (linha 141+)
├── services/ai_prompt_service.py
├── CreatorProfile/models.py
└── Analytics/services/image_pregen_policy.py
```

### Documentos Relacionados

- `CAROUSEL_PROMPTS.md` - Biblioteca de prompts para carrosséis
- `CAROUSEL_DESIGN_SYSTEM.md` - Guia visual e layouts
- `CAROUSEL_TESTING_GUIDE.md` - Casos de teste
- `ANALISE_COMPLETA_IMAGENS.md` - Sistema de geração de imagens atual
- `CAMPAIGNS_IMPLEMENTATION_GUIDE.md` - Sistema de campanhas

---

## 🔄 Histórico de Decisões

| Data | Decisão | Motivo |
|------|---------|--------|
| Jan 2025 | Usar DailyIdeasService como base | Sistema já tem análise semântica em 3 etapas (98% qualidade) |
| Jan 2025 | 6-8 slides como padrão | Sweet spot de engagement (50-60% completion) |
| Jan 2025 | Logo em primeiro + último slide | Reforça marca sem poluir conteúdo |
| Jan 2025 | Proporção 4:5 (vertical) | Ocupa mais espaço no feed mobile |
| Jan 2025 | Narrativa `list` como MVP | Maior taxa de completion (70%) |

---

## ✅ Checklist Pré-Implementação

- [ ] Documento lido e aprovado pela equipe
- [ ] Arquitetura revisada por tech lead
- [ ] Modelos de dados validados
- [ ] Integrações com sistema existente mapeadas
- [ ] Estimativas de tempo feitas
- [ ] Priorização definida (Fases 1-4)
- [ ] Testes planejados
- [ ] Métricas de sucesso acordadas

---

**Próximos Passos:**
1. Review deste documento com equipe técnica
2. Criar branch: `feature/carousel-implementation`
3. Iniciar Fase 1: MVP Carrossel
4. Sprint planning para primeiras 2 semanas

---

_Documento criado em: Janeiro 2025_  
_Última atualização: Janeiro 2025_  
_Responsável: Equipe PostNow_  
_Status: 📋 Planejamento_

