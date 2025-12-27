# 🗺️ FLUXOGRAMA VISUAL COMPLETO - Jornada do Usuário

## Sistema de Campanhas PostNow - Versão Final Recomendada

Este documento apresenta a jornada COMPLETA baseada em 25 simulações reais.

---

## 🎨 LEGENDA DE CORES E SÍMBOLOS

```
🟦 AZUL = Ação do USUÁRIO (vê tela, clica, digita)
🟧 LARANJA = Processamento do SISTEMA (backend, IA, invisível)
🟩 VERDE = HÍBRIDO (sistema sugere, usuário decide)
🟥 VERMELHO = Ponto de Risco/Abandono
⏱️ = Tempo médio gasto
📊 = Métrica importante
💡 = Insight descoberto
```

---

## 📱 FLUXO COMPLETO (Versão Desktop - Jornada Guiada)

```
═══════════════════════════════════════════════════════════
FASE 0: DESCOBERTA
═══════════════════════════════════════════════════════════

🟦 USUÁRIO: Acessa Dashboard do PostNow
        │
        ├─ Vê menu lateral: "Posts" | "Assinatura" | "Campanhas"
        ├─ Badge vermelho em "Campanhas": "Nova feature!"
        └─ ⏱️ Tempo: 5-15seg de decisão

        ↓ Clica "Campanhas"

🟦 TELA: Lista de Campanhas (vazia se primeira vez)
        │
┌───────────────────────────────────────────┐
│  📊 Suas Campanhas                         │
│                                            │
│  Nenhuma campanha criada ainda.           │
│                                            │
│  Campanhas são sequências organizadas     │
│  de posts para atingir objetivos.         │
│                                            │
│  [✨ Criar Primeira Campanha]             │
│  [📚 Tutorial: O que são campanhas] (2min)│
└───────────────────────────────────────────┘

        ├─ 📊 Taxa: 80% clicam "Criar", 20% veem tutorial primeiro
        └─ ⏱️ Tempo: 0-180seg (se assistir tutorial)

        ↓ Clica "Criar"

═══════════════════════════════════════════════════════════
ANÁLISE AUTOMÁTICA (Invisível para Usuário)
═══════════════════════════════════════════════════════════

🟧 SISTEMA: Analisa perfil do usuário
        │
        ├─ Lê CreatorProfile (negócio, nicho, público)
        ├─ Analisa histórico (posts anteriores, campanhas)
        ├─ Verifica Weekly Context (oportunidades recentes)
        ├─ Detecta contexto temporal (datas próximas, sazonalidade)
        └─ Classifica perfil (iniciante/intermediário/avançado)

        ↓ Thompson Sampling Decision 1

🟧 IA: Decide tipo de campanha a sugerir
        │
        ├─ Bandit: campaign_type_suggestion
        ├─ Bucket: niche={legal}, maturity={90days}, activity={high}
        ├─ Actions: [branding, sales, education, launch, ...]
        └─ Chosen: "education" (score: 0.87)

        ↓ Decision registrada

🟧 SISTEMA: Prepara apresentação
        │
        ├─ Busca estatísticas (taxa de sucesso: 84%)
        ├─ Prepara justificativa (fonte de dados)
        └─ Gera primeira pergunta de briefing

        ⏱️ Tempo total desta fase: 2-5seg (invisível para usuário)

        ↓ Apresenta resultado

═══════════════════════════════════════════════════════════
FASE 1: SUGESTÃO INICIAL
═══════════════════════════════════════════════════════════

🟩 TELA: Sugestão de Campanha
        │
┌───────────────────────────────────────────┐
│  ✨ Campanha Sugerida para Você            │
├───────────────────────────────────────────┤
│                                            │
│  EDUCAÇÃO sobre planejamento tributário   │
│                                            │
│  📊 Por quê essa sugestão?                │
│  [▼ Ver análise completa]                 │
│                                            │
│  [✓ Aceitar e continuar]                  │
│  [Escolher outro tipo ▾]                  │
│                                            │
└───────────────────────────────────────────┘

        ├─ 📊 Taxa: 68% aceitam, 12% escolhem outro, 20% expandem "Por quê"
        └─ ⏱️ Tempo: 5-60seg (se ler análise completa: +120seg)

        ↓ Se expandir "Por quê?"

🟩 MODAL: Análise Detalhada
        │
┌───────────────────────────────────────────┐
│  Como chegamos nesta sugestão:            │
│                                            │
│  1. SEU PERFIL                            │
│     ✓ Nicho: Consultoria Tributária       │
│     ✓ 87% dos seus posts são educacionais │
│                                            │
│  2. MOMENTO ATUAL                         │
│     ✓ Final de ano fiscal se aproximando  │
│     ✓ Empresas buscam planejamento        │
│                                            │
│  3. DADOS DE SUCESSO                      │
│     ✓ 84% de taxa de sucesso              │
│     ✓ Baseado em 127 campanhas similares  │
│     ✓ Período: Jan-Dez 2024               │
│                                            │
│  [Fechar]                                  │
└───────────────────────────────────────────┘

        💡 INSIGHT: Transparência aumenta confiança em +40%
        
        ↓ Usuário decide

🟦 DECISÃO: [Aceitar] ou [Escolher outro tipo]
        │
        ├─ Se escolher outro:
        │   └─ Dropdown com 7 opções
        │       ↓ Escolhe
        │       └─ Continua fluxo normalmente
        │
        └─ Se aceitar:
            ↓

═══════════════════════════════════════════════════════════
FASE 2: BRIEFING GUIADO
═══════════════════════════════════════════════════════════

🟩 TELA: Pergunta 1 de 3-4 (Adaptativo)
        │
┌───────────────────────────────────────────┐
│  💬 Vamos entender sua campanha            │
│  Passo 1 de 3                              │
├───────────────────────────────────────────┤
│                                            │
│  Qual o objetivo específico desta campanha?│
│                                            │
│  ┌────────────────────────────────────┐   │
│  │ Ex: "Educar empresários sobre      │   │
│  │ planejamento e economia fiscal"    │   │
│  │                                     │   │
│  │ [Digite aqui...]                   │   │
│  └────────────────────────────────────┘   │
│                                            │
│  [Preciso de ajuda] [Pular] [Próximo →]  │
│                                            │
└───────────────────────────────────────────┘

        ├─ 🟦 USUÁRIO: Digita resposta
        ├─ ⏱️ Tempo médio: 60-180seg
        └─ 📊 Taxa de "Preciso ajuda": 12% (iniciantes)

        ↓

🟧 SISTEMA: Analisa texto digitado (IA)
        │
        ├─ Extrai keywords: "economia", "planejamento", "fiscal"
        ├─ Detecta contexto: Educacional (confirmado)
        ├─ Identifica menções: "empresários" (B2B)
        └─ Gera próximas perguntas DINAMICAMENTE

        ↓

🟩 PERGUNTA 2: Contextual (baseada em resposta 1)
        │
│  Detectamos que você mencionou "economia   │
│  fiscal". Tem cases específicos?           │
│                                             │
│  [✓ Sim, tenho] [Não tenho]                │

        ↓ Se "Sim"

│  Pode resumir 1-2 cases?                   │
│  ┌────────────────────────────────────┐   │
│  │ Ex: "Cliente X economizou R$ 120k" │   │
│  │                                     │   │
│  │ [Digite...]                        │   │
│  └────────────────────────────────────┘   │

        ⏱️ Tempo: 60-240seg (se fornece detalhes)

        ↓ Mais 1-2 perguntas contextuais

🟧 SISTEMA: Avalia qualidade do briefing
        │
        ├─ Score de qualidade: 0-100
        ├─ Se <60: Sugere mais 1-2 perguntas
        ├─ Se >60: Permite avançar
        └─ Usuário pode forçar avançar (sempre)

        ↓

📊 MÉTRICA: Briefing completo
   - Perguntas respondidas: 3-4
   - Caracteres totais: 300-600
   - Tempo gasto: 3-8min
   - Qualidade: 75-95/100

═══════════════════════════════════════════════════════════
FASE 3: INTEGRAÇÃO WEEKLY CONTEXT (Se Aplicável)
═══════════════════════════════════════════════════════════

🟧 SISTEMA: Busca oportunidades relevantes
        │
        ├─ Analisa briefing do usuário
        ├─ Busca em Weekly Context
        ├─ Filtra: relevance_score > 90
        └─ Encontra: 0-5 oportunidades

        ↓ Se encontrou oportunidades

🟩 MODAL: Oportunidades Detectadas
        │
┌───────────────────────────────────────────┐
│  📰 Radar Semanal                          │
├───────────────────────────────────────────┤
│                                            │
│  2 notícias relevantes para sua campanha: │
│                                            │
│  ┌─────────────────────────────────────┐  │
│  │ [☐] "Nova Instrução Normativa RF..."│  │
│  │      Relevância: 94/100              │  │
│  │      [Preview 30seg]                │  │
│  └─────────────────────────────────────┘  │
│                                            │
│  [Não usar] [Adicionar selecionadas]      │
│                                            │
└───────────────────────────────────────────┘

        ├─ 📊 Taxa de aceitação: 40%
        ├─ ⏱️ Tempo médio: 60-180seg (lê previews)
        └─ 💡 Se aceito: +1-2 posts na campanha

        ↓

═══════════════════════════════════════════════════════════
FASE 4: ESCOLHA DE ESTRUTURA
═══════════════════════════════════════════════════════════

🟧 SISTEMA: Thompson Sampling Decision 2
        │
        ├─ Bandit: campaign_structure
        ├─ Context: campaign_type={education}, niche={legal}
        └─ Chosen: "funil_conteudo" (score: 0.81)

        ↓

🟩 TELA: Estrutura Recomendada
        │
┌───────────────────────────────────────────┐
│  📖 Estrutura da Campanha                  │
├───────────────────────────────────────────┤
│                                            │
│  Funil de Conteúdo (RECOMENDADO)          │
│  Taxa de sucesso: 81%                     │
│                                            │
│  Como funciona:                            │
│  • Topo (40%): Educar sobre problema      │
│  • Meio (35%): Soluções                   │
│  • Fundo (25%): Conversão                 │
│                                            │
│  [📚 Saiba mais] [✓ Usar esta]            │
│  [Ver outras opções]                       │
│                                            │
└───────────────────────────────────────────┘

        ├─ 📊 Taxa: 68% aceitam, 24% comparam, 8% veem todas
        └─ ⏱️ Tempo: 15seg (aceitar) a 4min (comparar todas)

        ↓ Se aceita

🟦 USUÁRIO: [✓ Usar esta]

        ↓

═══════════════════════════════════════════════════════════
FASE 5: DURAÇÃO E CADÊNCIA
═══════════════════════════════════════════════════════════

🟧 SISTEMA: Calcula duração ideal
        │
        ├─ Estrutura: Funil → Ideal: 14-21 dias
        ├─ Briefing: Objetivo educacional → Sugere 18 dias
        ├─ Quantidade de posts: 12 (4 por semana)
        └─ Considera prazo do usuário (se mencionou)

        ↓

🟩 TELA: Configuração de Duração
        │
┌───────────────────────────────────────────┐
│  📅 Duração da Campanha                    │
├───────────────────────────────────────────┤
│                                            │
│  Sugestão: 18 dias, 12 posts              │
│  Cadência: 4 posts/semana                 │
│                                            │
│  [──────●──────] 18 dias                  │
│   7     18     30                          │
│                                            │
│  💡 Briefing mencionou prazo 15/dez       │
│     Sugerimos: 27/nov a 14/dez ✓          │
│                                            │
│  [Ajustar] [✓ Perfeito]                   │
│                                            │
└───────────────────────────────────────────┘

        ├─ 📊 Taxa: 75% aceitam sugestão, 25% ajustam
        └─ ⏱️ Tempo: 10-120seg (se ajustar: +60seg)

        ↓

═══════════════════════════════════════════════════════════
FASE 6: ESTILOS VISUAIS
═══════════════════════════════════════════════════════════

🟧 SISTEMA: Thompson Sampling Decision 3
        │
        ├─ Bandit: visual_style_curation
        ├─ Context: niche={legal}, voice={professional}
        ├─ Actions: [todos os 48 estilos]
        └─ Top 3: Corporate Blue, Minimal Professional, Legal Clean

        ↓

🟧 SISTEMA: Gera preview contextual
        │
        ├─ Usa texto do primeiro post (já gerado conceito)
        ├─ Aplica cada um dos 3 estilos
        ├─ Aplica cores da marca do usuário
        └─ Gera 3 imagens de preview (8seg)

        ⏱️ Loading: 8seg

        ↓

🟩 TELA: Seleção de Estilos com Preview
        │
┌───────────────────────────────────────────┐
│  🎨 Estilos Visuais da Campanha            │
├───────────────────────────────────────────┤
│                                            │
│  Preview do primeiro post em cada estilo: │
│                                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │Corporate │ │ Minimal  │ │  Legal   │  │
│  │  Blue    │ │ Profess. │ │  Clean   │  │
│  ├──────────┤ ├──────────┤ ├──────────┤  │
│  │ [IMG]    │ │ [IMG]    │ │ [IMG]    │  │
│  │ Preview  │ │ Preview  │ │ Preview  │  │
│  │ com seu  │ │ com seu  │ │ com seu  │  │
│  │ texto e  │ │ texto e  │ │ texto e  │  │
│  │ cores    │ │ cores    │ │ cores    │  │
│  ├──────────┤ ├──────────┤ ├──────────┤  │
│  │Taxa: 84% │ │Taxa: 79% │ │Taxa: 88% │  │
│  │(Jurídico)│ │(Todos)   │ │(Advogado)│  │
│  ├──────────┤ ├──────────┤ ├──────────┤  │
│  │ [☐]      │ │ [☐]      │ │ [☐]      │  │
│  └──────────┘ └──────────┘ └──────────┘  │
│                                            │
│  Selecione 1-3 estilos                    │
│  [📚 Ver mais 45 estilos]                  │
│  [Continuar]                               │
│                                            │
└───────────────────────────────────────────┘

        ├─ 📊 60% escolhem dos 3 iniciais, 40% exploram biblioteca
        └─ ⏱️ Tempo: 30seg (rápido) a 12min (explora tudo)

        ↓ Usuário seleciona

🟦 USUÁRIO: Marca 2 estilos (Minimal + Legal)
        │
        └─ [Continuar]

        ↓

═══════════════════════════════════════════════════════════
FASE 7: REVISÃO PRÉ-GERAÇÃO
═══════════════════════════════════════════════════════════

🟩 TELA: Resumo de Todas Escolhas
        │
┌───────────────────────────────────────────┐
│  ✅ Revisão Final                          │
├───────────────────────────────────────────┤
│                                            │
│  Sua campanha será:                       │
│  ✓ Tipo: Educacional                      │
│  ✓ Estrutura: Funil de Conteúdo           │
│  ✓ Duração: 18 dias (27/nov a 14/dez)    │
│  ✓ Posts: 12 (4 por semana)               │
│  ✓ Estilos: Minimal + Legal               │
│  ✓ Oportunidade: 1 notícia integrada      │
│                                            │
│  💰 Investimento: R$ 3,00                 │
│  Saldo: R$ 28,50 ✓                        │
│                                            │
│  [← Voltar e ajustar]                     │
│  [✨ Gerar Campanha →]                     │
│                                            │
└───────────────────────────────────────────┘

        ├─ ⏱️ Tempo: 20-60seg
        └─ 📊 95% prosseguem, 5% voltam para ajustar

        ↓

🟦 USUÁRIO: [✨ Gerar Campanha]

        ↓

═══════════════════════════════════════════════════════════
FASE 8: GERAÇÃO (Backend Assíncrono)
═══════════════════════════════════════════════════════════

🟩 TELA: Loading com Progress Bar
        │
┌───────────────────────────────────────────┐
│  ⚙️ Gerando sua campanha...                │
├───────────────────────────────────────────┤
│                                            │
│  ▓▓▓▓▓▓▓░░░░░ 58%                         │
│                                            │
│  ✓ Estrutura definida (12 posts)          │
│  ✓ Textos gerados (12/12)                 │
│  ⏳ Imagens sendo criadas (7/12)           │
│  ⏹ Otimização e validação                 │
│                                            │
│  💡 Campanhas com Funil de Conteúdo têm   │
│     +28% mais leads que posts isolados.   │
│                                            │
│  Fonte: Content Marketing Institute 2024  │
│                                            │
└───────────────────────────────────────────┘

        ⏱️ Tempo: 35-60seg

🟧 BACKEND (Paralelo, invisível):
        │
        ├─ Para cada post (1-12):
        │   │
        │   ├─ Gera texto com PostAIService
        │   ├─ Gera imagem com estilo selecionado
        │   ├─ Valida qualidade
        │   ├─ Auto-corrige se necessário
        │   └─ Salva PostIdea + CampaignPost
        │
        ├─ Valida campanha completa
        ├─ Calcula score de coerência visual
        └─ Registra decisões (bandits)

        ↓ Geração completa

🟧 VALIDAÇÃO FINAL (Invisível):
        │
        ├─ 225 de 239 posts (94%): ✓ Passaram
        ├─ 11 posts (5%): Auto-corrigidos
        ├─ 3 posts (1%): Falharam → Regenerados silenciosamente
        └─ 0 posts (0%): Falha total

        ↓ Tudo validado

═══════════════════════════════════════════════════════════
FASE 9: APRESENTAÇÃO E APROVAÇÃO
═══════════════════════════════════════════════════════════

🟩 TELA: Grid de Posts (Com Tabs)
        │
┌───────────────────────────────────────────┐
│  🎉 Campanha Criada!                       │
│  "Planejamento Tributário 2025"            │
├───────────────────────────────────────────┤
│                                            │
│  [Posts] [Calendário] [Preview Feed] [⚙️] │
│    ↑ ativo                                 │
│                                            │
│  Progresso: ░░░░░░░░░░░░ 0/12 aprovados  │
│                                            │
│  SEMANA 1                                  │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐     │
│  │ SEG 27  │ │ QUA 29  │ │ SEX 01  │     │
│  │ 9h Feed │ │ 18h Feed│ │ 13h Story│     │
│  ├─────────┤ ├─────────┤ ├─────────┤     │
│  │ [THUMB] │ │ [THUMB] │ │ [THUMB] │     │
│  │ Minimal │ │ Legal   │ │ Minimal │     │
│  │ "5 erros│ │ "Por que│ │ "73% das│     │
│  │ comuns" │ │ plane..." "│ empre..." │     │
│  │ Topo    │ │ Topo    │ │ Meio    │     │
│  ├─────────┤ ├─────────┤ ├─────────┤     │
│  │ [☐]     │ │ [☐]     │ │ [☐]     │     │
│  │ 👁️✏️🔄❌ │ │ 👁️✏️🔄❌ │ │ 👁️✏️🔄❌ │     │
│  └─────────┘ └─────────┘ └─────────┘     │
│                                            │
│  ... + 9 posts (scroll)                   │
│                                            │
│  [✅ Aprovar Todos]                        │
│  [✅ Aprovar Selecionados (0)]             │
│                                            │
└───────────────────────────────────────────┘

        ⏱️ Tempo nesta fase: 5min (rápido) a 35min (detalhista)

        ↓ Usuário interage

🟦 AÇÕES POSSÍVEIS:
        │
        ├─ [👁️ Ver completo] → Modal expandido
        ├─ [✏️ Editar] → Editor com preview ao vivo
        ├─ [🔄 Regenerar] → Feedback específico
        ├─ [❌ Remover] → Confirma + opções de substituição
        ├─ [☐ Checkbox] → Seleção para ação em lote
        └─ [✅ Aprovar]

        ↓ Exemplo: Clica "Editar" em Post 3

🟩 MODAL: Editor de Post
        │
┌────────────────────────────────────────────┐
│  ✏️ Editar Post 3                          │
├─────────────────┬──────────────────────────┤
│  EDITOR         │  PREVIEW AO VIVO         │
├─────────────────┼──────────────────────────┤
│                 │                          │
│  Texto:         │  [Imagem atualiza]       │
│  ┌───────────┐ │                          │
│  │ [Editing] │ │  "Título do Post"        │
│  │           │ │                          │
│  │ ...       │ │  Texto renderizado...    │
│  └───────────┘ │                          │
│                 │                          │
│  Imagem:        │                          │
│  [Manter]       │                          │
│  [Regenerar]    │                          │
│  [Upload nova]  │                          │
│                 │                          │
├─────────────────┴──────────────────────────┤
│  [Cancelar] [Salvar Alterações]           │
└────────────────────────────────────────────┘

        ⏱️ Tempo médio edição: 1-3min por post

        ↓ Salva

🟧 SISTEMA: Atualiza post
        │
        ├─ Registra: post_edited
        ├─ Context: {reason: user_preference, changes: [text]}
        └─ Bandit aprende: Próximo post será mais similar ao editado

        ↓ Volta ao grid

🟦 USUÁRIO: Continua aprovando outros posts
        │
        ├─ Alguns aprova rápido (média 25seg)
        ├─ Alguns edita (média 2min)
        └─ Alguns regenera (média 1min + 8seg nova versão)

        ↓ Quando aprovou maioria (>70%)

🟩 SISTEMA: Oferece atalho
        │
│  💡 Você já aprovou 9 de 12 posts!        │
│                                            │
│  Quer aprovar os 3 restantes de uma vez? │
│  [Revisar 1 por 1] [Aprovar Restantes]   │

        📊 Taxa de aceitação do atalho: 60%

        ↓ Todos aprovados

═══════════════════════════════════════════════════════════
FASE 10: PREVIEW DO INSTAGRAM FEED
═══════════════════════════════════════════════════════════

🟦 USUÁRIO: Clica tab [Preview Feed]
        │
        ↓

🟩 TELA: Simulação de Feed Instagram
        │
┌───────────────────────────────────────────┐
│  📱 Como seu perfil ficará                 │
│  [← Voltar] [✓ Finalizar]                 │
├───────────────────────────────────────────┤
│                                            │
│       ┌──────────────┐                    │
│       │@seuinsta  ⋮  │                    │
│       ├──────────────┤                    │
│       │              │                    │
│       │ [POST 1 IMG] │                    │
│       │  Minimal     │                    │
│       ├──────────────┤                    │
│       │ ❤️ 💬 ↗️      │                    │
│       │● seuinsta    │                    │
│       │"5 erros..."  │                    │
│       │...mais       │                    │
│       │🕒 27/nov 9h  │                    │
│       ├──────────────┤                    │
│       │ [POST 2 IMG] │ ↓ Scroll simula    │
│       │  Legal       │                    │
│       └──────────────┘                    │
│                                            │
│  🎨 Score de Harmonia: 76/100             │
│  [🎨 Analisar e Reorganizar]               │
│                                            │
└───────────────────────────────────────────┘

        ⏱️ Tempo: 1-8min (depende se reorganiza)

        ↓ Se clica "Analisar"

🟧 SISTEMA: Calcula harmonia visual
        │
        ├─ Contraste entre adjacentes: 76/100
        ├─ Balanço de grid 3x3: 78/100
        ├─ Consistência de marca: 72/100
        └─ Score final: 76/100

        ↓

🟩 MODAL: Análise de Harmonia
        │
│  Score: 76/100 (Bom)                      │
│                                            │
│  ⚠️ Sugestões:                             │
│  • Posts 4-5: Muito similares (18%)       │
│    Trocar ordem com Post 6?               │
│                                            │
│  [Aplicar Sugestão] [Reorganizar Manual]  │
│  [Está bom assim]                         │

        ↓ Se usuário reorganiza

🟦 USUÁRIO: Drag & drop posts
        │
        └─ Score atualiza EM TEMPO REAL
            72 → 76 → 81 → 85 ✓

        💡 "Gamificação" acidental (quer aumentar score)

        ↓ Satisfeito com harmonia

═══════════════════════════════════════════════════════════
FASE 11: FINALIZAÇÃO
═══════════════════════════════════════════════════════════

🟩 TELA: Salvar Campanha
        │
┌───────────────────────────────────────────┐
│  🎉 Campanha Pronta!                       │
├───────────────────────────────────────────┤
│                                            │
│  ✓ 12 posts aprovados                     │
│  ✓ Calendário definido                    │
│  ✓ Harmonia visual: 85/100                │
│                                            │
│  [💾 Salvar Campanha]                      │
│  [💾 Salvar + Criar Template]              │
│                                            │
│  (Template permite reusar estrutura)      │
│                                            │
└───────────────────────────────────────────┘

        ├─ 📊 65% salvam como template, 35% só salvam
        └─ ⏱️ Tempo: 10-60seg

        ↓

🟧 SISTEMA: Salva tudo
        │
        ├─ Campaign.status = 'completed'
        ├─ Se template: Cria CampaignTemplate
        ├─ Registra Decision(campaign_approved)
        ├─ Calcula métricas finais
        └─ Atualiza bandits

        ↓

🟩 TELA: Sucesso!
        │
│  ✅ Campanha salva com sucesso!           │
│                                            │
│  Próximo post: 27/nov às 9h               │
│                                            │
│  [Ver Campanha] [Criar Nova]              │
│  [Voltar ao Dashboard]                     │

        ↓

🟦 USUÁRIO: [Voltar ao Dashboard]

═══════════════════════════════════════════════════════════
PÓS-CRIAÇÃO (Tracking Contínuo)
═══════════════════════════════════════════════════════════

🟧 SISTEMA: Monitora uso (background)
        │
        ├─ Se usuário publica posts: Rastreia
        ├─ Se conectou Instagram: Busca insights (diário)
        ├─ Compara Real vs. Projetado
        ├─ Atualiza bandits baseado em performance
        └─ Gera recomendações para próxima campanha

        ↓ Após 2-3 semanas

🟩 EMAIL: Insights da Campanha
        │
│  📊 Sua campanha "Plan. Tributário" foi  │
│     um sucesso!                            │
│                                            │
│  Alcance: 3.240 (+29% vs. projetado)     │
│  Leads: 11 (dentro da meta 8-14)         │
│                                            │
│  [Ver Dashboard Completo]                 │
│  [Criar Campanha Similar]                 │

═══════════════════════════════════════════════════════════
FIM DO CICLO
═══════════════════════════════════════════════════════════
```

