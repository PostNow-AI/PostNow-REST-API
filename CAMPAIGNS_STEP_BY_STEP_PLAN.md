# 📋 PLANO PASSO-A-PASSO - Implementação de Campaigns

## Seguindo Padrões Exatos do PostNow Atual

**Baseado em:** Análise completa do código existente  
**Objetivo:** Implementar mantendo mesma qualidade e estilo

---

## 🎯 PRINCÍPIOS NORTEADORES

### Do Django Rules (`.cursor/rules/django-rules.mdc`)

✅ **Django-First Approach:** Usar ferramentas built-in  
✅ **Modular Architecture:** Apps independentes  
✅ **Query Optimization:** select_related, prefetch_related  
✅ **Unified Response Format:**
```python
{
    "success": true/false,
    "data": {...},
    "message": "..."
}
```

### Do React Rules (`.cursor/rules/react-vite-rules.mdc`)

✅ **TanStack Query:** Caching e mutations  
✅ **React Hook Form + Zod:** Formulários  
✅ **Axios:** API calls  
✅ **Early returns:** Readability  
✅ **Tailwind:** Styling (zero CSS manual)  
✅ **Português:** Todo texto visível

---

# 🚀 SPRINT 1-2: Foundation (Semanas 1-2)

## Backend

### Tarefa 1.1: Criar App `Campaigns/`

```bash
cd PostNow-REST-API
python manage.py startapp Campaigns
```

### Tarefa 1.2: Configurar App

```python
# Campaigns/apps.py (seguir padrão de IdeaBank)

from django.apps import AppConfig

class CampaignsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Campaigns'
    verbose_name = 'Campanhas de Marketing'
```

**Registrar em settings:**
```python
# Sonora_REST_API/settings.py

INSTALLED_APPS = [
    ...
    'IdeaBank',
    'Campaigns',  # NOVO
    'Analytics',
    ...
]
```

### Tarefa 1.3: Models Iniciais

```python
# Campaigns/models.py (seguir padrão de IdeaBank/models.py)

from django.contrib.auth.models import User
from django.db import models

class CampaignType(models.TextChoices):
    BRANDING = 'branding', 'Branding e Posicionamento'
    SALES = 'sales', 'Campanha de Vendas'
    LAUNCH = 'launch', 'Lançamento de Produto/Serviço'
    EDUCATION = 'education', 'Educação de Mercado'
    ENGAGEMENT = 'engagement', 'Engajamento'
    LEAD_GEN = 'lead_generation', 'Geração de Leads'

class CampaignStatus(models.TextChoices):
    DRAFT = 'draft', 'Rascunho'
    ACTIVE = 'active', 'Ativa'
    COMPLETED = 'completed', 'Concluída'
    PAUSED = 'paused', 'Pausada'

class Campaign(models.Model):
    """Campanha publicitária completa."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='campaigns')
    
    # Informações básicas
    name = models.CharField(max_length=200, help_text="Nome da campanha")
    type = models.CharField(max_length=50, choices=CampaignType.choices)
    objective = models.TextField(help_text="Objetivo macro da campanha")
    main_message = models.TextField(help_text="Mensagem principal a comunicar")
    
    # Estrutura
    structure = models.CharField(max_length=50)  # 'aida', 'pas', 'funil', etc
    duration_days = models.IntegerField()
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    
    # Configurações de geração
    post_frequency = models.IntegerField(default=3)
    content_mix = models.JSONField(default=dict)  # {'feed': 0.5, 'reel': 0.3, 'story': 0.2}
    visual_styles = models.JSONField(default=list)  # ['minimal', 'corporate']
    
    # Status
    status = models.CharField(max_length=20, choices=CampaignStatus.choices, default='draft')
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'campaigns'
        verbose_name = 'Campanha'
        verbose_name_plural = 'Campanhas'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.get_type_display()}"


class CampaignPost(models.Model):
    """Post individual dentro de uma campanha."""
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='campaign_posts')
    post = models.ForeignKey('IdeaBank.Post', on_delete=models.CASCADE)
    
    # Posição na campanha
    sequence_order = models.IntegerField()
    scheduled_date = models.DateField()
    scheduled_time = models.TimeField(default='09:00:00')
    phase = models.CharField(max_length=50)  # 'awareness', 'interest', 'desire', 'action'
    
    # Status
    is_approved = models.BooleanField(default=False)
    approved_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'campaign_posts'
        ordering = ['campaign', 'sequence_order']
        unique_together = ['campaign', 'sequence_order']


class CampaignDraft(models.Model):
    """Auto-save de campanhas em progresso."""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, default='in_progress')
    
    current_phase = models.CharField(max_length=50)  # 'briefing', 'structure', 'styles', etc
    
    # Estado salvo (JSONField para flexibilidade)
    briefing_data = models.JSONField(default=dict)
    structure_chosen = models.CharField(max_length=50, null=True, blank=True)
    styles_chosen = models.JSONField(default=list)
    posts_data = models.JSONField(default=list)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'campaign_drafts'
        ordering = ['-updated_at']
```

### Tarefa 1.4: Migrations

