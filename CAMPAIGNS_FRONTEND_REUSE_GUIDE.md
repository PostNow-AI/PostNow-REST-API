# 🎨 GUIA DE REUTILIZAÇÃO - Frontend (React + TypeScript)

## Baseado em Análise Completa do PostNow-UI

---

## ✅ COMPONENTES UI 100% REUTILIZÁVEIS

### 1. Design System Completo (shadcn/ui)

**Localização:** `src/components/ui/`

**36 componentes prontos:**
- ✅ `button.tsx` - Todos os estilos (default, destructive, outline, ghost)
- ✅ `card.tsx` - Cards para posts, campanhas
- ✅ `dialog.tsx` - Modals (criar, editar, confirmar)
- ✅ `form.tsx` + `FormField` - Formulários react-hook-form
- ✅ `input.tsx`, `textarea.tsx`, `select.tsx` - Inputs
- ✅ `checkbox.tsx` - Para grid de aprovação!
- ✅ `tabs.tsx` - Para [Posts] [Calendário] [Preview]
- ✅ `progress.tsx` + `progress-bar.tsx` - Loading states
- ✅ `skeleton.tsx` - Loading placeholders
- ✅ `badge.tsx` - Badges de status
- ✅ `separator.tsx` - Divisores visuais
- ✅ `tooltip.tsx` - Explicações inline
- ✅ `alert.tsx`, `alert-dialog.tsx` - Avisos e confirmações
- ✅ `sheet.tsx` - Side panels (mobile-friendly)
- ✅ `container.tsx` - Layout padrão de páginas
- ✅ `scroll-area.tsx` - Scroll customizado
- ✅ E mais 20+ componentes

**Padrão de uso (reutilizar exatamente assim):**
```typescript
import {
  Button,
  Card,
  CardContent,
  CardHeader,
  Dialog,
  DialogContent,
  Form,
  FormField,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
  Checkbox,
  Badge,
} from "@/components/ui";
```

**Todos seguem:**
- Tailwind CSS para estilos
- Dark mode automático (useTheme)
- Acessibilidade (ARIA)
- Responsividade mobile

---

## 📐 PADRÕES DE ARQUITETURA FRONTEND

### Estrutura de Feature (Padrão Identificado)

**Exemplo: `IdeaBank/`**
```
features/IdeaBank/
├─ index.tsx                    # Página principal (exporta componente default)
├─ components/                  # Componentes específicos da feature
│   ├─ PostCreationDialog.tsx
│   ├─ PostList.tsx
│   ├─ PostViewDialog.tsx
│   └─ NoSubscriptionDialog.tsx
├─ hooks/                       # React hooks customizados
│   ├─ index.ts                # Re-exports
│   ├─ usePostCreationForm.ts
│   ├─ usePostList.ts
│   ├─ useCreatePostWithIdea.ts
│   └─ useDeletePost.ts
├─ services/                    # API calls
│   └─ index.ts                # Service object
├─ types/                       # TypeScript interfaces
│   └─ index.ts
└─ constants/                   # Schemas, options
    └─ index.ts
```

**Para Campaigns, seguir EXATAMENTE:**
```
features/Campaigns/
├─ index.tsx                    # Página dashboard de campanhas
├─ pages/                       # Múltiplas páginas (não só 1)
│   ├─ CampaignsDashboard.tsx
│   ├─ CampaignCreation.tsx
│   └─ CampaignDetail.tsx
├─ components/
│   ├─ wizard/                  # Componentes do wizard
│   │   ├─ FlowSelector.tsx
│   │   ├─ BriefingStep.tsx
│   │   ├─ StructureSelector.tsx
│   │   ├─ VisualStylePicker.tsx
│   │   └─ PreGenerationReview.tsx
│   ├─ approval/                # Componentes de aprovação
│   │   ├─ PostGridView.tsx
│   │   ├─ PostCard.tsx
│   │   ├─ PostDetailDialog.tsx
│   │   └─ RegenerateDialog.tsx
│   ├─ preview/                 # Preview de feed
│   │   ├─ InstagramFeedPreview.tsx
│   │   ├─ HarmonyAnalyzer.tsx
│   │   └─ ReorganizationTools.tsx
│   └─ shared/
│       ├─ ProgressIndicator.tsx
│       └─ LoadingWithTips.tsx
├─ hooks/
│   ├─ useCampaignCreation.ts
│   ├─ useCampaignAutoSave.ts
│   ├─ usePostApproval.ts
│   ├─ useVisualHarmony.ts
│   └─ index.ts
├─ services/
│   └─ index.ts                 # campaignService object
├─ types/
│   └─ index.ts
└─ constants/
    └─ schemas.ts               # Zod schemas
```

