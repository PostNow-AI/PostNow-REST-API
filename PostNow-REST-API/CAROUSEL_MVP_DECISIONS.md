# 📋 Decisões do MVP - Carrosséis Instagram

> **Data:** Janeiro 2025  
> **Status:** ✅ Todas Decisões Tomadas  
> **Pronto para:** Desenvolvimento Imediato

---

## 🎯 **DECISÕES FINAIS - SESSÃO DE DEFINIÇÃO**

### ✅ **Sistema de Créditos**

**Decisão:** Usar créditos existentes do usuário, **SEM deduzir no MVP**

**Motivo:**
- Usando créditos de desenvolvedor do Gemini
- Foco em validar funcionalidade, não em economia
- Simplifica implementação do MVP

**Implementação:**
```python
# Validação simples (usuário tem créditos?)
if CreditService.get_user_balance(user) > 0:
    # Permite gerar
    # NÃO deduzir no MVP
    pass
```

**Fase Futura:** Implementar cobrança após validação com usuários reais

---

### ✅ **Limites e Tiers**

**Decisão:** **SEM limites diários, SEM distinção free/premium**

**Motivo:**
- MVP foca em funcionalidade
- Não há distinção de planos no sistema atual
- Simplifica validação e testes

**Implementação:**
```python
# NÃO implementar no MVP:
# MAX_CAROUSELS_PER_DAY_FREE = 10
# MAX_CAROUSELS_PER_DAY_PREMIUM = 50
```

**Fase Futura:** Considerar limites se houver abuso

---

### ✅ **Preview Antes de Gerar**

**Decisão:** **NÃO implementar**

**Motivo:**
- Adiciona complexidade desnecessária
- Usuário pode editar depois (CRUD)
- Geração é rápida (~30-60 segundos)
- Foco em fluxo ágil

**Alternativa:** Sistema de edição completo após geração

---

### ✅ **Publicação no Instagram**

**Decisão:** **NÃO implementar no MVP → Fase 5**

**Motivo:**
- Requer integração complexa com Instagram Graph API
- Requer OAuth 2.0 Instagram/Facebook
- Não é crítico para validar geração de conteúdo
- MVP foca em criar carrosséis, não publicá-los

**Fase 5 incluirá:**
- Sprint 1: OAuth Instagram
- Sprint 2: Publicação
- Sprint 3: Captura de métricas

---

### ✅ **Captura de Métricas do Instagram**

**Decisão:** **NÃO implementar no MVP → Fase 5**

**Motivo:**
- Depende de publicação no Instagram
- Requer polling ou webhooks
- MVP foca em geração de conteúdo
- Métricas básicas (tempo de geração, origem) são suficientes

**MVP implementará:**
```python
class CarouselMetrics(models.Model):
    # ✅ MVP: Apenas básicos
    generation_time = models.FloatField()
    generation_source = models.CharField()
    
    # ⏸️ Fase 5: Campos do Instagram (null=True)
    impressions = models.IntegerField(null=True)
    views_per_slide = models.JSONField(null=True)
    swipe_through_rate = models.FloatField(default=0.0)
```

---

### ✅ **Edição de Slides**

**Decisão:** **Seguir padrão CRUD existente**

**Motivo:**
- Projeto já tem padrão estabelecido
- Consistência com IdeaBank, Campaigns
- `RetrieveUpdateDestroyAPIView` do DRF

**Implementação:**
```python
class CarouselDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CarouselPostSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return CarouselPost.objects.filter(post__user=self.request.user)

# Permite: GET, PATCH, PUT, DELETE
```

**Campos editáveis:**
- Título do carrossel
- Título de slides individuais
- Conteúdo de slides individuais
- Ordem dos slides (reordenação)

---

## 📊 **ESCOPO MVP - O QUE IMPLEMENTAR**

### ✅ **Backend (Django)**

```yaml
Modelos:
  - ✅ CarouselPost
  - ✅ CarouselSlide
  - ✅ CarouselGenerationSource
  - ✅ CarouselMetrics (estrutura básica)

Services:
  - ✅ CarouselGenerationService
    - generate_from_manual_input()
    - generate_from_daily_post()
    - generate_from_opportunity()
  - ✅ Reuso completo de DailyIdeasService

API Endpoints:
  Geração:
    - POST /api/v1/carousel/generate/
    - POST /api/v1/carousel/expand-post/
    - POST /api/v1/carousel/from-opportunity/
  
  CRUD:
    - GET  /api/v1/carousel/
    - GET  /api/v1/carousel/<id>/
    - PATCH /api/v1/carousel/<id>/
    - DELETE /api/v1/carousel/<id>/
  
  Helpers:
    - GET /api/v1/carousel/suggestions/

Validações:
  - ✅ Validação simples de créditos (has credits?)
  - ✅ NÃO deduzir créditos
  - ✅ NÃO limites diários
  - ✅ Validação de posts expansíveis
  - ✅ Validação de slide count (2-10)
```

### ✅ **Frontend (React + Vite)**

