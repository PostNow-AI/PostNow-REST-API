# Weekly Context — Propósito, UX e Critérios de Qualidade

## 1) Propósito (por que existe)
O Weekly Context existe para resolver um problema recorrente de criadores e negócios: **falta de pauta boa e acionável** toda semana.

Em vez de depender de “ideias genéricas” ou de pesquisa manual, o sistema entrega um e-mail semanal com oportunidades que:
- **são recentes** (busca com janela temporal e fontes priorizadas)
- **são confiáveis** (guardrails de fonte + validação de URL)
- **não se repetem** (anti-repetição semanal por histórico)
- **viram ação em 1 clique** (CTA para criar post no app)

O objetivo final é: **reduzir tempo de pesquisa**, **aumentar qualidade das ideias** e **acelerar a criação de conteúdo**.

---

## 2) Para quem é (usuários e stakeholders)
- **Usuário final (cliente PostNow)**: recebe o e-mail e escolhe oportunidades para virar post.
- **Time interno (CS/Ops)**: consegue forçar uma policy (override) para clientes especiais quando necessário.
- **CTO/Engenharia**: valida integridade do pipeline e rastreia problemas via logs estruturados.

---

## 3) UX: Jornada do usuário (o que acontece na prática)

### 3.1 Antes (dor)
- O usuário perde tempo buscando notícias/tendências
- Encontra links quebrados, fontes ruins ou conteúdo repetido
- Não consegue transformar em post rapidamente

### 3.2 Depois (experiência desejada)
1. **E-mail chega** (semanal) com oportunidades organizadas e rankeadas
2. Usuário **lê rapidamente** e escolhe 1–3 oportunidades (top picks)
3. Clica em **“Criar Post”** e cai no app com briefing pronto
4. Publica com mais velocidade e consistência

---

## 4) O que é um “e-mail bom” (contrato de UX)

Um bom Weekly Context precisa cumprir:
- **Links funcionam** (sem 404 / soft-404)
- **Fontes parecem “notícia/artigo”** (não listagem/tag/search/PDF)
- **Variedade de tipos** (não só “educativo”; diversidade forçada)
- **Score coerente** (0–100, critérios objetivos)
- **Sem repetição semanal** (o usuário não recebe os mesmos links da semana anterior)
- **CTA claro** (1 clique para transformar em post)

O que é proibido aparecer como output final:
- “Sem dados suficientes”, “Não encontrado”, “Indisponível”
- links quebrados
- páginas genéricas (home, tag, search)

---

## 5) Critérios de qualidade (como medimos se está bom)

### 5.1 Métricas operacionais (sem tracking de clique)
Disponíveis via logs:
- `[SOURCE_METRICS]` por seção (raw, selected, allow, denied, fallback)
- `[LOW_SOURCE_COVERAGE]` quando cobertura mínima não é atingida
- `[LOW_ALLOWLIST_RATIO]` quando a proporção allowlist cai
- `[URL_DROPPED_404]` quando links são descartados por inválidos

### 5.2 Métricas de produto (quando instrumentarmos)
(futuro) taxa de clique em CTA, taxa de posts criados a partir do e-mail, tempo até o primeiro post, etc.

---

## 6) Operação: quando usar override manual por cliente
Existe um campo opcional no perfil:
- `CreatorProfile.weekly_context_policy_override`

Use quando:
- Cliente VIP exige comportamento mais rígido (`business_strict`)
- Heurística automática não está escolhendo bem
- Você quer fazer um “controle” temporário sem mudar o código

Rollback:
- limpar o campo para voltar ao modo automático

---

## 7) Regras “hard” resumidas
- **Anti-repetição** por histórico (domain+path) com lookback configurável
- **Qualidade de fonte** (allowlist/denylist por seção + padrões)
- **Validação e recuperação de URLs** para evitar alucinação de links

---

## 8) Onde está a documentação técnica
- `docs/WEEKLY_CONTEXT_ARCHITECTURE.md`: arquitetura atual e componentes
- `docs/WEEKLY_CONTEXT_POLICIES.md`: policies + override + logs


