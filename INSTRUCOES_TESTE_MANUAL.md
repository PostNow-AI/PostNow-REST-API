# 🧪 TESTE MANUAL - INSTRUÇÕES

**Status:** Logs adicionados para diagnóstico

---

## 📋 FAÇA AGORA (PASSO A PASSO)

### 1️⃣ Hard Refresh no Navegador

**Importante:** Isso vai limpar o cache do React Query

- **Mac:** `Cmd + Shift + R`
- **Windows/Linux:** `Ctrl + Shift + R`
- **Ou:** Abra DevTools → Clique direito no botão Reload → "Empty Cache and Hard Reload"

---

### 2️⃣ Abra o DevTools Console

Pressione `F12` ou `Cmd + Option + I` (Mac)

---

### 3️⃣ Vá para `/campaigns/8`

A página vai recarregar.

---

### 4️⃣ Procure por logs no Console

Você deve ver:

```javascript
🔍 Campaign data: {
  id: 8,
  posts_count: 6,
  first_post: {...},
  has_ideas: true,  // ← DEVE SER TRUE!
  first_idea: {
    id: 407,
    content: "Você já pensou...",
    image_url: null
  }
}
```

---

### 5️⃣ Analise o Resultado

#### ✅ Se `has_ideas: true`
→ Os dados estão chegando!
→ Problema é no componente `PostGridView`

#### ❌ Se `has_ideas: false` ou `undefined`
→ React Query está com cache antigo
→ Preciso invalidar o cache de forma diferente

---

### 6️⃣ Verifique a Tab Network

1. Vá para a tab "Network" no DevTools
2. Procure por: `GET /api/v1/campaigns/8/`
3. Clique na requisição
4. Veja a "Response"
5. Procure por `campaign_posts[0].post.ideas`

---

## 🔍 O QUE DESCOBRIMOS ATÉ AGORA

✅ **Backend está OK:**
- Dados existem no banco
- Serializer funciona
- API retorna correto

❓ **Frontend pode ter:**
- Cache antigo do React Query
- Componente não renderizando dados

---

## 📊 ME ENVIE

Após fazer o teste acima, me envie:

1. ✅ O que apareceu no console (log `🔍 Campaign data`)
2. ✅ Screenshot da resposta HTTP em Network
3. ✅ Se os textos dos posts apareceram ou não

---

**Com essas informações, vou saber exatamente onde está o problema!**