```yaml
Telas:
  - ✅ Seleção de origem
    - Manual
    - Posts Diários
    - Oportunidades
  
  - ✅ Formulários
    - Input manual (tema)
    - Lista de posts sugeridos
    - Lista de oportunidades
  
  - ✅ Visualização
    - Preview de carrossel
    - Edição inline de slides
    - Reordenação drag & drop
  
  - ✅ Lista
    - Grid de carrosséis criados
    - Filtros e busca

Componentes:
  - ✅ CarouselOriginSelector
  - ✅ ManualCarouselForm
  - ✅ PostSuggestionsList
  - ✅ OpportunitiesList
  - ✅ CarouselEditor
  - ✅ CarouselGrid
```

---

## ❌ **FORA DO ESCOPO MVP**

### **NÃO Implementar:**

```yaml
❌ Fase 2-3 (Decidimos pular):
  - Múltiplas narrativas manuais
  - Templates de narrativas
  - Inteligência de swipe manual
  - Cliffhangers automáticos
  - Barras de progresso

❌ Fase 5 (Instagram):
  - Preview antes de gerar
  - OAuth Instagram
  - Publicação no Instagram
  - Agendamento de posts
  - Captura de métricas Instagram
  - Dashboard de métricas Instagram
  - Polling/webhooks Instagram

❌ Outros:
  - Sistema de custos/cobranças
  - Limites por tier
  - A/B testing
  - Análise de performance em tempo real
```

---

## 🧪 **TESTES PRIORITÁRIOS MVP**

### **Sprint 1 (Input Manual):**
```python
tests/test_carousel_generation.py:
  - test_generate_carousel_from_manual_input()
  - test_carousel_slide_count()
  - test_carousel_has_logo()
  - test_list_user_carousels()
```

### **Sprint 2 (Posts Diários):**
```python
tests/test_carousel_origins.py:
  - test_generate_carousel_from_daily_post()
  - test_detect_expandable_posts()
  - test_post_expansion_strategies()
  - test_semantic_analysis_reuse()
```

### **Sprint 3 (Weekly Context + CRUD):**
```python
tests/test_carousel_weekly.py:
  - test_generate_carousel_from_opportunity()
  - test_opportunity_relevance()

tests/test_carousel_crud.py:
  - test_edit_carousel_slide()
  - test_delete_carousel()
  - test_carousel_permissions()

tests/test_carousel_errors.py:
  - test_insufficient_credits()
  - test_post_not_expandable()
  - test_invalid_slide_count()
```

---

## 📅 **ROADMAP ATUALIZADO**

### **Fase 1: MVP Core (3 sprints)** ⭐ AGORA
- Sprint 1: Input Manual
- Sprint 2: Posts Diários
- Sprint 3: Weekly Context + CRUD
- **Resultado:** Sistema funcional de geração

### **Coleta de Dados: 1-2 meses**
- Usuários testam sistema
- Feedback qualitativo
- Métricas de uso (não Instagram ainda)

### **Fase 4: ML e Otimização (3-4 sprints)**
- ML sugere origem ideal
- ML infere narrativa
- Auto-otimização
- **Nota:** Pode ter dados limitados sem Instagram

### **Fase 5: Integração Instagram (2-3 sprints)** 🆕
- OAuth Instagram
- Publicação
- Captura de métricas
- **Resultado:** Sistema completo end-to-end

---

## 🎯 **CRITÉRIOS DE SUCESSO MVP**

### **Funcional:**
- [ ] Usuário cria carrossel via input manual
- [ ] Usuário expande post diário para carrossel
- [ ] Usuário cria carrossel de oportunidade
- [ ] Sistema gera 7 slides com qualidade 98%
- [ ] Logo aparece no primeiro e último slide
- [ ] Usuário edita slides individuais
- [ ] Usuário deleta carrosséis

### **Técnico:**
- [ ] Reusa 100% do DailyIdeasService
- [ ] Análise semântica em 3 etapas
- [ ] Tempo de geração < 60 segundos
- [ ] Sem erros críticos
- [ ] Cobertura de testes > 70%

### **Experiência:**
- [ ] Fluxo intuitivo
- [ ] Loading states claros
- [ ] Mensagens de erro úteis
- [ ] Interface responsiva

---

## 📞 **PRÓXIMOS PASSOS IMEDIATOS**

1. **Criar branch:** `git checkout -b carousel-mvp`
2. **Iniciar Sprint 1:** Implementar Input Manual
3. **Seguir documentação:** CAROUSEL_IMPLEMENTATION_GUIDE.md
4. **Testes contínuos:** Implementar testes a cada feature

---

## 📚 **Documentos Relacionados**

- `CAROUSEL_IMPLEMENTATION_GUIDE.md` - Guia técnico completo
- `CAROUSEL_CONTENT_ORIGINS.md` - Detalhes das 3 origens
- `CAROUSEL_STRATEGY_DECISION.md` - Justificativa estratégica
- `CAROUSEL_INDEX.md` - Índice geral

---

_Documento criado em: Janeiro 2025_  
_Todas decisões aprovadas: ✅_  
_Status: Pronto para desenvolvimento_

