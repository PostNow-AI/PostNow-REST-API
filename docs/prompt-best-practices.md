# Boas Práticas de Prompt para Geração de Imagem — PostNow

> Documento vivo. Toda decisão sobre prompts de imagem deve seguir estas práticas.
> Atualizar sempre que descobrirmos algo novo.

---

## 1. Modelo: Gemini + Imagen

### Motor atual

O PostNow usa **Gemini** (Google) para geração de imagens via Vertex AI. As práticas deste documento são otimizadas para este modelo, mas os princípios gerais se aplicam a qualquer IA de imagem.

### Capacidades confirmadas

- Entende linguagem natural descritiva (não precisa de keywords soltas)
- Entende negações: "Do not include watermarks" funciona
- Bom com composição e posicionamento espacial
- Bom com estilos de referência (art deco, bauhaus, editorial)
- Renderiza texto curto em inglês com boa qualidade
- Entende memory colors (nomes descritivos de cor)

### Limitações conhecidas

- **Texto renderizado**: máximo 25 caracteres confiáveis, palavras curtas
- **Caracteres acentuados**: ã, ç, é, ô, ü são zona de risco — podem sair corretos mas frequentemente falham (letras trocadas, omitidas ou distorcidas)
- **Caracteres não-latinos**: kanji, cirílico, árabe — alta taxa de erro
- **Texto longo**: parágrafos, subtítulos pequenos, hashtags — não renderizar
- **Ortografia**: não garantida — pode errar mesmo palavras simples
- **Múltiplas fontes de luz**: conflitam e geram resultados inconsistentes

### Decisão de idioma do prompt

| Parte do prompt | Idioma | Razão |
|---|---|---|
| Instruções visuais (composição, estilo, cores, iluminação) | **Inglês** | Gemini foi treinado majoritariamente em inglês; termos como "soft natural daylight" têm representação mais rica no modelo |
| Texto para renderizar na imagem | **PT-BR** | É o que o usuário final verá. Usar entre aspas: `"Conquiste Clientes"` |
| Seção EVITAR | **Inglês** | Melhor interpretação pelo modelo |
| Nomes de cores (memory colors) | **Inglês** | Memory colors são catalogados em inglês |

**Regra prática:** Tudo que é instrução para o modelo → inglês. Tudo que aparece visualmente para o usuário → PT-BR.

---

## 2. Cores

### REGRA: Usar Memory Colors, NUNCA hex codes

A IA de imagem interpreta cor conceitualmente (padrões visuais do treinamento), não como ciência de cor. Hex codes são ignorados ou mal interpretados.

**Errado:**
```
Paleta: #FF1493, #0066FF, #1A1A2E
```

**Certo:**
```
Paleta: vivid hot pink, bright cobalt blue, deep midnight navy
```

### Como descrever cores

Usar nomes baseados em objetos do mundo real (memory colors) + modificadores:

**Estrutura:** `[modificador de intensidade] + [memory color]`

**Modificadores de intensidade:** pale, soft, pastel, bright, deep, vivid, bold, dark, muted, rich

**Modificadores de temperatura:** warm, cool, icy, frosted, fiery, dusky, earthy

**Modificadores de acabamento:** glossy, matte, metallic, shimmering, iridescent, pearlescent

**Memory colors por família:**

| Família | Nomes reconhecidos pela IA |
|---|---|
| Red | cherry, cranberry, scarlet, ruby, wine, burgundy, brick, coral, ember, pomegranate, tomato, blush |
| Orange | pumpkin, tangerine, apricot, rust, amber, copper, burnt orange, saffron, persimmon, ginger |
| Yellow | lemon, canary, gold, butter, mustard, sunflower, honey, champagne, marigold, goldenrod |
| Green | emerald, olive, sage, forest, moss, mint, jade, chartreuse, pistachio, eucalyptus, fern, pine |
| Blue | sky, navy, royal, sapphire, denim, indigo, ice blue, teal, cobalt, cornflower, glacier, steel |
| Purple | lavender, plum, violet, eggplant, orchid, amethyst, mauve, lilac, wisteria, twilight |
| White | pearl, cream, ivory, alabaster, porcelain, eggshell, chalk, snow, linen, parchment |
| Black/Gray | charcoal, graphite, slate, ash, onyx, coal, obsidian, pewter, smoke, gunmetal |
| Brown | chocolate, coffee, cinnamon, chestnut, caramel, toffee, walnut, sand, taupe, sienna |
| Pink | rose, blush, salmon, flamingo, cotton candy, coral, peach, raspberry, cherry blossom |
| Cyan | aqua, turquoise, lagoon, ocean, seafoam, teal, cerulean, caribbean |

