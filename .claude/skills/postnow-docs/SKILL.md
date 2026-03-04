---
name: postnow-docs
description: Atualiza documentação existente. NÃO cria docs por PR/bugfix. Use para manter docs organizados.
argument-hint: [funcionalidade]
---

# PostNow Docs

Gerencio documentação seguindo as regras do CTO: atualizar existente, não criar por PR.

## Como usar

```
/postnow-docs <funcionalidade>
```

Exemplos:
- `/postnow-docs authentication` - Atualiza doc de autenticação
- `/postnow-docs email` - Atualiza doc do sistema de email
- `/postnow-docs` - Analiso mudanças e sugiro onde documentar

## Regras de Ouro

### O que NUNCA fazer
- Criar `docs/PR12_fix.md`
- Criar `docs/FIX_bug_email.md`
- Criar `docs/UPDATE_login.md`
- Documentar cada bugfix separadamente

### O que SEMPRE fazer
- Buscar doc existente da funcionalidade
- Atualizar seções relevantes
- Manter documentação concisa
- Só criar novo doc para feature completamente nova

## Processo

1. **Identifico** a funcionalidade afetada
2. **Busco** documentação existente em:
   - `docs/`
   - `README.md`
   - Docstrings no código
3. **Atualizo** seção relevante
4. **Se não existir**, crio doc geral da feature (não do PR)

## Estrutura de Docs

```
docs/
├── README.md           # Índice geral
├── authentication.md   # Sistema de auth
├── email_system.md     # Sistema de email
├── api_endpoints.md    # Endpoints da API
└── visual_styles.md    # Estilos visuais
```

## Template para Nova Feature

Só use se não existir doc da funcionalidade:

```markdown
# [Nome da Funcionalidade]

## Visão Geral
Breve descrição do que faz.

## Como Usar
Instruções de uso.

## Configuração
Variáveis de ambiente, settings, etc.

## Arquivos Relacionados
- `app/views.py` - Endpoints
- `app/services/` - Lógica

## Exemplos
Exemplos de uso.
```

## Exemplos

### Cenário 1: Bugfix em autenticação

**Errado:**
```
Criar docs/FIX_login_bug.md
```

**Certo:**
```
Atualizar docs/authentication.md seção "Problemas Conhecidos"
```

### Cenário 2: Nova feature de relatórios

**Certo:**
```
Criar docs/reports.md (doc geral da feature)
```

### Cenário 3: Melhoria em email existente

**Errado:**
```
Criar docs/PR40_email_improvements.md
```

**Certo:**
```
Atualizar docs/email_system.md
```

## Checklist

Antes de documentar:
- [ ] Busquei doc existente?
- [ ] Estou atualizando ao invés de criar novo?
- [ ] O nome do arquivo NÃO contém PR/FIX/UPDATE?
- [ ] A documentação é concisa?
