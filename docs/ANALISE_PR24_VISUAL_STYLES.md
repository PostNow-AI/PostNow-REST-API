# Análise Técnica: PR #24 - Sistema de Estilos Visuais

**Data:** 2026-02-23
**Autor:** Análise técnica via Claude Code
**Status:** Fechado - Aguardando decisão arquitetural

---

## Contexto

O PR #24 (`feat/visual-styles`) adiciona:
1. Fixture com 18 estilos visuais (`visual_style_preferences.json`)
2. Script para gerar imagens de preview (`generate_style_previews.py`)
3. Logo PostNow para uso nos previews (`postnow_logo.png`)

---

## Situação Atual

### Os estilos visuais estão em 3 lugares diferentes:

```
┌─────────────────────────────────────────────────────────────────────┐
│                     FONTE 1: FRONTEND (hardcoded)                   │
│                     onboardingNewSchema.ts                          │
├─────────────────────────────────────────────────────────────────────┤
│  visualStyleOptions = [                                             │
│    {                                                                │
│      id: "1",                                                       │
│      label: "Minimalista Moderno",                                  │
│      description: "Design limpo, espaços em branco...",  ← CURTA    │
│      preview_image_url: "https://s3.../minimalista..."              │
│    },                                                               │
│    // ... 18 estilos                                                │
│  ]                                                                  │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                     FONTE 2: BANCO DE DADOS                         │
│                     VisualStylePreference (MySQL)                   │
├─────────────────────────────────────────────────────────────────────┤
│  id: 1                                                              │
│  name: "Minimalista Moderno"                                        │
│  description: "### CARACTERÍSTICAS DO ESTILO ###                    │
│                Design minimalista profissional...                   │
│                ### ELEMENTOS VISUAIS ###                            │
│                - Fundo branco puro ou off-white                     │
│                - Espaço negativo generoso (60%)                     │
│                ### PALETA DE CORES ###                    ← COMPLETA│
│                - Primária: Branco (#FFFFFF)                         │
│                ### TIPOGRAFIA ###                                   │
│                - Sans-serif moderna (Inter, Helvetica)              │
│                ### EVITAR ###                                       │
│                - Gradientes e sombras dramáticas..."                │
│  preview_image_url: "https://s3.../minimalista..."                  │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                     FONTE 3: FIXTURE (PR #24)                       │
│                     visual_style_preferences.json                   │
├─────────────────────────────────────────────────────────────────────┤
│  (Mesmo conteúdo do banco de dados em formato JSON)                 │
└─────────────────────────────────────────────────────────────────────┘
```

### Fluxo atual:

```
ONBOARDING                          GERAÇÃO DE IMAGEM
    │                                       │
    ▼                                       ▼
Frontend (hardcoded)               Backend (banco de dados)
    │                                       │
    │ Mostra: nome + descrição curta        │ Usa: nome + descrição COMPLETA
    │         + imagem preview              │      para instruir a IA
    │                                       │
    └───────────── ID do estilo ───────────►│
```

---

## Problemas Identificados

### 1. Duplicação de dados (DRY violation)

| Dado | Frontend | Banco | Fixture |
|------|----------|-------|---------|
| Nome do estilo | ✅ | ✅ | ✅ |
| Descrição curta | ✅ | ❌ | ❌ |
| Descrição completa (IA) | ❌ | ✅ | ✅ |
| URL da imagem | ✅ | ✅ | ✅ |

**Risco:** Se alguém adicionar um estilo em um lugar e esquecer dos outros, o sistema quebra silenciosamente.

### 2. A fixture é redundante

Os dados **já existem** no banco de produção. A fixture:
- Não adiciona funcionalidade
- É apenas um "backup" em formato JSON
- Não tem mecanismo de auto-carregamento (não há migration)

### 3. Manutenção complexa

Para adicionar um novo estilo visual:

```
Passo 1: Editar frontend (onboardingNewSchema.ts)
         ↓
Passo 2: Editar fixture (visual_style_preferences.json)
         ↓
Passo 3: Gerar imagem de preview (rodar script)
         ↓
Passo 4: Upload imagem para S3
         ↓
Passo 5: Atualizar URLs nos 3 lugares
         ↓
Passo 6: Carregar fixture no banco (python manage.py loaddata)
         ↓
Passo 7: Deploy frontend + backend
```