```bash
python manage.py makemigrations Campaigns
python manage.py migrate
```

---

## Frontend

### Tarefa 1.5: Estrutura de Pastas

```bash
cd PostNow-UI/src/features
mkdir -p Campaigns/{pages,components/{wizard,approval,preview,shared},hooks,services,types,constants}
```

### Tarefa 1.6: Types TypeScript

```typescript
// features/Campaigns/types/index.ts

export interface Campaign {
  id: number;
  name: string;
  type: string;
  type_display: string;
  objective: string;
  main_message: string;
  structure: string;
  duration_days: number;
  status: string;
  posts_count: number;
  created_at: string;
  updated_at: string;
}

export interface CampaignPost {
  id: number;
  campaign_id: number;
  post_id: number;
  sequence_order: number;
  scheduled_date: string;
  phase: string;
  is_approved: boolean;
}

// ... mais types
```

### Tarefa 1.7: Service Skeleton

```typescript
// features/Campaigns/services/index.ts

import { api } from "@/lib/api";

export const campaignService = {
  async getCampaigns(): Promise<Campaign[]> {
    const response = await api.get("/api/v1/campaigns/");
    return response.data;
  },
  
  // ... mais métodos (implementar progressivamente)
};
```

---

# 🚀 SPRINT 3-4: Wizard de Criação (Semanas 3-4)

## Backend

### Tarefa 3.1: Serializers

```python
# Campaigns/serializers.py (seguir padrão de IdeaBank)

from rest_framework import serializers
from .models import Campaign, CampaignPost

class CampaignSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    posts_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Campaign
        fields = [
            'id', 'name', 'type', 'type_display', 'objective', 'main_message',
            'structure', 'duration_days', 'status', 'status_display',
            'posts_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_posts_count(self, obj):
        return obj.campaign_posts.count()


class CampaignCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Campaign
        fields = ['name', 'type', 'objective', 'main_message', 'structure', 'duration_days']
```

### Tarefa 3.2: Views CRUD

```python
# Campaigns/views.py

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .models import Campaign
from .serializers import CampaignSerializer, CampaignCreateSerializer
from AuditSystem.services import AuditService

class CampaignListView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CampaignSerializer
    
    def get_queryset(self):
        return Campaign.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        if self.request.method == "POST":
            return CampaignCreateSerializer
        return CampaignSerializer
    
    def perform_create(self, serializer):
        campaign = serializer.save(user=self.request.user)
        
        AuditService.log_operation(
            user=self.request.user,
            operation_category='campaign',
            action='campaign_created',
            status='success',
            resource_type='Campaign',
            resource_id=str(campaign.id),
            details={'campaign_name': campaign.name}
        )


class CampaignDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CampaignSerializer
    
    def get_queryset(self):
        return Campaign.objects.filter(user=self.request.user)
```

## Frontend

### Tarefa 3.3: Página Dashboard

```typescript
// features/Campaigns/pages/CampaignsDashboard.tsx

import { Container, Button } from "@/components/ui";
import { Plus } from "lucide-react";
import { useCampaigns } from "../hooks";

export const CampaignsDashboard = () => {
  const { campaigns, isLoading } = useCampaigns();
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  
  return (
    <Container
      headerTitle="Suas Campanhas"
      headerDescription="Gerencie campanhas de marketing completas"
      containerActions={
        <Button onClick={() => setIsCreateOpen(true)}>
          <Plus className="h-4 w-4" />
          Nova Campanha
        </Button>
      }
    >
      {isLoading ? (
        <LoadingSkeleton />
      ) : (
        <CampaignList campaigns={campaigns} />
      )}
      
      <CampaignCreationDialog 
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
      />
    </Container>
  );
};
```

---

# 📊 MAPEAMENTO COMPLETO DE REUTILIZAÇÃO

## O QUE JÁ EXISTE E FUNCIONA

### Backend Django

✅ **Sistema de Autenticação (JWT)**
- Middleware de auth
- Permissions
- User model
- **Ação:** Nenhuma

✅ **CreatorProfile com TODOS os dados**
- business_name, specialization, target_audience
- color_palette (5 cores)
- visual_style_ids
- voice_tone
- **Ação:** Reutilizar direto nos prompts

✅ **Sistema de Créditos Completo**
- Validação automática (middleware)
- Dedução
- Transações
- **Ação:** Funciona automaticamente

✅ **PostAIService (Orquestrador de IA)**
- Gemini, OpenAI, Anthropic
- Fallback automático
- Validação de créditos
- **Linha 98:** JÁ TEM lógica para campanhas!
- **Ação:** Expandir método `_generate_campaign_content()`

✅ **PromptService (1086 linhas!)**
- Prompts profissionais prontos
- Acessa CreatorProfile automaticamente
- **Ação:** Adicionar método `build_campaign_post_prompt()`

✅ **AuditSystem (Logging completo)**
- **Ação:** Adicionar category 'campaign'

✅ **Analytics (Bandits prontos!)**
- Decision, BanditArmStat, DecisionOutcome
- Thompson Sampling implementado
- **Ação:** Criar novos decision_types

