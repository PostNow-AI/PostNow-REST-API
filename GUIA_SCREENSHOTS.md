# 📸 GUIA DE SCREENSHOTS PARA APRESENTAÇÃO

**Data:** 05/01/2026  
**Resolução:** 1920x1080 (Full HD)  
**Ferramenta:** macOS Screenshot (Cmd+Shift+4) ou Snagit

---

## 🎯 PREPARAÇÃO

### ✅ Antes de Capturar

```bash
# 1. Limpar console do navegador
# Cmd+Option+I → Console → Limpar (🚫)

# 2. Zoom 100%
# Cmd+0 (reset zoom)

# 3. Modo claro/escuro
# Escolher um e manter consistente

# 4. Fechar outras tabs
# Deixar só a do sistema

# 5. Esconder bookmarks bar
# Cmd+Shift+B (toggle)

# 6. Tela cheia (opcional)
# F11 ou Cmd+Ctrl+F
```

---

## 📸 SCREENSHOTS ESSENCIAIS

### 1️⃣ DASHBOARD DE CAMPANHAS

**URL:** `http://localhost:5173/campaigns`

**Capturar:**
- Lista completa de campanhas (5 cards)
- Botão "+ Nova Campanha" visível
- Header com título "Minhas Campanhas"

**Dicas:**
- Scroll para mostrar todas as 5 campanhas
- Garantir que nomes e datas são legíveis
- Status badges visíveis (draft/pending/approved)

**Arquivo:** `01-dashboard-campanhas.png`

---

### 2️⃣ WIZARD - BRIEFING STEP (Step 1/5)

**URL:** `http://localhost:5173/campaigns/create`

**Capturar:**
- Progress bar no topo (20%)
- Campos do briefing pré-preenchidos
- Botão "Sugestão IA - Gerar outra"
- Switches de materiais (cases, fotos)

**Dicas:**
- Garantir que textos pré-preenchidos são legíveis
- Mostrar que campos estão completos (validação OK)
- Progress bar deve estar visível

**Arquivo:** `02-wizard-briefing-step.png`

---

### 3️⃣ WEEKLY CONTEXT MODAL

**URL:** `http://localhost:5173/campaigns/create` (após clicar Continuar no briefing)

**Capturar:**
- Modal aberto sobrepondo o wizard
- Lista de oportunidades (ou "Nenhuma disponível")
- Checkboxes de seleção
- Botões "Pular" e "Continuar (X selecionadas)"

**Dicas:**
- Selecionar 2 oportunidades antes de capturar
- Mostrar badges de categoria
- Texto "Oportunidades do Weekly Context" visível

**Arquivo:** `03-weekly-context-modal.png`

---

### 4️⃣ WIZARD - SELEÇÃO DE ESTRUTURA (Step 2/5)

**URL:** `http://localhost:5173/campaigns/create` (Step 2)

**Capturar:**
- Lista de 8 estruturas
- Primeira com badge "Recomendado IA"
- Uma estrutura selecionada (border primary)
- Progress bar (40%)

**Dicas:**
- Scroll para mostrar 4-5 estruturas
- Hover em uma para mostrar interação
- Garantir que descrições são legíveis

**Arquivo:** `04-wizard-estruturas.png`

---

### 5️⃣ WIZARD - ESTILOS VISUAIS (Step 4/5)

**URL:** `http://localhost:5173/campaigns/create` (Step 4)

**Capturar:**
- Grid de estilos visuais (3 colunas)
- Previews AI-gerados visíveis
- 2-3 estilos selecionados (checkmarks)
- Contador "X/5 selecionados"
- Progress bar (80%)

**Dicas:**
- Scroll para mostrar variedade (6-9 estilos visíveis)
- Estilos selecionados com border destacado
- Nomes dos estilos legíveis

**Arquivo:** `05-wizard-estilos-visuais.png`

---

### 6️⃣ WIZARD - REVIEW (Step 5/5)

**URL:** `http://localhost:5173/campaigns/create` (Step 5)

