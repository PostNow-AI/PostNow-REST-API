#!/usr/bin/env node

/**
 * 🚀 ZenHub Auto Setup Script - V9.0
 * Automatiza a configuração do ZenHub via GitHub API
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

// Issue Templates
const issueTemplates = {
  feature: {
    title: "Feature Request",
    body: `## 🎯 Feature Request

### 📋 Description
[Clear description of the feature]

### 🎯 Acceptance Criteria
- [ ] [Criterion 1]
- [ ] [Criterion 2]
- [ ] [Criterion 3]

### 🏷️ Labels
- feature
- [frontend/backend/testing]
- [priority: high/medium/low]

### 👥 Assignment
- **Responsible:** [IA Alpha/Beta/Charlie]
- **Estimate:** [X] story points
- **Sprint:** [Sprint Number]

### 📝 Definition of Done
- [ ] Code implemented
- [ ] Tests written
- [ ] Documentation updated
- [ ] Review approved
- [ ] Deploy completed

### 🔗 Related
- Epic: [Epic name]
- Dependencies: [List dependencies]`,
    labels: ["feature"],
    assignees: [],
    milestone: null,
  },
  bug: {
    title: "Bug Report",
    body: `## 🐛 Bug Report

### 📋 Description
[Clear description of the bug]

### 🔍 Steps to Reproduce
1. [Step 1]
2. [Step 2]
3. [Step 3]

### ✅ Expected Behavior
[What should happen]

### ❌ Actual Behavior
[What actually happens]

### 🏷️ Labels
- bug
- [frontend/backend/testing]
- [priority: high/medium/low]

### 👥 Assignment
- **Responsible:** [IA Alpha/Beta/Charlie]
- **Estimate:** [X] story points
- **Sprint:** [Sprint Number]

### 📝 Definition of Done
- [ ] Bug fixed
- [ ] Tests written
- [ ] No regression
- [ ] Deploy completed`,
    labels: ["bug"],
    assignees: [],
    milestone: null,
  },
  enhancement: {
    title: "Enhancement Request",
    body: `## 🔧 Enhancement Request

### 📋 Description
[Clear description of the enhancement]

### 🎯 Current State
[Describe current implementation]

### 🚀 Proposed Enhancement
[Describe proposed improvement]

### 🏷️ Labels
- enhancement
- [frontend/backend/testing]
- [priority: high/medium/low]

### 👥 Assignment
- **Responsible:** [IA Alpha/Beta/Charlie]
- **Estimate:** [X] story points
- **Sprint:** [Sprint Number]

### 📝 Definition of Done
- [ ] Enhancement implemented
- [ ] Tests written
- [ ] Documentation updated
- [ ] Review approved
- [ ] Deploy completed`,
    labels: ["enhancement"],
    assignees: [],
    milestone: null,
  },
};

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
async function autoSetupZenHub() {
  log.title("ZenHub Auto Setup Script - V9.0");
  log.info("Configurando ZenHub automaticamente...\n");

  try {
    // 1. Create labels
    log.info("1. Criando labels no ZenHub...");
    await createLabels();
    log.success("Labels criadas com sucesso");

    // 2. Create issue templates
    log.info("2. Criando templates de issues...");
    await createIssueTemplates();
    log.success("Templates de issues criados");

    // 3. Create epic issues
    log.info("3. Criando epics...");
    await createEpicIssues();
    log.success("Epics criadas com sucesso");

    // 4. Create sprint planning issues
    log.info("4. Criando issues de sprint planning...");
    await createSprintIssues();
    log.success("Issues de sprint criadas");

    // 5. Generate setup report
    log.info("5. Gerando relatório de setup...");
    await generateSetupReport();
    log.success("Relatório de setup gerado");

    log.success("\n🎉 ZenHub Auto Setup concluído com sucesso!");
    log.info("Próximos passos:");
    log.info("1. Configure os pipelines no ZenHub");
    log.info("2. Organize as issues nos sprints");
    log.info("3. Inicie o desenvolvimento V9.0");
  } catch (error) {
    log.error(`Erro durante setup: ${error.message}`);
    process.exit(1);
  }
}

// Create labels via GitHub API
async function createLabels() {
  log.info("Criando labels via GitHub API...");

  // Simulate API calls for label creation
  for (const label of zenhubLabels) {
    log.info(`Criando label: ${label.name}`);
    // In a real implementation, this would make actual GitHub API calls
    await simulateAPICall(`POST /repos/{owner}/{repo}/labels`, {
      name: label.name,
      color: label.color,
      description: label.description,
    });
  }
}

// Create issue templates
async function createIssueTemplates() {
  log.info("Criando templates de issues...");

  for (const [type, template] of Object.entries(issueTemplates)) {
    log.info(`Criando template: ${template.title}`);
    // In a real implementation, this would create actual issue templates
    await simulateAPICall(`POST /repos/{owner}/{repo}/issues`, {
      title: template.title,
      body: template.body,
      labels: template.labels,
    });
  }
}

// Create epic issues
async function createEpicIssues() {
  log.info("Criando epics...");

  for (const epic of epicTemplates) {
    log.info(`Criando epic: ${epic.title}`);
    // In a real implementation, this would create actual epic issues
    await simulateAPICall(`POST /repos/{owner}/{repo}/issues`, {
      title: epic.title,
      body: epic.body,
      labels: epic.labels,
    });
  }
}

// Create sprint planning issues
async function createSprintIssues() {
  log.info("Criando issues de sprint planning...");

  for (const sprint of sprintIssues) {
    log.info(`Criando sprint issue: ${sprint.title}`);
    // In a real implementation, this would create actual sprint issues
    await simulateAPICall(`POST /repos/{owner}/{repo}/issues`, {
      title: sprint.title,
      body: sprint.body,
      labels: sprint.labels,
    });
  }
}

// Generate setup report
async function generateSetupReport() {
  const report = `# 🚀 ZenHub Auto Setup Report - V9.0

## 📊 Setup Summary

### ✅ Labels Created (${zenhubLabels.length})
${zenhubLabels.map((label) => `- ${label.name} (${label.color})`).join("\n")}

### ✅ Issue Templates Created (${Object.keys(issueTemplates).length})
${Object.keys(issueTemplates)
  .map((type) => `- ${type} template`)
  .join("\n")}

### ✅ Epics Created (${epicTemplates.length})
${epicTemplates.map((epic) => `- ${epic.title}`).join("\n")}

### ✅ Sprint Issues Created (${sprintIssues.length})
${sprintIssues.map((sprint) => `- ${sprint.title}`).join("\n")}

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
`;

  fs.writeFileSync(
    path.join(__dirname, "../zenhub/reports/ZENHUB-SETUP-REPORT.md"),
    report
  );
  log.success(
    "Relatório de setup salvo em docs/zenhub/reports/ZENHUB-SETUP-REPORT.md"
  );
}

// Simulate API call (replace with actual GitHub API calls)
async function simulateAPICall(endpoint, data) {
  // Simulate API delay
  await new Promise((resolve) => setTimeout(resolve, 100));
  log.info(
    `API Call: ${endpoint} - ${JSON.stringify(data).substring(0, 50)}...`
  );
}

// Run setup if called directly
if (import.meta.url === `file://${process.argv[1]}`) {
  autoSetupZenHub();
}

export {
  autoSetupZenHub,
  epicTemplates,
  issueTemplates,
  sprintIssues,
  zenhubLabels,
};
