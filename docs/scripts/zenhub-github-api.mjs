#!/usr/bin/env node

/**
 * 🚀 ZenHub GitHub API Script - V9.0
 * Faz chamadas reais para a API do GitHub para configurar ZenHub
 */

import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Colors for console output
const colors = {
  reset: "\x1b[0m",
  bright: "\x1b[1m",
  red: "\x1b[31m",
  green: "\x1b[32m",
  yellow: "\x1b[33m",
  blue: "\x1b[34m",
  magenta: "\x1b[35m",
  cyan: "\x1b[36m",
};

const log = {
  info: (msg) => console.log(`${colors.cyan}ℹ️  ${msg}${colors.reset}`),
  success: (msg) => console.log(`${colors.green}✅ ${msg}${colors.reset}`),
  warning: (msg) => console.log(`${colors.yellow}⚠️  ${msg}${colors.reset}`),
  error: (msg) => console.log(`${colors.red}❌ ${msg}${colors.reset}`),
  title: (msg) =>
    console.log(`${colors.bright}${colors.blue}🚀 ${msg}${colors.reset}`),
};

// GitHub API Configuration
const GITHUB_TOKEN = process.env.GITHUB_TOKEN;
const REPO_OWNER = process.env.GITHUB_REPOSITORY_OWNER || "matheussb";
const REPO_NAME = process.env.GITHUB_REPOSITORY_NAME || "Sonora-UI";

// GitHub API Base URL
const GITHUB_API_BASE = "https://api.github.com";

// Headers for GitHub API
const getHeaders = () => ({
  Authorization: `token ${GITHUB_TOKEN}`,
  Accept: "application/vnd.github.v3+json",
  "Content-Type": "application/json",
});

// GitHub API call function
async function githubAPI(endpoint, method = "GET", data = null) {
  const url = `${GITHUB_API_BASE}${endpoint}`;
  const options = {
    method,
    headers: getHeaders(),
  };

  if (data) {
    options.body = JSON.stringify(data);
  }

  try {
    const response = await fetch(url, options);

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(
        `GitHub API Error: ${response.status} - ${
          errorData.message || response.statusText
        }`
      );
    }

    return await response.json();
  } catch (error) {
    log.error(`API call failed: ${error.message}`);
    throw error;
  }
}

// Create label
async function createLabel(label) {
  const endpoint = `/repos/${REPO_OWNER}/${REPO_NAME}/labels`;
  const data = {
    name: label.name,
    color: label.color,
    description: label.description,
  };

  log.info(`Creating label: ${label.name}`);
  return await githubAPI(endpoint, "POST", data);
}

// Create issue
async function createIssue(issue) {
  const endpoint = `/repos/${REPO_OWNER}/${REPO_NAME}/issues`;
  const data = {
    title: issue.title,
    body: issue.body,
    labels: issue.labels || [],
  };

  log.info(`Creating issue: ${issue.title}`);
  return await githubAPI(endpoint, "POST", data);
}

// ZenHub Labels Configuration
const zenhubLabels = [
  // Type Labels
  { name: "feature", color: "0e8a16", description: "Novas funcionalidades" },
  { name: "bug", color: "d93f0b", description: "Correções de bugs" },
  { name: "enhancement", color: "1d76db", description: "Melhorias" },
  { name: "documentation", color: "0075ca", description: "Documentação" },
  { name: "testing", color: "fef2c0", description: "Testes" },
  { name: "deployment", color: "5319e7", description: "Deploy" },

  // Priority Labels
  { name: "priority:high", color: "d93f0b", description: "Alta prioridade" },
  { name: "priority:medium", color: "fef2c0", description: "Média prioridade" },
  { name: "priority:low", color: "0e8a16", description: "Baixa prioridade" },

  // Component Labels
  { name: "frontend", color: "1d76db", description: "Frontend work" },
  { name: "backend", color: "5319e7", description: "Backend work" },
  { name: "ux", color: "fef2c0", description: "User Experience" },
  {
    name: "performance",
    color: "d93f0b",
    description: "Performance optimization",
  },
  { name: "security", color: "d93f0b", description: "Security related" },
  {
    name: "accessibility",
    color: "0e8a16",
    description: "Accessibility compliance",
  },

  // Status Labels
  { name: "wireframe", color: "1d76db", description: "Wireframe development" },
  {
    name: "approved",
    color: "0e8a16",
    description: "Approved for implementation",
  },
  { name: "implementation", color: "5319e7", description: "Live component" },
  { name: "blocked", color: "d93f0b", description: "Blocked by dependency" },

  // Epic Labels
  { name: "epic", color: "5319e7", description: "Epic issue" },
  { name: "foundation", color: "0e8a16", description: "Foundation epic" },
  { name: "ui-ux", color: "1d76db", description: "UI/UX Enhancement epic" },
  { name: "quality", color: "fef2c0", description: "Quality & Testing epic" },
];

