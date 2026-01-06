# 🎯 TOUR COMPLETO DO SISTEMA - Guia de Navegação

**Data:** 05/01/2026  
**Ambiente:** http://localhost:5173  
**Usuário:** rogeriofr86@gmail.com / admin123

---

## 🚀 CHECKLIST PRÉ-TOUR

### ✅ Serviços Rodando

```bash
# 1. Backend Django
ps aux | grep "manage.py runserver"
# ✅ Deve mostrar processo rodando na porta 8000

# 2. Frontend React/Vite
ps aux | grep "vite"
# ✅ Deve mostrar processo rodando na porta 5173

# 3. Redis
docker ps | grep redis
# ✅ Deve mostrar container ativo

# 4. Celery Worker
ps aux | grep celery
# ✅ Deve mostrar worker processando tasks
```

### ✅ Dados de Teste

```bash
# Verificar campanhas existentes
sqlite3 db.sqlite3 "SELECT COUNT(*) FROM campaigns;"
# ✅ Deve retornar >= 5

# Verificar estilos visuais
sqlite3 db.sqlite3 "SELECT COUNT(*) FROM visual_styles WHERE is_active=1;"
# ✅ Deve retornar 20

# Verificar créditos do usuário
sqlite3 db.sqlite3 "SELECT balance FROM user_credits WHERE user_id=1;"
# ✅ Deve retornar >= 1000
```

---

## 📱 TOUR PASSO-A-PASSO

### 1️⃣ LOGIN E DASHBOARD

**URL:** http://localhost:5173/login

**Ações:**
1. Abrir navegador (Chrome recomendado)
2. Navegar para http://localhost:5173
3. Se não logado, fazer login:
   - Email: `rogeriofr86@gmail.com`
   - Senha: `admin123`
4. Verificar redirect para `/campaigns`

**✅ O que validar:**
- [ ] Login bem-sucedido sem erros
- [ ] Redirect automático para dashboard
- [ ] Token JWT salvo no localStorage
- [ ] Sem erros no console (F12)

---

### 2️⃣ DASHBOARD DE CAMPANHAS

**URL:** http://localhost:5173/campaigns

**Ações:**
1. Observar lista de campanhas
2. Verificar cards de campanha exibindo:
   - Nome
   - Status (draft/pending_approval/approved)
   - Número de posts
   - Data de criação
3. Clicar em uma campanha existente

**✅ O que validar:**
- [ ] 5 campanhas aparecem na lista
- [ ] Botão "Criar Primeira Campanha" visível
- [ ] Cards responsivos (grid adapta)
- [ ] Hover states funcionando
- [ ] Sem skeleton infinito (carregamento OK)

**🐛 Possíveis Problemas:**
- Skeleton não para de carregar → Backend offline
- Erro 401 → Token expirado, fazer logout/login
- Lista vazia → Verificar banco de dados

---

### 3️⃣ DETALHES DA CAMPANHA

**URL:** http://localhost:5173/campaigns/:id

**Ações:**
1. Observar tabs: Posts / Calendário / Analytics
2. Verificar Grid de Posts:
   - Imagens aparecem
   - Textos visíveis
   - Checkboxes funcionam
3. Selecionar 2-3 posts
4. Verificar Bulk Actions aparecem
5. Testar botão "Preview Feed"

**✅ O que validar:**
- [ ] Imagens carregam (não quebradas)
- [ ] Textos completos visíveis
- [ ] Seleção múltipla funciona
- [ ] Bulk Actions: Aprovar/Reprovar/Regenerar/Deletar
- [ ] Modal de Preview abre
- [ ] Análise de Harmonia calcula score
- [ ] Badge de qualidade aparece (Excelente/Boa/etc)

**🎨 Testar Preview Instagram Feed:**
1. Clicar "Preview Feed"
2. Verificar grade 3x3
3. Ver análise de harmonia
4. Verificar score (0-100)
5. Ler sugestões se score < 80