### Paleta no prompt

Limitar a 2-3 cores dominantes + 1 cor de acento. Mais que isso gera resultados confusos.

```
Cores dominantes: warm ivory background, muted sage green elements
Cor de acento: deep burgundy details
```

### Cuidados com nomes ambíguos

Nomes como "salmon", "watermelon", "lavender" podem gerar o OBJETO (peixe, fruta, flor) ao invés da COR. Usar o sufixo "-color" quando houver ambiguidade: "salmon-color" ao invés de "salmon".

### Conversão hex → memory color

Para cores do onboarding do cliente (armazenadas em hex), usar `services/color_extraction.py`.
Pendência: melhorar de CSS3 names para memory colors (hoje converte #E07A5F → "salmon", deveria ser "warm terracotta").

**Fontes:**
- [Ideogram — Memory Colors](https://docs.ideogram.ai/using-ideogram/prompting-guide/9-prompting-references/memory-colors-for-naming-color-nuances)
- [img2go — Color in AI Art](https://www.img2go.com/blog/how-to-master-color-in-ai-art)
- [ArtyClick Color Name Finder](https://colors.artyclick.com/color-name-finder/)

---

## 3. Estrutura do Prompt

### REGRA: Descrever a cena, não listar keywords

A IA responde melhor a linguagem natural descritiva do que a listas de palavras-chave.

**Errado:**
```
post instagram, business, blue, modern, professional, 4:5
```

**Certo:**
```
Professional social media post for a tech consulting business.
Clean composition with a bright cobalt blue background.
Modern sans-serif typography with the title centered.
Vertical format 4:5 for Instagram feed.
```

### Ordem dos elementos no prompt

Seguir esta ordem (do mais importante ao menos):

1. **Tipo/Formato** — O que é e para que serve
2. **Sujeito** — O elemento principal da imagem
3. **Estilo** — Estética visual, medium
4. **Cores** — Paleta em memory colors
5. **Composição** — Enquadramento, layout, posicionamento
6. **Iluminação** — Tipo, direção, atmosfera
7. **Tipografia** — Se houver texto renderizado
8. **Restrições** — O que evitar (seção EVITAR)
9. **Qualidade** — Resolução, acabamento

### Tamanho do prompt

Manter entre 100-300 palavras. Prompts curtos demais geram resultados genéricos. Prompts longos demais confundem o modelo.

**Fontes:**
- [Google Cloud — Imagen Prompt Guide](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/image/img-gen-prompt-guide)
- [Google DeepMind — Nano Banana Prompt Guide](https://deepmind.google/models/gemini-image/prompt-guide/)

---

## 4. Composição

### REGRA: Ser específico sobre posicionamento

Não dizer "layout equilibrado". Descrever ONDE cada elemento está.

**Errado:**
```
Layout equilibrado com hierarquia visual clara
```

**Certo:**
```
Title text positioned in the upper third of the image.
Main visual element centered, occupying 40% of the frame.
Brand logo small (8% width) in the bottom-right corner.
Generous negative space (at least 30%) around the text for readability.
```

### Aspect ratios

Sempre especificar no prompt:
- **Feed Instagram:** 4:5 vertical (1080x1350px)
- **Stories/Reels:** 9:16 vertical (1080x1920px)
- **Post quadrado:** 1:1 (1080x1080px)

### Margem de segurança

Pedir margem de 8-10% nas bordas para evitar corte de texto no feed.

**Fontes:**
- [LetsEnhance — AI Prompt Guide 2026](https://letsenhance.io/blog/article/ai-text-prompt-guide/)
- [Google Developers Blog — Gemini 2.5 Flash](https://developers.googleblog.com/en/how-to-prompt-gemini-2-5-flash-image-generation-for-the-best-results/)

---

## 5. Iluminação

### REGRA: Sempre especificar a fonte de luz

Cor não existe sem luz. A iluminação define 50% do mood da imagem.

**Termos que a IA entende bem:**

| Efeito desejado | Termo no prompt |
|---|---|
| Suave e natural | "soft natural daylight", "diffused window light" |
| Profissional | "studio three-point lighting setup" |
| Quente e acolhedor | "warm golden hour sunlight" |
| Dramático | "dramatic side lighting with deep shadows" |
| Frio e tech | "cool ambient neon glow" |
| Nórdico/clean | "soft overcast nordic daylight" |
| Cinematográfico | "cinematic backlight with lens flare" |
| Noturno/neon | "neon lighting against dark background, bloom effect" |

### Regra de ouro

Definir UMA fonte de luz principal + UMA atmosfera. Múltiplas fontes conflitantes geram resultados inconsistentes.

**Fontes:**
- [ArtSmart — Color Theory in AI](https://artsmart.ai/blog/color-theory-in-ai/)

---

## 6. Tipografia / Texto na Imagem

### REGRA: Texto curto, entre aspas, com fonte descrita

A IA ainda tem dificuldade com texto. Regras para minimizar erros:

1. **Máximo 25 caracteres** — palavras curtas, títulos de 3-6 palavras
2. **Colocar entre aspas** — `"Conquiste Clientes"` não `Conquiste Clientes`
3. **Especificar fonte como estilo** — "bold sans-serif font" ou "elegant serif typeface"
4. **Descrever posição** — "centered in the upper third"
5. **Descrever cor do texto** — "white text" ou "dark text with subtle shadow for contrast"
6. **Especificar idioma** — "All rendered text must be in Brazilian Portuguese (PT-BR)"
7. **Nunca pedir parágrafos** — apenas títulos curtos

### Regras para acentos PT-BR

O Gemini tem dificuldade com caracteres acentuados. Estratégias:

1. **Preferir palavras sem acento quando possível** — "Sucesso" ao invés de "Você"
2. **Evitar ç e ã em títulos renderizados** — alto risco de distorção
3. **Testar antes de aprovar** — acentos podem sair corretos ou completamente errados
4. **Alternativa segura**: se o texto tem muitos acentos, considerar renderizar o texto via código (overlay) em vez de pedir à IA
5. **Palavras seguras** (sem acento): Sucesso, Resultados, Crescimento, Vendas, Lucro, Digital, Marketing, Performance, Estrategia, Impulso, Descubra, Transforme
6. **Palavras de risco** (com acento): Você, Ação, Conexão, Solução, Nutrição, Começar, Avanço, Promoção

### O que EVITAR em texto

- Nunca pedir mais de 3 frases distintas
- Nunca pedir textos longos ou subtítulos pequenos
- Nunca pedir hashtags renderizadas na imagem
- Nunca pedir códigos hex renderizados na imagem
- Nunca assumir que a IA vai acertar a ortografia de primeira — iterar

**Fontes:**
- [Ideogram — Text and Typography](https://docs.ideogram.ai/using-ideogram/prompting-guide/2-prompting-fundamentals/text-and-typography)
- [Google DeepMind — Nano Banana Prompt Guide](https://deepmind.google/models/gemini-image/prompt-guide/)

---

## 7. Estilo Visual

### REGRA: Descrever com referências reconhecíveis, não adjetivos vagos

A IA conhece referências culturais e estéticas do treinamento. Usar isso.

**Errado:**
```
Estilo moderno e bonito
```

**Certo:**
```
Clean minimalist design inspired by Apple product pages.
Soft gradient background transitioning from pale lavender to light sky blue.
Sans-serif typography with generous letter-spacing.
```

### Referências que funcionam bem

- Movimentos artísticos: "art deco poster", "bauhaus design", "swiss typography"
- Plataformas/marcas: "Apple-like product page", "editorial magazine layout"
- Fotografia: "editorial fashion photography", "flat lay product photography"
- Mood boards: "hygge-inspired Scandinavian", "Japanese zen minimalism"

### O que NÃO funciona

- Adjetivos vagos sozinhos: "bonito", "profissional", "moderno"
- Estilos contraditórios: "minimalist with intricate details"
- Referências obscuras que a IA provavelmente não conhece

---

## 8. Seção EVITAR (Negative Prompts)

### REGRA: Ser específico e concreto, nunca vago

**Errado:**
```
Evitar coisas feias, qualidade ruim, elementos inadequados
```

**Certo:**
```
Do not include: watermarks, stock photo badges, extra fingers,
distorted text, blurry elements, cluttered background,
colors outside the specified palette.
```

### Organizar por categoria

```
AVOID:
- Technical: blurry, low resolution, pixelated, banding in gradients
- Content: watermarks, stock badges, unrelated objects
- Text: misspelled words, extra characters, text in wrong language
- Style: colors outside brand palette, clashing fonts
```

### Cuidado com negações

Algumas IAs de imagem não entendem "no" ou "don't". Preferir listar o que excluir sem negação:
- Ao invés de "no watermark" → listar "watermark" na seção de exclusão
- O Gemini entende linguagem natural, então "Do not include watermarks" funciona

**Fontes:**
- [ArtSmart — Negative Prompts Guide](https://artsmart.ai/blog/how-negative-prompts-work-in-ai-image-generation/)
- [God of Prompt — 10 AI Image Mistakes](https://www.godofprompt.ai/blog/10-ai-image-generation-mistakes-99percent-of-people-make-and-how-to-fix-them)

---

## 9. Consistência de Feed (Instagram)

### REGRA: Manter elementos fixos entre posts

Para que os posts pareçam do mesmo feed:

1. **Posição fixa do logo** — sempre no mesmo canto, mesmo tamanho
2. **Mesma família tipográfica** — não variar fonte entre posts
3. **Paleta consistente** — mesmas cores de marca em todos os posts
4. **Estilo de iluminação consistente** — não misturar neon com natural entre posts
5. **Mesmo aspect ratio** — não alternar entre 1:1 e 4:5

### Como garantir no prompt

Incluir seção de "brand constraints" no prompt:
```
BRAND CONSTRAINTS:
- Logo: "PostNow" in bottom-right corner, 8% of image width
- Typography: modern sans-serif (similar to Inter or Poppins)
- Brand colors: bright electric amethyst as accent, pure white as primary
- Consistent style: all posts should feel like part of the same visual series
```

**Fontes:**
- [Typeface.ai — AI Brand Consistency](https://www.typeface.ai/blog/ai-brand-management-how-to-maintain-brand-consistency-with-ai-image-generators)
- [Nightjar — Photography Styles with AI](https://nightjar.so/blog/photography-styles-build-consistent-brand-aesthetic-with-ai)

---

## 10. Qualidade e Resolução

### REGRA: Especificar qualidade desejada com contexto

Não basta listar termos de qualidade — contextualizá-los com o uso.

**Básico (mínimo):**
```
High-quality rendering, sharp focus, no artifacts.
```

**Completo (recomendado):**
```
Professional social media quality, optimized for mobile viewing.
Sharp focus on text elements, smooth gradients without banding.
Clean edges on all graphic elements, no compression artifacts.
Ultra-detailed rendering suitable for Instagram feed at 1080x1350px.
```

**Termos que aumentam qualidade percebida:**

| Categoria | Termos |
|---|---|
| Resolução | "4K resolution", "ultra-detailed", "high-resolution" |
| Nitidez | "sharp focus", "crisp rendering", "tack-sharp" |
| Profissional | "studio quality", "magazine editorial quality", "professional photography" |
| Técnico | "HDR", "no artifacts", "smooth gradients", "clean edges" |
| Contexto | "optimized for mobile", "social media quality", "print-ready" |

### Qualidade vs. velocidade

Mais termos de qualidade = geração mais lenta. Para previews/drafts, usar apenas "high-quality, sharp focus". Para versão final, usar a versão completa.

---

## 11. Iteração

### REGRA: Mudar UMA variável por vez

Quando o resultado não for bom, não reescrever o prompt inteiro. Mudar um elemento:

1. Primeira tentativa: prompt completo
2. Se a cor estiver errada: ajustar apenas a seção de cores
3. Se a composição estiver ruim: ajustar apenas o posicionamento
4. Se o texto estiver ilegível: ajustar fonte/posição/contraste

Isso permite entender o que funciona e o que não funciona.

---

## 12. Templates de Referência (PostNow)

### Template: Post Feed Instagram (completo)

Este é o formato que o `image_generation_prompt()` deve gerar. Exemplo para uma consultoria de marketing digital:

```
Professional Instagram feed post (4:5 vertical format, 1080x1350px)
for a digital marketing consulting business.

STYLE:
Clean minimalist design inspired by editorial magazine layouts.
Soft gradient background transitioning from warm ivory to pale sky blue.
Modern sans-serif typography with generous letter-spacing.
Soft overcast nordic daylight illumination, diffused and even.

SUBJECT AND CONTEXT:
Main visual: abstract geometric shapes representing growth and strategy.
Theme: client acquisition and business growth.
Mood: confident, professional, aspirational.

COLORS:
- Background: warm ivory transitioning to pale sky blue
- Primary elements: deep cobalt blue
- Accent: vivid coral details
- Text: dark charcoal for maximum contrast

COMPOSITION:
Title text "Conquiste Clientes" (in Brazilian Portuguese) positioned in
the upper third, centered, in bold sans-serif font, dark charcoal color.
Main visual element centered, occupying 40% of the frame.
Generous negative space (at least 30%) around text for readability.
Safe margin of 10% on all edges — no important elements near borders.

LOGO:
Brand logo in bottom-right corner, occupying 8% of image width.
Semi-transparent, integrated harmoniously with the design.

QUALITY:
Professional social media quality, optimized for mobile viewing.
Sharp focus on text, smooth gradients, clean edges, no artifacts.

AVOID:
- Watermarks, stock photo badges
- Distorted or misspelled text
- Colors outside the specified palette
- Cluttered background, too many elements
- Hashtags or hex codes rendered in the image
- Text in any language other than Brazilian Portuguese
```

### Template: Post Feed Instagram (mínimo viável)

Para quando o estilo é mais simples ou o conteúdo é direto:

```
Instagram feed post, 4:5 vertical format.
Digital marketing business promoting client growth.

Clean design with warm ivory background and deep cobalt blue elements.
Bold sans-serif title "Mais Vendas" centered in the upper third,
dark charcoal text with subtle shadow for contrast.

Brand logo small in bottom-right corner (8% width).
Soft natural daylight, professional studio quality.
Safe margin 10% on all edges.

AVOID: watermarks, blurry text, cluttered background,
colors outside brand palette, text in wrong language.
```

### Template: Stories/Reels (9:16)

```
Instagram Stories format (9:16 vertical, 1080x1920px)
for a wellness coaching business.

STYLE:
Warm organic aesthetic inspired by Scandinavian hygge design.
Earthy tones with natural textures (linen, wood grain).
Warm golden hour sunlight illumination.

SUBJECT:
Motivational content about self-care and daily routines.
Central visual: soft botanical illustration, eucalyptus branches.

COLORS:
- Background: warm linen with subtle texture
- Primary: muted sage green
- Accent: soft terracotta
- Text: rich espresso brown

COMPOSITION:
Title "Cuide de Voce" in the center-upper area (avoid accent in "Voce"
for reliable rendering), elegant serif typeface, rich espresso brown.
Botanical elements framing the top and bottom thirds.
Central area kept clean for text readability.
Swipe-up area (bottom 15%) kept clear.
Safe margin 10% on all edges.

LOGO:
"WellLife" text logo, bottom-center, 10% width, muted sage green.

QUALITY:
High-quality, sharp text, smooth gradients, mobile-optimized.

AVOID:
- Blurry elements, low resolution
- Text near edges (Stories crop zone)
- More than 2 text blocks
- Accent characters: ê, ã, ç in rendered text
```

---

## Changelog

| Data | Mudança |
|---|---|
| 2026-03-13 | Adicionado: seção Gemini (capacidades, limitações, idioma). Regras PT-BR acentos. Templates completos (feed, stories). Seção Qualidade expandida. Reordenado seções (Modelo primeiro). |
| 2026-03-13 | Documento criado. Seções: cores (memory colors), estrutura, composição, iluminação, tipografia, estilo visual, EVITAR, consistência de feed, qualidade, iteração. |
