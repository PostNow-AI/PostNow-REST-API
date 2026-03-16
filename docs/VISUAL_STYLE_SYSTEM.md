# Sistema de Estilo Visual Dinâmico

## Visão Geral

O sistema gera estilos visuais únicos para cada imagem de post usando IA. Em vez de templates fixos, cada imagem recebe um estilo personalizado baseado no contexto do mercado, audiência, concorrência e preferências do usuário.

## Pipeline de Geração (5 etapas)

```
Conteúdo → Análise Semântica → Geração de Estilo → Montagem de Prompt → Geração de Imagem
```

1. **Conteúdo**: texto do post (feed, story, reels)
2. **Análise Semântica**: extrai temas, cores, mood do conteúdo (`ai_prompt_service.semantic_analysis_prompt`)
3. **Geração de Estilo**: cria estilo visual único com IA (`style_generation_service.generate_style`)
4. **Montagem de Prompt**: combina análise + estilo em prompt de imagem (`ai_prompt_service.image_generation_prompt`)
5. **Geração de Imagem**: Gemini gera a imagem final (`ai_service.generate_image`)

## Arquivos Principais

| Arquivo | Responsabilidade |
|---------|-----------------|
| `services/style_generation_service.py` | Geração de estilos, anti-repetição, contexto |
| `IdeaBank/utils/style_feedback.py` | Feedback loop (accepted/rejected + analytics) |
| `IdeaBank/views.py` | Endpoints de geração (`generate_post_idea`, `generate_from_opportunity`, `generate_image_for_idea`) |
| `IdeaBank/services/daily_ideas_service.py` | Geração diária automática |
| `CreatorProfile/models.py` | Model `GeneratedVisualStyle` |
| `IdeaBank/models.py` | Model `PostIdea` (FK para `GeneratedVisualStyle`) |

## Feedback Loop (3 Níveis)

### Nível 1 — Sinais Implícitos (implementado)

Quando o usuário interage com estilos, sinais são capturados automaticamente:

- **Primeira geração**: estilo marcado como `accepted`
- **Regeneração**: estilo anterior → `rejected`, novo → `accepted`
- **Reutilização** (`reuse_style_id`): incrementa `times_used`

O prompt de geração de estilo recebe histórico separado por feedback:
- Estilos aceitos → "use as inspiration"
- Estilos rejeitados → "avoid similar"
- Sem feedback → "vary from these"

### Nível 2 — Favoritos (implementado)

- Endpoint: `PATCH /api/creator-profile/styles/{id}/favorite/`
- Endpoint: `GET /api/creator-profile/styles/`
- Estilos favoritos aparecem no prompt como "strong inspiration"

### Nível 3 — Performance Instagram (infraestrutura pronta)

- Model `EngagementMetrics` (impressions, reach, saves, shares)
- Command `fetch_engagement_metrics` (cron)
- Campo `engagement_score` no `GeneratedVisualStyle`
- Estilos top performers alimentam o prompt

## Anti-Repetição

### Visual Approaches (8 técnicas)

O sistema roda entre 8 abordagens visuais diferentes para evitar monotonia:

1. Editorial Photography — fotografia lifestyle/produto com estilo editorial
2. Flat Illustration — ilustração vetorial bold com formas geométricas
3. Data Visualization / Infographic — layout data-driven com gráficos e hierarquia
4. Collage / Mixed Media — composição em camadas com recortes e texturas
5. Photographic Texture Close-up — macro de texturas reais como canvas
6. 3D Render / Clay Style — objetos 3D soft com material matte
7. Split Composition — canvas dividido em zonas contrastantes
8. Gradient Abstract — gradientes fluidos com elementos mínimos

A técnica é persistida em `style_data.visual_approach` para consulta e anti-repetição.

### Histórico de Estilos

Os últimos 10 estilos do usuário são passados no prompt, separados por feedback signal, para que a IA evite repetir padrões rejeitados.

## Models

### GeneratedVisualStyle (CreatorProfile)
```python
name              # Nome do estilo (gerado pela IA)
style_data        # JSONField com detalhes (cores, tipografia, approach, etc.)
is_favorite       # Boolean — marcado pelo usuário
times_used        # Contador de reutilizações
feedback_signal   # 'pending' | 'accepted' | 'rejected'
engagement_score  # Float — score de performance (Instagram)
```

### PostIdea.generated_style (IdeaBank)
FK para `GeneratedVisualStyle` — vincula a ideia ao estilo usado na imagem.

## Testes

- `services/tests/test_style_generation_service.py` — 68 testes (approaches, feedback, favoritos, performance, prompt, generate_style)
- `services/tests/test_style_feedback.py` — 23 testes (mark accepted/rejected, analytics events, admin, serializers, FK, engagement)

```bash
python -m pytest services/tests/test_style_generation_service.py services/tests/test_style_feedback.py -v
```

## Analytics Events

| Evento | Quando |
|--------|--------|
| `style_accepted` | Estilo marcado como aceito (primeira geração ou regeneração) |
| `style_rejected` | Estilo anterior rejeitado na regeneração |

Resource type: `GeneratedVisualStyle`