**✅ O que validar:**
- [ ] Grade renderiza sem quebrar
- [ ] Imagens não distorcidas (aspect ratio OK)
- [ ] Score calculado (não NaN)
- [ ] Badge colorido correto
- [ ] Sugestões aparecem se necessário

---

### 4️⃣ CRIAR NOVA CAMPANHA

**URL:** http://localhost:5173/campaigns/create

**Ações:**
1. Clicar "Criar Primeira Campanha" ou "+ Nova Campanha"
2. Verificar redirecionamento para página dedicada
3. Ver progress bar no topo (0% → 20% → 40%...)

**✅ O que validar:**
- [ ] Página abre sem erros
- [ ] Progress bar visível
- [ ] "Passo 1 de 5" exibido
- [ ] Card do wizard renderizado
- [ ] Botão "Voltar" funciona

---

### 5️⃣ STEP 1: BRIEFING

**Ações:**
1. Observar campos pré-preenchidos:
   - Objetivo da Campanha
   - Mensagem Principal
2. Verificar botão "Sugestão IA - Gerar outra"
3. Testar switches:
   - Tem cases/depoimentos?
   - Tem fotos/vídeos próprios?
4. Preencher campos adicionais se ativado
5. Clicar "Continuar →"

**✅ O que validar:**
- [ ] Campos vêm pré-preenchidos (IA)
- [ ] Botão "Gerar outra" visível
- [ ] Switches funcionam (expand/collapse)
- [ ] Validação Zod funciona (campos obrigatórios)
- [ ] Botão desabilitado se inválido
- [ ] Ao clicar "Continuar", modal abre

**🐛 Possíveis Problemas:**
- Campos vazios → Hook de sugestões não executou
- Erro ao continuar → Validação falhou (ver console)

---

### 6️⃣ WEEKLY CONTEXT MODAL

**Ações:**
1. Modal abre automaticamente após briefing
2. Ver lista de oportunidades
3. Verificar badges de categoria
4. Selecionar 1-2 oportunidades (opcional)
5. Clicar "Continuar" ou "Pular esta etapa"

**✅ O que validar:**
- [ ] Modal abre automaticamente
- [ ] Lista de oportunidades aparece
- [ ] Ou "Nenhuma oportunidade" se API falhar
- [ ] Checkboxes funcionam
- [ ] Cards clicáveis (seleção por card)
- [ ] Botão "Continuar" mostra contador (X selecionadas)
- [ ] Modal fecha ao continuar/pular

**🐛 Possíveis Problemas:**
- Modal não abre → Ver console (erro JS)
- Lista vazia → Backend retornando []
- Erro 404 → Endpoint não existe (graceful degradation OK)

---

### 7️⃣ STEP 2: ESTRUTURA

**Ações:**
1. Ver lista de 8 estruturas ranqueadas
2. Observar badges "Recomendado IA"
3. Ler descrição de cada estrutura
4. Ver previsão de posts
5. Selecionar uma estrutura
6. Clicar "Continuar →"

**✅ O que validar:**
- [ ] 8 estruturas aparecem
- [ ] Primeira tem badge "Recomendado IA"
- [ ] Ranking muda a cada reload (Thompson Sampling)
- [ ] Hover states funcionam
- [ ] Card selecionado destaca (border primary)
- [ ] Previsão de posts visível
- [ ] Botão "← Voltar" funciona

**🎯 Thompson Sampling Test:**
1. Anotar ordem das estruturas
2. Voltar (← Voltar)
3. Voltar ao step
4. Ver se ordem mudou (pode ou não)
5. Estruturas com melhor performance sobem

---

### 8️⃣ STEP 3: DURAÇÃO

**Ações:**
1. Ajustar slider de duração (7-90 dias)
2. Ver cálculo automático de posts
3. Verificar validação de limites
4. Confirmar duração
5. Clicar "Continuar →"

