# 🏗️ GUIA DE IMPLEMENTAÇÃO - Sistema de Campanhas PostNow

## 📋 Documento de Reutilização e Arquitetura

**Data:** 27/Dezembro/2024  
**Baseado em:** Análise completa do código existente  
**Objetivo:** Documentar TUDO que pode ser reutilizado para implementar Campaigns

---

## 🎯 VISÃO GERAL

Este documento mapeia:
1. ✅ **O que já existe** e pode ser reutilizado 100%
2. 🔧 **O que existe** mas precisa de adaptação leve
3. 🆕 **O que precisa ser criado** do zero
4. 📐 **Padrões de código** a seguir (Django + React)

---

# 📚 PARTE 1: BACKEND (Django) - O QUE REUTILIZAR

## 🏛️ Arquitetura de Apps Django

### Padrão Identificado no PostNow

**Estrutura de cada app:**
```
IdeaBank/                          ← Referência principal
├─ __init__.py
├─ apps.py                         # Configuração do app
├─ models.py                       # Post, PostIdea
├─ serializers.py                  # REST serializers
├─ views.py                        # API views (generics + @api_view)
├─ urls.py                         # Rotas do app
├─ admin.py                        # Django admin
├─ services/                       # Lógica de negócio
│   ├─ post_ai_service.py         # Geração com IA
│   ├─ prompt_service.py          # Construção de prompts
│   ├─ ai_model_service.py        # Validação de créditos
│   └─ ...
├─ management/commands/            # Comandos Django
│   └─ ...
├─ migrations/                     # Database migrations
│   └─ ...
└─ tests.py                        # Testes unitários
```

**Para Campaigns, seguir EXATAMENTE esta estrutura:**
```
Campaigns/
├─ __init__.py
├─ apps.py
├─ models.py                       # Campaign, CampaignPost, CampaignDraft, etc
├─ serializers.py
├─ views.py
├─ urls.py
├─ admin.py
├─ services/
│   ├─ campaign_builder_service.py
│   ├─ campaign_intent_service.py
│   ├─ visual_coherence_service.py
│   ├─ quality_validator_service.py
│   └─ weekly_context_integration_service.py
├─ management/commands/
│   ├─ detect_abandoned_campaigns.py
│   └─ update_campaign_bandits.py
├─ migrations/
└─ tests.py
```

---

## ✅ COMPONENTES 100% REUTILIZÁVEIS (Sem Modificação)

### 1. **AuditSystem** - Sistema de Logging

**Localização:** `AuditSystem/services.py`

**O que faz:**
- Log estruturado de todas operações
- Rastreamento de IP, user agent, duração
- Categorias: auth, account, profile, post, content, etc.

**Como usar em Campaigns:**
```python
from AuditSystem.services import AuditService

# Exemplo: Log de criação de campanha
AuditService.log_operation(
    user=request.user,
    operation_category='campaign',  # Nova categoria
    action='campaign_created',
    status='success',
    resource_type='Campaign',
    resource_id=str(campaign.id),
    details={'campaign_name': campaign.name, 'posts_count': campaign.posts.count()},
    request=request
)
```

**Modificações necessárias:**
```python
# AuditSystem/models.py - Adicionar em OPERATION_CHOICES:
OPERATION_CHOICES = [
    ...
    ('campaign', 'Operações de Campanha'),  # NOVO
]

# Adicionar em ACTION_CHOICES:
ACTION_CHOICES = [
    ...
    ('campaign_created', 'Campanha Criada'),  # NOVO
    ('campaign_approved', 'Campanha Aprovada'),  # NOVO
    ('campaign_abandoned', 'Campanha Abandonada'),  # NOVO
    ...
]
```

---

### 2. **Analytics** - Sistema de Bandits e Decisões

**Localização:** `Analytics/models.py`, `Analytics/services/`

