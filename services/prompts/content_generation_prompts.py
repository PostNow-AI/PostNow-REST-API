"""
Prompts para geração de conteúdo (posts, campanhas, edição).

Extraído de ai_prompt_service.py para separação de responsabilidades.
"""

import logging

from services.format_weekly_context import format_weekly_context_output
from services.get_creator_profile_data import get_creator_profile_data

logger = logging.getLogger(__name__)


def build_content_prompts(user, context: dict, posts_quantity: str) -> list[str]:
    """Build content generation prompts based on the user's creator profile."""
    profile_data = get_creator_profile_data(user)

    return [
        """
            Você é um estrategista de conteúdo e redator de marketing digital especializado em redes sociais. Sua função é criar posts para o Instagram totalmente personalizados, usando dados reais e verificados sobre a empresa, seu público e o mercado. Se alguma informação estiver ausente ou marcada como 'sem dados disponíveis', você deve ignorar essa parte sem criar suposições. Não invente dados, tendências, números ou nomes de concorrentes. Baseie todas as decisões de conteúdo nas informações recebidas do onboarding e no contexto pesquisado, sempre respeitando o tom e propósito da marca.
            """,
        f"""
            Abaixo estão as informações disponíveis:
            ---### 📊 CONTEXTO PESQUISADO (dados externos e verificados)
            {context}

            ---### 🏢 INFORMAÇÕES DA EMPRESA (dados internos do onboarding)
            - Nome da empresa: {profile_data['business_name']}
            - Descrição: {profile_data['business_description']}
            - Setor / nicho: {profile_data['specialization']}
            - Propósito: {profile_data['business_purpose']}
            - Valores e personalidade: {profile_data['brand_personality']}
            - Tom de voz: {profile_data['voice_tone']}
            - Público-alvo:  {profile_data['target_audience']}
            - Interesses do Público: {profile_data['target_interests']}
            - Tipos de post desejados: {profile_data.get('desired_post_types', ['Feed', 'Reels', 'Story'])}
            - Objetivo principal: {profile_data['business_purpose']}
            - Produtos ou serviços prioritários: {profile_data['products_services']}

            ---### 📌 TAREFA
            Crie {posts_quantity} posts para o Instagram, combinando as informações da empresa com o contexto pesquisado.
            Cada post deve conter:
            1. **Título curto e atrativo** (até 6 palavras, coerente com o tom da marca)
            2. **Legenda completa**, adaptada ao público e ao objetivo principal.
              - Baseie-se apenas em informações confirmadas (do onboarding e do contexto pesquisado).
              - Se alguma tendência, público ou concorrente não tiver dados disponíveis, ignore esse aspecto.
              - Você pode citar fontes ou dados do contexto apenas se forem relevantes e confiáveis.
            3. **Sugestão visual** (descrição de imagem, layout e estilo visual, coerente com a identidade da marca)
            4. **Hashtags recomendadas**, combinando:
              - As de {context['tendencies_hashtags']}
              - As tendências verificadas em {context['tendencies_popular_themes']}
              - Evite criar hashtags inexistentes.
            5. **CTA (chamada para ação)**, relevante e consistente com o objetivo {profile_data['business_purpose']}.

            ---### 🧭 DIRETRIZES DE QUALIDADE E CONFIABILIDADE
            - Não invente estatísticas, datas ou referências.
            - Prefira uma linguagem natural, persuasiva e compatível com {profile_data['voice_tone']}.
            - Se não houver dados de mercado ou público suficientes, foque na proposta de valor da empresa.
            - Inclua storytelling apenas se houver base no propósito, produto ou cliente real.
            - Caso detecte 'sem dados disponíveis' no contexto, não mencione isso explicitamente; apenas omita o conteúdo correspondente.
            - O conteúdo deve soar autêntico, relevante e profissional.

            ---### 💬 FORMATO DE SAÍDA (JSON)
            [
              {{
                "titulo": "Título do post",
                "tipo_post": "feed/reel/story",
                "legenda": "Texto completo da legenda",
                "sugestao_visual": "Descrição da imagem ou layout",
                "hashtags": ["#hashtag1", "#hashtag2", "#hashtag3"],
                "cta": "Chamada para ação"
              }}
            ]

            ---### ⚙️ CONFIGURAÇÕES RECOMENDADAS
            - **temperature:** 0.7 (para criatividade equilibrada)
            - **top_p:** 0.9
            - **max_tokens:** 2000
            - **presence_penalty:** 0.2
            - **frequency_penalty:** 0.1

            Essas configurações permitem gerar conteúdo criativo, porém sempre dentro dos limites de dados reais e verificados.
            """
    ]