---

## ✅ HOOKS PATTERN - TanStack Query

### Padrão Identificado (100% consistente em todo codebase)

**Para QUERIES (GET):**
```typescript
// features/IdeaBank/hooks/usePostList.ts

export const usePostList = () => {
  const {
    data,
    isLoading,
    isError,
    error,
    refetch
  } = useQuery({
    queryKey: ["posts-with-ideas"],  // Array único
    queryFn: ideaBankService.getPostsWithIdeas,
    staleTime: 5 * 60 * 1000,  // 5 minutos
  });
  
  return { data, isLoading, isError, error, refetch };
};
```

**Para MUTATIONS (POST/PUT/DELETE):**
```typescript
// features/IdeaBank/hooks/useCreatePostWithIdea.ts

export const useCreatePostWithIdea = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data: PostCreationData) => 
      ideaBankService.createPostWithIdea(data),
    
    onSuccess: (data) => {
      // SEMPRE invalidar queries relacionadas
      queryClient.invalidateQueries({ queryKey: ["posts-with-ideas"] });
      queryClient.invalidateQueries({ queryKey: ["post-stats"] });
      queryClient.invalidateQueries({ queryKey: ["monthly-credits"] });
      
      // Toast de sucesso
      toast.success("Post criado com sucesso!");
      
      return data;
    },
    
    onError: (error) => {
      // Toast de erro
      toast.error("Erro ao criar post");
      console.error("Error creating post:", error);
    },
  });
};
```

**Para Campaigns, replicar:**
```typescript
// features/Campaigns/hooks/useCampaignCreation.ts

export const useCampaignCreation = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data: CampaignCreationData) =>
      campaignService.createCampaign(data),
    
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["campaigns"] });
      queryClient.invalidateQueries({ queryKey: ["posts-with-ideas"] });
      queryClient.invalidateQueries({ queryKey: ["monthly-credits"] });
      toast.success("Campanha criada com sucesso!");
      return data;
    },
    
    onError: (error) => {
      const errorResult = handleApiError(error, {
        defaultTitle: "Erro ao criar campanha",
        defaultDescription: "Não foi possível criar a campanha. Tente novamente."
      });
      toast.error(errorResult.description);
    },
  });
};

// Hook para auto-save
export const useCampaignAutoSave = (campaignDraft) => {
  const [lastSave, setLastSave] = useState<Date | null>(null);
  
  useEffect(() => {
    const interval = setInterval(async () => {
      if (campaignDraft.hasChanges) {
        await campaignService.saveDraft(campaignDraft);
        setLastSave(new Date());
      }
    }, 30000);  // 30 segundos
    
    return () => clearInterval(interval);
  }, [campaignDraft]);
  
  return { lastSave };
};
```

---

## 📝 FORMS PATTERN - React Hook Form + Zod

### Padrão Identificado

**1. Schema Zod:**
```typescript
// features/IdeaBank/constants/index.ts

export const postCreationSchema = z.object({
  name: z.string().min(1, "Nome do post é obrigatório"),
  objective: z.enum(["sales", "branding", ...]),
  type: z.enum(["post", "story", "reel", "carousel"]),
  further_details: z.string().optional(),
  include_image: z.boolean(),
});

export type PostCreationFormData = z.infer<typeof postCreationSchema>;
```

