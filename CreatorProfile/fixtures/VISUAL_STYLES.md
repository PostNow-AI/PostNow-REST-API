# Visual Style Preferences

Catalogo de estilos visuais para geracao de imagens do PostNow.
Para adicionar novos estilos, basta acrescentar uma nova secao neste arquivo.

## Como gerar previews

Use o script `scripts/generate_style_previews.py` para gerar a imagem de preview e obter a URL do S3:

```bash
# Gerar preview de um estilo especifico:
python scripts/generate_style_previews.py --style-id=1

# Gerar todos os estilos:
python scripts/generate_style_previews.py

# Testar sem salvar (dry-run):
python scripts/generate_style_previews.py --dry-run
```

---

## 1. Minimalista Moderno

### CARACTERÍSTICAS DO ESTILO ###
Design minimalista profissional com foco em simplicidade e elegância.

### ELEMENTOS VISUAIS ###
- Fundo branco puro ou off-white
- Espaço negativo generoso (60% da composição)
- Uma única cor de acento usada com moderação
- Formas geométricas simples e sutis
- Alto contraste entre elementos

### PALETA DE CORES ###
- Primária: Branco (#FFFFFF) ou off-white (#F8F9FA)
- Secundária: Cinza claro (#E9ECEF)
- Acento: Usar cor da marca do cliente

### TIPOGRAFIA ###
- Família: Sans-serif moderna (Inter, Helvetica Neue, SF Pro)
- Peso: Bold para títulos, Regular para corpo
- Estilo: Clean, legível, espaçamento generoso

### COMPOSIÇÃO ###
- Layout respirável e equilibrado
- Hierarquia visual clara
- Foco em um elemento principal
- Alinhamento preciso

### ILUMINAÇÃO ###
- Luz natural, suave e uniforme
- Sem sombras pesadas
- Atmosfera clean e arejada

### EVITAR ###
- Gradientes e sombras dramáticas
- Múltiplas cores vibrantes
- Texturas pesadas ou patterns complexos
- Excesso de elementos decorativos

### QUALIDADE ###
- Renderização ultra-detalhada e nítida
- Acabamento premium de revista
- Aspecto ratio: 4:5 (Feed) ou 9:16 (Stories/Reels)

**Preview:** https://postnow-image-bucket-prod.s3.sa-east-1.amazonaws.com/style-previews/minimalista-moderno_0ed994b4.png

---

## 2. Bold Vibrante

### CARACTERÍSTICAS DO ESTILO ###
Design energético e impactante com cores saturadas e tipografia bold.

### ELEMENTOS VISUAIS ###
- Cores saturadas e complementares
- Blocos de cor com alto contraste
- Formas geométricas dinâmicas
- Movimento e energia na composição
- Estética pop art contemporânea

### PALETA DE CORES ###
- Azul elétrico (#0066FF)
- Rosa choque (#FF1493)
- Amarelo vibrante (#FFD700)
- Laranja vivo (#FF6B35)
- Usar combinações complementares

### TIPOGRAFIA ###
- Família: Display bold (Bebas Neue, Anton, Montserrat Black)
- Peso: Extra Bold / Black
- Estilo: Impactante, condensada ou expandida

### COMPOSIÇÃO ###
- Layout dinâmico com movimento
- Overlapping de elementos
- Hierarquia visual forte
- Assimetria controlada

### ILUMINAÇÃO ###
- Luz brilhante e uniforme
- Sem sombras (flat lighting)
- Cores puras e vibrantes

### EVITAR ###
- Tons pastéis ou dessaturados
- Layouts estáticos e simétricos
- Tipografia fina ou delicada
- Atmosfera séria ou corporativa

### QUALIDADE ###
- Cores nítidas sem banding
- Alto contraste e saturação
- Aspecto ratio: 4:5 (Feed) ou 9:16 (Stories/Reels)

**Preview:** https://postnow-image-bucket-prod.s3.sa-east-1.amazonaws.com/style-previews/bold-vibrante_55b8523c.png

---

## 3. Elegante Editorial

### CARACTERÍSTICAS DO ESTILO ###
Design premium de luxo com estética de revista de alto padrão.

### ELEMENTOS VISUAIS ###
- Paleta escura e sofisticada
- Acentos em dourado ou metálico
- Texturas premium sutis
- Composição simétrica e equilibrada
- Estética de editorial de moda

### PALETA DE CORES ###
- Primária: Azul marinho profundo (#1A1A2E)
- Secundária: Cinza carvão (#2D2D2D)
- Acento: Dourado (#D4AF37) ou champagne (#F7E7CE)
- Neutro: Creme (#FAF3E0)

### TIPOGRAFIA ###
- Família: Serif elegante (Playfair Display, Cormorant, Didot)
- Peso: Regular para corpo, Bold para títulos
- Estilo: Clássico, refinado, com tracking generoso

### COMPOSIÇÃO ###
- Simetria e equilíbrio
- Uso de molduras ou bordas sutis
- Hierarquia clara com espaço de respiro
- Layout de revista premium

### ILUMINAÇÃO ###
- Luz dramática suave
- Sombras delicadas e controladas
- Atmosfera cinematográfica

### EVITAR ###
- Cores vibrantes ou neon
- Tipografia casual ou divertida
- Layouts desordenados
- Elementos que pareçam baratos

### QUALIDADE ###
- Acabamento de luxo
- Texturas sutis de alta resolução
- Aspecto ratio: 4:5 (Feed) ou 9:16 (Stories/Reels)

**Preview:** https://postnow-image-bucket-prod.s3.sa-east-1.amazonaws.com/style-previews/elegante-editorial_94744677.png

---

## 4. Divertido Ilustrado

### CARACTERÍSTICAS DO ESTILO ###
Design artesanal com ilustrações hand-drawn e personalidade única.

### ELEMENTOS VISUAIS ###
- Ilustrações desenhadas à mão
- Traços visíveis de lápis/caneta
- Formas orgânicas e imperfeitas
- Doodles e elementos decorativos
- Texturas de papel ou craft

### PALETA DE CORES ###
- Terracota quente (#E07A5F)
- Verde sálvia (#81B29A)
- Creme (#F4F1DE)
- Coral suave (#F2CC8F)
- Tons terrosos e acolhedores

### TIPOGRAFIA ###
- Família: Handwritten ou marker-style (Caveat, Permanent Marker)
- Alternativa: Sans-serif arredondada (Nunito, Quicksand)
- Estilo: Casual, amigável, imperfeito

### COMPOSIÇÃO ###
- Layout orgânico e fluido
- Elementos sobrepostos naturalmente
- Bordas irregulares
- Espaço para "respirar"

### ILUMINAÇÃO ###
- Luz natural e quente
- Atmosfera acolhedora e caseira
- Sem iluminação artificial óbvia

### EVITAR ###
- Perfeição digital
- Linhas retas demais
- Cores frias ou corporativas
- Estética high-tech

### QUALIDADE ###
- Texturas de papel visíveis
- Traços autênticos e humanos
- Aspecto ratio: 4:5 (Feed) ou 9:16 (Stories/Reels)

**Preview:** https://postnow-image-bucket-prod.s3.sa-east-1.amazonaws.com/style-previews/divertido-ilustrado_017fa9c1.png

---

## 5. Profissional Corporativo

### CARACTERÍSTICAS DO ESTILO ###
Design empresarial que transmite confiança, autoridade e profissionalismo.

### ELEMENTOS VISUAIS ###
- Esquema de cores baseado em azul (confiança)
- Layout estruturado em grid
- Linhas limpas e organizadas
- Padrões geométricos sutis
- Ícones profissionais se necessário

### PALETA DE CORES ###
- Primária: Azul corporativo (#0052CC ou #2563EB)
- Secundária: Cinza profissional (#64748B)
- Neutro: Branco (#FFFFFF)
- Acento: Azul escuro (#1E3A5F)

### TIPOGRAFIA ###
- Família: Sans-serif profissional (Inter, Roboto, Open Sans)
- Peso: Medium para corpo, Semibold para títulos
- Estilo: Limpo, moderno, altamente legível

### COMPOSIÇÃO ###
- Grid-based layout organizado
- Alinhamento preciso
- Hierarquia clara de informação
- Espaço branco estratégico

### ILUMINAÇÃO ###
- Luz profissional de estúdio
- Sombras limpas e controladas
- Atmosfera confiável e séria

### EVITAR ###
- Cores vibrantes ou divertidas
- Layouts criativos demais
- Tipografia decorativa
- Elementos que reduzam credibilidade

### QUALIDADE ###
- Acabamento corporativo premium
- Linhas nítidas e precisas
- Aspecto ratio: 4:5 (Feed) ou 9:16 (Stories/Reels)

**Preview:** https://postnow-image-bucket-prod.s3.sa-east-1.amazonaws.com/style-previews/profissional-corporativo_25f126f2.png

---

## 6. Criativo Experimental

### CARACTERÍSTICAS DO ESTILO ###
Design artístico de colagem com mix de mídias e expressão criativa ousada.

### ELEMENTOS VISUAIS ###
- Colagem de elementos variados
- Recortes de fotos e texturas
- Formas geométricas sobrepostas
- Bordas rasgadas e irregulares
- Layering criativo com profundidade

### PALETA DE CORES ###
- Eclética mas harmônica
- Acentos vibrantes inesperados
- Mix de tons quentes e frios
- Pode usar cores da marca + complementares

### TIPOGRAFIA ###
- Mix de estilos: serif + sans-serif + handwritten
- Tamanhos variados
- Rotações e posicionamentos criativos
- Estilo de colagem editorial

### COMPOSIÇÃO ###
- Assimétrica e dinâmica
- Layers sobrepostos
- Tensão visual controlada
- Estética de revista independente

### ILUMINAÇÃO ###
- Variada conforme elementos
- Pode misturar estilos
- Sombras dramáticas se apropriado

### EVITAR ###
- Layouts previsíveis
- Simetria excessiva
- Paletas monótonas
- Estética corporativa tradicional

### QUALIDADE ###
- Texturas de alta resolução
- Bordas e recortes bem definidos
- Aspecto ratio: 4:5 (Feed) ou 9:16 (Stories/Reels)

**Preview:** https://postnow-image-bucket-prod.s3.sa-east-1.amazonaws.com/style-previews/criativo-experimental_7320d4af.png

---

## 7. Tech Futurista

### CARACTERÍSTICAS DO ESTILO ###
Design de startup tech com estética dark mode e elementos futuristas.

### ELEMENTOS VISUAIS ###
- Fundo escuro (dark mode)
- Cores neon como acento
- Formas geométricas clean
- Elementos de glass morphism
- Grids e linhas sutis

### PALETA DE CORES ###
- Base: Cinza carvão escuro (#1A1A1A ou #0F0F0F)
- Acento 1: Roxo elétrico (#8B5CF6)
- Acento 2: Ciano (#06B6D4)
- Acento 3: Azul neon (#3B82F6)
- Brilhos e glows sutis

### TIPOGRAFIA ###
- Família: Sans-serif geométrica (SF Pro, Inter, Manrope)
- Peso: Medium a Bold
- Estilo: Futurista, clean, tech-forward

### COMPOSIÇÃO ###
- Layout moderno e limpo
- Uso de cards com blur (glass morphism)
- Hierarquia clara
- Elementos floating

### ILUMINAÇÃO ###
- Glows neon sutis
- Luz ambiente escura
- Highlights em elementos chave
- Atmosfera digital

### EVITAR ###
- Fundos claros
- Cores quentes como primária
- Estética vintage ou retrô
- Elementos orgânicos demais

### QUALIDADE ###
- Renderização crisp e moderna
- Efeitos de blur de alta qualidade
- Aspecto ratio: 4:5 (Feed) ou 9:16 (Stories/Reels)

**Preview:** https://postnow-image-bucket-prod.s3.sa-east-1.amazonaws.com/style-previews/tech-futurista_f2a36ce0.png

---

## 8. Natural Orgânico

### CARACTERÍSTICAS DO ESTILO ###
Design artístico com texturas aquarela e sensação natural e orgânica.

### ELEMENTOS VISUAIS ###
- Texturas de aquarela
- Bordas suaves e bleeding
- Camadas transparentes
- Formas orgânicas fluidas
- Elementos botânicos se apropriado

### PALETA DE CORES ###
- Rosa dusty (#D4A5A5)
- Verde sálvia (#9DC08B)
- Lavanda suave (#E6E6FA)
- Creme (#FFF8E7)
- Terracota (#C4A484)

### TIPOGRAFIA ###
- Família: Script elegante (Playfair, Cormorant) ou serif delicada
- Alternativa: Sans-serif leve (Lato Light)
- Estilo: Feminino, delicado, artístico

### COMPOSIÇÃO ###
- Layout fluido e orgânico
- Elementos que "respiram"
- Assimetria natural
- Espaço negativo como elemento

### ILUMINAÇÃO ###
- Luz natural suave
- Atmosfera sonhadora
- Sem sombras duras
- Feeling de galeria de arte

### EVITAR ###
- Linhas duras e geométricas
- Cores saturadas demais
- Layouts rígidos
- Estética digital ou tech

### QUALIDADE ###
- Texturas de aquarela autênticas
- Transições suaves de cor
- Aspecto ratio: 4:5 (Feed) ou 9:16 (Stories/Reels)

**Preview:** https://postnow-image-bucket-prod.s3.sa-east-1.amazonaws.com/style-previews/natural-orgânico_620fe31a.png

---

## 9. Escandinavo Clean

### CARACTERÍSTICAS DO ESTILO ###
Design hygge-inspired com tons neutros e atmosfera acolhedora e serena.

### ELEMENTOS VISUAIS ###
- Paleta neutra e quente
- Texturas de madeira natural
- Linhas geométricas suaves
- Formas arredondadas
- Elementos de natureza minimalistas

### PALETA DE CORES ###
- Branco creme quente (#FAF9F6)
- Cinza quente claro (#D4D4D4)
- Bege natural (#E8DFD0)
- Madeira clara (#DEB887)
- Cinza escuro para texto (#4A4A4A)

### TIPOGRAFIA ###
- Família: Sans-serif elegante (Montserrat, Nunito, Poppins)
- Peso: Light a Regular
- Estilo: Minimalista, legível, acolhedor

### COMPOSIÇÃO ###
- Muito espaço de respiro
- Equilíbrio e harmonia
- Simplicidade intencional
- Layout clean e organizado

### ILUMINAÇÃO ###
- Luz natural difusa
- Atmosfera de dia nublado nórdico
- Suave e acolhedora
- Sem contrastes dramáticos

### EVITAR ###
- Cores vibrantes ou frias
- Elementos decorativos excessivos
- Texturas pesadas
- Layouts cluttered

### QUALIDADE ###
- Acabamento premium e sereno
- Texturas naturais de alta qualidade
- Aspecto ratio: 4:5 (Feed) ou 9:16 (Stories/Reels)

**Preview:** https://postnow-image-bucket-prod.s3.sa-east-1.amazonaws.com/style-previews/escandinavo-clean_2c20e4fa.png

---

## 10. Zen Japonês

### CARACTERÍSTICAS DO ESTILO ###
Estética japonesa minimalista seguindo o conceito 'ma' de vazio intencional.

### ELEMENTOS VISUAIS ###
- Equilíbrio assimétrico
- Muito espaço vazio (ma)
- Um elemento focal único
- Texturas de washi paper sutis
- Simplicidade extrema

### PALETA DE CORES ###
- Cinza quente (#808080)
- Verde natural (#7C9070)
- Bege areia (#C2B280)
- Preto carvão (#333333)
- Branco suave (#F5F5F5)

### TIPOGRAFIA ###
- Família: Sans-serif minimalista ou serif delicada
- Peso: Light a Regular
- Estilo: Refinado, com muito tracking
- Hierarquia sutil

### COMPOSIÇÃO ###
- Assimetria balanceada (regra dos terços japonesa)
- Espaço vazio como elemento principal
- Foco em um único ponto
- Menos é mais, elevado ao máximo

### ILUMINAÇÃO ###
- Luz natural suave
- Atmosfera meditativa
- Sem iluminação artificial óbvia
- Serenidade e calma

### EVITAR ###
- Múltiplos elementos competindo
- Cores vibrantes
- Layouts cheios
- Decorações desnecessárias

### QUALIDADE ###
- Texturas sutis de papel washi
- Acabamento refinado e contemplativo
- Aspecto ratio: 4:5 (Feed) ou 9:16 (Stories/Reels)

**Preview:** https://postnow-image-bucket-prod.s3.sa-east-1.amazonaws.com/style-previews/zen-japones_7a76d5ce.png

---

## 11. Jurídico Profissional

### CARACTERÍSTICAS DO ESTILO ###
Design para serviços jurídicos que transmite autoridade, tradição e confiança.

### ELEMENTOS VISUAIS ###
- Paleta autoritária e tradicional
- Elementos clássicos sutis
- Layout formal e estruturado
- Padrões de pinstripe discretos
- Detalhes em dourado se apropriado

### PALETA DE CORES ###
- Azul marinho profundo (#1B365D)
- Vinho/burgundy (#722F37)
- Creme clássico (#FFFDD0)
- Dourado sutil (#CFB53B)
- Branco (#FFFFFF)

### TIPOGRAFIA ###
- Família: Serif clássica (Times New Roman, Garamond, Baskerville)
- Peso: Regular para corpo, Bold para títulos
- Estilo: Tradicional, respeitável, legível

### COMPOSIÇÃO ###
- Layout formal com grid clássico
- Simetria e ordem
- Hierarquia clara e tradicional
- Margens generosas

### ILUMINAÇÃO ###
- Luz de estúdio profissional
- Atmosfera séria e respeitável
- Sombras controladas e sutis

### EVITAR ###
- Cores vibrantes ou modernas
- Layouts criativos ou assimétricos
- Tipografia casual
- Qualquer elemento que reduza credibilidade

### QUALIDADE ###
- Acabamento premium tradicional
- Aparência estabelecida e confiável
- Aspecto ratio: 4:5 (Feed) ou 9:16 (Stories/Reels)

**Preview:** https://postnow-image-bucket-prod.s3.sa-east-1.amazonaws.com/style-previews/juridico-profissional_2b528b65.png

---

## 12. Financeiro Clean

### CARACTERÍSTICAS DO ESTILO ###
Design para serviços financeiros focado em transmitir confiança e precisão.

### ELEMENTOS VISUAIS ###
- Paleta que transmite confiança
- Layout inspirado em data visualization
- Grids limpos e precisos
- Elementos geométricos de gráficos
- Linhas e formas matemáticas

### PALETA DE CORES ###
- Azul marinho (#003366)
- Verde floresta (#228B22)
- Branco (#FFFFFF)
- Dourado (#CFB53B)
- Cinza neutro (#6B7280)

### TIPOGRAFIA ###
- Família: Sans-serif moderna (IBM Plex, Roboto, Inter)
- Peso: Regular a Semibold
- Estilo: Preciso, profissional, números bem desenhados

### COMPOSIÇÃO ###
- Layout baseado em grid preciso
- Organização clara de informação
- Hierarquia que guia o olho
- Espaço branco estratégico

### ILUMINAÇÃO ###
- Luz profissional e limpa
- Atmosfera confiável
- Sem dramaticidade

### EVITAR ###
- Cores que pareçam arriscadas
- Layouts desorganizados
- Tipografia decorativa
- Elementos que reduzam confiança

### QUALIDADE ###
- Linhas nítidas e precisas
- Acabamento corporate premium
- Aspecto ratio: 4:5 (Feed) ou 9:16 (Stories/Reels)

**Preview:** https://postnow-image-bucket-prod.s3.sa-east-1.amazonaws.com/style-previews/financeiro-clean_f9e1dfd6.png

---

## 13. Neon Pop

### CARACTERÍSTICAS DO ESTILO ###
Estética retrô anos 80 com neon brilhante e vibe synthwave/vaporwave.

### ELEMENTOS VISUAIS ###
- Fundo escuro (preto/roxo profundo)
- Cores neon brilhantes
- Efeitos de glow visíveis
- Grid lines estilo retro
- Elementos chrome/metálicos

### PALETA DE CORES ###
- Base: Preto (#000000) ou roxo escuro (#1A0033)
- Rosa neon (#FF1493)
- Ciano elétrico (#00FFFF)
- Verde limão (#00FF00)
- Roxo neon (#BF00FF)

### TIPOGRAFIA ###
- Família: Display retro-futurista (Orbitron, Audiowide)
- Peso: Bold a Black
- Estilo: Com glow neon, futurista retrô

### COMPOSIÇÃO ###
- Contraste dramático claro/escuro
- Grid lines perspectiva 80s
- Elementos centralizados ou com simetria
- Camadas de glow

### ILUMINAÇÃO ###
- Neon brilhante contra fundo escuro
- Bloom e glow effects
- Atmosfera de night club
- Luz artificial dramática

### EVITAR ###
- Fundos claros
- Cores pastéis ou suaves
- Estética minimalista
- Looks corporativos

### QUALIDADE ###
- Glows suaves sem pixelização
- Alto contraste bem executado
- Aspecto ratio: 4:5 (Feed) ou 9:16 (Stories/Reels)

**Preview:** https://postnow-image-bucket-prod.s3.sa-east-1.amazonaws.com/style-previews/neon-pop_fd38025b.png

---

## 14. Gradiente Explosivo

### CARACTERÍSTICAS DO ESTILO ###
Design vibrante com gradientes bold multi-color e estética Instagram-native.

### ELEMENTOS VISUAIS ###
- Gradientes multi-cor suaves
- Formas abstratas fluidas
- Transições de cor smooth
- Elementos floating
- Estética digital moderna

### PALETA DE CORES ###
- Roxo profundo (#6B21A8)
- Rosa vibrante (#EC4899)
- Laranja quente (#F97316)
- Azul elétrico (#3B82F6)
- Gradientes smooth entre eles

### TIPOGRAFIA ###
- Família: Sans-serif moderna (Poppins, Montserrat)
- Peso: Bold a Black
- Cor: Branco puro com sombra sutil
- Estilo: Clean contra gradiente

### COMPOSIÇÃO ###
- Gradiente como hero element
- Formas orgânicas fluidas
- Tipografia em destaque
- Layout dinâmico

### ILUMINAÇÃO ###
- Glow ambiente suave
- Cores que parecem emitir luz
- Atmosfera digital vibrante

### EVITAR ###
- Banding no gradiente
- Cores que não combinam
- Layouts estáticos
- Tipografia que se perde no fundo

### QUALIDADE ###
- Gradientes smooth sem banding
- Transições de cor perfeitas
- Aspecto ratio: 4:5 (Feed) ou 9:16 (Stories/Reels)

**Preview:** https://postnow-image-bucket-prod.s3.sa-east-1.amazonaws.com/style-previews/gradiente-explosivo_03578c7a.png

---

## 15. Retro Anos 80

### CARACTERÍSTICAS DO ESTILO ###
Estética Miami Vice / Outrun com sunset vibes e nostalgia dos anos 80.

### ELEMENTOS VISUAIS ###
- Gradientes de sunset
- Padrões geométricos (triângulos, grids)
- Linhas horizontais
- Sol/sunset como motivo
- Elementos chrome metálico

### PALETA DE CORES ###
- Teal (#008080)
- Magenta (#FF00FF)
- Roxo (#800080)
- Coral (#FF7F7F)
- Laranja sunset (#FF6347)

### TIPOGRAFIA ###
- Família: Display retro (Outrun, Streamster, Miami)
- Peso: Bold
- Estilo: Chrome, outline, ou solid bold

### COMPOSIÇÃO ###
- Horizonte com sunset
- Grid de perspectiva
- Simetria central
- Layers de elementos geométricos

### ILUMINAÇÃO ###
- Luz de sunset quente
- Atmosfera nostálgica
- Glows em cores quentes
- Reflexos metálicos

### EVITAR ###
- Cores frias isoladas
- Estética moderna minimalista
- Layouts assimétricos demais
- Perder a vibe retrô

### QUALIDADE ###
- VHS scan lines sutis opcionais
- Acabamento nostálgico mas HD
- Aspecto ratio: 4:5 (Feed) ou 9:16 (Stories/Reels)

**Preview:** https://postnow-image-bucket-prod.s3.sa-east-1.amazonaws.com/style-previews/retro-anos-80_9b2c2c19.png

---

## 16. Gradiente Moderno

### CARACTERÍSTICAS DO ESTILO ###
Design sofisticado com gradientes sutis e elegantes, estética Apple/tech premium.

### ELEMENTOS VISUAIS ###
- Gradientes suaves e elegantes
- Transições de cor delicadas
- Composição minimalista
- Sombras sutis para profundidade
- Estética de empresa de tecnologia premium

### PALETA DE CORES ###
- Roxo suave para azul céu (#A855F7 → #38BDF8)
- Pêssego para rosa blush (#FBBF24 → #F472B6)
- Verde menta para azul (#34D399 → #60A5FA)
- Sempre tons pastéis sofisticados

### TIPOGRAFIA ###
- Família: Sans-serif premium (SF Pro, Inter, Söhne)
- Peso: Medium a Semibold
- Cor: Preto ou branco dependendo do fundo
- Estilo: Clean, Apple-like

### COMPOSIÇÃO ###
- Gradiente como background principal
- Tipografia em destaque central
- Layout minimalista
- Muito espaço de respiro

### ILUMINAÇÃO ###
- Suave e difusa
- Sombras delicadas
- Atmosfera premium e calma

### EVITAR ###
- Gradientes muito vibrantes
- Transições bruscas
- Elementos que distraiam
- Layouts complexos

### QUALIDADE ###
- Gradientes ultra-smooth
- Acabamento premium Apple-quality
- Aspecto ratio: 4:5 (Feed) ou 9:16 (Stories/Reels)

**Preview:** https://postnow-image-bucket-prod.s3.sa-east-1.amazonaws.com/style-previews/gradiente-moderno_bbc281ec.png

---

## 17. Flat Design

### CARACTERÍSTICAS DO ESTILO ###
Design flat moderno com cores sólidas bold e sem efeitos 3D.

### ELEMENTOS VISUAIS ###
- Cores sólidas sem gradientes
- Formas geométricas sharp
- Ícones estilo flat
- Sem sombras ou profundidade
- Estética 2D pura

### PALETA DE CORES ###
- Azul bright (#0EA5E9)
- Coral (#F97316)
- Amarelo (#FACC15)
- Teal (#14B8A6)
- Combinações harmônicas mas bold

### TIPOGRAFIA ###
- Família: Sans-serif geométrica (Roboto, Open Sans, Lato)
- Peso: Regular a Bold
- Estilo: Limpo, sem efeitos

### COMPOSIÇÃO ###
- Layout baseado em formas
- Hierarquia clara com cor
- Alinhamento preciso
- Simplicidade funcional

### ILUMINAÇÃO ###
- Sem iluminação (flat)
- Cores que falam por si
- Sem sombras ou highlights

### EVITAR ###
- Qualquer efeito 3D
- Sombras ou gradientes
- Texturas
- Complexidade desnecessária

### QUALIDADE ###
- Cores puras e precisas
- Bordas sharp e definidas
- Aspecto ratio: 4:5 (Feed) ou 9:16 (Stories/Reels)

**Preview:** https://postnow-image-bucket-prod.s3.sa-east-1.amazonaws.com/style-previews/flat-design_feba8f9d.png

---

## 18. Material Design

### CARACTERÍSTICAS DO ESTILO ###
Estética Google Material Design com cards, elevação e sombras realistas.

### ELEMENTOS VISUAIS ###
- Cards com elevação
- Sombras realistas (elevation)
- Camadas sobrepostas
- Botões floating style
- Hierarquia através de profundidade

### PALETA DE CORES ###
- Uma cor primária bold (ex: #6200EE)
- Cor de acento complementar
- Superfícies: Branco (#FFFFFF)
- Backgrounds: Cinza claro (#F5F5F5)
- Seguir Material color system

### TIPOGRAFIA ###
- Família: Roboto (oficial) ou similar
- Peso: Regular, Medium, Bold
- Hierarquia clara (H1, H2, body)
- Estilo: Funcional e legível

### COMPOSIÇÃO ###
- Cards como containers
- Hierarquia por elevação (z-index)
- Grid de 8dp
- Espaço intencional

### ILUMINAÇÃO ###
- Sombras seguindo princípios de elevação
- Luz vindo de cima
- Sombras soft e realistas
- Depth através de shadow

### EVITAR ###
- Sombras irrealistas
- Cores que quebrem o sistema
- Layouts sem hierarquia
- Elementos sem propósito

### QUALIDADE ###
- Sombras precisas por nível de elevação
- Sistema consistente
- Aspecto ratio: 4:5 (Feed) ou 9:16 (Stories/Reels)

**Preview:** https://postnow-image-bucket-prod.s3.sa-east-1.amazonaws.com/style-previews/material-design_8e97e4ee.png

---