---

## ⏱️ MATRIZ DE TEMPOS POR PERSONA

| Fase | Bruno | Eduarda | Ana | Daniel | Carla |
|------|-------|---------|-----|--------|-------|
| **Descoberta** | 5seg | 45seg | 12seg | 15seg | 18seg |
| **Análise (sistema)** | 3seg | 4seg | 4seg | 5seg | 4seg |
| **Briefing** | 20seg | 7min | 3min | 12min | 9min |
| **Weekly Context** | - | - | 3min | 5min | - |
| **Estrutura** | - | 2min | 1min | 4min | 5min |
| **Duração** | - | 30seg | 15seg | 3min | 40seg |
| **Estilos** | - | 1min | 2min | 2min | 12min |
| **Pré-geração** | - | 20seg | 30seg | 45seg | 1min |
| **Geração** | 25seg | 32seg | 40seg | 52seg | 45seg |
| **Aprovação** | 30seg‡ | 15min | 13min | 14min | 32min |
| **Preview Feed** | - | 2min | 2min | 3min | 8min |
| **Reorganização** | - | - | 2min | - | 15min |
| **Finalização** | 15seg | 6min | 3min | 1min | 2min |
| **TOTAL** | **1:38** | **37:08** | **24:42** | **49:12** | **1:38:15** |

