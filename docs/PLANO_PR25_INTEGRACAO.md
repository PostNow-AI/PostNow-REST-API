# Plano de Integração PR #25 ao Main

## Contexto

O PR #25 (`feat/prompts`) contém funcionalidades úteis, mas não pode ser mergeado como está porque:
1. Cria arquivo novo em vez de adicionar ao existente
2. Remove contexto pesquisado dos prompts (perda de funcionalidade)
3. Tem mapeamento de cores incompleto

Este documento define o que será integrado e como.

---

## ✅ O que será implementado AGORA

### 1. Sistema de Cores com `webcolors`
**Problema:** Mapeamento manual de 16 cores não cobre todas as paletas do frontend (30+ cores) nem cores extraídas de logos.

**Solução:** Usar biblioteca `webcolors` que converte qualquer HEX para o nome CSS3 mais próximo (147 cores).

**Arquivo:** `services/ai_prompt_service.py`

```python
import webcolors

def _hex_to_color_name(hex_color: str) -> str:
    """Converte qualquer HEX para o nome de cor mais próximo."""
    try:
        rgb = webcolors.hex_to_rgb(hex_color)
        # Tenta match exato primeiro
        return webcolors.rgb_to_name(rgb)
    except ValueError:
        # Se não encontrar, busca a cor mais próxima
        return _find_closest_color(rgb)

def _find_closest_color(rgb):
    """Encontra o nome da cor CSS3 mais próxima usando distância Euclidiana."""
    min_distance = float('inf')
    closest_name = None

    for hex_code, name in webcolors.CSS3_HEX_TO_NAMES.items():
        r, g, b = webcolors.hex_to_rgb(hex_code)
        distance = (r - rgb[0])**2 + (g - rgb[1])**2 + (b - rgb[2])**2
        if distance < min_distance:
            min_distance = distance
            closest_name = name

    return closest_name

def _format_colors_for_prompt(color_palette: list) -> str:
    """Formata paleta de cores para uso em prompts de IA."""
    if not color_palette:
        return "Cores não definidas"

    descriptions = []
    for hex_color in color_palette:
        if hex_color:
            name = _hex_to_color_name(hex_color)
            descriptions.append(f"- {name}")

    return "\n".join(descriptions) if descriptions else "Cores não definidas"
```

**Dependência:** `pip install webcolors`

---

### 2. Instruções Detalhadas de Logo
**Problema:** A IA às vezes não renderiza o logo corretamente. Instrução atual é vaga:
```
- Renderize a logomarca quando anexada.
```

**Solução:** Adicionar seção detalhada ao prompt de imagem.

**Arquivo:** `services/ai_prompt_service.py` → método `image_generation_prompt`

```python
def _build_logo_section(business_name: str, color_palette: list, position: str = "bottom-right corner") -> str:
    """Gera instruções detalhadas para preservação de logo."""
    colors_formatted = _format_colors_for_prompt(color_palette)

    return f"""
**LOGO (Elemento Preservado):**

Usando a imagem do logo de "{business_name}" anexada, posicione-a no {position}
com aproximadamente 8% da largura da imagem, garantindo que permaneça claramente
visível mas não dominante.

PRESERVAR EXATAMENTE: a forma e geometria do ícone, o texto "{business_name}"
(grafia e arranjo), e as proporções gerais do logo. O logo deve aparecer
exatamente como fornecido no anexo.

ALTERAR APENAS as cores do logo se necessário para contraste com o fundo.
Escolher das cores da paleta da marca que proporcionem máxima legibilidade:
{colors_formatted}

Manter o logo inalterado em todos os outros aspectos. Garantir que todas as
partes do logo estejam totalmente visíveis e legíveis contra qualquer cor de fundo.
""".strip()
```

---

### 3. Sistema de Análise Histórica
**O que faz:** Analisa posts anteriores para evitar repetição.

**Novo método em** `services/ai_prompt_service.py`:

```python
def build_historical_analysis_prompt(self, post_data: dict) -> list[str]:
    """Analisa histórico para evitar conteúdo repetitivo."""
    # Copiar do PR #25: IdeaBank/services/prompt_service.py linhas 1057-1200
```

---

### 4. Sistema de Posts Automáticos
**O que faz:** Gera posts baseados na análise histórica, garantindo originalidade.

**Novo método em** `services/ai_prompt_service.py`:

```python
def build_automatic_post_prompt(self, analysis_data: dict = None) -> list[str]:
    """Gera post automático baseado em análise histórica."""
    # Copiar do PR #25: IdeaBank/services/prompt_service.py linhas 1203-1366
```

---

### 5. Edição de Conteúdo com Preservação
**O que é:** Modo de edição que altera APENAS o que foi solicitado, preservando o resto.

**Diferença do atual:**
| Atual (regenerate) | Novo (edit) |
|--------------------|-------------|
| Recria o post inteiro | Edita só o que foi pedido |
| Usa contexto pesquisado | Preserva identidade original |

**Arquivo:** `services/ai_prompt_service.py`