**Modelos prontos:**
- `Decision` - Decisões de política
- `BanditArmStat` - Estado do Thompson Sampling
- `DecisionOutcome` - Resultado de decisões
- `AnalyticsEvent` - Eventos de telemetria

**Como usar:**
```python
from Analytics.models import Decision, BanditArmStat

# Criar nova decisão para campanhas
decision = Decision.objects.create(
    decision_type='campaign_type_suggestion',  # Novo tipo
    action='branding',  # Escolhido pelo bandit
    policy_id='campaign_type_thompson_v1',
    user=user,
    resource_type='Campaign',
    resource_id=str(campaign_draft.id),
    context={'bucket': 'niche=legal|maturity=new', ...}
)
```

**Serviços existentes para reutilizar:**
- `image_pregen_policy.py` - Template perfeito para campaign decisions
- `text_variant_policy.py` - Estrutura de decisões

**Adaptar para Campaigns:**
```python
# Analytics/services/campaign_policy.py (NOVO arquivo)

DECISION_TYPE_CAMPAIGN_TYPE = "campaign_type_suggestion"
DECISION_TYPE_CAMPAIGN_STRUCTURE = "campaign_structure"
DECISION_TYPE_VISUAL_STYLE = "visual_style_curation"

def make_campaign_type_decision(user, context):
    """
    Decisão de qual tipo de campanha sugerir
    Segue EXATAMENTE mesmo padrão de image_pregen_policy.py
    """
    # Copiar e adaptar lógica de choose_action_thompson()
    ...
```

---

### 3. **CreditSystem** - Validação e Dedução

**Localização:** `CreditSystem/models.py`, `CreditSystem/middleware.py`

**100% reutilizável:**
- Middleware de validação de créditos
- Modelos: `UserCredits`, `CreditTransaction`
- Lógica de dedução

**Não precisa modificar nada!**

Campanhas vão consumir créditos através dos Posts:
```python
# Campaigns/services/campaign_builder_service.py

def generate_campaign_posts(campaign):
    for post_data in campaign_structure:
        # Usa PostAIService existente (que já valida créditos!)
        post_ai_service = PostAIService()
        result = post_ai_service.generate_post_content(
            user=campaign.user,
            post_data=post_data
        )
        # Créditos já foram deduzidos automaticamente
```

---

### 4. **PostAIService** - Geração de Conteúdo com IA

**Localização:** `IdeaBank/services/post_ai_service.py`

**Reutilização: 95%**

```python
from IdeaBank.services.post_ai_service import PostAIService

# Em Campaigns, usar direto:
post_ai_service = PostAIService()
result = post_ai_service.generate_post_content(
    user=campaign.user,
    post_data={
        'name': f'{campaign.name} - Post {sequence}',
        'objective': post_structure['objective'],
        'type': post_structure['type'],
        'further_details': post_structure['theme'],
        'include_image': True
    }
)
```

**O que PostAIService JÁ FAZ:**
- ✅ Validação de créditos
- ✅ Geração de texto com IA (Gemini, OpenAI, Anthropic)
- ✅ Geração de imagem (se include_image=True)
- ✅ Dedução de créditos
- ✅ Logging e auditoria
- ✅ Fallback entre providers
- ✅ Usa dados do CreatorProfile automaticamente

**Linha 98 de post_ai_service.py:**
```python
# Special handling for campaign type - generate 3 posts
if post_data.get('type', '').lower() == 'campaign':
    return self._generate_campaign_content(user, post_data, provider, model)
```

**JÁ EXISTE lógica para campanhas!** Pode ser expandida.

---

### 5. **PromptService** - Construção de Prompts

**Localização:** `IdeaBank/services/prompt_service.py`

**1086 linhas de prompts profissionais!**

**Reutilização: 100%**

```python
from IdeaBank.services.prompt_service import PromptService

# Usa direto (já puxa CreatorProfile automaticamente):
prompt_service = PromptService()
prompt_service.user = campaign.user
prompt = prompt_service.build_content_prompt(post_data)
```

