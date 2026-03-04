---
name: postnow-docs
description: Atualiza documentação existente. NÃO cria docs por PR/bugfix. Use para manter docs organizados.
argument-hint: <funcionalidade>
disable-model-invocation: true
allowed-tools: Read, Edit, Write, Grep, Glob
---

# PostNow Docs

Gerencio documentação seguindo as regras do CTO: atualizar existente, não criar por PR.

## Argumentos

`$ARGUMENTS` - Nome da funcionalidade a documentar

Exemplo: `/postnow-docs authentication`

## Regras de Ouro

### NUNCA fazer
- Criar `docs/PR12_fix.md`
- Criar `docs/FIX_bug_email.md`
- Criar `docs/UPDATE_login.md`
- Documentar cada bugfix separadamente

### SEMPRE fazer
- Buscar doc existente da funcionalidade
- Atualizar seções relevantes
- Manter documentação concisa
- Só criar novo doc para feature completamente nova

## Processo

1. **Busco** documentação existente para `$ARGUMENTS`:
   - `docs/`
   - `README.md`
   - Docstrings no código

2. **Se encontrar**: Atualizo seção relevante

3. **Se não encontrar**: Crio doc geral da feature (não do PR)

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

Só uso se não existir doc da funcionalidade:

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
```

## Verificação

Antes de finalizar, confirmo:
- [ ] Nome do arquivo NÃO contém PR/FIX/UPDATE
- [ ] Atualizei doc existente (se havia)
- [ ] Documentação é concisa
