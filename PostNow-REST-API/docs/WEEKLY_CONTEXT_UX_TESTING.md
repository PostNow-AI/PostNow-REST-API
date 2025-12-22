# Weekly Context - Guia de Testes UX Híbrida

Este documento detalha como testar as 3 versões da experiência de geração de posts a partir do Weekly Context.

## Controle de Versão (Feature Flag)

No arquivo `PostNow-UI/src/features/WeeklyContext/index.tsx`, linha ~11:

```typescript
const GENERATION_UI_VERSION = "sheet" as "modal" | "sheet";
```

- `"modal"` → Usa V1/V2 (Dialog com customização)
- `"sheet"` → Usa V3 (Sheet premium com preview)

---

## ✅ V1/V2: Modal com Customização

### Como Testar

1. Defina `GENERATION_UI_VERSION = "modal"`
2. Acesse Radar Semanal
3. Clique em "Criar Post" em qualquer card

### Fluxo Esperado

**Etapa 1 - Customização:**
- [ ] Modal abre com título "Personalizar Geração"
- [ ] Mostra preview da oportunidade selecionada
- [ ] Form com campos:
  - Objetivo do Post (select)
  - Tipo de Conteúdo (select)
  - Instruções Adicionais (textarea opcional)
  - Gerar Imagem (switch)
- [ ] Botões "Cancelar" e "Gerar Ideia"

**Etapa 2 - Gerando:**
- [ ] Ao clicar "Gerar Ideia", modal atualiza para loading state
- [ ] Spinner animado visível
- [ ] Mensagem "Gerando sua ideia..."
- [ ] Preview da oportunidade mantido
- [ ] Tempo estimado exibido

**Etapa 3 - Sucesso:**
- [ ] Modal atualiza para success state
- [ ] Título muda para "Ideia Gerada com Sucesso!"
- [ ] Preview do post gerado:
  - Texto renderizado (com HTML se houver)
  - Imagem (se gerada)
  - Score e modelo IA exibidos
- [ ] Botões:
  - "Gerar Nova Versão" (volta para etapa 1)
  - "Ver no IdeaBank" (fecha e navega)

### Cenários de Teste

**Teste 1: Geração Padrão**
- Não preencher instruções adicionais
- Deixar objetivo e tipo padrão
- Desativar geração de imagem
- Verificar post gerado com sucesso

**Teste 2: Customização Completa**
- Preencher instruções: "Tom humorístico, mencione estatísticas"
- Mudar objetivo para "Vendas"
- Mudar tipo para "Carrossel"
- Ativar geração de imagem
- Verificar customizações aplicadas no post

**Teste 3: Regeneração**
- Gerar um post
- Clicar em "Gerar Nova Versão"
- Verificar volta para form de customização
- Alterar parâmetros
- Gerar novamente
- Verificar post diferente criado

**Teste 4: Navegação para IdeaBank**
- Gerar um post
- Clicar em "Ver no IdeaBank"
- Verificar navegação para `/ideabank`
- Verificar post aparece na lista
- Verificar cache atualizado

---

## ✨ V3: Sheet Premium com Preview

### Como Testar

1. Defina `GENERATION_UI_VERSION = "sheet"`
2. Acesse Radar Semanal
3. Clique em "Criar Post" em qualquer card

### Fluxo Esperado

**Etapa 1/3 - Customização:**
- [ ] Sheet abre do lado direito (não cobre toda tela)
- [ ] Radar Semanal permanece visível à esquerda
- [ ] Header mostra "Etapa 1/3"
- [ ] Form de customização idêntico ao Modal
- [ ] Oportunidade destacada em card colorido

**Etapa 2/3 - Gerando:**
- [ ] Sheet atualiza para loading state
- [ ] Header mostra "Etapa 2/3"
- [ ] Progress bar com animação (0% → 100%)
- [ ] Mensagens dinâmicas:
  - "Analisando fonte..." (0-25%)
  - "Processando contexto..." (25-50%)
  - "Gerando texto..." (50-75%)
  - "Refinando conteúdo..." (75-95%)
  - "Finalizando..." (95-100%)
- [ ] Card mostra oportunidade sendo processada

**Etapa 3/3 - Preview e Edição:**
- [ ] Sheet atualiza para preview state
- [ ] Header mostra "Etapa 3/3"
- [ ] Sistema de Tabs visível:
  - Tab "Texto"
  - Tab "Imagem"
  - Tab "Preview"

**Tab "Texto":**
- [ ] Textarea com conteúdo gerado
- [ ] Conteúdo é editável
- [ ] Botão "Copiar" funcional
- [ ] Metadados exibidos (modelo IA, tipo)
- [ ] Indicador de edição inline visível

**Tab "Imagem":**
- [ ] Se imagem gerada:
  - Imagem renderizada
  - Botão "Regenerar Imagem"
  - Botão "Baixar"
- [ ] Se sem imagem:
  - Estado vazio com mensagem
  - Botão "Voltar e Ativar"

