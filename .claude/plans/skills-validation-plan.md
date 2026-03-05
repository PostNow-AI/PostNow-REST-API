# Plano de Validação Completa - Skills PostNow

**Data:** 2026-03-04
**PR:** #45
**Branch:** fix/email-template-bugs

---

## Fase 1: Testes das Skills (Pendente)

### 1.1 Testar `/postnow-review` ✅ CONCLUÍDO
- [x] Executar skill em arquivo real
- [x] Verificar detecção de problemas
- [x] Corrigir problemas encontrados
- [x] Re-executar para confirmar correções

### 1.2 Testar `/postnow-extract`
- [ ] Identificar função candidata para extração
- [ ] Executar `/postnow-extract <função> utils`
- [ ] Verificar que função foi movida corretamente
- [ ] Verificar que imports foram atualizados
- [ ] Executar `/postnow-review` para validar resultado

### 1.3 Testar `/postnow-imports`
- [ ] Identificar arquivo com imports desorganizados
- [ ] Executar `/postnow-imports <arquivo>`
- [ ] Verificar ordenação (stdlib → Django → third-party → local)
- [ ] Verificar remoção de imports não utilizados
- [ ] Confirmar que código ainda funciona

### 1.4 Testar `/postnow-docs`
- [ ] Escolher funcionalidade para documentar
- [ ] Executar `/postnow-docs <funcionalidade>`
- [ ] Verificar que NÃO criou doc por PR/FIX
- [ ] Verificar que atualizou doc existente (ou criou doc geral)

---

## Fase 2: Testes Unitários

### 2.1 Testes para `batch_validation.py`
- [ ] Criar `/tmp/PostNow-REST-API/ClientContext/tests/test_batch_validation.py`
- [ ] Testar `validate_batch_token()` com token válido
- [ ] Testar `validate_batch_token()` com token inválido
- [ ] Testar `validate_batch_token()` sem token configurado
- [ ] Testar `validate_batch_number()` com valores válidos
- [ ] Testar `validate_batch_number()` com valores inválidos
- [ ] Testar `validate_batch_number()` com valores limite

### 2.2 Executar Testes
- [ ] Rodar `pytest ClientContext/tests/test_batch_validation.py`
- [ ] Verificar cobertura de código
- [ ] Corrigir falhas se houver

---

## Fase 3: Testes de Integração

### 3.1 Verificar E-mails
- [ ] Testar envio de e-mail de oportunidades
- [ ] Verificar nome do usuário (não "Usuário")
- [ ] Verificar ano no footer (2026)
- [ ] Verificar formatação de listas (não JSON)

### 3.2 Verificar Views Refatoradas
- [ ] Testar endpoint `/client-context/generate/`
- [ ] Verificar que autenticação funciona
- [ ] Verificar que validação de batch funciona

---

## Fase 4: Documentação

### 4.1 Guia de Uso das Skills
- [ ] Criar `docs/claude_skills_guide.md`
- [ ] Documentar cada skill com exemplos
- [ ] Incluir fluxo de trabalho recomendado
- [ ] Adicionar troubleshooting

### 4.2 Atualizar README do Projeto
- [ ] Mencionar skills disponíveis
- [ ] Link para guia de uso

---

## Fase 5: Code Review

### 5.1 Preparação
- [ ] Verificar que todos os testes passam
- [ ] Verificar que não há conflitos com main
- [ ] Revisar diff final do PR

### 5.2 Review do CTO
- [ ] Solicitar review de @MatheusBlanco
- [ ] Responder comentários
- [ ] Aplicar correções solicitadas

### 5.3 Merge
- [ ] Aprovar PR após review
- [ ] Fazer squash merge para main
- [ ] Deletar branch após merge

---

## Fase 6: Pós-Deploy

### 6.1 Validação em Produção
- [ ] Monitorar logs de erro
- [ ] Verificar e-mails em produção
- [ ] Confirmar que skills funcionam no projeto

### 6.2 Comunicação
- [ ] Notificar equipe sobre novas skills
- [ ] Compartilhar guia de uso

---

## Resumo de Prioridades

| Prioridade | Fase | Esforço |
|:----------:|------|:-------:|
| 🔴 Alta | 2.1 Testes unitários | Médio |
| 🔴 Alta | 5.2 Review do CTO | Baixo |
| 🟡 Média | 1.2-1.4 Testar outras skills | Médio |
| 🟡 Média | 3.1-3.2 Testes integração | Médio |
| 🟢 Baixa | 4.1-4.2 Documentação | Baixo |
| 🟢 Baixa | 6.1-6.2 Pós-deploy | Baixo |

---

## Critérios de Conclusão

- [ ] Todas as skills testadas e funcionando
- [ ] Testes unitários com >80% cobertura
- [ ] Nenhum bug crítico aberto
- [ ] PR aprovado pelo CTO
- [ ] Documentação atualizada