// Epic Templates
const epicTemplates = [
  {
    title: "Foundation Epic",
    body: `## 🏗️ Foundation Epic

### 📋 Description
Core infrastructure and backend improvements

### 🎯 Objectives
- [ ] Core services optimization
- [ ] Backend architecture improvements
- [ ] Performance monitoring setup
- [ ] Error tracking implementation

### 👥 Responsible
- **Primary:** IA Alpha
- **Support:** IA Charlie (testing)

### 📊 Estimate
- **Total:** 40 story points
- **Sprint 1:** 20 story points
- **Sprint 2:** 20 story points

### 🏷️ Labels
- epic
- foundation
- backend
- performance`,
    labels: ["epic", "foundation", "backend", "performance"],
  },
  {
    title: "UI/UX Enhancement Epic",
    body: `## 🎨 UI/UX Enhancement Epic

### 📋 Description
Frontend improvements and user experience

### 🎯 Objectives
- [ ] Design system consolidation
- [ ] UX improvements
- [ ] Responsive design
- [ ] Accessibility compliance

### 👥 Responsible
- **Primary:** IA Beta
- **Support:** IA Charlie (testing)

### 📊 Estimate
- **Total:** 30 story points
- **Sprint 5:** 30 story points

### 🏷️ Labels
- epic
- ui-ux
- frontend
- accessibility`,
    labels: ["epic", "ui-ux", "frontend", "accessibility"],
  },
  {
    title: "Quality & Testing Epic",
    body: `## 🛡️ Quality & Testing Epic

### 📋 Description
Comprehensive testing and quality assurance

### 🎯 Objectives
- [ ] Comprehensive testing
- [ ] Performance validation
- [ ] Production deployment
- [ ] Monitoring setup

### 👥 Responsible
- **Primary:** IA Charlie
- **Support:** IA Alpha (deployment)

### 📊 Estimate
- **Total:** 25 story points
- **Sprint 6:** 25 story points

### 🏷️ Labels
- epic
- quality
- testing
- deployment`,
    labels: ["epic", "quality", "testing", "deployment"],
  },
];