def build_standalone_post_prompt(user, post_data: dict, context: dict) -> list[str]:
    """Build prompt for standalone post generation from opportunity or manual creation."""
    profile_data = get_creator_profile_data(user)
    formatted_context = format_weekly_context_output(context)
    return [
        """
            Você é um estrategista de conteúdo e redator de marketing digital especializado em redes sociais. Sua função é criar um post para o Instagram totalmente personalizado e criativo para esta empresa. Caso o post seja de tipo "reels" ou "story", traga o conteúdo em formato de roteiro de reels ou story. Caso contrário, faça um post apropriado para ser postado no feed do usuário. Se alguma informação estiver ausente ou marcada como 'sem dados disponíveis', você deve ignorar essa parte sem criar suposições. Não invente dados, tendências, números ou nomes de concorrentes. Baseie o conteúdo dos posts no contexto pesquisado, sempre respeitando o tom de voz da marca, porém seja criativo e crie conteúdo engajador, utilizando o método AIDA. Usar também como referência a jornada do herói.""",
        f"""
            ============================================================
            ### DADOS DE ENTRADA (Inseridos pelo usuário):
            - Assunto do post: {post_data['name']}
            - Objetivo do post: {post_data['objective']}
            - Tipo do post: {post_data['type']}
            - Mais detalhes: {post_data['further_details']}
            ============================================================

            📊 CONTEXTO PESQUISADO (dados externos e verificados)
            → INPUT: {formatted_context}
            ============================================================

            🏢 INFORMAÇÕES DA EMPRESA (dados internos do onboarding)

            - Nome: {profile_data['business_name']}
            - Personalidade da marca: {profile_data['brand_personality']}
            - Público-alvo: {profile_data['target_audience']}
            ============================================================

            ============================================================
            SAÍDAS CONDICIONAIS:

            ############################################################
            CASO O POST SEJA TIPO "FEED":

            📌 TAREFA PRINCIPAL

            Criar **1 post para o Instagram**, combinando:
            ✔ dados da empresa
            ✔ contexto pesquisado
            ✔ Assunto, objetivo e mais detalhes

            O post deve incluir:

            1. **Título curto e atrativo**
               - Entre 2 e 5 palavras
               - Alinhado ao tom da marca

            2. **Legenda completa**
               - Baseada nos dados de contexto pesquisado e dados inseridos pelo usuário
               - Ignorar itens sem dados disponíveis
               - Limite máximo de 600 caracteres
               - Pode citar fontes reais quando relevante

            3. **Hashtags recomendadas**:
               - Adicione as hashtags de tendências verificadas: {', '.join(context.get('tendencies_hashtags', []))}
               - Não criar hashtags inventadas

            4. **CTA (chamada para ação)**
               - coerente com o conteúdo do post

            ============================================================
            🧭 DIRETRIZES DE QUALIDADE E CONFIABILIDADE

            - Manter linguagem natural sem grandes exageros.
            - Não exagerar na utilização de emojis, máximo de 5 por conteúdo gerado
            - Não inventar estatísticas, datas ou referências.
            - Linguagem persuasiva que expresse o tom do texto do post
            - Se faltar dados → focar na proposta de valor.
            - Storytelling só quando houver base real.
            - Nunca mencionar "sem dados disponíveis" no texto final.
            - Conteúdo deve soar autêntico e profissional.
            - Conteúdo deve sempre ser gerado em PT-BR

            ============================================================

            💬 FORMATO DE SAÍDA (APENAS UM JSON)

            {{
                "id": 1,
                "titulo": "Título do post",
                "sub_titulo": "Sub Título do post",
                "legenda": "Texto completo da legenda",
                "hashtags": ["#hashtag1", "#hashtag2", "#hashtag3"],
                "cta": "Chamada para ação"
            }}

            ############################################################
            CASO O POST SEJA TIPO "REELS" OU "STORY":

            📌 TAREFA PRINCIPAL

            Criar **1 post para o Instagram**, combinando:
            ✔ dados da empresa
            ✔ contexto pesquisado
            ✔ Assunto, objetivo e mais detalhes

            - O 1 (ÚNICO) conteúdo deve ser:
                - 5 ideais para Stories (PARA TIPO STORY)
                OU
                - 1 roteiro para vídeo de Reels entre 15 e 35 segundos (PARA TIPO REELS)

            ============================================================
            🧭 DIRETRIZES DE QUALIDADE E CONFIABILIDADE

            - Não inventar estatísticas, datas ou referências.
            - Manter linguagem natural sem grandes exageros.
            - Linguagem persuasiva que expresse o tom do texto do post
            - Se faltar dados → focar na proposta de valor.
            - Storytelling só quando houver base real.
            - Nunca mencionar "sem dados disponíveis" no texto final.
            - Conteúdo deve soar autêntico e profissional.
            - Conteúdo deve sempre ser gerado em PT-BR

            ============================================================

            💬 FORMATO DE SAÍDA (APENAS UM JSON)

            {{
                "titulo": "Título do post",
                "roteiro": "Roteiro do Reels ou Story"
            }}

            """
    ]


