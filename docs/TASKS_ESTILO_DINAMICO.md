# Tasks — Sistema de Estilo Visual Dinâmico

**Criado:** 2026-03-13
**Decisão:** A IA cria um estilo visual do zero para cada imagem. Estilos são salvos como ativo do usuário para reutilização futura.

**Documento de referência:** `docs/prompt-best-practices.md`

---

## Fase 1: Fundação (CONCLUÍDA 2026-03-13)

### Task 1.1: Modelo de Dados — GeneratedVisualStyle

**Arquivo:** `CreatorProfile/models.py`

Criar modelo para salvar estilos gerados pela IA:

```python
class GeneratedVisualStyle(models.Model):
    # Vinculação
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='generated_styles')
    created_at = models.DateTimeField(auto_now_add=True)

    # Identificação
    name = models.CharField(max_length=100)  # Nome curto gerado pela IA
    description = models.TextField()         # Descrição completa do estilo

    # Estilo estruturado (JSON com memory colors, não hex)
    style_data = models.JSONField()
    # Estrutura esperada do style_data:
    # {
    #     "aesthetic": "clean minimalist inspired by editorial magazines",
    #     "colors": {
    #         "background": "warm ivory",
    #         "primary": "deep cobalt blue",
    #         "accent": "vivid coral",
    #         "text": "dark charcoal"
    #     },
    #     "lighting": "soft overcast nordic daylight",
    #     "typography": "modern sans-serif, bold, generous letter-spacing",
    #     "composition": "title upper third, main visual centered 40%, logo bottom-right 8%",
    #     "mood": "confident, professional, aspirational",
    #     "references": ["editorial magazine layout", "Apple product page"]
    # }

    # Contexto de origem
    source_post_id = models.IntegerField(null=True, blank=True)  # Post que originou o estilo

    # Reutilização
    is_favorite = models.BooleanField(default=False)  # Usuário marcou como favorito
    times_used = models.IntegerField(default=1)       # Quantas vezes foi usado
```

**Checklist:**
- [x] Criar modelo
- [x] Criar migration (0016_add_generated_visual_style)
- [x] Registrar no admin
- [ ] Remover dependência de `VisualStylePreference` e `visual_style_ids` (débito — não quebrar agora)

---

### Task 1.2: Melhorar color_extraction.py — CSS3 → Memory Colors

**Arquivo:** `services/color_extraction.py`

O `_hex_to_color_name()` atual usa `webcolors` (CSS3, 148 nomes genéricos). Resultado: #E07A5F → "salmon" (IA pensa em peixe).

**O que fazer:**
1. Criar dicionário de memory colors mapeando ranges de HSL para nomes descritivos
2. Substituir `webcolors.CSS3_HEX_TO_NAMES` pelo novo dicionário
3. Output deve ser em inglês com modificadores: "warm terracotta", "deep midnight navy"
4. Manter fallback para `webcolors` caso a cor não case com nenhum range

**Exemplos de conversão esperada:**

| Hex | CSS3 atual (ruim) | Memory Color (esperado) |
|---|---|---|
| #E07A5F | salmon | warm terracotta |
| #7C9070 | gray | muted sage green |
| #722F37 | saddlebrown | deep wine red |
| #1A1A2E | black | deep midnight navy |
| #D4AF37 | darkgoldenrod | warm antique gold |
| #81B29A | darkseagreen | muted sage green |
| #FFFFFF | white | pure white |

**Checklist:**
- [x] Criar dicionário `MEMORY_COLORS` com ~80 cores organizadas por família HSL
- [x] Função `hex_to_memory_color(hex_code) -> str`
- [x] Testes manuais com os exemplos acima (todos corretos)
- [x] Atualizar `format_colors_for_prompt()` para usar o novo dicionário
- [x] `prompt_logo.py` já usa `format_colors_for_prompt()` — atualizado automaticamente
- [x] Removida dependência de `webcolors` (usa apenas `colorsys` da stdlib)
- [x] 27 testes unitários (`services/tests/test_color_extraction.py`)

---

### Task 1.3: Service de Geração de Estilo

**Arquivo novo:** `services/style_generation_service.py`

Service que recebe contexto e gera um estilo visual completo via IA (Gemini texto, não imagem).

**Input:**
- Perfil do cliente (nicho, paleta em memory colors, tom de voz, descrição)
- Conteúdo do post (tema, objetivo, análise semântica)
- [FUTURO] Histórico de estilos gerados (evitar repetição)
- [FUTURO] Analytics do Instagram (performance visual)
- [FUTURO] Contexto do feed (coerência visual)

**Output:** `GeneratedVisualStyle` salvo no banco

**Prompt da IA para gerar o estilo:**
- Deve seguir as boas práticas de `docs/prompt-best-practices.md`
- Deve retornar JSON estruturado (schema do `style_data`)
- Deve usar memory colors (nunca hex)
- Deve especificar iluminação, tipografia, composição, mood
- Deve considerar o nicho/setor do cliente

