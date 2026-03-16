# Melhorias Futuras — Sistema de Estilo Visual

Documentado em 2026-03-16 durante testes E2E do pipeline de geração de imagens.
Branch de entrega atual: `integration/opportunity-flow`

---

## 1. Consolidar etapas 2+3 do pipeline

**Prioridade**: Alta
**Impacto**: Performance (-10s por imagem) + qualidade (estilo consciente do título)
**Risco**: Médio — muda estrutura do pipeline

### Situação atual
O pipeline tem 3 chamadas de IA sequenciais antes de gerar a imagem:
1. Geração de conteúdo (legenda) → ~10-15s
2. Análise semântica (tema, objetos, emoções) → ~5-10s
3. Geração de estilo visual (aesthetic, colors, typography) → ~10-15s

As etapas 2 e 3 poderiam ser uma só chamada, porque o estilo precisa de contexto semântico e a análise semântica não tem utilidade isolada fora da geração de estilo.

### Proposta
- Unificar `semantic_analysis_prompt` + `generate_style` num único prompt
- O prompt recebe o texto da legenda + perfil + mercado + favoritos
- Retorna JSON com análise semântica + style_data + titulo_imagem tudo junto
- Economiza 1 chamada de IA (~10s) por imagem

### Arquivos afetados
- `services/ai_prompt_service.py` — `semantic_analysis_prompt()`
- `services/style_generation_service.py` — `generate_style()`
- `IdeaBank/views.py` — `generate_post_idea()`, `generate_from_opportunity()`, `generate_image_for_idea()`
- `IdeaBank/services/daily_ideas_service.py` — `_generate_image_for_feed_post()`

---

## 2. Passar briefing original para geração de estilo

**Prioridade**: Alta
**Impacto**: Qualidade (estilos mais contextualizados)
**Risco**: Baixo — adicionar parâmetro, sem mudar estrutura

### Situação atual
A etapa 3 (geração de estilo) recebe apenas o output da etapa 2 (análise semântica).
O `further_details` original do usuário (rico em contexto e intenção) se perde na cadeia.

### Proposta
- Adicionar parâmetro `original_brief` na função `generate_style()`
- Incluir seção no `STYLE_GENERATION_PROMPT_TEMPLATE`: "ORIGINAL BRIEF: {original_brief}"
- Passar `further_details` ou `opportunity_data` como brief

### Arquivos afetados
- `services/style_generation_service.py` — `generate_style()`, template
- `IdeaBank/views.py` — chamadas de `generate_style()`

---

## 3. Validação + retry entre etapas

**Prioridade**: Média
**Impacto**: Resiliência (menos estilos genéricos por JSON inválido)
**Risco**: Baixo

### Situação atual
Se a etapa 2 gera JSON mal-formado, `json.loads()` falha ou retorna `{}`.
A etapa 3 recebe análise semântica vazia e gera estilo genérico.
Não há retry nem fallback inteligente.

### Proposta
- Validar output JSON de cada etapa antes de passar para a próxima
- Se inválido, retry 1x com prompt simplificado
- Se falhar 2x, usar fallback com dados mínimos do briefing original
- Logar warnings para monitoramento

### Arquivos afetados
- `IdeaBank/views.py` — blocos try/except das etapas 2 e 3
- Possivelmente extrair para helper `_safe_parse_ai_json()`

---

## 4. Persistir visual_approach no style_data

**Prioridade**: Alta
**Impacto**: Debugging + anti-repetição futura
**Risco**: Muito baixo — 2 linhas de código

### Situação atual
`_pick_visual_approach()` escolhe uma técnica visual (das 8 em VISUAL_APPROACHES)
e injeta no prompt, mas NÃO salva qual técnica foi usada no `style_data` do
GeneratedVisualStyle. O campo `visual_approach` fica vazio no banco.

Isso significa que `_pick_visual_approach()` não consegue verificar quais técnicas
foram usadas recentemente de forma confiável, e debugging é difícil.

### Proposta
- Após gerar o estilo, salvar `style.visual_approach = approach_technique` no style_data
- Ou adicionar campo dedicado no model GeneratedVisualStyle

### Arquivos afetados
- `services/style_generation_service.py` — `generate_style()`, após parse do JSON

---

## 5. Texto gibberish em telas/elementos visuais

**Prioridade**: Baixa (limitação do modelo)
**Impacto**: Qualidade visual em ~20% das imagens
**Risco**: N/A

### Situação atual
Gemini gera texto ilegível/gibberish em celulares, laptops, certificados e dashboards.
A regra de blur existe no prompt ("keep it blurred or show abstract shapes") mas
o modelo nem sempre respeita.

### Proposta (quando modelos melhorarem)
- Monitorar com novos modelos Gemini se o problema persiste
- Considerar pós-processamento para detectar e borrar texto em telas (via OCR + blur)
- Por enquanto, aceitar como limitação conhecida

---

## Ordem de execução sugerida

```
1. Item 4 (visual_approach) — 5 minutos, risco zero
2. Item 2 (briefing original) — 30 minutos, risco baixo
3. Item 1 (consolidar etapas) — 2-3 horas, precisa testes E2E
4. Item 3 (validação/retry) — 1 hora, pode fazer junto com item 1
5. Item 5 (gibberish) — aguardar evolução do modelo
```