**Capturar:**
- Resumo completo da campanha:
  - Objetivo
  - Estrutura
  - Duração
  - Estilos selecionados
- Radio group de qualidade (Fast/Premium)
- Estimativas de tempo/custo
- Botão "Gerar Campanha!"
- Progress bar (100%)

**Dicas:**
- Selecionar "Premium" para mostrar diferença
- Estimativas devem estar visíveis
- Scroll se necessário para mostrar tudo

**Arquivo:** `06-wizard-review.png`

---

### 7️⃣ PROGRESS TRACKING (Durante Geração)

**URL:** `http://localhost:5173/campaigns/:id` (durante geração)

**Capturar:**
- Progress bar grande no topo da página
- Percentual (ex: "45% Completo")
- Ação atual ("Gerando texto 3/8" ou "Gerando imagem 2/8")
- Posts aparecendo gradualmente no grid abaixo

**Dicas:**
- Capturar entre 40-60% (nem início, nem fim)
- Mostrar ação de geração de imagem (mais impactante)
- Ver se posts já gerados aparecem abaixo

**⏱️ Timing:** Capturar nos primeiros 2-3 minutos após clicar "Gerar"

**Arquivo:** `07-progress-tracking.png`

---

### 8️⃣ GRID DE POSTS GERADOS

**URL:** `http://localhost:5173/campaigns/:id` (após geração completa)

**Capturar:**
- Grid completo de posts (2-3 linhas)
- Imagens visíveis e legíveis
- Checkboxes para seleção
- 2-3 posts selecionados (checked)
- Barra de Bulk Actions aparecendo

**Dicas:**
- Scroll para mostrar 6-8 posts
- Imagens de alta qualidade (não pixeladas)
- Textos parcialmente visíveis nos cards
- Barra de Bulk Actions no topo

**Arquivo:** `08-grid-posts-gerados.png`

---

### 9️⃣ PREVIEW INSTAGRAM FEED

**URL:** `http://localhost:5173/campaigns/:id` (clicar "Preview Feed")

**Capturar:**
- Modal aberto com grade 3x3
- 9 posts em formato quadrado
- Análise de harmonia:
  - Score (ex: 87/100)
  - Badge colorido ("Boa Harmonia")
  - Sugestões (se score < 80)

**Dicas:**
- Garantir que 9 imagens são visíveis
- Score deve estar em destaque
- Badge bem visível (verde/azul preferível)
- Modal centralizado

**Arquivo:** `09-preview-instagram-feed.png`

---

### 🔟 BULK ACTIONS (Ações em Massa)

**URL:** `http://localhost:5173/campaigns/:id`

**Capturar:**
- 4-5 posts selecionados (checkboxes)
- Barra de Bulk Actions expandida:
  - "X posts selecionados"
  - Botões: Aprovar / Reprovar / Regenerar / Deletar
- Grid de posts ao fundo

**Dicas:**
- Selecionar número significativo (4-5)
- Mostrar hover em um dos botões
- Contador de posts selecionados visível

**Arquivo:** `10-bulk-actions.png`

---

### 1️⃣1️⃣ DETALHES DE UM POST

**URL:** `http://localhost:5173/campaigns/:id` (clicar "Ver" em um post)

**Capturar:**
- Modal ou página de detalhes
- Imagem grande e legível
- Texto completo do post
- Hashtags visíveis
- CTA destacado
- Botões de ação (Editar/Aprovar/Reprovar)

**Dicas:**
- Escolher post com boa imagem
- Texto deve ser legível (fonte adequada)
- Mostrar que imagem + texto combinam

**Arquivo:** `11-detalhes-post.png`

---

### 1️⃣2️⃣ ANÁLISE DE HARMONIA (Detalhada)

**URL:** `http://localhost:5173/campaigns/:id/harmony` (se existir rota)

**Capturar:**
- Breakdown detalhado do score:
  - Variedade de cores
  - Diversidade de composição
  - Consistência de estilo
