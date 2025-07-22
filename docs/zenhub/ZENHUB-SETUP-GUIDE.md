# 🚀 ZenHub Setup Guide - V9.0

**GUIA RÁPIDO PARA CONFIGURAÇÃO DO ZENHUB**

> **📅 Criado:** 15/07/2025  
> **🎯 Objetivo:** Configurar ZenHub automaticamente via GitHub API  
> **🔧 Status:** Pronto para execução

---

## 🎯 **CONFIGURAÇÃO RÁPIDA**

### **1️⃣ CRIAR GITHUB TOKEN**

1. **Acesse:** https://github.com/settings/tokens
2. **Clique:** "Generate new token (classic)"
3. **Configure:**

   - **Note:** `ZenHub V9.0 Setup`
   - **Expiration:** 90 days
   - **Permissions:**
     - ✅ `repo` (Full control of private repositories)
     - ✅ `issues` (Full control of issues)

4. **Copie o token** (você só verá uma vez!)

### **2️⃣ CONFIGURAR TOKEN**

```bash
# Configure o token no terminal
export GITHUB_TOKEN=seu_token_aqui

# Ou adicione ao seu .bashrc/.zshrc
echo 'export GITHUB_TOKEN=seu_token_aqui' >> ~/.bashrc
source ~/.bashrc
```

### **3️⃣ EXECUTAR SCRIPT**

```bash
# Execute o script de configuração
node scripts/zenhub-github-api.mjs
```

---

## 📋 **O QUE O SCRIPT FAZ**

### **✅ CRIA AUTOMATICAMENTE:**

1. **23 Labels** organizadas por categoria:

   - Type: feature, bug, enhancement, documentation, testing, deployment
   - Priority: high, medium, low
   - Component: frontend, backend, ux, performance, security, accessibility
   - Status: wireframe, approved, implementation, blocked
   - Epic: epic, foundation, ui-ux, quality

2. **3 Epics** principais:

   - Foundation Epic (IA Alpha)
   - UI/UX Enhancement Epic (IA Beta)
   - Quality & Testing Epic (IA Charlie)

3. **4 Sprint Issues** de planejamento:
   - Sprint 1: Foundation - Core Services Optimization
   - Sprint 2: Foundation - Performance & Security
   - Sprint 5: UI/UX Enhancement
   - Sprint 6: Quality & Deployment

---

## 🎯 **PRÓXIMOS PASSOS**

### **✅ APÓS EXECUTAR O SCRIPT:**

1. **Configure ZenHub Pipelines:**

   - Main Pipeline: Backlog → Sprint Planning → In Progress → Ready for Deploy → Deployed
   - Wireframe Pipeline: Wireframe Backlog → Wireframe Development → Wireframe Review → Wireframe Approved → Implementation Ready

2. **Organize Issues:**

   - Mova epics para pipelines apropriados
   - Atribua issues aos sprints
   - Configure capacity planning da equipe

3. **Inicie Desenvolvimento:**
   - Comece com Sprint 1: Foundation
   - Siga metodologia V9.0
   - Acompanhe progresso via ZenHub

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

## 🚨 **TROUBLESHOOTING**

### **❌ ERRO: GitHub token não encontrado**

```bash
# Configure o token
export GITHUB_TOKEN=seu_token_aqui
```

### **❌ ERRO: Permissões insuficientes**

- Verifique se o token tem permissões `repo` e `issues`
- Recrie o token se necessário

### **❌ ERRO: Rate limit exceeded**

- Aguarde alguns minutos e tente novamente
- GitHub tem limite de 5000 requests/hora

### **❌ ERRO: Repository not found**

- Verifique se o repositório existe
- Confirme se o token tem acesso ao repositório

---

## 📈 **MÉTRICAS DE SUCESSO**

### **🎯 TARGETS V9.0**

- **Velocity:** 20+ story points por sprint
- **Quality:** >90% code coverage, <5% bug rate
- **Performance:** <3s load time
- **Coordination:** 0 conflitos, handoffs suaves

### **📊 REPORTING**

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

## 🚀 **EXECUÇÃO FINAL**

```bash
# 1. Configure o token
export GITHUB_TOKEN=seu_token_aqui

# 2. Execute o script
node scripts/zenhub-github-api.mjs

# 3. Verifique o relatório
cat ZENHUB-GITHUB-API-REPORT.md

# 4. Configure ZenHub pipelines
# 5. Organize issues
# 6. Inicie desenvolvimento V9.0
```

---

**🚀 STATUS: PRONTO PARA EXECUÇÃO**

_Configure o token do GitHub e execute o script para configurar automaticamente o ZenHub V9.0._

**📋 CHECKLIST:**

- [ ] Criar GitHub token com permissões repo + issues
- [ ] Configurar GITHUB_TOKEN no terminal
- [ ] Executar `node scripts/zenhub-github-api.mjs`
- [ ] Verificar relatório gerado
- [ ] Configurar pipelines no ZenHub
- [ ] Organizar issues nos sprints
- [ ] Iniciar desenvolvimento V9.0
