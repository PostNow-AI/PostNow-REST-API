# Integração Frontend - Onboarding com Persistência de Dados

> **Status:** ✅ IMPLEMENTADO E TESTADO (19/02/2026)
>
> **Backend:** Branch `fix/onboarding-data-persistence` - Commit `3a6f994`
> **Frontend:** Branch `Dashboard-2.0` - Commit `e122423`

---

## Problema Resolvido

Anteriormente, quando um usuário fazia o onboarding em uma aba anônima (incógnito), os dados preenchidos eram perdidos após o signup porque:

1. Os dados ficavam apenas no localStorage/state do frontend
2. Não havia mecanismo para transferir os dados para o backend antes do signup
3. Ao fechar a aba anônima, o localStorage era limpo

## Solução Implementada

Novos endpoints que permitem salvar dados temporariamente no backend, vinculados a um `session_id`, e transferi-los automaticamente para o perfil do usuário após o signup.

---

## Novos Endpoints

### 1. Salvar Dados Temporários (Anônimo)

```
POST /api/v1/creator-profile/onboarding/temp-data/
```

**Autenticação:** Não requerida (AllowAny)

**Request Body:**
```json
{
  "session_id": "uuid-gerado-pelo-frontend",
  "business_name": "Minha Empresa",
  "specialization": "Advocacia Tributária",
  "business_description": "Descrição do negócio...",
  "business_purpose": "Propósito da empresa...",
  "brand_personality": "Profissional e confiável",
  "products_services": "Consultoria jurídica...",
  "business_location": "São Paulo",
  "target_audience": "Empresários",
  "target_interests": "Finanças, Gestão",
  "main_competitors": "Empresa X, Empresa Y",
  "reference_profiles": "@perfil1, @perfil2",
  "voice_tone": "Profissional",
  "color_1": "#FF6B6B",
  "color_2": "#4ECDC4",
  "color_3": "#45B7D1",
  "color_4": "#96CEB4",
  "color_5": "#FFEAA7",
  "visual_style_ids": [1, 2, 3]
}
```

**Response (201 Created):**
```json
{
  "status": "ok",
  "session_id": "uuid-gerado-pelo-frontend",
  "message": "Dados salvos temporariamente com sucesso",
  "expires_at": "2026-02-26T21:17:00Z"
}
```

**Notas:**
- Dados expiram em 7 dias
- Pode ser chamado múltiplas vezes (dados são mesclados)
- Todos os campos são opcionais, exceto `session_id`

---

### 2. Recuperar Dados Temporários

```
GET /api/v1/creator-profile/onboarding/temp-data/?session_id=uuid
```

**Autenticação:** Não requerida (AllowAny)

**Response (200 OK):**
```json
{
  "session_id": "uuid-gerado-pelo-frontend",
  "business_data": {
    "business_name": "Minha Empresa",
    "specialization": "Advocacia",
    ...
  },
  "branding_data": {
    "voice_tone": "Profissional",
    "color_1": "#FF6B6B",
    ...
  },
  "created_at": "2026-02-19T21:17:00Z",
  "updated_at": "2026-02-19T21:30:00Z"
}
```

**Response (404 Not Found):**
```json
{
  "error": "No data found for this session"
}
```

---

### 3. Vincular Dados ao Usuário (Após Signup)

```
POST /api/v1/creator-profile/onboarding/link-data/
```

**Autenticação:** Requerida (Bearer Token)

**Request Body:**
```json
{
  "session_id": "uuid-gerado-pelo-frontend"
}
```

**Response (200 OK):**
```json
{
  "status": "ok",
  "message": "Dados vinculados ao perfil com sucesso",
  "profile": {
    "business_name": "Minha Empresa",
    "specialization": "Advocacia",
    "step_1_completed": true,
    "step_2_completed": true,
    "onboarding_completed": true,
    ...
  }
}
```

**Response (404 Not Found):**
```json
{
  "status": "not_found",
  "message": "Nenhum dado temporário encontrado para esta sessão"
}
```

---

## Fluxo de Integração

