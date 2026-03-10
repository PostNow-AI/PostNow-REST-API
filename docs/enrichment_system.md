# Sistema de Enrichment de Contexto

**Última atualização:** 2026-03-09
**Status:** Produção

---

## Visão Geral

Sistema de enriquecimento de contexto em duas fases que gera e-mails semanais com oportunidades de conteúdo e inteligência de mercado.

### Cronograma Semanal

| Dia | Horário (UTC) | Fase | Descrição |
|-----|---------------|------|-----------|
| Domingo | 06:00 | 1a | Gera contexto semanal (Gemini AI) |
| Domingo | 09:00 | 1b | Transforma em oportunidades ranqueadas |
| Segunda | 10:00 | 2a | Enriquece + envia e-mail de Oportunidades |
| Quarta | 10:00 | 2b | Enriquece + envia e-mail de Inteligência |

---

## Arquitetura de Busca

### Provedores

| Serviço | Função | Custo |
|---------|--------|-------|
| **Serper API** | Busca Google (resultados reais) | $1/1K queries (2.500 grátis/mês) |
| **Jina Reader** | Extrai conteúdo das páginas | Grátis (1M tokens/mês) |
| **SourceEvaluator** | Avalia relevância com IA | Usa Claude Haiku |

### Fluxo de Enrichment

```
1. Serper busca "tendências marketing digital Brasil 2026"
   → Retorna 10 links com snippets

2. source_quality.py filtra (remove spam, redes sociais, etc)
   → 6-8 links válidos

3. SourceEvaluatorService avalia relevância
   → Seleciona 3 melhores para o tipo de conteúdo

4. Jina Reader extrai conteúdo das 3 URLs
   → Markdown limpo de cada página

5. AI gera análise enriquecida
   → enriched_analysis para o usuário
```

### Sistema de Fallback (4 Estratégias)

Se a busca primária não encontrar 3 fontes:

| Estratégia | Descrição |
|------------|-----------|
| 1. Primária | News (newsjacking) ou Web (outros) |
| 2. Alternativa | Troca tipo: Web ↔ News |
| 3. Simplificada | Remove palavras clickbait da query |
| 4. Reformulação IA | Claude gera queries alternativas |

**Resultado:** 100% de sucesso em 17 cenários de teste.

---

## Variáveis de Ambiente

### Obrigatórias

| Variável | Descrição |
|----------|-----------|
| `CRON_SECRET` | Token de autenticação para endpoints batch |
| `API_BASE_URL` | URL base da API |
| `SERPER_API_KEY` | API key do Serper (serper.dev) |

### Opcionais

| Variável | Descrição | Default |
|----------|-----------|---------|
| `JINA_API_KEY` | API key do Jina (para rate limits maiores) | - |
| `ANTHROPIC_API_KEY` | Para SourceEvaluator e reformulação de queries | - |

### Configuração do Serper

1. Criar conta em [serper.dev](https://serper.dev)
2. Copiar API key do dashboard
3. Adicionar `SERPER_API_KEY` no Vercel/ambiente

**Custos estimados:**
- Free tier: 2.500 queries/mês (~104 usuários)
- 100 usuários: ~$2.40/mês

---

## Endpoints

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/client-context/generate-opportunities/` | GET | Gera oportunidades (Fase 1b) |
| `/client-context/enrich-and-send-opportunities-email/` | GET | Enriquece + envia segunda |
| `/client-context/send-market-intelligence-email/` | GET | Enriquece + envia quarta |

---

## Estrutura de Arquivos

```
services/
├── serper_search_service.py      # Busca no Google via Serper
├── jina_reader_service.py        # Extração de conteúdo
└── source_evaluator_service.py   # Avaliação com IA

ClientContext/
├── services/
│   ├── context_enrichment_service.py    # Orquestra enrichment
│   ├── opportunities_email_service.py   # E-mail de segunda
│   └── market_intelligence_*.py         # E-mail de quarta
├── utils/
│   ├── search_utils.py           # Pipeline de busca + fallbacks
│   ├── source_quality.py         # Scoring e filtros
│   ├── url_validation.py         # Validação de URLs
│   └── url_dedupe.py             # Deduplicação
```

---

## Tipos de Conteúdo

O sistema otimiza buscas por tipo:

| Tipo | API | Keywords |
|------|-----|----------|
| `polemica` | Web | debate, crítica, problema |
| `educativo` | Web | como, guia, tutorial |
| `newsjacking` | **News** | novo, anuncia, lança |
| `entretenimento` | Web | viral, meme, trend |
| `estudo_caso` | Web | case, sucesso, resultados |
| `futuro` | Web | tendência, previsão, 2026 |

---

## Domínios Bloqueados

O `source_quality.py` bloqueia automaticamente:

- **Redes sociais:** instagram.com, facebook.com, linkedin.com, tiktok.com
- **Vídeos:** youtube.com, vimeo.com (não são fontes citáveis)
- **Dicionários:** wikipedia.org, dicio.com.br, significados.com.br
- **Q&A:** quora.com, reddit.com
- **User-generated:** medium.com, academia.edu

---

## Monitoramento

### Logs de Diagnóstico

Quando uma busca não encontra 3 fontes:

```
[ENRICHMENT FAILURE] Got 2/3 sources for: "query original"
[ENRICHMENT FAILURE] primary: raw=10, validated=1, blocked: 4 (youtube.com, instagram.com)
[ENRICHMENT FAILURE] alternate: raw=8, validated=1
```

### Métricas

| Métrica | Esperado |
|---------|----------|
| Fontes por oportunidade | 3 |
| Taxa de sucesso | >95% |
| Tempo por busca | 2-5s |

---

## Troubleshooting

### Poucas fontes encontradas

1. Verificar se `SERPER_API_KEY` está configurada
2. Checar logs de domínios bloqueados
3. Query pode ser muito específica (sistema tentará reformular)

### Conteúdo não extraído

1. Jina Reader pode ter timeout (30s)
2. Site pode bloquear scrapers
3. Conteúdo < 100 chars é ignorado

### Créditos Serper

```bash
# Verificar créditos restantes
curl -H "X-API-KEY: $SERPER_API_KEY" https://google.serper.dev/account
```

---

## Histórico de Mudanças

| Data | Mudança |
|------|---------|
| 2026-03-09 | Substituição Google CSE → Serper + Jina Reader |
| 2026-03-09 | Sistema de 4 fallbacks para garantir 3 fontes |
| 2026-03-09 | SourceEvaluatorService para avaliação com IA |
| 2026-02-27 | Implementação inicial (Two-Phase System) |