**2. Hook de Form:**
```typescript
const form = useForm<PostCreationData>({
  resolver: zodResolver(postCreationSchema),
  defaultValues: {
    name: "",
    objective: "branding" as const,
    type: "post" as const,
    further_details: "",
    include_image: false,
  },
});
```

**3. Componente Form:**
```typescript
<Form {...form}>
  <form onSubmit={form.handleSubmit(handleSubmit)}>
    <FormField
      control={form.control}
      name="name"
      render={({ field }) => (
        <FormItem>
          <FormLabel>Nome do Post</FormLabel>
          <FormControl>
            <Input placeholder="Ex: Post sobre..." {...field} />
          </FormControl>
          <FormDescription>
            Dica: Seja específico
          </FormDescription>
          <FormMessage />
        </FormItem>
      )}
    />
    
    <Button type="submit" disabled={isCreating}>
      {isCreating && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
      Criar Post
    </Button>
  </form>
</Form>
```

**Para Campaigns:**
```typescript
// constants/briefingSchema.ts

export const campaignBriefingSchema = z.object({
  objective: z.string().min(10, "Descreva o objetivo em pelo menos 10 caracteres"),
  main_message: z.string().min(5, "Mensagem principal é obrigatória"),
  has_cases: z.boolean().optional(),
  cases_description: z.string().optional(),
  has_materials: z.boolean().optional(),
  duration_days: z.number().min(7).max(30),
  // ...
});
```

---

## 🔌 API SERVICE PATTERN

### Padrão Identificado

**Arquivo de serviço:**
```typescript
// features/IdeaBank/services/index.ts

import { api } from "@/lib/api";
import type { ... } from "../types";

export const ideaBankService = {
  async getPostsWithIdeas(): Promise<PostsWithIdeasResponse> {
    const response = await api.get("api/v1/ideabank/posts/all-with-ideas/");
    return response.data;
  },
  
  async createPostWithIdea(data: PostCreationData): Promise<PostCreationResponse> {
    const response = await api.post("api/v1/ideabank/generate/post-idea/", data);
    return response.data;
  },
  
  async deletePost(postId: number): Promise<void> {
    await api.delete(`api/v1/ideabank/posts/${postId}/`);
  },
  
  // ... mais métodos
};
```

**Para Campaigns:**
```typescript
// features/Campaigns/services/index.ts

import { api } from "@/lib/api";
import type {
  Campaign,
  CampaignDraft,
  CampaignCreationData,
  CampaignGenerationResponse,
  WeeklyContextOpportunity
} from "../types";

export const campaignService = {
  // Listar campanhas
  async getCampaigns(): Promise<Campaign[]> {
    const response = await api.get("/api/v1/campaigns/");
    return response.data;
  },
  
  // Criar draft inicial
  async createDraft(data: Partial<CampaignCreationData>): Promise<CampaignDraft> {
    const response = await api.post("/api/v1/campaigns/drafts/", data);
    return response.data;
  },
  
  // Auto-save
  async saveDraft(draft: CampaignDraft): Promise<void> {
    await api.post("/api/v1/campaigns/drafts/save/", draft);
  },
  
  // Gerar conteúdo completo
  async generateContent(campaignId: number): Promise<CampaignGenerationResponse> {
    const response = await api.post(`/api/v1/campaigns/${campaignId}/generate/`);
    return response.data;
  },
  
  // Aprovar post individual
  async approvePost(campaignId: number, postId: number): Promise<void> {
    await api.post(`/api/v1/campaigns/${campaignId}/posts/${postId}/approve/`);
  },
  
  // Aprovar todos
  async approveCampaign(campaignId: number): Promise<void> {
    await api.post(`/api/v1/campaigns/${campaignId}/approve/`);
  },
  
  // Reorganizar posts
  async reorganizePosts(campaignId: number, newOrder: number[]): Promise<void> {
    await api.patch(`/api/v1/campaigns/${campaignId}/reorganize/`, {
      post_order: newOrder
    });
  },
  
  // Weekly Context
  async getOpportunities(campaignId: number): Promise<WeeklyContextOpportunity[]> {
    const response = await api.get(`/api/v1/campaigns/${campaignId}/opportunities/`);
    return response.data;
  },
  
  // Adicionar oportunidade
  async addOpportunity(campaignId: number, opportunityId: number): Promise<void> {
    await api.post(`/api/v1/campaigns/${campaignId}/opportunities/${opportunityId}/add/`);
  },
};
```