### Diagrama do Fluxo

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Usuário inicia onboarding                                   │
│     │                                                           │
│     ▼                                                           │
│  ┌──────────────────────────────────────┐                       │
│  │ Gerar session_id (UUID)              │                       │
│  │ Salvar em localStorage/sessionStorage │                       │
│  └──────────────────────────────────────┘                       │
│     │                                                           │
│     ▼                                                           │
│  2. A cada step completado                                      │
│     │                                                           │
│     ├──► POST /onboarding/track/ (tracking)                     │
│     │                                                           │
│     └──► POST /onboarding/temp-data/ (dados reais) ◄── NOVO!   │
│     │                                                           │
│     ▼                                                           │
│  3. Usuário chega no signup (step 19)                           │
│     │                                                           │
│     ▼                                                           │
│  ┌──────────────────────────────────────┐                       │
│  │ POST /auth/registration/             │                       │
│  │ (com session_id no header ou body)   │                       │
│  └──────────────────────────────────────┘                       │
│     │                                                           │
│     ▼                                                           │
│  4. Após receber token de autenticação                          │
│     │                                                           │
│     ▼                                                           │
│  ┌──────────────────────────────────────┐                       │
│  │ POST /onboarding/link-data/          │ ◄── NOVO!            │
│  │ Authorization: Bearer <token>         │                       │
│  │ Body: { "session_id": "..." }        │                       │
│  └──────────────────────────────────────┘                       │
│     │                                                           │
│     ▼                                                           │
│  5. Dados vinculados ao perfil do usuário                      │
│     │                                                           │
│     ▼                                                           │
│  ┌──────────────────────────────────────┐                       │
│  │ Limpar session_id do storage         │                       │
│  │ Redirecionar para dashboard          │                       │
│  └──────────────────────────────────────┘                       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Implementação Sugerida (React/TypeScript)

### 1. Hook para Gerenciar Session ID

```typescript
// hooks/useOnboardingSession.ts
import { useCallback, useEffect, useState } from 'react';
import { v4 as uuidv4 } from 'uuid';

const SESSION_KEY = 'onboarding_session_id';

export function useOnboardingSession() {
  const [sessionId, setSessionId] = useState<string | null>(null);

  useEffect(() => {
    // Tentar recuperar session_id existente
    let id = sessionStorage.getItem(SESSION_KEY);

    if (!id) {
      // Gerar novo session_id
      id = uuidv4();
      sessionStorage.setItem(SESSION_KEY, id);
    }

    setSessionId(id);
  }, []);

  const clearSession = useCallback(() => {
    sessionStorage.removeItem(SESSION_KEY);
    setSessionId(null);
  }, []);

  return { sessionId, clearSession };
}
```

### 2. Serviço de API para Onboarding

```typescript
// services/onboardingService.ts
import api from './api';

interface OnboardingData {
  session_id: string;
  business_name?: string;
  specialization?: string;
  business_description?: string;
  business_purpose?: string;
  brand_personality?: string;
  products_services?: string;
  business_location?: string;
  target_audience?: string;
  target_interests?: string;
  main_competitors?: string;
  reference_profiles?: string;
  voice_tone?: string;
  color_1?: string;
  color_2?: string;
  color_3?: string;
  color_4?: string;
  color_5?: string;
  visual_style_ids?: number[];
}

export const onboardingService = {
  // Salvar dados temporários (anônimo)
  async saveTempData(data: OnboardingData) {
    const response = await api.post('/creator-profile/onboarding/temp-data/', data);
    return response.data;
  },

  // Recuperar dados temporários
  async getTempData(sessionId: string) {
    try {
      const response = await api.get(`/creator-profile/onboarding/temp-data/?session_id=${sessionId}`);
      return response.data;
    } catch (error: any) {
      if (error.response?.status === 404) {
        return null;
      }
      throw error;
    }
  },

  // Vincular dados ao usuário (após login)
  async linkDataToUser(sessionId: string) {
    const response = await api.post('/creator-profile/onboarding/link-data/', {
      session_id: sessionId,
    });
    return response.data;
  },

  // Tracking de step (existente)
  async trackStep(sessionId: string, stepNumber: number, completed: boolean = false) {
    const response = await api.post('/creator-profile/onboarding/track/', {
      session_id: sessionId,
      step_number: stepNumber,
      completed,
    });
    return response.data;
  },
};
```

### 3. Componente de Step do Onboarding