**✅ O que validar:**
- [ ] Slider funciona (arrastar)
- [ ] Número de posts calcula automaticamente
- [ ] Validação: mín 7 dias, máx 90 dias
- [ ] Texto explicativo claro
- [ ] Progress bar avança para 60%

---

### 9️⃣ STEP 4: ESTILOS VISUAIS

**Ações:**
1. Scrollar pelos 20 estilos
2. Ver previews AI-gerados
3. Observar ranking (Thompson Sampling)
4. Selecionar 2-3 estilos
5. Verificar contador "X/5 selecionados"
6. Tentar selecionar 6º (deve bloquear)
7. Clicar "Continuar →"

**✅ O que validar:**
- [ ] 20 estilos carregam
- [ ] Previews não quebradas
- [ ] Grid responsivo (3 cols desktop, 1 col mobile)
- [ ] Seleção múltipla funciona
- [ ] Contador atualiza
- [ ] Limite máximo (5) respeitado
- [ ] Botão desabilitado se < 1 selecionado
- [ ] Progress bar → 80%

**🎨 Estilos Esperados:**
- Minimal Professional
- Bold & Vibrant
- Tech & Futuristic
- Warm & Human
- Corporate Blue
- Storytelling Cinematic
- Flat Design Modern
- Luxury Premium
- Playful Colorful
- Dark Mode Elegant
- (+ 10 outros)

---

### 🔟 STEP 5: REVIEW

**Ações:**
1. Ver resumo completo da campanha:
   - Objetivo
   - Estrutura escolhida
   - Duração
   - Estilos selecionados
2. Verificar estimativa de créditos
3. Testar Radio Group de qualidade:
   - ⚡ Geração Rápida (Fast)
   - ✨ Geração Premium
4. Ver diferenças de tempo/custo
5. Clicar "Gerar Campanha!"

**✅ O que validar:**
- [ ] Resumo completo aparece
- [ ] Dados corretos (do wizard)
- [ ] Radio group de qualidade funciona
- [ ] Estimativas atualizam ao trocar qualidade
- [ ] Fast: ~3-4min, R$ X
- [ ] Premium: ~5-6min, R$ Y
- [ ] Botão "← Voltar" funciona
- [ ] Progress bar → 100%

**💰 Estimativas Esperadas (8 posts):**
- Fast: R$ 1.84 (~4 min)
- Premium: R$ 2.16 (~6 min)

---

### 1️⃣1️⃣ GERAÇÃO ASSÍNCRONA

**Ações:**
1. Após clicar "Gerar Campanha!"
2. Ver loading overlay (~2s)
3. Redirect para `/campaigns/:id`
4. Ver progress bar aparecendo
5. Observar polling (atualiza a cada 2s)
6. Ver steps:
   - "Gerando texto 1/8..."
   - "Gerando texto 2/8..."
   - ...
   - "Gerando imagem 1/8..."
   - "Gerando imagem 2/8..."
7. Aguardar conclusão (4-6 min)
8. Ver toast "Campanha gerada com sucesso!"

**✅ O que validar:**
- [ ] Redirect automático para detalhes
- [ ] Progress bar aparece
- [ ] Polling ativo (ver Network tab)
- [ ] Status atualiza: pending → processing → completed
- [ ] Percentual calcula corretamente
- [ ] Ação atual exibida ("Gerando texto X/Y")
- [ ] Posts aparecem conforme gerados
- [ ] Imagens carregam
- [ ] Toast de sucesso ao finalizar
- [ ] Progress bar desaparece

**🐛 Possíveis Problemas:**
- Progress não atualiza → Celery worker offline
- Travou em X% → Ver logs do Celery
- Erro 500 → Ver backend logs
- Imagens não aparecem → SQLite locked, rodar script

**🔧 Se Imagens Não Aparecerem (SQLite Dev):**
```bash
cd PostNow-REST-API
source venv/bin/activate
python scripts/generate_campaign_images.py --campaign-id <ID>
```

---

### 1️⃣2️⃣ VALIDAR POSTS GERADOS