- Gráficos ou badges por categoria
- Sugestões de melhoria

**Dicas:**
- Se não tiver rota dedicada, capturar modal do Preview
- Focar em métricas visuais

**Arquivo:** `12-analise-harmonia-detalhada.png`

---

## 🎨 SCREENSHOTS BÔNUS (Nice-to-Have)

### B1: Login Page
**Arquivo:** `bonus-01-login.png`

### B2: Onboarding (se relevante)
**Arquivo:** `bonus-02-onboarding.png`

### B3: Calendário de Publicação (se implementado)
**Arquivo:** `bonus-03-calendario.png`

### B4: Analytics de Campanha (se implementado)
**Arquivo:** `bonus-04-analytics.png`

---

## 🖼️ PÓS-PROCESSAMENTO

### ✅ Edição Recomendada

**Ferramenta:** Figma, Photoshop, ou macOS Preview

**Ações:**
1. **Crop/Resize:**
   - Remover barras desnecessárias
   - Manter 16:9 ou 4:3

2. **Anotações (Opcional):**
   - Adicionar setas vermelhas
   - Círculos destacando features
   - Textos explicativos

3. **Blur de Dados Sensíveis:**
   - Email (se visível)
   - Dados reais de cliente (se houver)

4. **Ajustes:**
   - Brilho/Contraste (se necessário)
   - Saturação (não exagerar)

5. **Formato de Exportação:**
   - PNG (alta qualidade)
   - JPG (se precisar reduzir tamanho)

---

## 📁 ORGANIZAÇÃO DOS ARQUIVOS

### Estrutura de Pastas

```
/Users/rogerioresende/Desktop/Postnow/screenshots/
├── essenciais/
│   ├── 01-dashboard-campanhas.png
│   ├── 02-wizard-briefing-step.png
│   ├── 03-weekly-context-modal.png
│   ├── 04-wizard-estruturas.png
│   ├── 05-wizard-estilos-visuais.png
│   ├── 06-wizard-review.png
│   ├── 07-progress-tracking.png
│   ├── 08-grid-posts-gerados.png
│   ├── 09-preview-instagram-feed.png
│   ├── 10-bulk-actions.png
│   ├── 11-detalhes-post.png
│   └── 12-analise-harmonia-detalhada.png
├── bonus/
│   ├── bonus-01-login.png
│   ├── bonus-02-onboarding.png
│   ├── bonus-03-calendario.png
│   └── bonus-04-analytics.png
└── editados/
    ├── 01-dashboard-campanhas-anotado.png
    ├── 02-wizard-briefing-step-anotado.png
    └── ...
```

---

## 🎬 CRIANDO GIF ANIMADO (Opcional)

### Para Demonstração Rápida

**Ferramenta:** Licecap (Mac) ou ScreenToGif (Windows)

**Fluxos para GIF:**

### GIF 1: Wizard Completo (15s)
1. Briefing (2s)
2. Weekly Context (2s)
3. Estrutura (2s)
4. Duração (2s)
5. Estilos (4s)
6. Review (3s)

### GIF 2: Geração em Ação (10s)
1. Clicar "Gerar Campanha"
2. Progress bar 0% → 100% (timelapse)
3. Posts aparecendo

### GIF 3: Preview Instagram (8s)
1. Clicar "Preview Feed"
2. Modal abre
3. Score calcula
4. Badge aparece
5. Fechar modal

**Configurações:**
- FPS: 10-15
- Resolução: 800x600 (GIF é pesado)
- Duração: 8-15s cada

---

## ✅ CHECKLIST DE CAPTURA

### Antes de Iniciar
- [ ] Backend rodando
- [ ] Frontend rodando
- [ ] Login feito
- [ ] 5 campanhas no banco
- [ ] Console limpo (sem erros)
- [ ] Zoom 100%
- [ ] Modo claro/escuro escolhido