```python
def build_content_edit_prompt(self, current_content: str, instructions: str = None) -> str:
    """
    Prompt para edição de conteúdo preservando identidade.
    Diferente de regenerate que recria o post inteiro.
    """
    instructions_section = ""
    if instructions:
        instructions_section = f"\n- Alterações solicitadas: {instructions}"

    return f"""
Você é um especialista em ajustes e refinamentos de conteúdo para marketing digital.
Sua missão é editar o material já criado (copy) mantendo sua identidade visual, estilo e tom,
alterando **apenas o que for solicitado**.

### DADOS DE ENTRADA:
- Conteúdo original: {current_content}{instructions_section}

### REGRAS PARA EDIÇÃO:

1. **Mantenha toda a identidade visual e estilística do conteúdo original**
2. **Modifique somente o que foi solicitado**, sem alterar nada além disso
3. Ajuste apenas as frases, palavras ou CTA especificadas
4. Nunca descaracterize o material já feito - a ideia é **refinar e ajustar**, não recriar
5. O resultado deve estar pronto para uso imediato

### SAÍDA ESPERADA:
- Versão revisada do conteúdo com as alterações solicitadas aplicadas
- Todo o restante deve permanecer idêntico ao original
- Material final pronto para publicação
"""
```

**Nota:** Este método coexiste com `regenerate_standalone_post_prompt`. O endpoint pode escolher qual usar baseado no tipo de edição solicitada.

---

### 6. Edição de Imagem com Preservação
**O que é:** Modo de edição que altera APENAS o que foi solicitado na imagem.

**Exemplo:** "Mude a cor do fundo para azul" → muda SÓ o fundo, mantém todo o resto.

**Arquivo:** `services/ai_prompt_service.py`

```python
def build_image_edit_prompt(self, user_prompt: str) -> str:
    """
    Prompt para edição de imagem preservando identidade visual.
    Diferente de image_generation que cria imagem nova.
    """
    return f"""
Você é um especialista em design digital e edição de imagens para marketing.
Sua missão é editar a imagem já criada, mantendo **100% da identidade visual,
layout, estilo, cores e elementos originais**, alterando **apenas o que for solicitado**.

### DADOS DE ENTRADA:
- Imagem original: [IMAGEM ANEXADA]
- Alterações solicitadas: {user_prompt if user_prompt else 'crie uma variação sutil mantendo a identidade'}

### REGRAS PARA EDIÇÃO:

1. **Nunca recrie a imagem do zero.**
   O design, estilo, paleta de cores, tipografia e identidade visual devem
   permanecer exatamente iguais à arte original.

2. **Aplique apenas as mudanças solicitadas.**
   Exemplo: se o pedido for "mudar o título para X", altere somente o texto
   do título, mantendo a fonte, cor, tamanho e posicionamento original.

3. **Não adicione novos elementos** que não foram solicitados.
   O layout deve permanecer idêntico.

4. **Respeite sempre a logomarca oficial** caso já esteja aplicada na arte.

5. O resultado deve parecer exatamente a mesma imagem original,
   com apenas os pontos ajustados conforme solicitado.

### SAÍDA ESPERADA:
- A mesma imagem original, com apenas as alterações solicitadas aplicadas
- Nada além do que foi pedido deve ser modificado
- Design final pronto para uso, fiel ao original
"""
```

**Nota:** Este método coexiste com `image_generation_prompt`. O endpoint pode escolher qual usar baseado no tipo de operação.

---

## ❌ O que NÃO será implementado

### Capas de Reels/Stories
**Motivo:** Não usado atualmente.

**Funções descartadas:**
- `_build_reel_image_prompt`
- `_build_story_image_prompt`

---

### Prompts separados para Feed/Reel/Story
**Motivo:** Removem contexto pesquisado, que é funcionalidade importante do main.

**O main já tem prompts funcionais que usam:**
- Contexto pesquisado (tendências, concorrentes, hashtags)
- Dados do perfil

**Funções descartadas:**
- `_build_feed_post_prompt`
- `_build_reel_prompt`
- `_build_story_prompt`

---

## Checklist de Implementação

### Cores e Logo
- [x] Instalar dependência: `pip install webcolors`
- [x] Adicionar funções de cores em `ai_prompt_service.py`
- [x] Adicionar `_build_logo_section` em `ai_prompt_service.py`
- [x] Integrar logo section no `image_generation_prompt`

### Análise Histórica e Posts Automáticos
- [x] Adicionar `build_historical_analysis_prompt`
- [x] Adicionar `build_automatic_post_prompt`

### Edição com Preservação
- [x] Adicionar `build_content_edit_prompt`
- [x] Adicionar `build_image_edit_prompt`

### Testes e Finalização
- [x] Testar conversão de cores (147 cores CSS3)
- [ ] Testar geração de imagem com logo (requer teste E2E)
- [ ] Testar edição de conteúdo com preservação (requer teste E2E)
- [ ] Testar edição de imagem com preservação (requer teste E2E)
- [ ] Atualizar PR #25 ou criar novo PR
- [ ] Fechar PR #25 original

---

## Referências

- PR #25: https://github.com/PostNow-AI/PostNow-REST-API/pull/25
- Pesquisa sobre cores: https://medium.com/codex/rgb-to-color-names-in-python-the-robust-way-ec4a9d97a01f
- Midjourney colors: https://www.cometapi.com/how-to-get-specific-colors-in-midjourney-v7/
- Gemini prompting: https://developers.googleblog.com/en/how-to-prompt-gemini-2-5-flash-image-generation-for-the-best-results/