```typescript
// components/OnboardingStep.tsx
import { useEffect } from 'react';
import { useOnboardingSession } from '../hooks/useOnboardingSession';
import { onboardingService } from '../services/onboardingService';

interface StepProps {
  stepNumber: number;
  data: Record<string, any>;
  onNext: () => void;
}

export function OnboardingStep({ stepNumber, data, onNext }: StepProps) {
  const { sessionId } = useOnboardingSession();

  const handleComplete = async () => {
    if (!sessionId) return;

    try {
      // 1. Salvar dados no backend
      await onboardingService.saveTempData({
        session_id: sessionId,
        ...data,
      });

      // 2. Marcar step como completado
      await onboardingService.trackStep(sessionId, stepNumber, true);

      // 3. Ir para próximo step
      onNext();
    } catch (error) {
      console.error('Erro ao salvar dados do onboarding:', error);
      // Mostrar erro para o usuário
    }
  };

  useEffect(() => {
    // Registrar visita ao step
    if (sessionId) {
      onboardingService.trackStep(sessionId, stepNumber, false);
    }
  }, [sessionId, stepNumber]);

  return (
    // ... UI do step
    <button onClick={handleComplete}>Continuar</button>
  );
}
```

### 4. Após Signup - Vincular Dados

```typescript
// pages/SignupPage.tsx
import { useOnboardingSession } from '../hooks/useOnboardingSession';
import { onboardingService } from '../services/onboardingService';
import { authService } from '../services/authService';

export function SignupPage() {
  const { sessionId, clearSession } = useOnboardingSession();

  const handleSignup = async (email: string, password: string) => {
    try {
      // 1. Criar conta
      const authResult = await authService.signup(email, password);

      // 2. Salvar token
      localStorage.setItem('access_token', authResult.access);

      // 3. Vincular dados do onboarding ao novo usuário
      if (sessionId) {
        try {
          await onboardingService.linkDataToUser(sessionId);
          console.log('Dados do onboarding vinculados com sucesso!');
        } catch (error) {
          console.warn('Não foi possível vincular dados do onboarding:', error);
          // Não é erro crítico, continuar normalmente
        }

        // 4. Limpar session
        clearSession();
      }

      // 5. Redirecionar para dashboard
      navigate('/dashboard');

    } catch (error) {
      console.error('Erro no signup:', error);
    }
  };

  return (
    // ... UI de signup
  );
}
```

### 5. Recuperar Dados ao Reabrir Onboarding

```typescript
// pages/OnboardingPage.tsx
import { useEffect, useState } from 'react';
import { useOnboardingSession } from '../hooks/useOnboardingSession';
import { onboardingService } from '../services/onboardingService';

export function OnboardingPage() {
  const { sessionId } = useOnboardingSession();
  const [initialData, setInitialData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadSavedData() {
      if (!sessionId) {
        setLoading(false);
        return;
      }

      try {
        const savedData = await onboardingService.getTempData(sessionId);
        if (savedData) {
          // Combinar business_data e branding_data
          setInitialData({
            ...savedData.business_data,
            ...savedData.branding_data,
          });
        }
      } catch (error) {
        console.error('Erro ao carregar dados salvos:', error);
      } finally {
        setLoading(false);
      }
    }

    loadSavedData();
  }, [sessionId]);

  if (loading) {
    return <LoadingSpinner />;
  }

  return (
    <OnboardingFlow initialData={initialData} />
  );
}
```

---

## Campos por Step

### Step 1-8: Dados do Negócio (business_data)

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `business_name` | string | Sim | Nome da empresa |
| `business_phone` | string | Não | WhatsApp |
| `business_website` | string | Não | URL do site |
| `business_instagram_handle` | string | Não | @ do Instagram |
| `specialization` | string | Sim | Nicho de atuação |
| `business_description` | string | Sim | Descrição do negócio |
| `business_purpose` | string | Não | Propósito/missão |
| `brand_personality` | string | Não | Personalidade da marca |
| `products_services` | string | Não | Produtos/serviços |
| `business_location` | string | Não | Localização |
| `target_audience` | string | Não | Público-alvo |
| `target_interests` | string | Não | Interesses do público |
| `main_competitors` | string | Não | Concorrentes |
| `reference_profiles` | string | Não | Perfis de referência |