def build_campaign_prompts(user, context: dict) -> list:
    """Build campaign generation prompts based on the user's creator profile."""
    profile_data = get_creator_profile_data(user)
    formatted_context = format_weekly_context_output(context)

    return [
        """
            Você é um estrategista de conteúdo e redator de marketing digital especializado em redes sociais. Sua função é criar posts para o Instagram totalmente personalizados, usando dados reais e verificados sobre a empresa, seu público e o mercado. Se alguma informação estiver ausente ou marcada como 'sem dados disponíveis', você deve ignorar essa parte sem criar suposições. Não invente dados, tendências, números ou nomes de concorrentes. Baseie todas as decisões de conteúdo nas informações recebidas do onboarding e no contexto pesquisado, sempre respeitando o tom e propósito da marca.
            """,
        f"""
            ============================================================
            📊 CONTEXTO PESQUISADO (dados externos e verificados)

            → INPUT:
            {formatted_context}

            ============================================================

            🏢 INFORMAÇÕES DA EMPRESA (dados internos do onboarding)

            - Nome: {profile_data['business_name']}
            - Descrição: {profile_data['business_description']}
            - Site da empresa: {profile_data['business_website']}
            - Setor / nicho de mercado: {profile_data['specialization']}
            - Propósito da empresa: {profile_data['business_purpose']}
            - Valores e personalidade: {profile_data['brand_personality']}
            - Tom de voz: {profile_data['voice_tone']}
            - Público-alvo: {profile_data['target_audience']}
            - Interesses do Público: {profile_data['target_interests']}
            - Produtos ou serviços prioritários: {profile_data['products_services']}

            ============================================================
            📌 TAREFA PRINCIPAL

            Criar **3 posts para o Instagram**, combinando:
              ✔ dados da empresa
              ✔ contexto pesquisado
              ✔ tom de voz e objetivosOs 3 posts devem ser:
              - 1 Post para Feed (post_text_feed)- 1 Post para Stories (post_text_stories)- 1 Post para Reels (post_text_reels)
              - 1 Post para Stories (post_text_stories)
              - 1 Post para Reels (post_text_reels)

            O "post_text_feed" deve incluir:

            1. **Título curto e atrativo**
              - Entre 2 e 5 palavras
              - Alinhado ao tom da marca
              - Deve aparecer escrito na imagem

            2. **Legenda completa**
              - Baseada nos dados de contexto pesquisado, crie uma legenda criativa para o post
              - Ignorar itens sem dados disponíveis
              - Limite máximo de 600 caracteres
              - Pode citar fontes reais quando relevante

            3. **Sugestão visual**
              - Descrição da imagem, layout, estilo
              - Coerente com o propósito e valores da empresa.
              - Adicionar "Título do post" à "sugestão visual" é obrigatório
              - Adicionar "Sub Título do post" à sugestão visual é facultativo. Você pode escolher de acordo com o conceito e estética desejados
              - Adicionar "Chamada para ação" à sugestão visual é facultativo. Você pode escolher de acordo com o conceito e estética desejados.
              - Nunca adicione o texto de "legenda completa" à sugestão visual.
              - Nunca adicione o texto de "Hashtags" à sugestão visual.

            4. **Hashtags recomendadas**:
              - Adicione as hashtags de tendências verificadas: {', '.join(context['tendencies_hashtags'])}
              - Não criar hashtags inventadas

            5. **CTA (chamada para ação)**
              - coerente com o conteúdo do post

            O "post_text_stories" deve incluir:
            - Roteiro diário para geração de stories baseados no contexto pesquisado.

            O "post_text_reels" deve incluir:
            - Roteiro diário para geração de um video de reels baseados no contexto pesquisado.
            - Roteiro deve ser escrito baseado no método de criação de conteúdo AIDA.

            ============================================================
            🧭 DIRETRIZES DE QUALIDADE E CONFIABILIDADE

            - Não inventar estatísticas, datas ou referências.
            - Linguagem natural, persuasiva e compatível com {profile_data['voice_tone']}.
            - Se faltar dados → focar na proposta de valor.
            - Storytelling só quando houver base real.
            - Nunca mencionar "sem dados disponíveis" no texto final.
            - Conteúdo deve soar autêntico e profissional.


            ============================================================

            💬 FORMATO DE SAÍDA (JSON)

            {{
              "post_text_feed": {{
                "titulo": "Título do post",
                "sub_titulo": "Sub Título do post",
                "legenda": "Texto completo da legenda",
                "sugestao_visual": "Descrição da imagem ou layout",
                "hashtags": ["#hashtag1", "#hashtag2", "#hashtag3"],
                "cta": "Chamada para ação"
              }},
              "post_text_stories": {{
                "titulo": "Igual ao título do feed",
                "roteiro": "Roteiro do Stories"
              }},
              "post_text_reels": {{
                "titulo": "Igual ao título do feed",
                "roteiro": "Roteiro do Reels"
              }}
            }}

          """
    ]


