# SocialMediaIntegration Module

Sistema de agendamento e publicacao automatizada de posts no Instagram.

## Visao Geral

Este modulo implementa a integracao completa com a Instagram Graph API para:
- Gerenciar contas Instagram Business/Creator conectadas
- Agendar posts para publicacao automatica
- Processar publicacoes via cron job
- Monitorar status e logs de publicacao

## Arquitetura

```
SocialMediaIntegration/
├── models.py                  # Models Django
├── views.py                   # REST API endpoints
├── urls.py                    # Rotas
├── admin.py                   # Django Admin
├── serializers/
│   ├── instagram_account_serializers.py
│   └── scheduled_post_serializers.py
├── services/
│   ├── instagram_publish_service.py   # Publicacao via Graph API
│   └── scheduled_post_processor.py    # Processador de posts agendados
└── migrations/
    └── 0001_initial.py
```

## Models

### InstagramAccount
Armazena contas Instagram conectadas via OAuth.

| Campo | Tipo | Descricao |
|-------|------|-----------|
| user | FK(User) | Usuario dono da conta |
| instagram_user_id | CharField | ID do usuario no Instagram |
| instagram_username | CharField | @username |
| facebook_page_id | CharField | ID da Facebook Page vinculada |
| access_token | TextField | Token de acesso (deve ser criptografado) |
| token_expires_at | DateTimeField | Data de expiracao do token |
| status | CharField | connected, disconnected, token_expired, error |

### ScheduledPost
Posts agendados para publicacao automatica.

| Campo | Tipo | Descricao |
|-------|------|-----------|
| user | FK(User) | Usuario dono do post |
| instagram_account | FK(InstagramAccount) | Conta para publicar |
| post_idea | FK(PostIdea) | Vinculo com IdeaBank (opcional) |
| caption | TextField | Legenda (max 2200 chars) |
| media_type | CharField | IMAGE, VIDEO, CAROUSEL, REELS, STORY |
| media_urls | JSONField | Lista de URLs das midias |
| scheduled_for | DateTimeField | Data/hora de publicacao |
| status | CharField | draft, scheduled, publishing, published, failed, cancelled |
| retry_count | IntegerField | Tentativas de retry |
| last_error | TextField | Ultimo erro |

### PublishingLog
Audit log de tentativas de publicacao.

| Campo | Tipo | Descricao |
|-------|------|-----------|
| scheduled_post | FK(ScheduledPost) | Post relacionado |
| attempt_number | IntegerField | Numero da tentativa |
| status | CharField | started, container_created, processing, success, error, retry |
| api_endpoint | CharField | Endpoint chamado |
| request_data | JSONField | Payload da requisicao (sem tokens) |
| response_data | JSONField | Resposta da API |
| error_message | TextField | Mensagem de erro |
| duration_ms | IntegerField | Duracao em ms |

## Endpoints da API

### Contas Instagram

| Metodo | Endpoint | Descricao |
|--------|----------|-----------|
| GET | `/api/v1/social/instagram/accounts/` | Lista contas |
| GET | `/api/v1/social/instagram/accounts/{id}/` | Detalhes |
| POST | `/api/v1/social/instagram/accounts/{id}/disconnect/` | Desconecta |

### Posts Agendados

| Metodo | Endpoint | Descricao |
|--------|----------|-----------|
| GET | `/api/v1/social/scheduled-posts/` | Lista posts |
| POST | `/api/v1/social/scheduled-posts/` | Cria agendamento |
| GET | `/api/v1/social/scheduled-posts/{id}/` | Detalhes |
| PATCH | `/api/v1/social/scheduled-posts/{id}/` | Atualiza |
| DELETE | `/api/v1/social/scheduled-posts/{id}/` | Exclui |
| POST | `/api/v1/social/scheduled-posts/{id}/cancel/` | Cancela |
| POST | `/api/v1/social/scheduled-posts/{id}/publish-now/` | Publica agora |
| POST | `/api/v1/social/scheduled-posts/{id}/retry/` | Retenta |
| GET | `/api/v1/social/scheduled-posts/calendar/` | Calendario |
| GET | `/api/v1/social/scheduled-posts/stats/` | Estatisticas |

### Cron (GitHub Actions)

| Metodo | Endpoint | Descricao |
|--------|----------|-----------|
| POST | `/api/v1/social/cron/publish-scheduled/` | Processa agendados |
| POST | `/api/v1/social/cron/retry-failed/` | Retenta falhas |
| GET | `/api/v1/social/cron/stats/` | Estatisticas |

> **Nota:** Endpoints de cron requerem header `Authorization: Bearer {CRON_SECRET}`

## Fluxo de Publicacao

```
1. Usuario cria ScheduledPost com status='scheduled'
                    |
                    v
2. GitHub Actions executa cron a cada 5 minutos
                    |
                    v
3. ScheduledPostProcessor.process_pending_posts()
                    |
                    v
4. Para cada post due:
   a. Valida token da conta Instagram
   b. InstagramPublishService.publish_post()
      i.   Cria media container (POST /media)
      ii.  Aguarda processamento (GET /media?fields=status_code)
      iii. Publica container (POST /media_publish)
      iv.  Obtem permalink
   c. Atualiza status para 'published' ou 'failed'
                    |
                    v
5. Se falha e can_retry, agenda retry com backoff exponencial
```

## Configuracao

### Variaveis de Ambiente

```bash
# Instagram Graph API
INSTAGRAM_APP_ID=your_app_id
INSTAGRAM_APP_SECRET=your_app_secret

# Cron Secret (usado pelo GitHub Actions)
CRON_SECRET=your_secure_random_string

# Opcional: Criptografia de tokens
FERNET_KEY=your_fernet_key
```

### GitHub Actions

O workflow `.github/workflows/instagram-publish-scheduler.yml` executa:
- **A cada 5 minutos:** Processa posts agendados
- **Manualmente:** retry-failed, stats

## Limites do Instagram

| Limite | Valor |
|--------|-------|
| Posts via API por 24h | 25 |
| Caracteres na legenda | 2200 |
| Hashtags por post | 30 |
| Items no carrossel | 10 |
| Tamanho de video | 100MB |
| Duracao de video | 15 min |

## Seguranca

- [ ] **TODO:** Implementar criptografia de tokens com Fernet
- [x] Tokens nao sao logados em request_data
- [x] Cron endpoints requerem Bearer token
- [x] Endpoints REST requerem autenticacao

## Tratamento de Erros

| Erro | Acao |
|------|------|
| TOKEN_EXPIRED | Marca conta como token_expired, notifica usuario |
| CONNECTION_ERROR | Agenda retry com backoff |
| PROCESSING_TIMEOUT | Agenda retry |
| CONTAINER_EXPIRED | Falha definitiva |

## Proximos Passos

1. Implementar criptografia de tokens (Fernet)
2. Adicionar notificacoes por email/push
3. Implementar rate limiting
4. Adicionar testes unitarios
5. Solicitar App Review para `instagram_content_publish`

## Referencias

- [Instagram Graph API - Content Publishing](https://developers.facebook.com/docs/instagram-platform/instagram-graph-api/content-publishing)
- [Meta App Review](https://developers.facebook.com/docs/app-review/)