### Step 13-17: Identidade Visual (branding_data)

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `voice_tone` | string | Sim | Tom de voz |
| `logo` | string | Não | Logo em base64 |
| `color_1` | string | Não | Cor 1 (hex: #FFFFFF) |
| `color_2` | string | Não | Cor 2 |
| `color_3` | string | Não | Cor 3 |
| `color_4` | string | Não | Cor 4 |
| `color_5` | string | Não | Cor 5 |
| `visual_style_ids` | number[] | Não | IDs dos estilos visuais |

---

## Tratamento de Erros

### Erros Comuns

| Status | Erro | Ação Recomendada |
|--------|------|------------------|
| 400 | `session_id is required` | Verificar se session_id está sendo enviado |
| 404 | `No data found` | Dados expiraram ou não existem, ignorar |
| 401 | `Unauthorized` | Token expirou, redirecionar para login |
| 500 | `Server error` | Retry com backoff exponencial |

### Exemplo de Tratamento

```typescript
async function safeSaveTempData(data: OnboardingData) {
  const maxRetries = 3;

  for (let i = 0; i < maxRetries; i++) {
    try {
      return await onboardingService.saveTempData(data);
    } catch (error: any) {
      if (error.response?.status >= 500 && i < maxRetries - 1) {
        // Retry em caso de erro do servidor
        await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1)));
        continue;
      }
      throw error;
    }
  }
}
```

---

## Considerações de Segurança

1. **Session ID:** Use UUID v4 para evitar colisões e dificultar adivinhação
2. **Expiração:** Dados expiram automaticamente em 7 dias
3. **Validação:** Backend valida todos os campos antes de salvar
4. **Sanitização:** Dados são sanitizados antes de salvar no perfil

---

## Checklist de Implementação

- [x] Instalar `uuid` package: `npm install uuid @types/uuid`
- [x] Criar hook `useOnboardingSession` → Implementado em `useOnboardingStorage.ts`
- [x] Criar serviço `onboardingService` → Implementado em `services/index.ts`
- [x] Atualizar componentes de step para salvar dados
- [x] Atualizar página de signup para vincular dados
- [x] Atualizar página de onboarding para carregar dados salvos
- [x] Testar fluxo completo em aba anônima
- [x] Testar recuperação de dados após fechar/reabrir aba

---

## Resultados dos Testes (19/02/2026)

### Testes de API (27 testes - todos passaram)

| Teste | Resultado |
|-------|-----------|
| Salvar dados temporários (POST /temp-data/) | ✅ |
| Recuperar dados temporários (GET /temp-data/) | ✅ |
| Merge de dados (business + branding) | ✅ |
| Tracking de steps | ✅ |
| Session ID inválido retorna 404 | ✅ |
| Link sem autenticação retorna 401 | ✅ |
| Vincular dados ao usuário autenticado | ✅ |
| Perfil criado com dados corretos | ✅ |
| Dados temporários deletados após link | ✅ |

### Teste E2E no Navegador

| Etapa | Resultado |
|-------|-----------|
| Frontend gera session_id único | ✅ |
| Dados enviados ao backend durante preenchimento | ✅ |
| Backend salva dados na tabela OnboardingTempData | ✅ |
| Dados persistem sem autenticação | ✅ |
| Dados aparecem no dashboard após signup | ✅ |

### Exemplo de Dados Salvos

```json
{
  "session_id": "onb_mlu0q46a_iqffhl54",
  "business_data": {
    "business_name": "Empresa Teste Automatizado",
    "business_phone": "(11) 99999-8888",
    "business_instagram_handle": "empresateste"
  },
  "branding_data": {
    "color_1": "#FF6B6B",
    "color_2": "#4ECDC4",
    "color_3": "#45B7D1",
    "color_4": "#96CEB4",
    "color_5": "#FFBE0B"
  }
}
```

---

## Arquivos Modificados

### Backend (PostNow-REST-API)

| Arquivo | Mudança |
|---------|---------|
| `CreatorProfile/models.py` | Adicionado modelo `OnboardingTempData` |
| `CreatorProfile/services.py` | Adicionado `OnboardingDataService` |
| `CreatorProfile/views.py` | Adicionados endpoints temp-data e link-data |
| `CreatorProfile/urls.py` | Adicionadas rotas para novos endpoints |
| `CreatorProfile/serializers.py` | Adicionado `OnboardingTempDataSerializer` |
| `CreatorProfile/admin.py` | Adicionado admin para OnboardingTempData |
| `CreatorProfile/migrations/0012_add_onboarding_temp_data.py` | Migration |

### Frontend (PostNow-UI)

| Arquivo | Mudança |
|---------|---------|
| `src/features/Auth/Onboarding/services/index.ts` | Adicionadas funções de API |
| `src/features/Auth/Onboarding/hooks/useOnboardingStorage.ts` | Refatorado para sincronizar com backend |
| `src/features/Auth/Onboarding/OnboardingNew.tsx` | Atualizado para usar linkDataToUser |
| `src/features/Auth/GoogleAuth/hooks/useGoogleCallback.ts` | Atualizado para vincular dados após OAuth |

---

## Suporte

Em caso de dúvidas, entre em contato com o time de backend ou abra uma issue no repositório.