---

## 🪝 HOOKS REUTILIZÁVEIS

### 1. **useAuth** (Contexto de Autenticação)

**Localização:** `src/hooks/useAuth.ts`

**Reutilizar em Campaigns:**
```typescript
import { useAuth } from "@/hooks";

const CampaignCreation = () => {
  const { user } = useAuth();
  
  // Acessa user.creator_profile.business_name, etc.
  const business Name = user?.creator_profile?.business_name;
};
```

---

### 2. **Padrão de Loading States**

**Identificado em todas features:**
```typescript
if (isLoading) {
  return (
    <Container>
      <div className="space-y-4">
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    </Container>
  );
}

if (isError) {
  return (
    <Container>
      <div className="flex flex-col items-center justify-center py-16">
        <AlertCircle className="h-24 w-24 text-red-400 mb-4" />
        <h2 className="text-2xl font-semibold">Erro ao carregar</h2>
        <p>{error.message}</p>
        <Button onClick={() => refetch()}>Tentar Novamente</Button>
      </div>
    </Container>
  );
}
```

**Aplicar em Campaigns:**
- Mesma estrutura
- Skeleton para loading
- Error state com retry
- Container para layout

---

## 🎨 COMPONENTES ESPECÍFICOS PARA ADAPTAR

### 1. **PostCreationDialog** → **CampaignCreationWizard**

**Padrão atual (IdeaBank):**
- Dialog grande (max-w-6xl)
- Form com react-hook-form + zod
- Cards organizando seções
- Submit com loading state

**Adaptar para Campaigns:**
```typescript
export const CampaignCreationWizard = ({ isOpen, onClose }) => {
  const [currentStep, setCurrentStep] = useState<Step>("flow");
  const { user } = useAuth();
  
  const form = useForm<CampaignBriefingData>({
    resolver: zodResolver(campaignBriefingSchema),
    defaultValues: { ... },
  });
  
  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh]">
        <DialogHeader>
          <DialogTitle>Criar Nova Campanha</DialogTitle>
        </DialogHeader>
        
        {/* Multi-step wizard */}
        {currentStep === "flow" && <FlowSelector onSelect={setFlow} />}
        {currentStep === "briefing" && <BriefingStep form={form} />}
        {currentStep === "structure" && <StructureSelector />}
        {currentStep === "styles" && <VisualStylePicker />}
        {currentStep === "review" && <PreGenerationReview />}
      </DialogContent>
    </Dialog>
  );
};
```

---

### 2. **PostList** → **CampaignGrid**

**Padrão atual:**
```typescript
export const PostList = () => {
  const { data: posts, isLoading } = usePostList();
  
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {posts?.map(post => (
        <PostCard key={post.id} post={post} />
      ))}
    </div>
  );
};
```

**Adaptar para Campaigns:**
```typescript
export const PostGridView = ({ campaignPosts }) => {
  const [selectedPosts, setSelectedPosts] = useState<Set<number>>(new Set());
  
  return (
    <div className="space-y-4">
      <ProgressBar 
        approved={approvedCount} 
        total={campaignPosts.length} 
      />
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {campaignPosts.map(post => (
          <PostCard
            key={post.id}
            post={post}
            selectable
            selected={selectedPosts.has(post.id)}
            onSelectChange={(selected) => handleSelect(post.id, selected)}
          />
        ))}
      </div>
      
      <BulkActions>
        <Button onClick={() => approveBulk(selectedPosts)}>
          Aprovar Selecionados ({selectedPosts.size})
        </Button>
      </BulkActions>
    </div>
  );
};
```

