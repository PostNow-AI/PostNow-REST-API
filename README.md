# Weekly Context (E-mail semanal de oportunidades)

Este repositório/branch contém a implementação e documentação do **Weekly Context**: um pipeline que pesquisa fontes recentes, gera oportunidades rankeadas com IA e envia um e-mail semanal com links válidos e sem repetição.

## Onde está a documentação “atual” (o que usamos hoje)

- **Políticas + Override por cliente (Admin + logs + como operar)**  
  `PostNow-REST-API/docs/WEEKLY_CONTEXT_POLICIES.md`

- **Arquitetura do Weekly Context (pipeline end-to-end)**  
  `PostNow-REST-API/docs/WEEKLY_CONTEXT_ARCHITECTURE.md`

## Como validar rapidamente (CTO)

### Backend

- Rodar testes do módulo:
  - `venv/bin/python manage.py test ClientContext.tests -v 2`
- Rodar processo completo (gera e envia e-mail):
  - `venv/bin/python scripts/trigger_team_validation.py`

## Principais mudanças desta entrega

- Policy automática por cliente (resolver) e **override manual por cliente** via `CreatorProfile.weekly_context_policy_override`
- Telemetria e alertas em logs: `[POLICY]`, `[SOURCE_METRICS]`, `[LOW_SOURCE_COVERAGE]`, `[LOW_ALLOWLIST_RATIO]`
- Migração: `CreatorProfile/migrations/0010_creatorprofile_weekly_context_policy_override.py`

## Observações importantes

- A documentação antiga não reflete o sistema atual do Weekly Context e foi substituída por este guia.

### **🚀 ZENHUB**

- **Configurações** - Templates e configurações do ZenHub
- **Scripts** - Automação de setup via GitHub API
- **Relatórios** - Relatórios de configuração e setup

### **🔧 SCRIPTS**

- **zenhub-setup.mjs** - Setup básico (simulado)
- **zenhub-auto-setup.mjs** - Setup automático (simulado)
- **zenhub-github-api.mjs** - Setup real via GitHub API

---

## 🚀 **QUICK START**

### **1️⃣ CONFIGURAR ZENHUB**

```bash
# Configure o token do GitHub
export GITHUB_TOKEN=seu_token_aqui

# Execute o script de configuração
node docs/scripts/zenhub-github-api.mjs
```

### **2️⃣ VERIFICAR DOCUMENTAÇÃO**

```bash
# Metodologia V9.0
cat docs/methodologies/V9.md

# Configuração ZenHub
cat docs/zenhub/config/zenhub-config.md

# Guia de setup
cat docs/zenhub/ZENHUB-SETUP-GUIDE.md
```

### **3️⃣ EXECUTAR SCRIPTS**

```bash
# Setup básico (simulado)
node docs/scripts/zenhub-setup.mjs

# Setup automático (simulado)
node docs/scripts/zenhub-auto-setup.mjs

# Setup real via GitHub API
node docs/scripts/zenhub-github-api.mjs
```

---

## 📊 **ESPECIALIZAÇÃO DAS IAs**

### **👥 IA ALPHA (Backend/Architecture)**

- **Responsabilidades:** Backend, Performance, Security, Deployment
- **Capacity:** 20 story points por sprint
- **Labels:** `backend`, `performance`, `security`, `architecture`
- **Epics:** Foundation, Service Integration

### **👥 IA BETA (Frontend/UX)**

- **Responsabilidades:** Frontend, UX, Components, Accessibility
- **Capacity:** 20 story points por sprint
- **Labels:** `frontend`, `ux`, `components`, `accessibility`
- **Epics:** UI/UX Enhancement

### **👥 IA CHARLIE (Testing/Quality)**

- **Responsabilidades:** Testing, CI/CD, Quality Assurance, Documentation
- **Capacity:** 15 story points por sprint
- **Labels:** `testing`, `quality`, `ci-cd`, `documentation`
- **Epics:** Quality & Testing

---

## 📅 **SPRINT PLANNING (6 SPRINTS)**

### **🏗️ Sprint 1-2: Foundation**

- **Objetivo:** Core infrastructure and backend improvements
- **IA Alpha:** 20 SP (Core services, Performance monitoring)
- **IA Charlie:** 5 SP (Testing support)
- **Epic:** Foundation

### **🔗 Sprint 3-4: Service Integration**

- **Objetivo:** API integration and database optimization
- **IA Alpha:** 20 SP (API integration, Security)
- **IA Charlie:** 5 SP (Testing support)
- **Epic:** Foundation

### **🎨 Sprint 5: Component Enhancement**

- **Objetivo:** Frontend improvements and user experience
- **IA Beta:** 20 SP (Design system, UX improvements)
- **IA Charlie:** 5 SP (Testing support)
- **Epic:** UI/UX Enhancement