### Screenshots Essenciais
- [ ] 01 - Dashboard
- [ ] 02 - Briefing Step
- [ ] 03 - Weekly Context Modal
- [ ] 04 - Estruturas
- [ ] 05 - Estilos Visuais
- [ ] 06 - Review
- [ ] 07 - Progress Tracking
- [ ] 08 - Grid de Posts
- [ ] 09 - Preview Instagram
- [ ] 10 - Bulk Actions
- [ ] 11 - Detalhes Post
- [ ] 12 - Harmonia

### Screenshots Bônus (Opcional)
- [ ] B1 - Login
- [ ] B2 - Onboarding
- [ ] B3 - Calendário
- [ ] B4 - Analytics

### GIFs Animados (Opcional)
- [ ] GIF 1 - Wizard Completo
- [ ] GIF 2 - Geração em Ação
- [ ] GIF 3 - Preview Instagram

### Pós-Processamento
- [ ] Crop/Resize
- [ ] Anotações (se necessário)
- [ ] Blur de dados sensíveis
- [ ] Exportar em PNG
- [ ] Organizar em pastas

---

## 🎯 PRIORIZAÇÃO PARA APRESENTAÇÃO

### 🔴 ESSENCIAIS (Usar no Slide Deck)

1. **Dashboard** - Mostra lista de campanhas
2. **Wizard Review** - Resumo completo, escolha de qualidade
3. **Progress Tracking** - Geração assíncrona em ação
4. **Grid de Posts** - Resultado final com imagens
5. **Preview Instagram** - Harmonia visual e score

**Total: 5 screenshots**

### 🟡 IMPORTANTES (Backup/Detalhes)

6. **Briefing Step** - Sugestões IA
7. **Estilos Visuais** - 20 opções com previews
8. **Bulk Actions** - Ações em massa

**Total: 3 screenshots**

### 🟢 NICE-TO-HAVE (Se Tempo Permitir)

9. **Weekly Context Modal** - Oportunidades
10. **Estruturas** - Thompson Sampling
11. **Detalhes Post** - Zoom em qualidade
12. **Harmonia Detalhada** - Breakdown de scores

**Total: 4 screenshots**

---

## 📊 USO NOS SLIDES

### Slide 1: Problema
- Sem screenshot (só texto)

### Slide 2: Solução
- **Screenshot:** Dashboard (overview)

### Slide 3: Como Funciona
- **Screenshot:** Wizard Review (fluxo completo)

### Slide 4: IA em Ação
- **Screenshot:** Progress Tracking
- **Opcional:** GIF de geração

### Slide 5: Resultado
- **Screenshot:** Grid de Posts
- **Screenshot:** Preview Instagram Feed

### Slide 6: Diferenciais
- **Screenshot:** Estilos Visuais (20 opções)
- **Screenshot:** Bulk Actions

### Slide 7: Próximos Passos
- Sem screenshot (roadmap)

---

## 🎨 DICAS DE DESIGN PARA SLIDES

### Layout Recomendado

```
┌─────────────────────────────────┐
│ TÍTULO DO SLIDE                 │
├─────────────────────────────────┤
│                                 │
│   ┌─────────────────────────┐   │
│   │                         │   │
│   │    SCREENSHOT AQUI      │   │
│   │                         │   │
│   └─────────────────────────┘   │
│                                 │
│ Texto explicativo curto (1-2    │
│ frases abaixo do screenshot)    │
│                                 │
└─────────────────────────────────┘
```

### Boas Práticas

✅ **DO:**
- Bordas arredondadas nos screenshots
- Sombra sutil (drop shadow)
- Espaçamento generoso
- 1 screenshot grande por slide
- Texto mínimo (deixar imagem falar)

❌ **DON'T:**
- Múltiplos screenshots pequenos
- Screenshots pixelados
- Muito texto sobre a imagem
- Cortar partes importantes

---

**Tempo Estimado Total:**
- Captura: 30 minutos
- Edição básica: 15 minutos
- Organização: 5 minutos
- **TOTAL: 50 minutos**

**Pronto para:** Slides de apresentação, documentação, marketing