def build_historical_analysis_prompt(user, post_data: dict) -> list[str]:
    """Analisa posts anteriores para evitar conteúdo repetitivo."""
    profile_data = get_creator_profile_data(user)

    name = post_data.get('name', '')
    objective = post_data.get('objective', '')
    further_details = post_data.get('further_details', '')

    return [
        """
            Você é um estrategista criativo especializado em copywriting e conteúdo digital.
            Sua função é analisar o histórico de conteúdos anteriores, entender o estilo,
            linguagem e temas já abordados, e criar um novo direcionamento criativo inédito.
            """,
        f"""
            🧾 DADOS DE PERSONALIZAÇÃO DO CLIENTE:

            Nome do negócio: {profile_data.get('business_name', 'Não informado')}
            Setor/Nicho: {profile_data.get('specialization', 'Não informado')}
            Descrição do negócio: {profile_data.get('business_description', 'Não informado')}
            Público-alvo: {profile_data.get('target_audience', 'Não informado')}
            Interesses do público-alvo: {profile_data.get('target_interests', 'Não informado')}
            Localização do negócio: {profile_data.get('business_location', 'Não informado')}
            Tom de voz: {profile_data.get('voice_tone', 'Profissional')}

            🎯 OBJETIVO GERAL:

            Assunto: {name}
            Objetivo: {objective}
            Mais detalhes: {further_details}

            📌 TAREFA:

            1. Analise o contexto e crie um direcionamento criativo NOVO
            2. Identifique temas e abordagens a EVITAR (para não repetir)
            3. Sugira novos títulos, subtítulos e CTAs originais

            📦 FORMATO DE SAÍDA (JSON):

            {{
                "historical_analysis": "Resumo do que já foi feito (para referência)",
                "avoid_list": ["tema a evitar 1", "expressão a evitar 2", "CTA a evitar 3"],
                "new_direction": "Nova linha criativa e conceito principal",
                "new_headline": "Sugestão de título inédito",
                "new_subtitle": "Sugestão de subtítulo complementar",
                "new_cta": "Sugestão de CTA original"
            }}
            """
    ]