✅ **WeeklyContextService**
- Busca de oportunidades
- Ranking, anti-repetição
- **Ação:** Criar adapter para campanhas

### Frontend React

✅ **Design System Completo (36 componentes)**
- Button, Card, Dialog, Form, Tabs, Checkbox, etc.
- **Ação:** Reutilizar 100%

✅ **API Client (axios com interceptors)**
- Auth automático
- Token refresh
- Error handling
- **Ação:** Reutilizar 100%

✅ **TanStack Query Setup**
- QueryClient configurado
- Padrões de hooks
- **Ação:** Seguir padrão

✅ **React Hook Form + Zod**
- Todos formulários seguem mesmo padrão
- **Ação:** Seguir padrão

✅ **InstagramPreview (WeeklyContext)**
- JÁ existe preview de Instagram!
- **Ação:** Adaptar para grid 3x3

✅ **Container Layout**
- Usado em TODAS as páginas
- **Ação:** Reutilizar

---

## 🆕 O QUE PRECISA SER CRIADO (Novo)

### Backend (5% novo)

1. **Models específicos:**
   - `Campaign` (principal)
   - `CampaignPost` (join table)
   - `CampaignDraft` (auto-save)
   - `CampaignTemplate` (opcional V2)

2. **Services novos:**
   - `campaign_builder_service.py` (orquestra geração)
   - `visual_coherence_service.py` (analisa harmonia)
   - `quality_validator_service.py` (valida posts)

3. **Constants:**
   - Estruturas narrativas (AIDA, PAS, Funil)
   - Dados de cada framework

4. **Bandit policies:**
   - `campaign_policy.py` (decisions)

### Frontend (10% novo)

1. **Componentes específicos:**
   - `CampaignCreationWizard` (multi-step)
   - `PostGridView` (grid com checkboxes)
   - `InstagramFeedPreview` (grid 3x3 draggable)
   - `HarmonyAnalyzer` (score visual)
   - `VisualStylePicker` (biblioteca de estilos)

2. **Hooks:**
   - `useCampaignCreation`
   - `useCampaignAutoSave`
   - `useVisualHarmony`

3. **Pages:**
   - `CampaignsDashboard`
   - `CampaignCreation`
   - `CampaignDetail`

---

## 📈 ESTIMATIVA DE ESFORÇO POR TAREFA

| Tarefa | Reutilização | Novo | Esforço |
|--------|--------------|------|---------|
| Models | 70% (Post model) | 30% (Campaign) | 1 dia |
| Serializers | 90% (padrão) | 10% (específicos) | 1 dia |
| Views CRUD | 95% (padrão DRF) | 5% (config) | 1 dia |
| Views Custom | 60% (padrão) | 40% (lógica) | 3 dias |
| Services IA | 80% (PostAIService) | 20% (campaign logic) | 2 dias |
| Services Validation | 0% | 100% | 3 dias |
| Services Coherence | 0% | 100% | 2 dias |
| Bandit Integration | 80% (estrutura) | 20% (policies) | 2 dias |
| **BACKEND TOTAL** | **75%** | **25%** | **15 dias** |
|  |  |  |  |
| Components UI | 100% (shadcn) | 0% | 0 dias |
| Wizard | 70% (Dialog) | 30% (steps) | 3 dias |
| Grid Approval | 60% (PostList) | 40% (checkboxes) | 2 dias |
| Feed Preview | 50% (Instagram Preview) | 50% (grid 3x3) | 3 dias |
| Hooks TanStack | 90% (padrão) | 10% (específicos) | 2 dias |
| Services API | 95% (padrão) | 5% (endpoints) | 1 dia |
| Types | 80% (Post types) | 20% (Campaign) | 1 dia |
| **FRONTEND TOTAL** | **80%** | **20%** | **12 dias** |
|  |  |  |  |
| **TOTAL GERAL** | **~78%** | **~22%** | **27 dias (5.4 semanas)** |

**Com equipe de 2 devs: 3 semanas**  
**Com equipe de 3 devs: 2 semanas**

---

## 🎯 PRÓXIMO PASSO IMEDIATO

Você pediu para NÃO desenvolver ainda. Então recomendo:

### ✅ AGORA (Próximas 2h):

1. **Ler estes 3 documentos:**
   - `CAMPAIGNS_IMPLEMENTATION_GUIDE.md` (Backend)
   - `CAMPAIGNS_FRONTEND_REUSE_GUIDE.md` (Frontend)
   - `CAMPAIGNS_STEP_BY_STEP_PLAN.md` (Este arquivo)

2. **Validar entendimento:**
   - Reutilizamos 78% do código existente
   - Apenas 22% precisa ser criado
   - Padrões estão documentados

3. **Decidir:**
   - Aprovar para desenvolvimento?
   - Quer protótipo Figma antes?
   - Recrutar beta users agora?

### ⏭️ DEPOIS (Quando aprovar):

1. **Mudar para Agent Mode**
2. **Começar Sprint 1:** Criar models e migrations
3. **Beta paralelo:** Recrutar 10 usuários

---

**Documentação completa de reutilização finalizada!** 📚✅