---

## 📦 TYPES TYPESCRIPT PATTERN

### Padrão Identificado

**Sempre criar:**
```typescript
// features/Campaigns/types/index.ts

export interface Campaign {
  id: number;
  name: string;
  type: CampaignType;
  type_display: string;
  objective: string;
  status: CampaignStatus;
  duration_days: number;
  posts_count: number;
  created_at: string;
  updated_at: string;
}

export interface CampaignPost {
  id: number;
  campaign_id: number;
  post: Post;  // Reusa tipo do IdeaBank
  sequence_order: number;
  scheduled_date: string;
  scheduled_time: string;
  phase: string;
  is_approved: boolean;
}

export interface CampaignDraft {
  id: number;
  user_id: number;
  current_phase: string;
  briefing_data: BriefingData;
  structure_chosen: string | null;
  styles_chosen: string[];
  created_at: string;
  updated_at: string;
}

export type CampaignType = 
  | "branding" 
  | "sales" 
  | "launch" 
  | "education" 
  | "engagement";

export type CampaignStatus = 
  | "draft" 
  | "active" 
  | "completed" 
  | "paused";

// Request/Response types
export interface CampaignCreationData {
  name: string;
  type: CampaignType;
  objective: string;
  main_message: string;
  duration_days: number;
}

export interface CampaignGenerationResponse {
  campaign: Campaign;
  posts: CampaignPost[];
  message: string;
}
```

---

## 🎯 COMPONENTES ESPECÍFICOS DO POSTNOW PARA REUTILIZAR

### 1. **Container** (Layout Padrão)

**Uso em TODAS as páginas:**
```typescript
import { Container } from "@/components/ui";

export const CampaignsDashboard = () => {
  return (
    <Container
      headerTitle="Suas Campanhas"
      headerDescription="Gerencie campanhas de marketing completas"
      containerActions={
        <Button onClick={handleCreate}>
          <Plus className="h-4 w-4" />
          Nova Campanha
        </Button>
      }
    >
      {/* Conteúdo */}
    </Container>
  );
};
```

---

### 2. **Tabs** (Para [Posts] [Calendário] [Preview])

**Padrão shadcn:**
```typescript
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui";

<Tabs defaultValue="posts">
  <TabsList>
    <TabsTrigger value="posts">Posts</TabsTrigger>
    <TabsTrigger value="calendar">Calendário</TabsTrigger>
    <TabsTrigger value="preview">Preview Feed</TabsTrigger>
  </TabsList>
  
  <TabsContent value="posts">
    <PostGridView />
  </TabsContent>
  
  <TabsContent value="calendar">
    <CalendarView />
  </TabsContent>
  
  <TabsContent value="preview">
    <InstagramFeedPreview />
  </TabsContent>
</Tabs>
```

---

### 3. **Checkbox** (Para Seleção em Lote)

**Uso:**
```typescript
import { Checkbox } from "@/components/ui";

<Checkbox
  checked={selectedPosts.has(post.id)}
  onCheckedChange={(checked) => {
    const newSet = new Set(selectedPosts);
    if (checked) {
      newSet.add(post.id);
    } else {
      newSet.delete(post.id);
    }
    setSelectedPosts(newSet);
  }}
/>
```

---

## 🎨 COMPONENTE EXISTENTE PERFEITO PARA ADAPTAR

### **InstagramPreview** (WeeklyContext)

**Localização:** `features/WeeklyContext/components/InstagramPreview.tsx`

**Já existe preview de Instagram!**