// Sprint Planning Issues
const sprintIssues = [
  {
    title: "Sprint 1: Foundation - Core Services Optimization",
    body: `## 🏗️ Sprint 1: Foundation - Core Services Optimization

### 📋 Sprint Goal
Optimize core services and backend architecture

### 🎯 Objectives
- [ ] Core services optimization
- [ ] Backend architecture improvements
- [ ] Performance monitoring setup
- [ ] Error tracking implementation

### 👥 Team Capacity
- **IA Alpha:** 20 story points (Backend, Performance)
- **IA Charlie:** 5 story points (Testing support)

### 📊 Sprint Metrics
- **Total Capacity:** 25 story points
- **Epic:** Foundation
- **Duration:** 2 weeks

### 🏷️ Labels
- epic
- foundation
- backend
- performance
- sprint-1`,
    labels: ["epic", "foundation", "backend", "performance", "sprint-1"],
  },
  {
    title: "Sprint 2: Foundation - Performance & Security",
    body: `## 🚀 Sprint 2: Foundation - Performance & Security

### 📋 Sprint Goal
Implement performance monitoring and security improvements

### 🎯 Objectives
- [ ] Performance monitoring implementation
- [ ] Security improvements
- [ ] Error tracking setup
- [ ] Database optimization

### 👥 Team Capacity
- **IA Alpha:** 20 story points (Performance, Security)
- **IA Charlie:** 5 story points (Testing support)

### 📊 Sprint Metrics
- **Total Capacity:** 25 story points
- **Epic:** Foundation
- **Duration:** 2 weeks

### 🏷️ Labels
- epic
- foundation
- backend
- performance
- security
- sprint-2`,
    labels: [
      "epic",
      "foundation",
      "backend",
      "performance",
      "security",
      "sprint-2",
    ],
  },
  {
    title: "Sprint 5: UI/UX Enhancement",
    body: `## 🎨 Sprint 5: UI/UX Enhancement

### 📋 Sprint Goal
Improve frontend components and user experience

### 🎯 Objectives
- [ ] Design system consolidation
- [ ] UX improvements
- [ ] Responsive design
- [ ] Accessibility compliance

### 👥 Team Capacity
- **IA Beta:** 20 story points (Frontend, UX)
- **IA Charlie:** 5 story points (Testing support)

### 📊 Sprint Metrics
- **Total Capacity:** 25 story points
- **Epic:** UI/UX Enhancement
- **Duration:** 2 weeks

### 🏷️ Labels
- epic
- ui-ux
- frontend
- accessibility
- sprint-5`,
    labels: ["epic", "ui-ux", "frontend", "accessibility", "sprint-5"],
  },
  {
    title: "Sprint 6: Quality & Deployment",
    body: `## 🛡️ Sprint 6: Quality & Deployment

### 📋 Sprint Goal
Comprehensive testing and production deployment

### 🎯 Objectives
- [ ] Comprehensive testing
- [ ] Performance validation
- [ ] Production deployment
- [ ] Monitoring setup

### 👥 Team Capacity
- **IA Charlie:** 15 story points (Testing, Quality)
- **IA Alpha:** 5 story points (Deployment support)

### 📊 Sprint Metrics
- **Total Capacity:** 20 story points
- **Epic:** Quality & Testing
- **Duration:** 2 weeks

### 🏷️ Labels
- epic
- quality
- testing
- deployment
- sprint-6`,
    labels: ["epic", "quality", "testing", "deployment", "sprint-6"],
  },
];

// Main setup function
async function setupZenHubWithGitHubAPI() {
  log.title("ZenHub GitHub API Setup Script - V9.0");
  log.info("Configurando ZenHub via GitHub API...\n");

  // Check if GitHub token is available
  if (!GITHUB_TOKEN) {
    log.error("GitHub token não encontrado. Configure a variável GITHUB_TOKEN");
    log.info("Para configurar o token:");
    log.info("1. Acesse https://github.com/settings/tokens");
    log.info("2. Crie um token com permissões: repo, issues");
    log.info("3. Configure: export GITHUB_TOKEN=seu_token");
    process.exit(1);
  }

  try {
    // 1. Create labels
    log.info("1. Criando labels no GitHub...");
    const createdLabels = [];
    for (const label of zenhubLabels) {
      try {
        const result = await createLabel(label);
        createdLabels.push(result);
        log.success(`Label criada: ${label.name}`);
      } catch (error) {
        if (error.message.includes("already exists")) {
          log.warning(`Label já existe: ${label.name}`);
        } else {
          log.error(`Erro ao criar label ${label.name}: ${error.message}`);
        }
      }
    }
    log.success(`Labels criadas: ${createdLabels.length}`);

    // 2. Create epic issues
    log.info("2. Criando epics...");
    const createdEpics = [];
    for (const epic of epicTemplates) {
      try {
        const result = await createIssue(epic);
        createdEpics.push(result);
        log.success(`Epic criada: ${epic.title}`);
      } catch (error) {
        log.error(`Erro ao criar epic ${epic.title}: ${error.message}`);
      }
    }
    log.success(`Epics criadas: ${createdEpics.length}`);

    // 3. Create sprint planning issues
    log.info("3. Criando issues de sprint planning...");
    const createdSprints = [];
    for (const sprint of sprintIssues) {
      try {
        const result = await createIssue(sprint);
        createdSprints.push(result);
        log.success(`Sprint issue criada: ${sprint.title}`);
      } catch (error) {
        log.error(
          `Erro ao criar sprint issue ${sprint.title}: ${error.message}`
        );
      }
    }
    log.success(`Sprint issues criadas: ${createdSprints.length}`);

    // 4. Generate final report
    log.info("4. Gerando relatório final...");
    await generateFinalReport(createdLabels, createdEpics, createdSprints);
    log.success("Relatório final gerado");

    log.success("\n🎉 ZenHub GitHub API Setup concluído com sucesso!");
    log.info("Próximos passos:");
    log.info("1. Configure os pipelines no ZenHub");
    log.info("2. Organize as issues nos sprints");
    log.info("3. Inicie o desenvolvimento V9.0");
  } catch (error) {
    log.error(`Erro durante setup: ${error.message}`);
    process.exit(1);
  }
}

