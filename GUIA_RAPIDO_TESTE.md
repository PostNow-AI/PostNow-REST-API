# 🧪 GUIA RÁPIDO - Como Testar Sistema de Campanhas

**Tempo total:** 20-30 minutos  
**Pré-requisito:** Backend e Frontend rodando

---

## 🚀 PASSO 1: Iniciar Servidores (2min)

### Terminal 1 - Backend
```bash
cd /Users/rogerioresende/Desktop/Postnow/PostNow-REST-API
source venv/bin/activate
python manage.py runserver
```

**Verificar:** `http://localhost:8000/admin` deve abrir

### Terminal 2 - Frontend
```bash
cd /Users/rogerioresende/Desktop/Postnow/PostNow-UI
npm run dev
```

**Verificar:** `http://localhost:5175` deve abrir (ou porta que aparecer)

---

## 👤 PASSO 2: Criar Usuário de Teste (3min)

### Opção A: Via Django Admin (Mais Fácil)

1. Abrir: `http://localhost:8000/admin`
2. Login com superuser existente
3. Users → Add User
   - Username: `teste_campanhas`
   - Password: `teste123`
4. Creator Profiles → Add
   - User: teste_campanhas
   - Business Name: "Teste Campanhas"
   - Specialization: "Consultoria"
   - (Preencher campos básicos)
   - ✅ Marcar: step_1_completed, step_2_completed, onboarding_completed

### Opção B: Via Shell (Mais Rápido)

```bash
python manage.py shell

from django.contrib.auth.models import User
from CreatorProfile.models import CreatorProfile

# Criar usuário
user = User.objects.create_user(
    username='teste_campanhas',
    email='teste@campanhas.com',
    password='teste123'
)

# Criar perfil
CreatorProfile.objects.create(
    user=user,
    business_name="Consultoria Teste",
    specialization="Marketing Digital",
    business_description="Empresa de testes",
    target_audience="Empresários",
    voice_tone="Profissional",
    color_1="#1E40AF",
    step_1_completed=True,
    step_2_completed=True,
    onboarding_completed=True
)
```

---

## 🎯 PASSO 3: Testar Fluxo de Campanha (15min)

### 3.1. Login (1min)

1. Abrir: `http://localhost:5175`
2. Fazer login com: `teste_campanhas` / `teste123`
3. Deve redirecionar para `/ideabank` (dashboard)

### 3.2. Acessar Campanhas (1min)

1. Menu lateral → **"Campanhas"** (ícone ⚡)
2. Deve mostrar tela vazia: "Nenhuma campanha criada ainda"
3. Botão: **"Nova Campanha"** ou **"Criar Primeira Campanha"**

### 3.3. Criar Campanha - Briefing (3min)

1. Clicar "Nova Campanha"
2. Dialog abre com **"Briefing"**
3. Preencher:
   - Objetivo: "Posicionar como autoridade em marketing digital"
   - Mensagem: "Marketing não é custo, é investimento"
   - Tem cases? **SIM**
   - Casos: "Cliente X aumentou vendas em 40%"
4. Clicar **"Continuar"**

**✅ Verificar:** Avançou para próximo step sem erros

### 3.4. Escolher Estrutura (2min)

1. Deve mostrar 4 cards de estruturas:
   - AIDA (Recomendado) - 87%
   - Funil de Conteúdo - 81%
   - PAS - 72%
   - Sequência Simples - 89%
2. Clicar em **"AIDA"**

**✅ Verificar:** Avançou para escolha de estilos (ou duração)

### 3.5. Gerar Campanha (CRÍTICO - 5min)

1. Se pedir estilos: Escolher 2-3
2. Se pedir duração: Aceitar sugerido (12-14 dias)
3. Clicar **"Gerar Campanha"**
4. **Loading deve aparecer** (com progress bar)
5. Aguardar geração (30-60seg esperado)

**✅ Verificar:**
- Loading não trava
- Progress bar atualiza
- Não dá erro 500
- Após concluir: Grid de posts aparece

### 3.6. Grid de Posts (3min)

1. Deve mostrar **8-12 posts** em grid 3 colunas
2. Cada post tem:
   - Checkbox
   - Thumbnail de imagem
   - Preview de texto
   - Data e horário
   - Fase (Atenção, Interesse, etc)
   - Ações: 👁️ ✏️ 🔄 ❌

**✅ Testar:**
- Marcar 2-3 checkboxes
- Clicar "Aprovar Selecionados"
- Clicar "Aprovar Todos"

### 3.7. Preview Instagram (2min)

1. Clicar tab **"Preview Feed"** (se disponível)
2. Deve mostrar simulação de grid 3x3 do Instagram
3. Com header @seuperfil

**✅ Verificar:** Preview renderiza corretamente

---

## 🐛 O QUE PROCURAR (Bugs Prováveis)

### Backend

- ❌ Erro 500 ao gerar campanha
- ❌ Timeout na geração (>60seg)
- ❌ Posts não são criados
- ❌ Créditos não são deduzidos

### Frontend

- ❌ Loading infinito
- ❌ Wizard não avança
- ❌ Grid não aparece
- ❌ Checkboxes não funcionam
- ❌ Imagens não carregam

### Integração

- ❌ CORS errors
- ❌ 401 Unauthorized
- ❌ Data não sincroniza

---

## 📝 COMO REPORTAR BUGS

**Formato:**

```
BUG #X: [Título curto]

COMO REPRODUZIR:
1. Fazer login
2. Clicar em X
3. Preencher Y
4. Erro acontece

ERRO OBSERVADO:
- Mensagem: "..."
- Console: [screenshot ou texto]
- Network: [status code]

ESPERADO:
- Deveria fazer Z

SEVERIDADE: Alta/Média/Baixa
```

---

## ✅ SUCESSO ESPERADO

Se tudo funcionar:

1. ✅ Campanha criada em 2-5min
2. ✅ 8-12 posts gerados automaticamente
3. ✅ Grid mostrando todos posts
4. ✅ Aprovação em lote funcionando
5. ✅ Preview do Instagram renderizando

**Se isso acontecer:** 🎉 **MVP FUNCIONAL!**

---

## 🎯 APÓS TESTES

**Se funcionar bem:**
- Parte para beta com 10 usuários
- Documento está pronto

**Se encontrar bugs:**
- Me reporte (formato acima)
- Eu corrijo imediatamente
- Testamos de novo

---

**Boa sorte nos testes! Estou aguardando seu feedback!** 🚀

**Dica:** Comece simples (criar 1 campanha pequena), depois teste cenários complexos.