```typescript
// Pode reutilizar para Preview de Feed de Campanhas
import { InstagramPreview } from "@/features/WeeklyContext/components";

// Ou criar versão expandida:
export const InstagramFeedPreview = ({ posts }) => {
  const grid = arrangeInGrid(posts, 3);
  
  return (
    <div className="instagram-feed-container">
      <InstagramHeader username={user.instagram_handle} />
      
      <div className="grid grid-cols-3 gap-1">
        {grid.map(post => (
          <InstagramPost 
            key={post.id}
            image={post.image_url}
            caption={post.content}
          />
        ))}
      </div>
    </div>
  );
};
```

---

## 📊 REUTILIZAÇÃO DE LÓGICA DE NEGÓCIO

### WeeklyContext Integration (90% pronto!)

**Componente existente:**
```typescript
// features/WeeklyContext/hooks/useWeeklyContext.ts
// features/WeeklyContext/components/OpportunityCard.tsx
```

**Já tem:**
- ✅ Busca de oportunidades
- ✅ Card de oportunidade com score
- ✅ Botão "Criar Post" a partir de oportunidade

**Para Campaigns:**
- Adaptar `OpportunityCard` para ter botão "Adicionar à Campanha"
- Reutilizar mesma estrutura de dados

---

## 🔄 PADRÕES DE NAVEGAÇÃO E ROTAS

**Identificado em `App.tsx`:**
```typescript
<Routes>
  <Route path="/" element={<ProtectedRoute />}>
    <Route path="/ideabank" element={<IdeaBank />} />
    <Route path="/subscription" element={<Subscription />} />
    <Route path="/profile" element={<Profile />} />
    
    {/* Para Campaigns, adicionar: */}
    <Route path="/campaigns" element={<CampaignsDashboard />} />
    <Route path="/campaigns/new" element={<CampaignCreation />} />
    <Route path="/campaigns/:id" element={<CampaignDetail />} />
  </Route>
</Routes>
```

**Adicionar no menu lateral:**
```typescript
// components/DashboardLayout.tsx

const menuItems = [
  { title: "Posts", icon: ClipboardList, url: "/ideabank" },
  { title: "Campanhas", icon: Zap, url: "/campaigns" },  // NOVO
  { title: "Assinatura", icon: Wallet, url: "/subscription" },
];
```

---

## 💡 PADRÕES DE ERROR HANDLING

**Utilitário identificado:**
```typescript
// lib/utils/errorHandling.ts

import { handleApiError } from "@/lib/utils/errorHandling";

// Uso em mutations:
onError: (error: unknown) => {
  const errorResult = handleApiError(error, {
    defaultTitle: "Erro ao criar campanha",
    defaultDescription: "Não foi possível criar. Tente novamente."
  });
  toast.error(errorResult.description);
}
```

**Aplicar em TODOS os hooks de Campaigns**

---

## 🎯 RESUMO DE REUTILIZAÇÃO

| Componente | Reutilização | Ação Necessária |
|------------|--------------|-----------------|
| **AuditSystem** | 95% | Adicionar categorias campaign |
| **Analytics (Bandits)** | 100% | Criar novos decision_types |
| **CreditSystem** | 100% | Nenhuma (funciona automático) |
| **PostAIService** | 95% | Já tem lógica campaign! Expandir |
| **PromptService** | 100% | Adicionar método campaign |
| **WeeklyContext** | 90% | Adapter para campanhas |
| **Design System (UI)** | 100% | Nenhuma |
| **TanStack Query** | 100% | Seguir padrão existente |
| **React Hook Form** | 100% | Seguir padrão existente |
| **API Client (axios)** | 100% | Nenhuma |
| **Error Handling** | 100% | Nenhuma |

**Reutilização Total: ~95%**

**Apenas 5% precisa ser criado do zero:**
- Models específicos de Campaign
- Lógica de estruturas narrativas (AIDA, PAS, Funil)
- Visual coherence analyzer
- Reorganização de grid

---

*Próximo arquivo: Implementação passo-a-passo seguindo padrões...*

