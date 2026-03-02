# Correção de Registros SPF - postnow.com.br

## Problema Identificado

O domínio `postnow.com.br` possui **dois registros SPF separados**, o que é inválido conforme RFC 7208.

### Situação Atual (Incorreta)
```
TXT: "v=spf1 include:spf.umbler.com ~all"
TXT: "v=spf1 include:spf.mailjet.com ?all"
```

### Problema
- O padrão SPF permite apenas **UM registro** por domínio
- Ter múltiplos registros causa falha na validação SPF
- Pode afetar a entregabilidade de emails a longo prazo

## Solução

Unificar os dois registros em **um único registro** que inclua ambos os serviços.

### Registro SPF Correto
```
v=spf1 include:spf.umbler.com include:spf.mailjet.com ~all
```

## Serviços Afetados

| Serviço | Função | Necessário? |
|---------|--------|-------------|
| **Umbler** | Hospedagem de caixas de email @postnow.com.br | Sim |
| **Mailjet** | Envio de emails transacionais do sistema PostNow | Sim |

## Passos para Correção

### 1. Acessar o Painel DNS

O DNS do domínio postnow.com.br está gerenciado em um dos seguintes locais:
- Registro.br
- Umbler
- Outro provedor de DNS

### 2. Localizar Registros TXT

Buscar por registros do tipo **TXT** que contenham `v=spf1`.

### 3. Remover Registros Antigos

Deletar os dois registros SPF existentes:
- `v=spf1 include:spf.umbler.com ~all`
- `v=spf1 include:spf.mailjet.com ?all`

### 4. Adicionar Novo Registro Unificado

Criar um novo registro TXT:

| Campo | Valor |
|-------|-------|
| **Tipo** | TXT |
| **Nome/Host** | @ (ou deixar vazio, dependendo do provedor) |
| **Valor** | `v=spf1 include:spf.umbler.com include:spf.mailjet.com ~all` |
| **TTL** | 3600 (ou padrão) |

### 5. Aguardar Propagação DNS

- A propagação pode levar de 1 a 48 horas
- Geralmente completa em 1-2 horas

### 6. Verificar no Mailjet

Após propagação, forçar verificação no Mailjet:

```bash
# Via API
curl -X POST "https://api.mailjet.com/v3/REST/dns/4759250023/check" \
  -u "$MJ_APIKEY_PUBLIC:$MJ_APIKEY_PRIVATE"
```

Ou acessar: Dashboard Mailjet → Sender domains → postnow.com.br → Check DNS

## Verificação

### Comando para verificar SPF atual:
```bash
dig postnow.com.br TXT +short
```

### Resultado esperado após correção:
```
"v=spf1 include:spf.umbler.com include:spf.mailjet.com ~all"
```

Deve haver apenas **UMA** linha com `v=spf1`.

## Impacto

### Durante a correção
- Nenhum downtime esperado
- Emails continuarão sendo enviados normalmente

### Após a correção
- Melhor taxa de entrega de emails
- Validação SPF correta em todos os servidores de destino
- Score de reputação melhorado

## Referências

- [RFC 7208 - SPF](https://tools.ietf.org/html/rfc7208)
- [Documentação Mailjet - SPF](https://documentation.mailjet.com/hc/en-us/articles/360042412734)
- [Documentação Umbler - SPF](https://help.umbler.com/hc/pt-br/articles/210313303)

---

**Data da análise:** 2026-02-27
**Status:** Pendente de correção
**Prioridade:** Média (sistema funcionando, mas com configuração subótima)
