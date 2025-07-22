#!/usr/bin/env node

/**
 * 🚀 ZenHub Setup Script - V9.0
 * Automatiza a configuração do ZenHub para o projeto Sonora UI
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

// ZenHub Configuration
const zenhubConfig = {
  labels: [
    // Type Labels
    { name: "feature", color: "0e8a16", description: "Novas funcionalidades" },
    { name: "bug", color: "d93f0b", description: "Correções de bugs" },
    { name: "enhancement", color: "1d76db", description: "Melhorias" },
    { name: "documentation", color: "0075ca", description: "Documentação" },
    { name: "testing", color: "fef2c0", description: "Testes" },
    { name: "deployment", color: "5319e7", description: "Deploy" },

    // Priority Labels
    { name: "priority:high", color: "d93f0b", description: "Alta prioridade" },
    {
      name: "priority:medium",
      color: "fef2c0",
      description: "Média prioridade",
    },
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
    {
      name: "wireframe",
      color: "1d76db",
      description: "Wireframe development",
    },
    {
      name: "approved",
      color: "0e8a16",
      description: "Approved for implementation",
    },
    { name: "implementation", color: "5319e7", description: "Live component" },
    { name: "blocked", color: "d93f0b", description: "Blocked by dependency" },
  ],

  pipelines: [
    {
      name: "Main Pipeline",
      columns: [
        { name: "Backlog", position: 0 },
        { name: "Sprint Planning", position: 1 },
        { name: "In Progress", position: 2 },
        { name: "Development", position: 3 },
        { name: "Testing", position: 4 },
        { name: "Review", position: 5 },
        { name: "Ready for Deploy", position: 6 },
        { name: "Deployed", position: 7 },
      ],
    },
    {
      name: "Wireframe Pipeline",
      columns: [
        { name: "Wireframe Backlog", position: 0 },
        { name: "Wireframe Development", position: 1 },
        { name: "Wireframe Review", position: 2 },
        { name: "Wireframe Approved", position: 3 },
        { name: "Implementation Ready", position: 4 },
      ],
    },
  ],

  automationRules: {
    autoAssignment: {
      backend: "IA Alpha",
      performance: "IA Alpha",
      architecture: "IA Alpha",
      frontend: "IA Beta",
      ux: "IA Beta",
      components: "IA Beta",
      testing: "IA Charlie",
      "ci-cd": "IA Charlie",
      quality: "IA Charlie",
    },
    autoLabeling: {
      frontend: ["frontend", "ux"],
      backend: ["backend", "performance"],
      testing: ["testing", "quality"],
    },
  },
};

// Sprint Templates
const sprintTemplates = [
  {
    name: "Sprint 1-2: Foundation",
    goal: "Core infrastructure and backend improvements",
    capacity: {
      "IA Alpha": 20, // story points
      "IA Beta": 0, // story points
      "IA Charlie": 5, // story points
    },
    epics: ["Foundation"],
    labels: ["foundation", "backend", "performance"],
  },
  {
    name: "Sprint 3-4: Service Integration",
    goal: "API integration and database optimization",
    capacity: {
      "IA Alpha": 20, // story points
      "IA Beta": 0, // story points
      "IA Charlie": 5, // story points
    },
    epics: ["Foundation"],
    labels: ["backend", "api", "database"],
  },
  {
    name: "Sprint 5: Component Enhancement",
    goal: "Frontend improvements and user experience",
    capacity: {
      "IA Alpha": 0, // story points
      "IA Beta": 20, // story points
      "IA Charlie": 5, // story points
    },
    epics: ["UI/UX Enhancement"],
    labels: ["frontend", "ux", "components"],
  },
  {
    name: "Sprint 6: Quality & Deployment",
    goal: "Comprehensive testing and production deployment",
    capacity: {
      "IA Alpha": 5, // story points
      "IA Beta": 0, // story points
      "IA Charlie": 15, // story points
    },
    epics: ["Quality & Testing"],
    labels: ["testing", "quality", "deployment"],
  },
];

// Epic Templates
const epicTemplates = [
  {
    name: "Foundation",
    description: "Core infrastructure and backend improvements",
    objectives: [
      "Core services optimization",
      "Backend architecture improvements",
      "Performance monitoring setup",
      "Error tracking implementation",
    ],
    responsible: {
      primary: "IA Alpha",
      support: "IA Charlie",
    },
    estimate: {
      total: 40,
      sprint1: 20,
      sprint2: 20,
    },
    labels: ["epic", "foundation", "backend", "performance"],
  },
  {
    name: "UI/UX Enhancement",
    description: "Frontend improvements and user experience",
    objectives: [
      "Design system consolidation",
      "UX improvements",
      "Responsive design",
      "Accessibility compliance",
    ],
    responsible: {
      primary: "IA Beta",
      support: "IA Charlie",
    },
    estimate: {
      total: 30,
      sprint5: 30,
    },
    labels: ["epic", "ui-ux", "frontend", "accessibility"],
  },
  {
    name: "Quality & Testing",
    description: "Comprehensive testing and quality assurance",
    objectives: [
      "Comprehensive testing",
      "Performance validation",
      "Production deployment",
      "Monitoring setup",
    ],
    responsible: {
      primary: "IA Charlie",
      support: "IA Alpha",
    },
    estimate: {
      total: 25,
      sprint6: 25,
    },
    labels: ["epic", "quality", "testing", "deployment"],
  },
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

// Main setup function
async function setupZenHub() {
  log.title("ZenHub Setup Script - V9.0");
  log.info("Configurando ZenHub para Sonora UI...\n");

  try {
    // 1. Validate project structure
    log.info("1. Validando estrutura do projeto...");
    await validateProjectStructure();
    log.success("Estrutura do projeto validada");

    // 2. Generate configuration files
    log.info("2. Gerando arquivos de configuração...");
    await generateConfigFiles();
    log.success("Arquivos de configuração gerados");

    // 3. Create setup instructions
    log.info("3. Criando instruções de setup...");
    await createSetupInstructions();
    log.success("Instruções de setup criadas");

    // 4. Generate issue templates
    log.info("4. Gerando templates de issues...");
    await generateIssueTemplates();
    log.success("Templates de issues gerados");

    log.success("\n🎉 ZenHub Setup concluído com sucesso!");
    log.info("Próximos passos:");
    log.info("1. Acesse o ZenHub e conecte este repositório");
    log.info("2. Configure os pipelines conforme zenhub-config.md");
    log.info("3. Crie as labels listadas no arquivo");
    log.info("4. Configure os templates de issues");
    log.info("5. Inicie o primeiro sprint");
  } catch (error) {
    log.error(`Erro durante setup: ${error.message}`);
    process.exit(1);
  }
}

// Validate project structure
async function validateProjectStructure() {
  const requiredFiles = [
    "docs/methodologies/V8.md",
    "docs/methodologies/V9.md",
  ];

  for (const file of requiredFiles) {
    if (!fs.existsSync(file)) {
      throw new Error(`Arquivo obrigatório não encontrado: ${file}`);
    }
  }
}

// Generate configuration files
async function generateConfigFiles() {
  const configDir = path.join(__dirname, "../zenhub/templates");

  // Create config directory
  if (!fs.existsSync(configDir)) {
    fs.mkdirSync(configDir, { recursive: true });
  }

  // Generate labels configuration
  const labelsConfig = {
    labels: zenhubConfig.labels,
    assignmentRules: zenhubConfig.automationRules.autoAssignment,
    autoLabeling: zenhubConfig.automationRules.autoLabeling,
  };

  fs.writeFileSync(
    path.join(configDir, "labels.json"),
    JSON.stringify(labelsConfig, null, 2)
  );

  // Generate pipeline configuration
  const pipelineConfig = {
    pipelines: zenhubConfig.pipelines,
    automationRules: zenhubConfig.automationRules,
  };

  fs.writeFileSync(
    path.join(configDir, "pipelines.json"),
    JSON.stringify(pipelineConfig, null, 2)
  );

  // Generate sprint templates
  fs.writeFileSync(
    path.join(configDir, "sprint-templates.json"),
    JSON.stringify(sprintTemplates, null, 2)
  );

  // Generate epic templates
  fs.writeFileSync(
    path.join(configDir, "epic-templates.json"),
    JSON.stringify(epicTemplates, null, 2)
  );
}

// Create setup instructions
async function createSetupInstructions() {
  const instructions = `# 🚀 ZenHub Setup Instructions

## 📋 Setup Checklist

### ✅ ZenHub Configuration
- [ ] Connect repository to ZenHub
- [ ] Configure custom pipelines (see docs/zenhub/templates/pipelines.json)
- [ ] Create all labels (see docs/zenhub/templates/labels.json)
- [ ] Set up auto-assignment rules
- [ ] Configure sprint templates (see docs/zenhub/templates/sprint-templates.json)
- [ ] Set up epic templates (see docs/zenhub/templates/epic-templates.json)
- [ ] Configure issue templates (see docs/zenhub/templates/issue-templates/)
- [ ] Set up analytics tracking

### ✅ Team Setup
- [ ] Assign IA Alpha responsibilities (backend, performance, security)
- [ ] Assign IA Beta responsibilities (frontend, ux, components)
- [ ] Assign IA Charlie responsibilities (testing, quality, documentation)
- [ ] Configure capacity planning
- [ ] Set up communication protocols

### ✅ Workflow Setup
- [ ] Configure main pipeline
- [ ] Configure wireframe pipeline
- [ ] Set up quality gates
- [ ] Configure automation rules
- [ ] Set up reporting templates

## 🎯 First Sprint Setup

1. Create Sprint 1: Foundation
2. Assign IA Alpha to backend issues
3. Set capacity: IA Alpha (20 SP), IA Charlie (5 SP)
4. Move issues to Sprint Planning
5. Start development

## 📊 Success Metrics

- Velocity: 20+ story points per sprint
- Quality: >90% code coverage, <5% bug rate
- Performance: <3s load time
- Coordination: 0 conflicts, smooth handoffs

## 🚨 Emergency Protocols

- If conflict detected: Stop work, comment in ZenHub, move to "Blocked"
- If system breaks: Rollback, create bug issue, coordinate fix
- If blocked: Update issue status, communicate with team

## 📞 Support

- Check docs/methodologies/V9.md for full methodology
- Check docs/zenhub/config/zenhub-config.md for detailed configuration
- Use docs/zenhub/templates/ directory for templates and configs
`;

  fs.writeFileSync(
    path.join(__dirname, "../zenhub/templates/SETUP_INSTRUCTIONS.md"),
    instructions
  );
}

// Generate issue templates
async function generateIssueTemplates() {
  const templatesDir = path.join(
    __dirname,
    "../zenhub/templates/issue-templates"
  );

  if (!fs.existsSync(templatesDir)) {
    fs.mkdirSync(templatesDir, { recursive: true });
  }

  for (const [type, template] of Object.entries(issueTemplates)) {
    const templateContent = {
      name: template.title,
      description: `Template for ${type} issues`,
      title: template.title,
      body: template.body,
      labels: [type],
      assignees: [],
      milestone: null,
    };

    fs.writeFileSync(
      path.join(templatesDir, `${type}.json`),
      JSON.stringify(templateContent, null, 2)
    );
  }
}

// Run setup if called directly
if (import.meta.url === `file://${process.argv[1]}`) {
  setupZenHub();
}

export { epicTemplates, setupZenHub, sprintTemplates, zenhubConfig };