**O que PromptService JÁ FAZ:**
- ✅ Acessa `CreatorProfile` automaticamente
- ✅ Incorpora: business_name, specialization, target_audience, voice_tone, etc.
- ✅ Prompts otimizados para Feed, Reel, Story
- ✅ Aplica método AIDA
- ✅ Compliance com Meta/Google Ads

**Para Campaigns:**
- Criar método adicional: `build_campaign_post_prompt(post_data, campaign_structure)`
- Adiciona contexto da fase da campanha (Atenção, Interesse, Desejo, Ação)

---

### 6. **WeeklyContextService** - Busca de Oportunidades

**Localização:** `ClientContext/services/weekly_context_service.py`

**Reutilização: 90%**

```python
from ClientContext.services.weekly_context_service import WeeklyContextService

# Buscar oportunidades para campanhas:
service = WeeklyContextService()
opportunities = await service.get_opportunities_for_user(
    user=campaign.user,
    min_score=90,
    limit=3
)
```

**Já está pronto!** Sistema de:
- Busca de notícias relevantes
- Ranking por score
- Anti-repetição
- Validação de URLs

**Adaptação necessária:**
```python
# Campaigns/services/weekly_context_integration_service.py (NOVO)

class WeeklyContextCampaignIntegration:
    """
    Adapter entre Weekly Context e Campaigns
    """
    def find_relevant_for_campaign(self, campaign, min_score=90):
        """
        Filtra oportunidades relevantes para campanha específica
        """
        all_opportunities = WeeklyContextService.get_opportunities(user)
        
        # Filtra por alinhamento com objetivo da campanha
        relevant = [
            opp for opp in all_opportunities
            if self._matches_campaign_objective(opp, campaign)
            and opp.score >= min_score
        ]
        
        return relevant[:3]
```

---

## 🔧 COMPONENTES QUE PRECISAM ADAPTAÇÃO LEVE

### 1. **Post Model** - Reutilizar para CampaignPost

**Modelo atual:**
```python
# IdeaBank/models.py
class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    objective = models.CharField(choices=PostObjective.choices)
    type = models.CharField(choices=PostType.choices)
    further_details = models.TextField()
    include_image = models.BooleanField()
    is_automatically_generated = models.BooleanField()
    created_at = models.DateTimeField(auto_now_add=True)
```

**Para Campaigns:**
```python
# Campaigns/models.py

# REUTILIZA Post existente (composição):
class CampaignPost(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='campaign_posts')
    post = models.ForeignKey('IdeaBank.Post', on_delete=models.CASCADE)
    
    # Metadados específicos de campanha:
    sequence_order = models.IntegerField()
    scheduled_date = models.DateField()
    scheduled_time = models.TimeField(default='09:00')
    phase = models.CharField(max_length=50)  # 'awareness', 'interest', etc
    
    is_approved = models.BooleanField(default=False)
    approved_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['campaign', 'sequence_order']
        unique_together = ['campaign', 'sequence_order']
```

**Vantagem:** Não duplica lógica. Post e PostIdea continuam fazendo o que sabem fazer.

---

### 2. **Serializers Pattern** - Seguir Padrão Existente

**Padrão identificado em `IdeaBank/serializers.py`:**

