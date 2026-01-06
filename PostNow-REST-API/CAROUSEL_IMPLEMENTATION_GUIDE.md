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

### Novo Modelo: CarouselPost

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
            ('tutorial', 'Tutorial Passo-a-Passo'),
            ('list', 'Lista/Checklist'),
            ('story', 'Storytelling'),
            ('comparison', 'Comparação'),
            ('before_after', 'Antes e Depois'),
            ('myths', 'Mitos vs. Verdades'),
            ('infographic', 'Infográfico'),
            ('quiz', 'Quiz/Teste'),
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
```

### Novo Service: CarouselGenerationService

```python
# Criar em IdeaBank/services/carousel_generation_service.py

class CarouselGenerationService:
    """
    Service para geração de carrosséis usando base do DailyIdeasService.
    
    Fluxo:
    1. Análise semântica do tema (3 etapas - reuso)
    2. Escolha de tipo de narrativa
    3. Estruturação de slides (6-8)
    4. Geração de texto para cada slide
    5. Análise visual contextual
    6. Geração de imagens harmônicas
    7. Aplicação de elementos de swipe
    8. Logo estratégica
    9. Validação de consistência
    """
    
    def __init__(self):
        self.daily_ideas_service = DailyIdeasService()
        self.prompt_service = AIPromptService()
        self.ai_service = AiService()
        self.s3_service = S3Service()
    
    def generate_carousel(
        self,
        user: User,
        theme: str,
        narrative_type: str = 'list',
        slide_count: int = 7,
        logo_placement: str = 'first_last'
    ) -> CarouselPost:
        """
        Gera um carrossel completo.
        
        Args:
            user: Usuário que está criando
            theme: Tema/assunto do carrossel
            narrative_type: Tipo de narrativa (tutorial, list, story, etc)
            slide_count: Número de slides (recomendado: 6-8)
            logo_placement: Onde colocar a logo
        
        Returns:
            CarouselPost com todos os slides gerados
        """
        
        # 1. Análise Semântica (reusa DailyIdeasService)
        semantic_analysis = self._perform_semantic_analysis(user, theme)
        
        # 2. Estruturar Narrativa
        slides_structure = self._structure_narrative(
            theme, narrative_type, slide_count, semantic_analysis
        )
        
        # 3. Gerar Texto dos Slides
        slides_content = self._generate_slides_text(
            user, slides_structure, semantic_analysis
        )
        
        # 4. Gerar Imagens Harmônicas
        slides_with_images = self._generate_harmonic_images(
            user, slides_content, logo_placement
        )
        
        # 5. Criar CarouselPost no banco
        carousel_post = self._save_carousel_to_db(
            user, theme, narrative_type, slides_with_images, logo_placement
        )
        
        return carousel_post
```

**Ver código completo em:** `CAROUSEL_PROMPTS.md`

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

### Fase 1: MVP Carrossel (2-3 sprints)

**Objetivo:** Gerar carrosséis básicos funcionais

**Entregáveis:**
- [ ] Modelo `CarouselPost` e `CarouselSlide`
- [ ] `CarouselGenerationService` básico
- [ ] Tipo de narrativa: `list` (lista/checklist)
- [ ] 7 slides fixos
- [ ] Logo em primeiro e último slide
- [ ] Elementos básicos de swipe (setas + numeração)
- [ ] Reuso completo do sistema de análise semântica
- [ ] Endpoint API: `POST /api/v1/carousel/generate/`

**Validação:**
```python
# Teste mínimo viável
carousel = CarouselGenerationService().generate_carousel(
    user=user,
    theme="5 dicas para aumentar engajamento no Instagram",
    narrative_type='list',
    slide_count=7,
    logo_placement='first_last'
)

assert carousel.slides.count() == 7
assert carousel.slides.first().image_url != ''
assert carousel.slides.first().has_arrow == True
assert carousel.slides.first().has_numbering == True
```

### Fase 2: Múltiplas Narrativas (2 sprints)

**Objetivo:** Suportar diferentes tipos de narrativa

**Entregáveis:**
- [ ] Template: `tutorial` (passo-a-passo)
- [ ] Template: `story` (storytelling)
- [ ] Template: `before_after` (antes e depois)
- [ ] Template: `comparison` (comparação)
- [ ] Prompts especializados por tipo
- [ ] Escolha automática de narrativa baseada no tema
- [ ] Análise de harmonia visual entre slides

### Fase 3: Inteligência de Swipe (1-2 sprints)

**Objetivo:** Maximizar taxa de swipe-through

**Entregáveis:**
- [ ] Cliffhangers automáticos entre slides
- [ ] Barra de progresso visual
- [ ] Variação de cor gradiente
- [ ] CTAs intermediários dinâmicos
- [ ] Análise de "tensão narrativa"
- [ ] A/B testing de elementos de swipe

### Fase 4: Otimização e Analytics (1 sprint)

**Objetivo:** Medir e melhorar performance

**Entregáveis:**
- [ ] Métricas de swipe-through
- [ ] Dashboard de performance
- [ ] Aprendizado de máquina (qual narrativa funciona melhor)
- [ ] Sugestão automática de melhorias
- [ ] Variantes automáticas para teste

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