### **🛡️ Sprint 6: Quality & Deployment**

- **Objetivo:** Comprehensive testing and production deployment
- **IA Charlie:** 15 SP (Testing, Quality assurance)
- **IA Alpha:** 5 SP (Deployment support)
- **Epic:** Quality & Testing

---

## 📊 **MÉTRICAS DE SUCESSO**

### **🎯 TARGETS V9.0**

- **Velocity:** 20+ story points por sprint
- **Quality:** >90% code coverage, <5% bug rate
- **Performance:** <3s load time
- **Coordination:** 0 conflitos, handoffs suaves

### **📈 REPORTING TEMPLATE**

```markdown
## 📊 Sprint Report [N]

- **Sprint Goal:** [Objetivo alcançado?]
- **Velocity:** [X] story points
- **Completed:** [X] issues
- **In Progress:** [X] issues
- **Blocked:** [X] issues
- **Team Performance:** IA Alpha [X] SP, IA Beta [X] SP, IA Charlie [X] SP
```

---

## 🚨 **PROTOCOLOS DE EMERGÊNCIA**

### **⚠️ CONFLITO DETECTADO**

1. PARAR trabalho imediatamente
2. Comentar no ZenHub issue
3. Mover para pipeline "Blocked"
4. Resolver conflito antes de continuar

### **⚠️ SISTEMA QUEBRADO**

1. Rollback imediato
2. Criar issue de bug no ZenHub
3. Análise de causa raiz
4. Fix coordenado e testado

### **⚠️ BLOQUEADO**

1. Atualizar status da issue
2. Comunicar com equipe
3. Identificar dependências
4. Coordenar resolução

---

## 📞 **SUPORTE E DOCUMENTAÇÃO**

### **📚 DOCUMENTAÇÃO COMPLETA**

- **docs/methodologies/V9.md** - Metodologia completa V9.0
- **docs/zenhub/config/zenhub-config.md** - Configuração detalhada
- **docs/zenhub/ZENHUB-README.md** - Resumo executivo
- **docs/zenhub/ZENHUB-SETUP-GUIDE.md** - Guia de configuração

### **🔧 SCRIPTS DISPONÍVEIS**

- **docs/scripts/zenhub-github-api.mjs** - Setup real via GitHub API
- **docs/scripts/zenhub-setup.mjs** - Setup básico (simulado)
- **docs/scripts/zenhub-auto-setup.mjs** - Setup automático (simulado)

### **📊 FERRAMENTAS INTEGRADAS**

- **ZenHub Analytics** - Métricas de sprint
- **GitHub Actions** - CI/CD automation
- **Sentry** - Error tracking
- **Lighthouse** - Performance monitoring

---

## 🏆 **BENEFÍCIOS V9.0**

### **✅ ANTES vs DEPOIS**

```
❌ ANTES (V8.0):
- Gestão manual de tarefas
- Coordenação não estruturada
- Falta de visibilidade
- Métricas limitadas

✅ AGORA (V9.0 ZENHUB):
- Gestão automatizada via ZenHub
- Coordenação estruturada
- Visibilidade total
- Métricas detalhadas
- Entrega previsível
```

### **🎯 RESULTADO ESPERADO**

- **Zero confusão metodológica**
- **Máxima produtividade das IAs**
- **Qualidade consistente**
- **Coordenação perfeita via ZenHub**
- **Entrega previsível e rastreável**

---

## 🚀 **EXECUÇÃO FINAL**

```bash
# 1. Configure o token do GitHub
export GITHUB_TOKEN=seu_token_aqui

# 2. Execute o script de configuração
node docs/scripts/zenhub-github-api.mjs

# 3. Verifique o relatório gerado
cat docs/zenhub/reports/ZENHUB-GITHUB-API-REPORT.md

# 4. Configure os pipelines no ZenHub
# 5. Organize as issues nos sprints
# 6. Inicie o desenvolvimento V9.0
```

---

**🚀 STATUS: REPOSITÓRIO DE DOCUMENTAÇÃO - PRONTO PARA USO**

_Esta estrutura organiza toda a documentação e metodologias do projeto Sonora UI de forma clara e acessível._

**📋 CHECKLIST FINAL:**

- [ ] Configurar GitHub token
- [ ] Executar script de configuração ZenHub
- [ ] Verificar relatórios gerados
- [ ] Configurar pipelines no ZenHub
- [ ] Organizar issues nos sprints
- [ ] Iniciar desenvolvimento V9.0
- [ ] Monitorar métricas e ajustar conforme necessário

**🎉 DOCUMENTAÇÃO COMPLETA - PRONTA PARA USO!**
