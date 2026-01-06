# 🎨 Biblioteca de Prompts para Carrosséis Instagram

> **Documento Complementar:** CAROUSEL_IMPLEMENTATION_GUIDE.md  
> **Objetivo:** Centralizar todos os prompts de IA usados na geração de carrosséis  
> **Status:** Referência Técnica

---

## 📋 Índice

1. [Prompts de Estruturação](#prompts-de-estruturação)
2. [Prompts por Tipo de Narrativa](#prompts-por-tipo-de-narrativa)
3. [Prompts de Geração de Texto](#prompts-de-geração-de-texto)
4. [Prompts de Geração de Imagem](#prompts-de-geração-de-imagem)
5. [Prompts de Harmonia Visual](#prompts-de-harmonia-visual)
6. [Prompts de Validação](#prompts-de-validação)

---

## 🎯 Prompts de Estruturação

### 1. Análise de Tema e Escolha de Narrativa

```python
def prompt_choose_narrative_type(theme: str, creator_profile: dict) -> str:
    return f"""
Você é um especialista em estratégia de conteúdo para Instagram.

Analise o tema abaixo e determine qual tipo de narrativa de carrossel funcionará melhor:

TEMA: {theme}

PERFIL DO CRIADOR:
- Nicho: {creator_profile['specialization']}
- Público-alvo: {creator_profile['target_audience']}
- Tom de voz: {creator_profile['voice_tone']}
- Objetivo: Engajamento e swipe-through máximo

TIPOS DISPONÍVEIS E SEUS USOS:
1. tutorial: Passo-a-passo educacional (completion rate: 85%)
2. list: Lista/checklist prático (completion rate: 70%)
3. story: Storytelling emocional (completion rate: 65%)
4. comparison: Comparação lado a lado (completion rate: 63%)
5. before_after: Transformação/resultado (completion rate: 75%)
6. myths: Mitos vs. Verdades (completion rate: 80%)
7. infographic: Dados/estatísticas (completion rate: 68%)
8. quiz: Interativo com resultado (completion rate: 90%)

Responda APENAS com um JSON:
{{
  "narrative_type": "tipo_escolhido",
  "reason": "Breve justificativa de 1 linha",
  "estimated_completion_rate": 0.75,
  "hook_suggestion": "Título sugerido para capa"
}}
"""
```

### 2. Estruturação de Slides

```python
def prompt_structure_slides(
    theme: str,
    narrative_type: str,
    slide_count: int,
    semantic_analysis: dict
) -> str:
    return f"""
Você é um arquiteto de conteúdo especializado em carrosséis do Instagram.

Crie a estrutura completa de um carrossel de {slide_count} slides.

TEMA: {theme}
TIPO DE NARRATIVA: {narrative_type}
ANÁLISE SEMÂNTICA: {semantic_analysis}

REGRAS:
- Slide 1 deve ser uma CAPA impactante (hook forte)
- Slides intermediários desenvolvem a narrativa
- Último slide deve ter CTA claro
- Cada slide precisa incentivar swipe para o próximo
- Usar elementos: setas (→), numeração (1/{slide_count}), cliffhangers

Retorne JSON com estrutura:
{{
  "slides": [
    {{
      "sequence": 1,
      "role": "cover|content|cta",
      "title": "Título do slide",
      "content_brief": "O que deve ser abordado",
      "swipe_trigger": "Como incentivar próximo slide",
      "visual_suggestion": "Sugestão de elemento visual",
      "background_color_hex": "#FFFFFF"
    }},
    ...
  ]
}}
"""
```

---

## 📖 Prompts por Tipo de Narrativa

### Tutorial (Passo-a-Passo)

```python
def prompt_tutorial_narrative(theme: str, steps: int, profile: dict) -> str:
    return f"""
Crie uma narrativa de tutorial passo-a-passo para carrossel Instagram.

TEMA: {theme}
NÚMERO DE PASSOS: {steps}
PÚBLICO: {profile['target_audience']}
TOM DE VOZ: {profile['voice_tone']}

ESTRUTURA OBRIGATÓRIA:
Slide 1 (Capa):
- Título: "Como [fazer X] em {steps} passos simples"
- Promessa clara de resultado
- Design: Título grande + imagem conceitual

Slides 2 a {steps+1} (Passos):
- Numeração: "Passo 1/{steps}", "Passo 2/{steps}"...
- Cada passo em um slide
- Linguagem: Imperativa e direta ("Faça X", "Configure Y")
- Final de cada slide: Seta → + "Próximo passo"

Slide {steps+2} (Resultado + CTA):
- Título: "Resultado final" ou "Agora é sua vez"
- Recapitulação breve
- CTA: Comentar/salvar/compartilhar

RETORNAR: Array JSON com texto de cada slide
"""
```

### Lista/Checklist

```python
def prompt_list_narrative(theme: str, items: int, profile: dict) -> str:
    return f"""
Crie uma lista/checklist viral para carrossel Instagram.

TEMA: {theme}
NÚMERO DE ITENS: {items}
PÚBLICO: {profile['target_audience']}

REGRAS DE OURO:
1. Título deve criar FOMO: "X coisas que você PRECISA fazer"
2. Cada item = 1 slide
3. Itens devem ser acionáveis (não apenas informativos)
4. Ordem: Do mais fácil ao mais impactante
5. Último item deve ser surpreendente ("bônus")

FORMATO DE CADA ITEM:
- Emoji relevante no início
- Título curto (máx 5 palavras)
- Descrição breve (2-3 linhas)
- Por que é importante (1 linha)

SLIDE FINAL:
- "Quantos você já faz? Comenta aí! 👇"
- Incentivo para salvar o post

RETORNAR: JSON com slides estruturados
"""
```

### Storytelling

```python
def prompt_story_narrative(theme: str, arc: str, profile: dict) -> str:
    return f"""
Construa uma narrativa de storytelling para carrossel Instagram.

TEMA: {theme}
ARCO NARRATIVO: {arc}  # Ex: "problema-solução", "jornada-herói"
VOZ DA MARCA: {profile['voice_tone']}

ESTRUTURA DE STORYTELLING:
Slide 1 (Hook emocional):
- Frase que cria conexão imediata
- Situação relatable
- Ex: "Eu também achava que era impossível..."

Slides 2-3 (Problema/Conflito):
- Desenvolva a dor/desafio
- Use emoção autêntica
- Leitor deve pensar: "Isso sou eu!"

Slides 4-5 (Jornada/Transformação):
- Ponto de virada
- O que mudou
- Descobertas pelo caminho

Slide 6-7 (Resultado/Aprendizado):
- Transformação concluída
- Lições aprendidas
- Prova social/resultado

Slide 8 (Mensagem + CTA):
- Mensagem inspiradora
- "Você também pode"
- CTA emocional (compartilhar com quem precisa)

RETORNAR: Slides com narrativa coesa e emocional
"""
```

### Antes e Depois

```python
def prompt_before_after(theme: str, transformation: dict, profile: dict) -> str:
    return f"""
Crie narrativa "Antes e Depois" para carrossel Instagram.

TEMA: {theme}
TRANSFORMAÇÃO: {transformation}
NICHO: {profile['specialization']}

ESTRUTURA:
Slide 1 (Teaser):
- "Como eu saí de [ANTES] para [DEPOIS] em X dias/meses"
- Criar curiosidade sobre o "como"

Slides 2-3 (Situação ANTES):
- Detalhar problema/dor inicial
- Ser específico com números/detalhes
- Gerar empatia

Slides 4-6 (O Processo):
- O que foi feito
- Decisões-chave
- Obstáculos superados
- Cronologia clara

Slide 7 (Situação DEPOIS):
- Resultados concretos
- Números/métricas
- Antes vs. Depois lado a lado

Slide 8 (Como Replicar + CTA):
- "Você também pode conseguir"
- Próximos passos
- CTA: Salvar para depois ou comentar

IMPORTANTE: Ser autêntico, evitar exageros
RETORNAR: JSON com slides detalhados
"""
```

### Mitos vs. Verdades

```python
def prompt_myths_vs_truths(theme: str, myths_count: int, profile: dict) -> str:
    return f"""
Crie carrossel "Mitos vs. Verdades" para Instagram.

TEMA: {theme}
NÚMERO DE MITOS: {myths_count}
ESPECIALIZAÇÃO: {profile['specialization']}

FORMATO DE CADA MITO:
Slide par (Mito):
- Fundo vermelho/laranja (alerta)
- "❌ MITO: [crença comum errada]"
- Explicar por que as pessoas acreditam nisso

Slide ímpar (Verdade):
- Fundo verde/azul (correto)
- "✅ VERDADE: [informação correta]"
- Explicação científica/técnica
- Fonte/referência quando aplicável

SLIDE 1 (Intro):
- "{myths_count} mitos sobre {theme} que você precisa parar de acreditar"
- Design impactante

SLIDE FINAL:
- Recapitulação
- "Compartilhe para educar mais pessoas"
- Oferta de conteúdo complementar

TONE: Educativo mas não condescendente
OBJETIVO: Posicionar como autoridade
RETORNAR: Slides estruturados com mitos e verdades
"""
```

---

## ✍️ Prompts de Geração de Texto

### Texto para Slide Individual

```python
def prompt_generate_slide_text(
    slide_structure: dict,
    semantic_analysis: dict,
    profile: dict,
    previous_slides: list
) -> str:
    return f"""
Gere o texto otimizado para um slide de carrossel Instagram.

CONTEXTO DO SLIDE:
- Sequência: {slide_structure['sequence']}/total
- Papel: {slide_structure['role']}  # cover, content, cta
- Título sugerido: {slide_structure['title']}
- O que abordar: {slide_structure['content_brief']}

ANÁLISE SEMÂNTICA:
{semantic_analysis}

PERFIL DA MARCA:
- Tom de voz: {profile['voice_tone']}
- Público: {profile['target_audience']}
- Personalidade: {profile['brand_personality']}

SLIDES ANTERIORES (para continuidade):
{previous_slides}

REGRAS DE TEXTO:
1. Máximo 50 caracteres no título
2. Corpo: 80-120 caracteres
3. Usar quebras de linha estratégicas
4. Incluir elemento de swipe se não for último slide
5. Tom consistente com slides anteriores
6. Linguagem: Direta, acionável, envolvente

ELEMENTOS DE SWIPE (se aplicável):
- Seta → no final
- Frase cortada: "E o melhor é..." [próximo slide]
- FOMO: "Não pule este próximo"

FORMATO DE RETORNO:
{{
  "title": "Título do slide",
  "body": "Texto principal\\nCom quebras de linha",
  "swipe_cta": "Deslize para descobrir →",
  "visual_emphasis": ["palavra1", "palavra2"]  # Palavras para destacar
}}
"""
```

### Caption/Legenda do Carrossel

```python
def prompt_generate_carousel_caption(
    carousel_theme: str,
    narrative_type: str,
    slides_summary: list,
    profile: dict
) -> str:
    return f"""
Crie a legenda perfeita para este carrossel Instagram.

TEMA: {carousel_theme}
TIPO: {narrative_type}
RESUMO DOS SLIDES: {slides_summary}

PERFIL:
- Tom de voz: {profile['voice_tone']}
- Público: {profile['target_audience']}
- Especialização: {profile['specialization']}

ESTRUTURA DA LEGENDA:
1. HOOK (1-2 linhas):
   - Frase impactante que para o scroll
   - Relacionada ao tema mas não repete a capa

2. CONTEXTO (2-3 linhas):
   - Por que este conteúdo importa
   - Para quem é

3. INCENTIVO AO SWIPE (1 linha):
   - "Deslize para descobrir os X segredos que..."
   - Criar curiosidade sobre o conteúdo completo

4. CTA PRINCIPAL (1 linha):
   - Salvar, comentar ou compartilhar
   - Específico e acionável

5. HASHTAGS (separadas por linha):
   - 15-20 hashtags estratégicas
   - Mix: nicho (5), broad (10), branded (5)

MÁXIMO: 2.200 caracteres
EMOJIS: 3-5 no total (não exagerar)
TOM: {profile['voice_tone']}

RETORNAR: Legenda completa formatada
"""
```

---

## 🎨 Prompts de Geração de Imagem

### Prompt Base para Slide

```python
def prompt_generate_slide_image(
    slide_data: dict,
    slide_text: dict,
    visual_context: dict,
    profile: dict,
    include_logo: bool
) -> str:
    return f"""
Gere uma imagem profissional para slide de carrossel Instagram.

DADOS DO SLIDE:
- Sequência: {slide_data['sequence']}/{visual_context['total_slides']}
- Papel: {slide_data['role']}
- Cor de fundo sugerida: {slide_data['background_color_hex']}

TEXTO DO SLIDE:
- Título: {slide_text['title']}
- Corpo: {slide_text['body']}
- Palavras para destacar: {slide_text['visual_emphasis']}

CONTEXTO VISUAL (Harmonia com carrossel):
- Paleta de cores: {profile['color_palette']}
- Estilo visual predominante: {visual_context['visual_style']}
- Slide anterior tinha: {visual_context['previous_slide_description']}

ESPECIFICAÇÕES TÉCNICAS:
- Tamanho: 1080x1350px (proporção 4:5)
- Formato: Vertical para feed Instagram
- Safe zone: 80px de margem em todas as bordas
- Tipografia mínima legível: 24px

ELEMENTOS OBRIGATÓRIOS:
{f"- Logo da marca: canto inferior direito, 120-180px largura" if include_logo else ""}
- Numeração: "{slide_data['sequence']}/{visual_context['total_slides']}" (canto superior direito)
{f"- Seta direcional: → (canto inferior direito)" if slide_data['sequence'] < visual_context['total_slides'] else ""}

DIREÇÃO CRIATIVA:
- Estilo: Minimalista e profissional
- Hierarquia: Título > Corpo > Elementos secundários
- Contraste: Garantir legibilidade (mín. 4.5:1)
- Espaçamento: Generoso, não poluir

CONSISTÊNCIA:
- Manter mesmo estilo de ícones dos slides anteriores
- Cores devem fazer transição suave do slide anterior
- Tipografia: mesma família do carrossel inteiro

ELEMENTOS A EVITAR:
- Fotos genéricas de banco de imagens
- Texto minúsculo ou ilegível
- Poluição visual (menos é mais)
- Ícones de estilos misturados

RETORNAR: Imagem otimizada para Instagram Feed
"""
```

### Prompt para Capa (Slide 1)

```python
def prompt_generate_cover_image(
    theme: str,
    hook_title: str,
    profile: dict,
    narrative_type: str
) -> str:
    return f"""
Crie uma CAPA impactante para carrossel Instagram.

TEMA: {theme}
TÍTULO DA CAPA: {hook_title}
TIPO DE CONTEÚDO: {narrative_type}

OBJETIVO: Parar o scroll e gerar curiosidade

PERFIL DA MARCA:
- Paleta: {profile['color_palette']}
- Tom visual: {profile['visual_style']}
- Nicho: {profile['specialization']}

ELEMENTOS DA CAPA:
1. TÍTULO PRINCIPAL:
   - Fonte: Bold/Black, 56-72px
   - Posição: Centro-superior
   - Máximo: 6 palavras
   - Alto contraste com fundo

2. SUBTÍTULO (opcional):
   - Complementa o título
   - Fonte: 32-40px
   - Abaixo do título principal

3. VISUAL DE APOIO:
   - Pode ser: ícone, ilustração, foto conceitual
   - NÃO deve competir com o título
   - Ocupa max. 40% da imagem

4. LOGO DA MARCA:
   - Posição: Centro-superior ou inferior
   - Tamanho: 120-180px (15% da imagem)
   - Garantir visibilidade

5. ELEMENTO DE SWIPE:
   - Seta → no canto inferior direito
   - "Deslize para ver →" discreto
   - Cor: Contraste com fundo

DESIGN:
- Minimalista e clean
- Hierarquia visual clara
- Cores vibrantes mas não agressivas
- Espaço negativo generoso (40-50%)

PSICOLOGIA:
- Criar curiosidade visual
- Gap de informação (não revelar tudo)
- Profissional mas acessível

FORMATO: 1080x1350px, vertical, alta resolução
"""
```

### Prompt para Slide de CTA (Final)

```python
def prompt_generate_cta_image(
    carousel_theme: str,
    cta_message: str,
    profile: dict,
    slides_colors: list
) -> str:
    return f"""
Crie o slide FINAL (CTA) de um carrossel Instagram.

TEMA DO CARROSSEL: {carousel_theme}
MENSAGEM CTA: {cta_message}

OBJETIVO: Conversão/Ação (comentar, salvar, seguir)

CORES USADAS NO CARROSSEL: {slides_colors}
PALETA DA MARCA: {profile['color_palette']}

ELEMENTOS DO SLIDE FINAL:
1. MENSAGEM PRINCIPAL:
   - CTA claro e direto
   - Fonte: Bold, 40-56px
   - Centro da imagem

2. RECAPITULAÇÃO (opcional):
   - "Recapitulando: X, Y, Z"
   - Lista de bullets
   - Fonte menor: 24-28px

3. CHAMADA PARA AÇÃO:
   - "Salve este post para revisitar"
   - "Comenta qual foi sua dica favorita"
   - "Compartilhe com quem precisa ver isso"
   - Fonte: 28-36px, destacada

4. LOGO DA MARCA:
   - Obrigatório neste slide
   - Posição: Centro-inferior
   - Tamanho: 150-200px
   - Reforçar identidade

5. INFORMAÇÕES DE CONTATO (opcional):
   - Instagram handle
   - Website
   - Discretos no rodapé

DESIGN:
- Mais clean que os outros slides
- Respiro visual (menos elementos)
- Cor de fundo: Complementar às cores do carrossel
- Pode usar gradiente sutil

EMOÇÃO:
- Tom: Inspirador, positivo, motivador
- Sensação de "missão cumprida"
- Valorizar quem chegou até aqui

SEM SETAS: Este é o último slide, não precisa →
"""
```

---

## 🎭 Prompts de Harmonia Visual

### Análise de Consistência entre Slides

```python
def prompt_analyze_visual_consistency(slides_data: list) -> str:
    return f"""
Analise a consistência visual entre os slides deste carrossel Instagram.

SLIDES: {slides_data}

AVALIAR:
1. PALETA DE CORES:
   - Cores estão harmônicas?
   - Transições suaves ou abruptas?
   - Score: 0-100

2. TIPOGRAFIA:
   - Mesma família de fontes?
   - Hierarquia consistente?
   - Tamanhos proporcionais?
   - Score: 0-100

3. LAYOUT:
   - Grid/alinhamento consistente?
   - Safe zones respeitadas?
   - Espaçamento uniforme?
   - Score: 0-100

4. ELEMENTOS VISUAIS:
   - Ícones do mesmo estilo?
   - Setas/numeração consistentes?
   - Densidade visual similar?
   - Score: 0-100

5. NARRATIVA VISUAL:
   - Progressão clara?
   - Slides se complementam?
   - Flow visual coeso?
   - Score: 0-100

RETORNAR JSON:
{{
  "overall_consistency_score": 0-100,
  "color_consistency": {{
    "score": 0-100,
    "issues": ["lista de problemas"],
    "suggestions": ["melhorias"]
  }},
  "typography_consistency": {{...}},
  "layout_consistency": {{...}},
  "visual_elements_consistency": {{...}},
  "narrative_flow": {{...}},
  "critical_issues": ["problemas que quebram experiência"],
  "quick_wins": ["ajustes rápidos para melhorar"]
}}
"""
```

### Prompt de Correção de Harmonia

```python
def prompt_fix_visual_harmony(
    problematic_slide: dict,
    reference_slides: list,
    issues: list
) -> str:
    return f"""
Corrija a harmonia visual deste slide para manter consistência do carrossel.

SLIDE PROBLEMÁTICO:
{problematic_slide}

SLIDES DE REFERÊNCIA (corretos):
{reference_slides}

PROBLEMAS IDENTIFICADOS:
{issues}

TAREFA:
Regenere o slide mantendo:
- Mesmo estilo visual dos slides de referência
- Mesma família tipográfica
- Cores dentro da paleta estabelecida
- Layout e grid consistentes
- Densidade de elementos similar

PRESERVAR:
- Conteúdo/texto do slide
- Mensagem/informação
- Elementos de swipe (setas, números)

AJUSTAR:
- Cores para harmonizar
- Tipografia para consistência
- Espaçamentos para uniformidade
- Elementos visuais para coesão

RETORNAR: Slide corrigido mantendo identidade do carrossel
"""
```

---

## ✅ Prompts de Validação

### Validação de Qualidade do Carrossel

```python
def prompt_validate_carousel_quality(carousel_data: dict) -> str:
    return f"""
Avalie a qualidade deste carrossel Instagram sob critérios profissionais.

DADOS DO CARROSSEL:
{carousel_data}

CRITÉRIOS DE AVALIAÇÃO:

1. HOOK/CAPA (0-10):
   - Título impactante?
   - Cria curiosidade?
   - Design profissional?

2. NARRATIVA (0-10):
   - Coesão entre slides?
   - Progressão lógica?
   - Mantém interesse?

3. SWIPE TRIGGERS (0-10):
   - Elementos de continuidade?
   - Cliffhangers efetivos?
   - Incentiva avançar?

4. CONSISTÊNCIA VISUAL (0-10):
   - Harmonia de cores?
   - Tipografia uniforme?
   - Layout consistente?

5. CTA FINAL (0-10):
   - Call-to-action claro?
   - Fechamento forte?
   - Incentiva ação?

6. MOBILE-FIRST (0-10):
   - Legível em mobile?
   - Safe zones respeitadas?
   - Elementos não cortados?

7. BRAND ALIGNMENT (0-10):
   - Alinhado ao perfil?
   - Tom de voz correto?
   - Logo bem aplicada?

8. ENGAGEMENT POTENTIAL (0-10):
   - Potencial de swipe-through?
   - Conteúdo salvável?
   - Compartilhável?

RETORNAR JSON:
{{
  "overall_score": 0-100,
  "scores_by_criteria": {{...}},
  "strengths": ["pontos fortes"],
  "weaknesses": ["pontos fracos"],
  "critical_issues": ["problemas graves"],
  "improvement_suggestions": ["melhorias específicas"],
  "estimated_completion_rate": "50-60%",
  "ready_for_publish": true/false,
  "next_steps": ["o que fazer antes de publicar"]
}}
"""
```

---

## 📚 Uso dos Prompts

### Exemplo de Fluxo Completo

```python
# 1. Escolher tipo de narrativa
narrative_prompt = prompt_choose_narrative_type(theme, creator_profile)
narrative_choice = ai_service.generate_text(narrative_prompt, user)

# 2. Estruturar slides
structure_prompt = prompt_structure_slides(theme, narrative_choice['narrative_type'], 7, semantic_analysis)
slides_structure = ai_service.generate_text(structure_prompt, user)

# 3. Gerar texto para cada slide
for slide in slides_structure:
    text_prompt = prompt_generate_slide_text(slide, semantic_analysis, profile, previous_slides)
    slide_text = ai_service.generate_text(text_prompt, user)
    
    # 4. Gerar imagem para cada slide
    image_prompt = prompt_generate_slide_image(slide, slide_text, visual_context, profile, include_logo)
    slide_image = ai_service.generate_image(image_prompt, user_logo, user)

# 5. Validar qualidade
validation_prompt = prompt_validate_carousel_quality(carousel_data)
quality_report = ai_service.generate_text(validation_prompt, user)

# 6. Gerar legenda
caption_prompt = prompt_generate_carousel_caption(theme, narrative_type, slides_summary, profile)
carousel_caption = ai_service.generate_text(caption_prompt, user)
```

---

## 🔧 Personalização de Prompts

### Variáveis Dinâmicas Disponíveis

```python
PROFILE_VARS = {
    'business_name': str,
    'specialization': str,
    'target_audience': str,
    'voice_tone': str,
    'brand_personality': str,
    'color_palette': list,
    'visual_style': str
}

SEMANTIC_VARS = {
    'main_theme': str,
    'emotion': str,
    'keywords': list,
    'target_pain_point': str,
    'desired_outcome': str
}

VISUAL_CONTEXT_VARS = {
    'total_slides': int,
    'current_sequence': int,
    'previous_slide_colors': list,
    'visual_style': str,
    'logo_placement': str
}
```

---

_Documento atualizado: Janeiro 2025_  
_Manutenção: Equipe PostNow_