```python
# Sempre ter:
# 1. Serializer de listagem (read)
# 2. Serializer de criação (write)
# 3. Serializer com related (nested)
# 4. Serializer para request validation

class CampaignSerializer(serializers.ModelSerializer):
    """Listagem de campanhas"""
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    posts_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Campaign
        fields = ['id', 'name', 'type', 'type_display', 'posts_count', ...]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_posts_count(self, obj):
        return obj.campaign_posts.count()


class CampaignCreateSerializer(serializers.ModelSerializer):
    """Criação de campanha"""
    class Meta:
        model = Campaign
        fields = ['name', 'type', 'objective', ...]


class CampaignWithPostsSerializer(serializers.ModelSerializer):
    """Campanha com posts nested"""
    campaign_posts = CampaignPostSerializer(many=True, read_only=True)
    
    class Meta:
        model = Campaign
        fields = ['id', 'name', 'campaign_posts', ...]


class CampaignGenerationRequestSerializer(serializers.Serializer):
    """Validação de request de geração"""
    objective = serializers.CharField()
    message = serializers.CharField()
    duration_days = serializers.IntegerField()
    # ...
```

---

### 3. **Views Pattern** - Class-Based + Function-Based

**Padrão identificado:**

```python
# IdeaBank/views.py

# CRUD: Class-based views (DRF generics)
class PostListView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PostSerializer
    
    def get_queryset(self):
        return Post.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        if self.request.method == "POST":
            return PostCreateSerializer
        return PostSerializer
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        AuditService.log_post_operation(...)  # SEMPRE logar


# Operações customizadas: Function-based (@api_view)
@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def generate_post_idea(request):
    serializer = PostGenerationRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({"error": ..., "details": serializer.errors}, status=400)
    
    try:
        # Lógica...
        return Response({"success": True, "data": ...}, status=200)
    except Exception as e:
        return Response({"error": str(e)}, status=500)
```

**Para Campaigns:**
```python
# Campaigns/views.py

# CRUD básico
class CampaignListView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CampaignSerializer
    
    def get_queryset(self):
        return Campaign.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        campaign = serializer.save(user=self.request.user)
        AuditService.log_operation(
            user=self.request.user,
            operation_category='campaign',
            action='campaign_created',
            ...
        )

# Geração de campanha (customizado)
@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def generate_campaign_content(request, campaign_id):
    # Seguir padrão de generate_post_idea()
    ...
```

---

### 4. **URLs Pattern** - app_name + urlpatterns

**Padrão identificado:**

```python
# IdeaBank/urls.py

app_name = 'ideabank'  # Sempre definir

urlpatterns = [
    # CRUD
    path('posts/', views.PostListView.as_view(), name='post-list'),
    path('posts/<int:pk>/', views.PostDetailView.as_view(), name='post-detail'),
    
    # Operações customizadas
    path('generate/post-idea/', views.generate_post_idea, name='generate-post-idea'),
    
    # Cron jobs
    path('cron/daily-content-generation/', views.vercel_cron_daily_content_generation),
]
```

**Para Campaigns:**
```python
# Campaigns/urls.py

app_name = 'campaigns'

urlpatterns = [
    # CRUD
    path('', views.CampaignListView.as_view(), name='campaign-list'),
    path('<int:pk>/', views.CampaignDetailView.as_view(), name='campaign-detail'),
    
    # Operações de campanha
    path('drafts/', views.CampaignDraftListView.as_view(), name='draft-list'),
    path('<int:pk>/generate/', views.generate_campaign_content, name='generate-content'),
    path('<int:pk>/approve/', views.approve_campaign, name='approve-campaign'),
    path('<int:pk>/posts/<int:post_id>/approve/', views.approve_campaign_post),
    
    # Weekly Context integration
    path('<int:pk>/opportunities/', views.get_weekly_context_opportunities),
    path('<int:pk>/opportunities/<int:opp_id>/add/', views.add_opportunity_to_campaign),
    
    # Auto-save
    path('drafts/save/', views.save_campaign_draft, name='save-draft'),
    
    # Cron (se necessário)
    path('cron/detect-abandoned/', views.detect_abandoned_campaigns),
]
```

**Registrar em URLs principais:**
```python
# Sonora_REST_API/urls.py

urlpatterns = [
    ...
    path('api/v1/campaigns/', include('Campaigns.urls')),  # NOVO
]
```

---

Continua no próximo arquivo (dividindo por tamanho)...