// Generate final report
async function generateFinalReport(labels, epics, sprints) {
  const report = `# 🚀 ZenHub GitHub API Setup Report - V9.0

## 📊 Setup Summary

### ✅ Labels Created (${labels.length})
${labels.map((label) => `- ${label.name} (${label.color})`).join("\n")}

### ✅ Epics Created (${epics.length})
${epics.map((epic) => `- ${epic.title} (#${epic.number})`).join("\n")}

### ✅ Sprint Issues Created (${sprints.length})
${sprints.map((sprint) => `- ${sprint.title} (#${sprint.number})`).join("\n")}

## 🎯 Next Steps

### 1. Configure ZenHub Pipelines
- Main Pipeline: Backlog → Sprint Planning → In Progress → Ready for Deploy → Deployed
- Wireframe Pipeline: Wireframe Backlog → Wireframe Development → Wireframe Review → Wireframe Approved → Implementation Ready

### 2. Organize Issues
- Move epics to appropriate pipelines
- Assign issues to sprints
- Set up team capacity planning

### 3. Start Development
- Begin with Sprint 1: Foundation
- Follow V9.0 methodology
- Track progress via ZenHub

## 📊 Team Assignment Matrix

| Issue Type | IA Alpha | IA Beta | IA Charlie |
|------------|----------|---------|------------|
| Backend | ✅ Primary | ❌ | 🔄 Support |
| Frontend | ❌ | ✅ Primary | 🔄 Support |
| Testing | 🔄 Support | 🔄 Support | ✅ Primary |
| Performance | ✅ Primary | ❌ | 🔄 Support |
| UX/UI | ❌ | ✅ Primary | 🔄 Support |
| Security | ✅ Primary | ❌ | 🔄 Support |
| Deployment | ✅ Primary | ❌ | ✅ Primary |

## 🚀 V9.0 Methodology Ready

The ZenHub setup is complete and ready for V9.0 methodology implementation.

## 🔗 GitHub Issues Created

### Epics
${epics.map((epic) => `- [${epic.title}](${epic.html_url})`).join("\n")}

### Sprint Planning
${sprints.map((sprint) => `- [${sprint.title}](${sprint.html_url})`).join("\n")}
`;

  fs.writeFileSync(
    path.join(__dirname, "../zenhub/reports/ZENHUB-GITHUB-API-REPORT.md"),
    report
  );
  log.success(
    "Relatório final salvo em docs/zenhub/reports/ZENHUB-GITHUB-API-REPORT.md"
  );
}

// Run setup if called directly
if (import.meta.url === `file://${process.argv[1]}`) {
  setupZenHubWithGitHubAPI();
}

export { createIssue, createLabel, setupZenHubWithGitHubAPI };
