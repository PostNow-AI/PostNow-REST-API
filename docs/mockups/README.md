# Mockups de E-mail

Esta pasta contém os mockups HTML dos e-mails enviados pelo sistema de Inteligência de Mercado.

## Arquivos

| Arquivo | Descrição | Dia de Envio |
|---------|-----------|--------------|
| `mock_email_monday_opportunities.html` | E-mail de Oportunidades de Conteúdo | Segunda-feira |
| `mock_email_wednesday_market_intelligence.html` | E-mail de Inteligência de Mercado | Quarta-feira |
| `mockup_unified_monday.html` | Versão inicial do mockup de segunda | - |
| `mockup_unified_wednesday.html` | Versão inicial do mockup de quarta | - |

## Como Visualizar

Abra qualquer arquivo `.html` diretamente no navegador para visualizar o layout do e-mail.

## Fluxo de E-mails

```
DOMINGO
├── 06:00 UTC - Geração de contexto semanal (WeeklyContextService)
└── 09:00 UTC - Geração de oportunidades (OpportunitiesGenerationService)

SEGUNDA-FEIRA
└── 10:00 UTC - Enriquecimento + Envio de Oportunidades
    ├── ContextEnrichmentService (adiciona fontes via Google Search)
    └── OpportunitiesEmailService (envia mock_email_monday_opportunities)

QUARTA-FEIRA
└── 10:00 UTC - Enriquecimento + Envio de Inteligência de Mercado
    ├── MarketIntelligenceEnrichmentService (adiciona fontes)
    └── MarketIntelligenceEmailService (envia mock_email_wednesday_market_intelligence)
```

## Relação com o Código

| Mockup | Template Python | Serviço |
|--------|-----------------|---------|
| `mock_email_monday_opportunities.html` | `ClientContext/utils/opportunities_email.py` | `OpportunitiesEmailService` |
| `mock_email_wednesday_market_intelligence.html` | `ClientContext/utils/market_intelligence_email.py` | `MarketIntelligenceEmailService` |

## Seções do E-mail de Inteligência de Mercado (Quarta)

1. **Panorama do Mercado** - Visão geral do setor
2. **Análise da Concorrência** - Principais concorrentes e estratégias
3. **Insights do Público** - Perfil e comportamento do público-alvo
4. **Tendências da Semana** - Temas, hashtags e keywords em alta
5. **Calendário Estratégico** - Datas relevantes e eventos
6. **Sua Marca** - Presença online e reputação

## Seções do E-mail de Oportunidades (Segunda)

1. **Oportunidades Polêmicas** - Temas controversos para engajamento
2. **Conteúdo Educativo** - Ideias para educar a audiência
3. **Newsjacking** - Aproveitar notícias do momento
4. **Entretenimento** - Conteúdo leve e viral
5. **Estudos de Caso** - Histórias de sucesso
6. **Visão de Futuro** - Tendências emergentes