def build_automatic_post_prompt(user, analysis_data: dict = None) -> list[str]:
    """Gera post automático baseado em análise histórica."""
    profile_data = get_creator_profile_data(user)

    analysis_json = analysis_data if analysis_data else {
        "historical_analysis": "",
        "avoid_list": [],
        "new_direction": "",
        "new_headline": "",
        "new_subtitle": "",
        "new_cta": ""
    }

    return [
        """
            Você é um especialista em copywriting estratégico e criativo para redes sociais.
            Sua missão é gerar conteúdo ORIGINAL baseado no direcionamento criativo fornecido.
            """,
        f"""
            🧠 DIRECIONAMENTO CRIATIVO (do módulo de análise histórica):

            {analysis_json}

            Função de cada campo:
            - historical_analysis: referência do que foi feito (NÃO repetir)
            - avoid_list: lista de ideias/expressões/CTAs a EVITAR
            - new_direction: linha criativa que deve guiar o novo conteúdo
            - new_headline/new_subtitle/new_cta: inspirações para o novo conteúdo

            🧾 DADOS DO CLIENTE:

            Nome do negócio: {profile_data.get('business_name', 'Não informado')}
            Setor/Nicho: {profile_data.get('specialization', 'Não informado')}
            Descrição do negócio: {profile_data.get('business_description', 'Não informado')}
            Público-alvo: {profile_data.get('target_audience', 'Não informado')}
            Interesses do público-alvo: {profile_data.get('target_interests', 'Não informado')}
            Tom de voz: {profile_data.get('voice_tone', 'Profissional')}

            🎯 REGRAS:

            1. Use new_direction como base criativa principal
            2. NUNCA use nada da avoid_list
            3. Inspire-se em new_headline/new_subtitle/new_cta, mas reescreva
            4. Estrutura AIDA (Atenção, Interesse, Desejo, Ação)
            5. Média de 5 emojis por texto
            6. Tom de voz: {profile_data.get('voice_tone', 'Profissional')}

            📦 FORMATO DE SAÍDA:

            {{
                "titulo": "Título curto e criativo (até 8 palavras)",
                "sub_titulo": "Subtítulo complementar",
                "legenda": "Texto completo da copy com ~5 emojis",
                "hashtags": ["#hashtag1", "#hashtag2", "#hashtag3"],
                "cta": "Chamada para ação original"
            }}
            """
    ]


def build_content_edit_prompt(current_content: str, instructions: str = None) -> list[str]:
    """Prompt para edição de conteúdo preservando identidade."""
    instructions_section = ""
    if instructions:
        instructions_section = f"\n- Alterações solicitadas: {instructions}"

    return [
        """
            Você é um especialista em ajustes e refinamentos de conteúdo para marketing digital.
            Sua missão é editar o material já criado mantendo sua identidade, estilo e tom,
            alterando APENAS o que for solicitado.
            """,
        f"""
            ### DADOS DE ENTRADA:
            - Conteúdo original: {current_content}{instructions_section}

            ### REGRAS PARA EDIÇÃO:

            1. **Mantenha toda a identidade visual e estilística do conteúdo original**:
                - Tom de voz e estilo da copy
                - Estrutura do texto
                - Quantidade de emojis similar

            2. **Modifique somente o que foi solicitado**, sem alterar nada além disso

            3. Ajuste apenas as frases, palavras ou CTA especificadas, mantendo a
               mesma estrutura e parágrafos curtos

            4. Nunca descaracterize o material já feito - a ideia é **refinar e ajustar**,
               não recriar do zero

            5. O resultado deve estar pronto para uso imediato

            ### SAÍDA ESPERADA:

            Retorne o conteúdo revisado no mesmo formato do original, com apenas as
            alterações solicitadas aplicadas. Todo o restante deve permanecer idêntico.
            """
    ]


def build_image_edit_prompt(user_prompt: str = None) -> list[str]:
    """Prompt para edição de imagem preservando identidade visual."""
    edit_instructions = user_prompt if user_prompt else 'crie uma variação sutil mantendo a identidade'

    return [
        f"""
            Você é um especialista em design digital e edição de imagens para marketing.
            Sua missão é editar a imagem já criada, mantendo **100% da identidade visual,
            layout, estilo, cores e elementos originais**, alterando **apenas o que for solicitado**.

            ### DADOS DE ENTRADA:
            - Imagem original: [IMAGEM ANEXADA]
            - Alterações solicitadas: {edit_instructions}

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
    ]