**Ações:**
1. Após geração completa
2. Ver grid de posts
3. Abrir 2-3 posts para ler
4. Verificar qualidade:
   - Texto coerente
   - Hashtags relevantes
   - CTAs presentes
   - Imagens alinhadas com texto
   - Estilo visual consistente

**✅ O que validar:**
- [ ] 8 posts criados (ou N conforme escolhido)
- [ ] Todos têm imagem
- [ ] Textos bem escritos (português correto)
- [ ] Hashtags no final (#relevante #nicho)
- [ ] CTAs claros ("Comente", "Salve", etc)
- [ ] Imagens profissionais (não pixeladas)
- [ ] Harmonia visual entre posts

**🔍 Quality Validator - O que foi auto-corrigido:**
- Textos longos resumidos (max 2200 chars)
- CTAs adicionados se faltavam
- Hashtags formatadas corretamente
- Emojis excessivos removidos

---

### 1️⃣3️⃣ TESTAR BULK ACTIONS

**Ações:**
1. Selecionar 3-4 posts (checkboxes)
2. Ver barra de Bulk Actions aparecer
3. Testar cada ação:
   - **Aprovar Todos:** Ver confirmação
   - **Reprovar Todos:** Ver confirmação
   - **Regenerar Todos:** Ver modal (SKIP em dev)
   - **Deletar Todos:** Ver confirmação

**✅ O que validar:**
- [ ] Barra aparece ao selecionar
- [ ] Contador correto (X posts selecionados)
- [ ] Aprovar funciona (status muda)
- [ ] Reprovar funciona
- [ ] Deletar pede confirmação
- [ ] Actions aplicam em batch
- [ ] Loading states durante ações

**⚠️ Regenerar:**
- Em dev (SQLite): Pode dar erro de concorrência
- Em prod (MySQL): Funciona 100%

---

### 1️⃣4️⃣ PREVIEW INSTAGRAM FEED

**Ações:**
1. Clicar "Preview Feed" ou "Ver no Feed"
2. Modal abre com grade 3x3
3. Ver 9 primeiros posts (ou menos se < 9)
4. Verificar análise de harmonia:
   - Score (0-100)
   - Badge colorido
   - Sugestões (se score < 80)
5. Fechar modal

**✅ O que validar:**
- [ ] Modal abre sem erros
- [ ] Grade renderiza corretamente
- [ ] Aspect ratio preservado (quadrado)
- [ ] Score calculado e exibido
- [ ] Badge correto:
   - 90-100: Verde "Excelente"
   - 80-89: Azul "Boa"
   - 70-79: Amarelo "Regular"
   - < 70: Vermelho "Precisa Melhorar"
- [ ] Sugestões claras se < 80
- [ ] Modal fecha (X ou fora)

**🎨 Harmonia Visual - Como Funciona:**
- Analisa cores dominantes
- Verifica variedade de composição
- Detecta repetição excessiva
- Sugere ajustes

---

## 🎯 CHECKLIST FINAL DE VALIDAÇÃO

### ✅ FUNCIONALIDADES CORE

- [ ] Login funciona
- [ ] Dashboard lista campanhas
- [ ] Wizard completo (5 steps)
- [ ] Weekly Context Modal abre
- [ ] Thompson Sampling ranqueia
- [ ] 20 estilos carregam
- [ ] Review mostra resumo
- [ ] Geração assíncrona funciona
- [ ] Progress tracking atualiza
- [ ] Posts gerados com qualidade
- [ ] Imagens aparecem
- [ ] Grid de aprovação funciona
- [ ] Bulk Actions aplicam
- [ ] Preview Instagram abre
- [ ] Análise de harmonia calcula

### ✅ UX E PERFORMANCE

- [ ] Sem erros no console
- [ ] Sem warnings críticos
- [ ] Loading states visíveis
- [ ] Transições suaves
- [ ] Responsivo (mobile + desktop)
- [ ] Tooltips explicativos
- [ ] Toasts informativos
- [ ] Validações claras

### ✅ EDGE CASES

- [ ] Logout funciona
- [ ] Token expirado redireciona
- [ ] 404 em rota inválida
- [ ] Erro de API mostra fallback
- [ ] Sem créditos bloqueia geração
- [ ] Limite de posts respeitado

---

## 🐛 PROBLEMAS CONHECIDOS E SOLUÇÕES

### 1. Imagens Não Aparecem (Dev)

**Causa:** SQLite não suporta concorrência (database locked)

**Solução:**
```bash
cd PostNow-REST-API
source venv/bin/activate
python scripts/generate_campaign_images.py --campaign-id <ID>
```

**Status:** ✅ Funciona 100% em produção (MySQL)

---

### 2. Weekly Context Lista Vazia

**Causa:** Service retorna mock data vazio

**Solução:** Normal, é mock para demonstração

**Status:** ✅ Graceful degradation, não quebra

---

### 3. Progress Não Atualiza

**Causa:** Celery worker não rodando

**Solução:**
```bash
cd PostNow-REST-API
celery -A Sonora_REST_API worker --loglevel=info
```

**Status:** ✅ Verificar antes de demonstração

---

### 4. Drag & Drop Não Aparece

**Causa:** Componente não integrado (intencional)

**Solução:** Será integrado em Sprint 1

**Status:** 📝 Código pronto, UI pendente

---

## 📸 MOMENTOS-CHAVE PARA SCREENSHOTS

### Screenshot 1: **Dashboard de Campanhas**
- Capturar lista com 5 campanhas
- Cards visíveis com status

### Screenshot 2: **Wizard - Briefing Step**
- Campos pré-preenchidos
- Botão "Sugestão IA"

### Screenshot 3: **Weekly Context Modal**
- Oportunidades listadas
- Seleção múltipla

### Screenshot 4: **Seleção de Estilos**
- Grid 3x3 com previews
- Badges de ranking

### Screenshot 5: **Review Step**
- Resumo completo
- Radio de qualidade (Fast/Premium)

### Screenshot 6: **Progress Tracking**
- Barra de progresso
- Ação atual ("Gerando texto X/Y")

### Screenshot 7: **Grid de Posts Gerados**
- 8 posts com imagens
- Checkboxes de seleção

### Screenshot 8: **Preview Instagram Feed**
- Grade 3x3
- Análise de harmonia (score verde)

---

## 🎬 ROTEIRO DE DEMONSTRAÇÃO (5 MIN)

### Minuto 1: **Contexto**
> "Sistema de criação de campanhas com IA. Automatiza geração de posts para Instagram com harmonia visual."

### Minuto 2: **Wizard Rápido**
> "5 passos simples: Briefing (auto-preenchido por IA) → Weekly Context (oportunidades) → Estrutura (Thompson Sampling) → Duração → Estilos (20 opções)"

### Minuto 3: **Geração Assíncrona**
> "Celery + Redis. Não trava UI. Progress tracking em tempo real. 4-6 minutos para 8 posts."

### Minuto 4: **Quality Validator**
> "Valida qualidade automaticamente. Auto-corrige textos longos, adiciona CTAs, formata hashtags."

### Minuto 5: **Preview e Harmonia**
> "Preview Instagram Feed. Análise de harmonia visual. Score 0-100. Sugestões de melhoria."

**Finalizar:**
> "95% funcional. Falta integrar Drag & Drop e Jornadas Adaptativas (2-3 semanas)."

---

**Checklist Pré-Demo:**
- [ ] Backend rodando (port 8000)
- [ ] Frontend rodando (port 5173)
- [ ] Celery worker ativo
- [ ] Redis online
- [ ] 5 campanhas no banco
- [ ] 10.000 créditos no usuário
- [ ] Login testado (rogeriofr86@gmail.com / admin123)
- [ ] Console limpo (sem erros)

**Tempo Total de Tour:** 30-45 minutos  
**Tempo de Demo:** 5-10 minutos