**Tab "Preview":**
- [ ] Mock do Instagram renderizado:
  - Header com nome do perfil
  - Imagem (se houver)
  - Texto do post
  - Hashtags destacadas em azul
  - Ícones de ação (like, comment, send, save)
  - Timestamp "Agora mesmo"
- [ ] Preview responsivo

**Ações Finais:**
- [ ] Botão "← Voltar" (retorna para etapa 1)
- [ ] Botão "Salvar e Ver no IdeaBank" (fecha e navega)
- [ ] Botão "Salvar e Criar Outro" (salva mas mantém sheet aberta)

### Cenários de Teste V3

**Teste 1: Fluxo Completo sem Parar**
- Clicar "Criar Post"
- Preencher customização
- Aguardar geração
- Navegar entre tabs
- Editar texto na tab "Texto"
- Ver preview no mock do Instagram
- Salvar e ver no IdeaBank

**Teste 2: Edição Inline**
- Gerar post
- Ir para tab "Texto"
- Editar conteúdo (adicionar/remover linhas)
- Ir para tab "Preview"
- Verificar mudanças refletidas no preview
- Salvar

**Teste 3: Criar Múltiplos Posts**
- Gerar primeiro post
- Clicar "Salvar e Criar Outro"
- Verificar:
  - Sheet permanece aberta
  - Form resetado para defaults
  - Volta para etapa 1/3
- Gerar segundo post
- Repetir processo

**Teste 4: Voltar e Modificar**
- Gerar post
- Ver preview
- Clicar "← Voltar"
- Verificar volta para form de customização
- Alterar parâmetros
- Gerar novamente
- Verificar novo post criado

**Teste 5: Responsividade**
- Testar em tela desktop (1920px)
  - Sheet ocupa ~50% da largura
  - Radar visível ao lado
- Testar em tablet (768px)
  - Sheet ocupa ~70% da largura
- Testar em mobile (375px)
  - Sheet ocupa 100% da largura
  - Radar temporariamente oculto

---

## 🎯 Checklist Rápido (5 minutos)

### V1/V2 (Modal)
- [ ] Clicar "Criar Post" abre modal
- [ ] Customizar e gerar funciona
- [ ] Preview aparece
- [ ] "Ver no IdeaBank" navega corretamente
- [ ] "Gerar Nova Versão" funciona

### V3 (Sheet)
- [ ] Clicar "Criar Post" abre sheet lateral
- [ ] Radar permanece visível
- [ ] Progresso das etapas 1/3 → 2/3 → 3/3
- [ ] Progress bar anima durante geração
- [ ] 3 tabs funcionam (Texto, Imagem, Preview)
- [ ] Edição inline funciona
- [ ] Preview do Instagram renderiza
- [ ] "Salvar e Criar Outro" mantém sheet aberta

---

## 🐛 Troubleshooting

### Modal/Sheet não abre
- Verificar console do navegador
- Confirmar `generatingOpportunity` não é null
- Verificar componente Dialog/Sheet importado corretamente

### Geração não completa
- Verificar network tab: chamada para `/api/v1/ideabank/generate/post-idea/`
- Confirmar status 200 ou ver erro retornado
- Verificar créditos suficientes
- Verificar logs do backend

### Preview não renderiza
- Verificar `generatedPost` não é null
- Confirmar estrutura do response tem `post` e `idea`
- Verificar `content` ou `content_preview` existe

### Tabs não mudam
- Verificar ShadCN Tabs instalado corretamente
- Confirmar state de tab sendo gerenciado
- Ver console para erros de renderização

---

## 📊 Métricas a Coletar (Futuro)

### V1/V2
- Taxa de abertura do modal
- Taxa de customização vs padrão
- Taxa de regeneração
- Taxa de navegação para IdeaBank
- Tempo médio no modal

### V3 Adicionais
- Tempo médio na sheet
- Navegação entre tabs (qual mais usada)
- Taxa de edição inline
- Uso de "Salvar e Criar Outro" (fluxo contínuo)
- Cliques em "Voltar" (indica indecisão)

---

## ✅ Critérios de Aprovação

Para considerar a feature **pronta para produção**:

### V1/V2
- [ ] Modal abre e fecha corretamente
- [ ] Geração completa sem erros
- [ ] Preview renderiza conteúdo
- [ ] Navegação funciona
- [ ] Regeneração funciona
- [ ] Erros tratados graciosamente

### V3 Adicional
- [ ] Sheet não interfere com Radar
- [ ] Sistema de etapas flui naturalmente
- [ ] Progress bar sincroniza com geração
- [ ] Todas as 3 tabs funcionam
- [ ] Edição inline salva mudanças
- [ ] Preview do Instagram preciso
- [ ] Fluxo contínuo funciona

---

**Data de Validação**: ___/___/______  
**Versão Testada**: [ ] V1/V2 Modal [ ] V3 Sheet  
**Status**: [ ] Aprovado [ ] Pendente [ ] Bugs Encontrados

