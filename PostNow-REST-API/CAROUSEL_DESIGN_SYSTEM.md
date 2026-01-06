# 🎨 Design System para Carrosséis Instagram

> **Documento Complementar:** CAROUSEL_IMPLEMENTATION_GUIDE.md  
> **Objetivo:** Guia visual e padrões de design para carrosséis  
> **Status:** Referência Visual e Técnica

---

## 📋 Índice

1. [Fundamentos Visuais](#fundamentos-visuais)
2. [Grid e Layout](#grid-e-layout)
3. [Tipografia](#tipografia)
4. [Paletas de Cores](#paletas-de-cores)
5. [Elementos de Interface](#elementos-de-interface)
6. [Templates por Tipo](#templates-por-tipo)
7. [Tratamento de Logo](#tratamento-de-logo)
8. [Exemplos Práticos](#exemplos-práticos)

---

## 🎯 Fundamentos Visuais

### Dimensões e Proporções

```yaml
Instagram Feed Carousel:
  formato_recomendado: "4:5 (Vertical)"
  pixels: "1080x1350"
  formato_alternativo: "1:1 (Quadrado)"
  pixels_alternativo: "1080x1080"
  
Áreas Importantes:
  safe_zone: "80-100px de margem"
  area_cortada_feed: "Top 100px pode ser cortada"
  area_visivel_garantida: "980x1150px (vertical)"
```

### Hierarquia Visual

```
Nível 1 - TÍTULO PRINCIPAL:
  Tamanho: 56-72px
  Peso: Bold/Black (700-900)
  Cor: Alto contraste
  Espaço vertical: 40px acima e abaixo

Nível 2 - SUBTÍTULO/DESTAQUE:
  Tamanho: 36-48px
  Peso: SemiBold (600)
  Cor: Cor da marca ou secundária
  Espaço vertical: 24px acima e abaixo

Nível 3 - CORPO DE TEXTO:
  Tamanho: 24-32px
  Peso: Regular/Medium (400-500)
  Cor: Neutro (alto contraste)
  Line-height: 1.4-1.6
  Espaço vertical: 16px entre parágrafos

Nível 4 - ELEMENTOS SECUNDÁRIOS:
  Tamanho: 18-24px
  Peso: Regular (400)
  Cor: Secundária ou neutra
  Uso: Numeração, setas, notas
```

### Princípios de Design

```
1. MENOS É MAIS:
   - Máximo 3 níveis de hierarquia por slide
   - Espaço negativo = 40-50% da imagem
   - Não poluir visualmente

2. LEGIBILIDADE PRIMEIRO:
   - Contraste mínimo: 4.5:1 (WCAG AA)
   - Contraste ideal: 7:1 (WCAG AAA)
   - Teste em telas pequenas (mobile)

3. CONSISTÊNCIA:
   - Mesma família tipográfica em todos os slides
   - Grid alinhado slide a slide
   - Cores harmônicas (paleta de 3-5 cores)

4. PROGRESSÃO VISUAL:
   - Cores podem variar gradualmente
   - Elementos aumentam em densidade (ou diminuem)
   - Sensação de movimento/narrativa
```

---

## 📐 Grid e Layout

### Sistema de Grid 12x12

```
Layout Base (1080x1350px):
┌─────────────────────────────────┐
│ [Safe Zone - 80px]              │
│ ┌─────────────────────────────┐ │
│ │ [Grid 12 colunas × 12 linhas]│ │
│ │                               │ │
│ │  [Área de Conteúdo Ativo]    │ │
│ │                               │ │
│ │  920x1190px                   │ │
│ │                               │ │
│ └─────────────────────────────┘ │
│ [Safe Zone - 80px]              │
└─────────────────────────────────┘

Grid Spacing:
- Column width: ~76px
- Gutter: 20px
- Row height: ~99px
```

### Templates de Layout

#### Layout 1: Título Centralizado

```
┌───────────────────────────┐
│                           │
│      [LOGO opcional]      │ ← Linha 1-2
│                           │
│                           │
│      ╔═════════════╗      │
│      ║   TÍTULO    ║      │ ← Linhas 4-6
│      ║  PRINCIPAL  ║      │
│      ╚═════════════╝      │
│                           │
│     Subtítulo breve       │ ← Linha 7
│                           │
│      [Elemento visual]    │ ← Linhas 8-10
│                           │
│     Deslize → [1/7]       │ ← Linha 11-12
└───────────────────────────┘
```

#### Layout 2: Texto à Esquerda

```
┌───────────────────────────┐
│ [1/7]      [Logo]         │ ← Linha 1
│                           │
│ TÍTULO                    │ ← Linhas 2-3
│ GRANDE                    │
│                           │
│ Corpo do texto aqui       │ ← Linhas 4-8
│ com múltiplas linhas      │
│ bem espaçadas para        │
│ leitura confortável       │
│                           │
│     [Elemento visual]     │ ← Linhas 9-11
│     ou ícone              │
│              Deslize →    │ ← Linha 12
└───────────────────────────┘
```

#### Layout 3: Split Screen

```
┌───────────────────────────┐
│ [1/7]           [Logo]    │
├───────────────────────────┤
│          TÍTULO           │ ← Linhas 2-3
├─────────────┬─────────────┤
│             │             │
│   CONTEÚDO  │   VISUAL    │ ← Linhas 4-10
│   TEXTUAL   │   OU        │
│             │   ÍCONE     │
│             │             │
├─────────────┴─────────────┤
│         Deslize →         │ ← Linha 11-12
└───────────────────────────┘
```

#### Layout 4: Lista Vertical

```
┌───────────────────────────┐
│ [2/7]           [Logo]    │
│                           │
│ ✓ Ponto 1                 │ ← Linhas 3-4
│   Explicação breve        │
│                           │
│ ✓ Ponto 2                 │ ← Linhas 5-6
│   Explicação breve        │
│                           │
│ ✓ Ponto 3                 │ ← Linhas 7-8
│   Explicação breve        │
│                           │
│ ✓ Ponto 4                 │ ← Linhas 9-10
│   Explicação breve        │
│                           │
│              Deslize →    │ ← Linha 12
└───────────────────────────┘
```

---

## 🔤 Tipografia

### Famílias de Fontes Recomendadas

```yaml
Opção 1 - Sans Serif Moderna:
  titulo: "Inter Black / Montserrat ExtraBold"
  corpo: "Inter Regular / Montserrat Regular"
  destaque: "Inter SemiBold / Montserrat SemiBold"
  
Opção 2 - Profissional Clean:
  titulo: "Helvetica Neue Bold / Arial Black"
  corpo: "Helvetica Neue Regular / Arial"
  destaque: "Helvetica Neue Medium"
  
Opção 3 - Moderna e Amigável:
  titulo: "Poppins Bold / Nunito Black"
  corpo: "Poppins Regular / Nunito Regular"
  destaque: "Poppins SemiBold / Nunito SemiBold"

Opção 4 - Corporativa:
  titulo: "Roboto Bold / Open Sans Bold"
  corpo: "Roboto Regular / Open Sans Regular"
  destaque: "Roboto Medium / Open Sans SemiBold"
```

### Scale Tipográfica (Base: 1080px width)

```yaml
Display (Capas):
  size: 72px
  line_height: 1.1
  letter_spacing: -0.02em
  use: Títulos de impacto

H1 (Títulos Principais):
  size: 56px
  line_height: 1.2
  letter_spacing: -0.01em
  use: Títulos de slides

H2 (Subtítulos):
  size: 40px
  line_height: 1.3
  letter_spacing: 0
  use: Subtítulos, destaques

H3 (Terciário):
  size: 32px
  line_height: 1.4
  letter_spacing: 0
  use: Seções menores

Body Large:
  size: 28px
  line_height: 1.5
  letter_spacing: 0
  use: Corpo principal

Body Regular:
  size: 24px
  line_height: 1.6
  letter_spacing: 0
  use: Corpo secundário

Small:
  size: 20px
  line_height: 1.5
  letter_spacing: 0.01em
  use: Notas, números de slide

Tiny:
  size: 18px
  line_height: 1.4
  letter_spacing: 0.02em
  use: Disclaimers, créditos
```

### Regras de Uso

```
MÁXIMO DE CARACTERES POR LINHA:
- Título: 30-40 caracteres
- Subtítulo: 40-60 caracteres
- Corpo: 50-70 caracteres

QUEBRAS DE LINHA:
- Evitar palavras órfãs (1 palavra na última linha)
- Quebrar em pontos naturais (vírgulas, "e", "ou")
- Não quebrar nomes próprios

ALL CAPS:
- Usar apenas em títulos curtos (máx. 4 palavras)
- Aumentar letter-spacing (+0.05em)
- Reduzir tamanho em 10-15% vs. sentence case

ÊNFASE:
- Bold: Palavras-chave (máx. 3 por slide)
- Cor: Destaque com cor da marca
- NUNCA: Sublinhado (confunde com link)
```

---

## 🎨 Paletas de Cores

### Estrutura de Paleta para Carrossel

```yaml
Paleta Completa (6-7 cores):
  primary: "#HEX"       # Cor da marca (títulos, CTAs)
  secondary: "#HEX"     # Cor de apoio (destaques)
  accent: "#HEX"        # Cor de contraste (elementos interativos)
  
  background_light: "#HEX"  # Fundo claro
  background_dark: "#HEX"   # Fundo escuro
  
  text_primary: "#HEX"      # Texto principal (escuro)
  text_secondary: "#HEX"    # Texto secundário (claro)
  
  neutral_1: "#HEX"         # Cinza claro
  neutral_2: "#HEX"         # Cinza médio
  neutral_3: "#HEX"         # Cinza escuro
```

### Estratégias de Aplicação

#### Estratégia 1: Monocromática + Acento

```yaml
Slide 1: fundo=#F5F5F5, acento=brand_color
Slide 2: fundo=#F5F5F5, acento=brand_color
Slide 3: fundo=#F5F5F5, acento=brand_color
...
Slide 7: fundo=#F5F5F5, acento=brand_color

Vantagem: Máxima consistência
Uso: Conteúdo corporativo, profissional
```

#### Estratégia 2: Gradiente Progressivo

```yaml
Slide 1: fundo=brand_color (100%), texto=white
Slide 2: fundo=brand_color (85%) + secondary (15%)
Slide 3: fundo=brand_color (70%) + secondary (30%)
Slide 4: fundo=brand_color (50%) + secondary (50%)
Slide 5: fundo=brand_color (30%) + secondary (70%)
Slide 6: fundo=brand_color (15%) + secondary (85%)
Slide 7: fundo=secondary (100%), texto=white

Vantagem: Sensação de progressão
Uso: Storytelling, jornadas
```

#### Estratégia 3: Alternância High Contrast

```yaml
Slide 1: fundo=brand_color_dark, texto=white
Slide 2: fundo=white, texto=brand_color_dark
Slide 3: fundo=brand_color_dark, texto=white
Slide 4: fundo=white, texto=brand_color_dark
...

Vantagem: Ritmo visual, separação clara
Uso: Listas, comparações
```

#### Estratégia 4: Zona de Cor por Seção

```yaml
Intro (Slides 1-2): Cores vibrantes, energéticas
Desenvolvimento (Slides 3-5): Cores neutras, foco em conteúdo
Conclusão (Slides 6-7): Retorno às cores vibrantes

Vantagem: Narrativa visual clara
Uso: Tutoriais, educacional
```

### Testes de Contraste

```python
# Ferramenta para calcular contraste
def calculate_contrast_ratio(color1_hex, color2_hex):
    """
    Calcula contrast ratio entre duas cores.
    
    WCAG Standards:
    - AA (mínimo): 4.5:1 para texto normal
    - AA (grande): 3:1 para texto ≥24px
    - AAA (ideal): 7:1 para texto normal
    """
    # Implementação baseada em WCAG 2.1
    pass

# Exemplos de combinações aprovadas:
combinations = {
    "white_on_dark_blue": 12.63,  # ✅ AAA
    "black_on_white": 21.00,      # ✅ AAA
    "dark_gray_on_light": 7.12,   # ✅ AAA
    "brand_on_light": 4.89,       # ✅ AA
    "light_gray_on_white": 2.98,  # ❌ Falha
}
```

---

## 🧩 Elementos de Interface

### Numeração de Slides

```
Opção 1 - Minimalista:
┌─────────────────────┐
│ 1/7        [Logo]   │
│                     │
└─────────────────────┘

Estilo:
- Posição: Canto superior esquerdo
- Tamanho: 20-24px
- Cor: Neutra (30-40% opacidade)
- Fonte: Regular

Opção 2 - Destaque:
┌─────────────────────┐
│ ╔═══╗      [Logo]   │
│ ║1/7║               │
│ ╚═══╝               │
└─────────────────────┘

Estilo:
- Background: Cor da marca
- Texto: Branco, Bold
- Tamanho: 24px
- Border-radius: 8px
- Padding: 8px 12px

Opção 3 - Barra de Progresso:
┌─────────────────────┐
│ ████░░░░░░  [Logo]  │
│ 1 de 7              │
└─────────────────────┘

Estilo:
- Barra: 60% largura da tela
- Preenchido: Cor da marca
- Vazio: Cinza claro (20% opacidade)
- Height: 4px
```

### Setas Direcionais

```
Opção 1 - Seta Simples:
                  →
Estilo:
- Tamanho: 32-40px
- Cor: Cor da marca
- Posição: Canto inferior direito
- Padding: 40px das bordas

Opção 2 - Seta com Fundo:
               ┌───┐
               │ → │
               └───┘
Estilo:
- Background: Cor da marca
- Seta: Branca
- Tamanho total: 56x56px
- Border-radius: 50% (circular)
- Posição: Canto inferior direito

Opção 3 - Seta + Texto:
            Deslize →
Estilo:
- Texto: 18-20px, SemiBold
- Seta: 24px
- Cor: Cor da marca ou contraste
- Posição: Centro-inferior ou direita
- Animação: Pulsar suavemente (opcional)
```

### Checkboxes/Bullets

```
Para Listas (Checked):
✓ Item completado
✓ Outro item

Estilo:
- Ícone: ✓ ou ✔
- Tamanho: 28-32px
- Cor: Verde (#4CAF50) ou cor da marca
- Espaçamento: 16px entre ícone e texto

Para Listas (Unchecked):
☐ Item pendente
☐ Outro item

Estilo:
- Ícone: ☐ ou ⬜
- Tamanho: 28-32px
- Cor: Cinza (#9E9E9E)
- Espaçamento: 16px entre ícone e texto

Bullets Numerados:
1️⃣ Primeiro passo
2️⃣ Segundo passo

Estilo:
- Emojis: Números coloridos
- Ou: Círculos com números
- Tamanho: 36-40px
- Espaçamento: 20px entre número e texto
```

### CTAs e Botões

```
Botão Primário:
┌─────────────────────┐
│  CLIQUE AQUI →      │
└─────────────────────┘

Estilo:
- Background: Cor da marca
- Texto: Branco, Bold, 28-32px
- Padding: 16px 40px
- Border-radius: 8-12px
- Shadow: 0 4px 12px rgba(0,0,0,0.15)

Botão Secundário:
┌─────────────────────┐
│  Saiba mais →       │
└─────────────────────┘

Estilo:
- Background: Transparente
- Texto: Cor da marca, SemiBold
- Border: 2px solid cor_da_marca
- Padding: 12px 32px
- Border-radius: 8-12px

CTA Textual:
"Salve este post para não esquecer 💾"

Estilo:
- Sem fundo
- Texto: 24-28px, Medium
- Cor: Cor da marca
- Emoji: Opcional, contextual
- Posição: Centro ou inferior
```

---

## 📦 Templates por Tipo

### Template: Lista/Checklist

```
SLIDE 1 (Capa):
┌───────────────────────────┐
│      [LOGO]               │
│                           │
│   7 DICAS QUE TODO        │
│   [NICHO] PRECISA         │
│   CONHECER                │
│                           │
│   [Ícone relevante]       │
│                           │
│   Deslize para ver → 1/7  │
└───────────────────────────┘
Colors: Brand vibrant + white

SLIDES 2-7 (Itens):
┌───────────────────────────┐
│ 2/7          [Logo mini]  │
│                           │
│ ✓ DICA #1                 │
│                           │
│ Texto explicativo da      │
│ dica aqui com múltiplas   │
│ linhas se necessário      │
│                           │
│ [Ícone ou visual]         │
│                           │
│              Próximo →    │
└───────────────────────────┘
Colors: White + brand accents

SLIDE 8 (CTA):
┌───────────────────────────┐
│                           │
│   RECAPITULANDO:          │
│   ✓ Dica 1                │
│   ✓ Dica 2                │
│   ✓ ...                   │
│                           │
│   Qual você vai           │
│   aplicar primeiro?       │
│   Comenta aí! 👇          │
│                           │
│   [LOGO]                  │
└───────────────────────────┘
Colors: Brand color + white text
```

### Template: Tutorial Passo-a-Passo

```
SLIDE 1 (Capa):
┌───────────────────────────┐
│                           │
│  COMO [FAZER X]           │
│  EM 5 PASSOS              │
│                           │
│  ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐    │
│  │1│→│2│→│3│→│4│→│5│    │
│  └─┘ └─┘ └─┘ └─┘ └─┘    │
│                           │
│  Simples e rápido         │
│  Deslize → [LOGO]         │
└───────────────────────────┘

SLIDES 2-6 (Passos):
┌───────────────────────────┐
│ ╔═══════╗    [Logo]       │
│ ║PASSO 1║                 │
│ ╚═══════╝                 │
│                           │
│ TÍTULO DO PASSO           │
│                           │
│ Instruções claras e       │
│ objetivas de como         │
│ executar este passo       │
│                           │
│ [Screenshot ou ícone]     │
│                           │
│         Próximo passo →   │
└───────────────────────────┘

SLIDE 7 (Resultado):
┌───────────────────────────┐
│                           │
│    RESULTADO FINAL        │
│                           │
│  [Imagem do resultado]    │
│                           │
│  Agora é sua vez!         │
│  Tenta e marca a gente    │
│  no stories 📸            │
│                           │
│    [LOGO]                 │
└───────────────────────────┘
```

### Template: Antes e Depois

```
SLIDE 1 (Teaser):
┌───────────────────────────┐
│                           │
│  DE [ANTES]               │
│  PARA [DEPOIS]            │
│  EM X DIAS                │
│                           │
│  Veja como →              │
│                           │
│  [LOGO]                   │
└───────────────────────────┘

SLIDES 2-3 (Antes):
┌───────────────────────────┐
│ ANTES                     │
├───────────────────────────┤
│                           │
│ [Imagem/Descrição         │
│  da situação inicial]     │
│                           │
│ Problemas:                │
│ • Problema 1              │
│ • Problema 2              │
│                           │
│         Continue →        │
└───────────────────────────┘
Colors: Red/Orange tones

SLIDES 4-5 (Processo):
┌───────────────────────────┐
│ O QUE MUDEI               │
├───────────────────────────┤
│                           │
│ Estratégia 1:             │
│ [Detalhes]                │
│                           │
│ Estratégia 2:             │
│ [Detalhes]                │
│                           │
│ Cronologia visual         │
│                           │
│         Continua →        │
└───────────────────────────┘
Colors: Neutral

SLIDES 6-7 (Depois):
┌───────────────────────────┐
│ DEPOIS                    │
├───────────────────────────┤
│                           │
│ [Imagem/Descrição         │
│  da situação final]       │
│                           │
│ Resultados:               │
│ ✓ Resultado 1             │
│ ✓ Resultado 2             │
│                           │
│    Você também pode! →    │
└───────────────────────────┘
Colors: Green/Blue tones

SLIDE 8 (CTA):
┌───────────────────────────┐
│                           │
│ RESUMO DA TRANSFORMAÇÃO   │
│                           │
│ Antes → Depois            │
│ [Dados comparativos]      │
│                           │
│ Quer replicar?            │
│ Salva este post!          │
│                           │
│ [LOGO]                    │
└───────────────────────────┘
```

---

## 🏷️ Tratamento de Logo

### Posicionamentos Estratégicos

```yaml
Estratégia 1 - Primeira e Última:
  slide_1:
    position: "centro-superior"
    size: 150-180px
    prominence: "alta"
  
  slides_2_a_6:
    logo: "não incluir"
  
  slide_7:
    position: "centro-inferior"
    size: 150-200px
    prominence: "alta"

Estratégia 2 - Watermark Constante:
  todos_slides:
    position: "canto-inferior-direito"
    size: 60-80px
    opacity: 85%
    prominence: "baixa (não distrai)"

Estratégia 3 - Apenas Capa:
  slide_1:
    position: "centro ou superior-direito"
    size: 120-150px
    prominence: "média"
  
  slides_2_a_7:
    logo: "não incluir"
    reasoning: "Foco total no conteúdo"
```

### Tratamentos Visuais

```css
/* Fundo Claro */
.logo-on-light {
  filter: none;
  version: "escura/colorida";
  shadow: "0 2px 4px rgba(0,0,0,0.08)"; /* sutil */
}

/* Fundo Escuro */
.logo-on-dark {
  filter: "brightness(0) invert(1)"; /* Se não tiver versão branca */
  version: "clara/branca preferível";
  glow: "0 0 8px rgba(255,255,255,0.3)"; /* opcional */
}

/* Fundo Fotográfico */
.logo-on-photo {
  backdrop: "retângulo semi-transparente";
  backdrop-color: "rgba(255,255,255,0.9) ou rgba(0,0,0,0.8)";
  backdrop-blur: "8px"; /* iOS style */
  padding: "12px 20px";
  border-radius: "8px";
}

/* Watermark */
.logo-watermark {
  opacity: 0.75-0.85;
  size: "60-80px";
  position: "fixed, canto inferior direito";
  margin: "40px";
  mix-blend-mode: "multiply"; /* Se escura em fundo claro */
}
```

### Checklist de Logo

```
✅ Logo tem versão vetorial (SVG ou alta resolução)?
✅ Existe versão monocromática (branca/preta)?
✅ Logo funciona em tamanhos pequenos (60px)?
✅ Contraste com fundo é adequado (4.5:1)?
✅ Logo não está cortada pelas margens?
✅ Posição consistente em slides similares?
✅ Tamanho proporcional ao conteúdo (não domina)?
✅ Safe zone respeitada (não será cortada no feed)?
```

---

## 📸 Exemplos Práticos

### Exemplo 1: Carrossel de Marketing Digital

```
TEMA: "5 Estratégias de Crescimento no Instagram"
TIPO: Lista
SLIDES: 7
ESTILO: Profissional, moderno, vibrante

PALETA:
- Primary: #E91E63 (Rosa/Magenta Instagram)
- Secondary: #9C27B0 (Roxo)
- Background: #FFFFFF
- Text: #212121

TIPOGRAFIA:
- Título: Montserrat Bold
- Corpo: Inter Regular

LAYOUT:
Slides 1, 7: Centralizado + Logo grande
Slides 2-6: Layout de lista + Logo watermark
```

### Exemplo 2: Carrossel de Saúde/Bem-estar

```
TEMA: "Jornada de 30 Dias para Vida Saudável"
TIPO: Storytelling
SLIDES: 8
ESTILO: Calmo, inspirador, natural

PALETA:
- Primary: #4CAF50 (Verde natureza)
- Secondary: #8BC34A (Verde claro)
- Tertiary: #FFC107 (Amarelo sol)
- Background: Gradiente verde suave
- Text: #1B5E20 (Verde escuro)

TIPOGRAFIA:
- Título: Poppins Bold
- Corpo: Poppins Regular

LAYOUT:
Transição gradual de cores escuras (dia 1) para claras (dia 30)
Logo: Apenas primeiro e último slide
```

### Exemplo 3: Carrossel de Tecnologia

```
TEMA: "Antes e Depois: Automação de Processos"
TIPO: Before/After
SLIDES: 7
ESTILO: Tech, clean, corporativo

PALETA:
- Primary: #2196F3 (Azul tech)
- Secondary: #00BCD4 (Ciano)
- Danger: #F44336 (Vermelho - para "antes")
- Success: #4CAF50 (Verde - para "depois")
- Background: #F5F5F5 (Cinza claro)
- Text: #37474F (Cinza escuro)

TIPOGRAFIA:
- Título: Roboto Bold
- Corpo: Roboto Regular
- Mono: Roboto Mono (para números/código)

LAYOUT:
Slides "Antes": Fundo vermelho suave
Slides "Depois": Fundo verde suave
Comparativos: Split screen 50/50
```

---

## 🛠️ Ferramentas de Design

### Softwares Recomendados

```yaml
Design Profissional:
  - Figma (recomendado para templates)
  - Adobe Photoshop
  - Adobe Illustrator
  - Canva Pro

Automação/Geração:
  - Figma API (para geração programática)
  - Bannerbear (templates dinâmicos)
  - Placid (geração automática)

Otimização:
  - TinyPNG (compressão de imagem)
  - ImageOptim (otimização lossless)
  - Squoosh (compressão web)

Testes:
  - Instagram Preview Apps
  - Later/Planoly (visualização de feed)
```

### Plugins Figma Úteis

```
- Stark (teste de contraste/acessibilidade)
- Content Reel (conteúdo placeholder)
- Unsplash (fotos de qualidade)
- Auto Layout (grids responsivos)
- Instance Finder (encontrar componentes)
- Design Lint (validação de design)
```

---

## 📋 Checklist de Qualidade Visual

```yaml
Antes de Publicar:
  Dimensões:
    - [ ] 1080x1350px ou 1080x1080px
    - [ ] Todos os slides mesma proporção
    - [ ] Safe zone respeitada (80px margem)
  
  Tipografia:
    - [ ] Texto legível em mobile (mín. 24px)
    - [ ] Contraste adequado (4.5:1 mínimo)
    - [ ] Mesma família tipográfica em todos
    - [ ] Hierarquia visual clara
  
  Cores:
    - [ ] Paleta harmônica e consistente
    - [ ] Transições suaves entre slides
    - [ ] Cores acessíveis (teste daltonismo)
  
  Logo:
    - [ ] Visível mas não dominante
    - [ ] Contraste adequado com fundo
    - [ ] Não será cortada no feed
  
  Elementos de Swipe:
    - [ ] Setas/números presentes
    - [ ] Cliffhangers entre slides
    - [ ] Barra de progresso (opcional)
  
  Consistência:
    - [ ] Grid alinhado slide a slide
    - [ ] Espaçamentos uniformes
    - [ ] Elementos posicionados consistentemente
  
  Final:
    - [ ] Testado em mobile real
    - [ ] Preview no Instagram (ferramenta)
    - [ ] Arquivos otimizados (<1MB cada)
    - [ ] Backups salvos
```

---

_Documento atualizado: Janeiro 2025_  
_Manutenção: Equipe PostNow Design_