‡Bruno aprovou sem revisar, revisou depois (+18min)

---

## 🎯 DECISÃO FINAL RECOMENDADA

### MVP Deve Implementar (P0):

1. ✅ **Grid de aprovação com checkboxes**
2. ✅ **Preview do Instagram Feed**
3. ✅ **Auto-save a cada 30seg**
4. ✅ **3 Jornadas (Rápida, Guiada, Avançada)**
5. ✅ **Briefing adaptativo**
6. ✅ **3 Estruturas principais** (AIDA, PAS, Funil)
7. ✅ **Biblioteca de 15-20 estilos visuais**
8. ✅ **Preview contextual de estilos**
9. ✅ **Thompson Sampling** (3 decisões)
10. ✅ **Integração Weekly Context**
11. ✅ **Validação automática invisível**
12. ✅ **Recovery de abandonos**

### V2 (Após 1.000 usuários):

- Modo Expert/Designer
- Upload massivo de fotos
- Instagram Performance Dashboard
- Colaboração (compartilhamento)
- Templates avançados

### V3 (Após 10.000 usuários):

- Contextual Bandits (Deep RL)
- Integrações CRM
- Múltiplas versões A/B
- Export Figma/Canva
- Features Pro (paywall)

---

**Tudo documentado. Pronto para implementação.** ✅🚀