### 4. Inconsistência potencial

| Cenário | Resultado |
|---------|-----------|
| Estilo no frontend, não no banco | Usuário seleciona, mas IA não tem instruções → imagem genérica |
| Estilo no banco, não no frontend | Usuário não consegue selecionar |
| IDs diferentes | Usuário seleciona "Minimalista", IA recebe instruções de "Bold" |

---

## Opções de Arquitetura

### Opção A: Frontend-first (Single Source of Truth no Frontend)

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FRONTEND                                    │
│                    (única fonte de dados)                           │
├─────────────────────────────────────────────────────────────────────┤
│  visualStyleOptions = [                                             │
│    {                                                                │
│      id: "1",                                                       │
│      name: "Minimalista Moderno",                                   │
│      shortDescription: "Design limpo...",      ← Para mostrar       │
│      aiDescription: "### CARACTERÍSTICAS...",  ← Para IA            │
│      preview_image_url: "https://s3.../..."                         │
│    }                                                                │
│  ]                                                                  │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
              API envia estilo completo para backend
                              │
                              ▼
                    Backend usa para gerar imagem
```

**Prós:**
- Uma única fonte de verdade
- Frontend controla tudo
- Não precisa de banco para estilos
- Deploy simples

**Contras:**
- Descrições longas aumentam bundle do frontend
- Mudanças requerem deploy do frontend

---

### Opção B: Backend-first (Single Source of Truth no Banco)

```
┌─────────────────────────────────────────────────────────────────────┐
│                      BANCO DE DADOS                                 │
│                   (única fonte de dados)                            │
├─────────────────────────────────────────────────────────────────────┤
│  VisualStylePreference:                                             │
│    - id, name, short_description, ai_description, preview_url       │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    GET /api/visual-styles/
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         FRONTEND                                    │
│                    (busca da API)                                   │
├─────────────────────────────────────────────────────────────────────┤
│  const { data: styles } = useQuery(['visualStyles'], fetchStyles)   │
└─────────────────────────────────────────────────────────────────────┘
```

**Prós:**
- Uma única fonte de verdade
- Pode alterar estilos sem deploy do frontend
- Pode adicionar painel admin para gerenciar estilos
- Mais flexível para o futuro

**Contras:**
- Requer chamada de API no onboarding
- Precisa de tratamento de loading/erro
- Onboarding fica dependente do backend

---

## Recomendação

### Curto prazo (agora)

**Fechar o PR #24** porque:
1. O sistema funciona como está
2. A fixture adiciona complexidade sem resolver o problema
3. A duplicação de dados continua existindo

### Médio prazo (próximo sprint)

**Escolher uma arquitetura unificada:**

| Critério | Opção A (Frontend) | Opção B (Backend) |
|----------|-------------------|-------------------|
| Simplicidade | ✅ Mais simples | ❌ Requer API call |
| Flexibilidade | ❌ Requer deploy | ✅ Alterável sem deploy |
| Performance onboarding | ✅ Dados já carregados | ❌ Espera API |
| Escalabilidade | ❌ Bundle cresce | ✅ Dados no servidor |

**Minha sugestão:** Opção B (Backend-first) porque:
- Permite gerenciar estilos via admin
- Facilita adicionar novos estilos
- Separa dados de código
- O onboarding já faz outras chamadas de API

---

## Ações Sugeridas

1. [ ] CTO decide qual arquitetura seguir (A ou B)
2. [ ] Criar tarefa para unificar fonte de dados
3. [ ] Remover duplicação após implementação
4. [ ] Documentar processo de adicionar novo estilo

---

## Referências

- PR #24: https://github.com/PostNow-AI/PostNow-REST-API/pull/24
- Frontend styles: `Sonora-UI/src/features/Auth/Onboarding/constants/onboardingNewSchema.ts`
- Backend model: `CreatorProfile/models.py` → `VisualStylePreference`
- Prompt service: `services/ai_prompt_service.py` (linhas 887-923)