**Checklist:**
- [x] Criar `generate_style(user, semantic_analysis, ai_service) -> GeneratedVisualStyle`
- [x] Prompt em inglês que instrui a IA a criar o estilo (seguindo boas práticas)
- [x] Parse do JSON retornado pela IA (com suporte a markdown blocks)
- [x] Salvar no banco como `GeneratedVisualStyle`
- [x] Tratamento de erro (JSON inválido → fallback, campos faltando → merge com defaults)
- [x] 20 testes (`services/tests/test_style_generation_service.py`) — 17 unitários + 3 integração (xfail por migration pré-existente)

---

### Task 1.4: Integrar no Pipeline de Geração de Imagem

**Arquivo:** `services/ai_prompt_service.py` (método `image_generation_prompt`)

Substituir o estilo fixo aleatório pelo estilo gerado dinamicamente.

**O que mudar:**
1. Remover chamada a `get_random_visual_style()` em `get_creator_profile_data()`
2. Chamar `StyleGenerationService.generate_style()` antes de `image_generation_prompt()`
3. Passar o `style_data` (JSON) para o prompt de imagem
4. Refatorar o prompt para seguir a estrutura dos templates (seções STYLE, COLORS, COMPOSITION, etc.)
5. Prompt em inglês para instruções, PT-BR apenas para texto renderizado

**Checklist:**
- [x] `image_generation_prompt()` recebe `generated_style` (opcional, retrocompatível)
- [x] Prompt refatorado com seções: STYLE, SUBJECT AND CONTEXT, COLORS, COMPOSITION, LOGO, QUALITY, AVOID
- [x] Prompt em inglês (conforme decisão de idioma do documento)
- [x] Cores formatadas com memory colors (via `format_colors_for_prompt`)
- [x] Fallback quando `generated_style` é None
- [x] Integrado em 4 chamadores: views.py (3x) + daily_ideas_service.py (1x)
- [x] Coberto pelos testes de integração do style_generation (xfail por migration pré-existente)

---

## Débito Técnico da Fase 1

### VisualStylePreference e visual_style_ids — NÃO REMOVER AGORA

O sistema antigo (`VisualStylePreference`, `visual_style_ids`, `get_random_visual_style()`) ainda é usado em:
- **Frontend**: Onboarding step 14 (seleção de estilos visuais)
- **Endpoint**: `visual-style-preferences/` (lista os 18 estilos com previews)
- **Serializers**: `CreatorProfileSerializer`, `OnboardingTempDataSerializer`
- **Services**: `get_creator_profile_data.py`, `adapted_semantic_analysis_prompt()`

**Por que não remover agora:**
- O frontend depende desses campos no onboarding
- `adapted_semantic_analysis_prompt()` ainda injeta `visual_style` do perfil
- Remover quebraria o fluxo de onboarding

**Quando remover:**
- Após o frontend ser atualizado para não usar mais `visual_style_ids` no onboarding
- Após `adapted_semantic_analysis_prompt()` ser refatorado para usar o estilo gerado
- Migração de dados: criar migration que remove `visual_style_ids` do `CreatorProfile`

### Migration conflitante tendencies_data

O banco de teste tem uma migration que tenta adicionar `tendencies_data` mas a coluna já existe. Isso impede testes `django_db`. Precisa ser resolvido para que os testes de integração rodem.

### pytest-django adicionado

`pytest-django` foi instalado e `DJANGO_SETTINGS_MODULE` configurado em `pyproject.toml`. Testes existentes não foram afetados.

---

## Fase 2: Feedback Loop — Reutilização e Favoritos (CONCLUÍDA 2026-03-14)

### Task 2.1: Reutilização de Estilo

- [x] Endpoint `GET /creator-profile/styles/` para listar estilos (filtro `?favorites=true`)
- [x] Opção de "usar este estilo novamente" (`reuse_style_id` no `ImageGenerationRequestSerializer`)
- [x] Incrementar `times_used` quando reutilizado
- [x] Endpoint `PATCH /creator-profile/styles/<id>/favorite/` para toggle favorito
- [x] `GeneratedVisualStyleSerializer` (id, name, style_data, is_favorite, times_used, feedback_signal, created_at)

### Task 2.2: Refatorar prompt-best-practices.md

- [ ] Conectar seção Estilo Visual (7) com o service criado
- [ ] Conectar seção Consistência de Feed (9) com estilos salvos
- [ ] Expandir seção Iteração (11) com dados reais de uso
- [ ] Adicionar critérios de avaliação objetivos (seção nova)

### Task 2.3: Decisão sobre Overlay de Texto

- [ ] Definir critério: quando usar IA vs. overlay de código para texto PT-BR
- [ ] Se overlay: implementar serviço de composição (Pillow/PIL)
- [ ] Documentar a decisão no prompt-best-practices.md

---

## Fase 3: Feedback Loop — Sinais Implícitos e Performance (CONCLUÍDA 2026-03-14)

### Task 3.1: Sinais Implícitos (accepted/rejected)

- [x] FK `generated_style` no `PostIdea` (vincula estilo ao post)
- [x] Campo `feedback_signal` (pending/accepted/rejected) no `GeneratedVisualStyle` com db_index
- [x] Lógica: marca `accepted` na primeira geração, `rejected` na regeneração
- [x] Helper `_mark_style_feedback()` em `IdeaBank/views.py`
- [x] Vinculação em 4 pontos: `generate_post_idea`, `generate_from_opportunity`, `generate_image_for_idea`, `_generate_image_for_feed_post`
- [x] Emite `AnalyticsEvent` (STYLE_ACCEPTED/STYLE_REJECTED) com resource_type=GeneratedVisualStyle
- [x] `_gather_previous_styles()` agora busca 10 estilos e separa em 3 seções: LIKED / REJECTED / pending

### Task 3.2: Favoritos como referência forte no prompt

- [x] `_gather_favorite_styles(user, limit=3)` — busca estilos com `is_favorite=True`
- [x] Nova seção `### FAVORITE STYLES` no `STYLE_GENERATION_PROMPT_TEMPLATE`
- [x] Regra 12: "new style MUST share DNA with at least one favorite while still being unique"

### Task 3.3: Instagram Engagement — Coleta de Métricas

- [x] `InstagramInsightsService` — `fetch_media_insights(media_id, access_token)` via Graph API
- [x] Model `EngagementMetrics` (impressions, reach, engagement, saves, shares, engagement_rate, raw_data)
- [x] FK chain: EngagementMetrics → ScheduledPost → PostIdea → GeneratedVisualStyle
- [x] Campo `engagement_score` no `GeneratedVisualStyle`
- [x] Management command `fetch_engagement_metrics --days N` (coleta e atualiza scores)

### Task 3.4: Performance no prompt de geração

- [x] `_gather_performance_data(user, limit=5)` — busca estilos com maior engagement_score
- [x] Nova seção `### TOP PERFORMING STYLES` no template
- [x] Regra 13: "incorporate elements from top performing styles"
- [x] Se não tem dados, seção não aparece (string vazia)

### Pendentes (Fase 3)

### Task 3.5: Campanhas Visuais
- [ ] Modelo `Campaign` que agrupa posts com mesmo estilo
- [ ] Reutilização automática do estilo da campanha

### Task 3.6: Identificação de Estilo (UX)
- [ ] Como o usuário identifica/nomeia estilos salvos
- [ ] Thumbnail/preview do estilo
- [ ] Busca/filtro de estilos por tipo, cor, mood

### Task 3.7: A/B Testing de Prompts
- [ ] Versionamento de prompts como código
- [ ] Comparação de resultados entre versões
- [ ] Métricas de qualidade por versão

---

## Código afetado (acumulado)

| Arquivo | Mudança |
|---|---|
| `CreatorProfile/models.py` | `GeneratedVisualStyle` + campos `feedback_signal`, `engagement_score` |
| `CreatorProfile/admin.py` | `feedback_signal` em list_display e list_filter |
| `CreatorProfile/serializers.py` | `GeneratedVisualStyleSerializer` |
| `CreatorProfile/views.py` | `list_generated_styles`, `toggle_style_favorite` |
| `CreatorProfile/urls.py` | `styles/`, `styles/<id>/favorite/` |
| `IdeaBank/models.py` | FK `generated_style` no `PostIdea` |
| `IdeaBank/views.py` | `_mark_style_feedback`, vinculação em 3 endpoints |
| `IdeaBank/serializers.py` | `reuse_style_id` no `ImageGenerationRequestSerializer` |
| `IdeaBank/services/daily_ideas_service.py` | Vincula `generated_style` ao `PostIdea` |
| `Analytics/constants.py` | `STYLE_ACCEPTED`, `STYLE_REJECTED`, `GENERATED_VISUAL_STYLE` |
| `services/style_generation_service.py` | `_gather_favorite_styles`, `_gather_performance_data`, prompt enriquecido |
| `SocialMediaIntegration/models.py` | `EngagementMetrics` |
| `SocialMediaIntegration/services/instagram_insights_service.py` | **Novo** |
| `SocialMediaIntegration/management/commands/fetch_engagement_metrics.py` | **Novo** |

---

## Testes

| Arquivo | Qtd | Cobertura |
|---|---|---|
| `services/tests/test_style_generation_service.py` | 42 | Prompt, parsing, directions, feedback no prompt |
| `services/tests/test_style_feedback.py` | 23 | Models, FK, serializers, admin, URLs, helper |
| `Analytics/tests/test_constants.py` | 6 | Constantes novas |
| `SocialMediaIntegration/tests/test_instagram_insights_service.py` | 5 | Insights API (success, rate limit, errors) |

---

## Changelog

| Data | Mudança |
|---|---|
| 2026-03-14 | Feedback loop completo: sinais implícitos, favoritos, performance Instagram. |
| 2026-03-13 | Fase 1 concluída: modelo, memory colors, service, integração. |
| 2026-03-13 | Documento criado com 3 fases, 12 tasks, ordem de execução. |
