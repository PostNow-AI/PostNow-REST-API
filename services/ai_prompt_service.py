import logging

from format_weekly_context import format_weekly_context_output
from services.get_creator_profile_data import get_creator_profile_data

logger = logging.getLogger(__name__)


class AIPromptService:
    def __init__(self):
        self.user = None

    def set_user(self, user) -> None:
        """Set the user for whom the prompts will be generated."""
        self.user = user

    def build_context_prompts(self) -> dict:
        """Build context prompts based on the user's creator profile."""
        profile_data = get_creator_profile_data(self.user)

        return [
            """
            Você é um analista de mercado especializado em marketing digital e pesquisa competitiva. Sua função é coletar informações atualizadas e factuais sobre empresas, setores e públicos, para gerar um contexto confiável usado na criação de conteúdo personalizado. Sempre que possível, baseie suas respostas em fontes verificáveis encontradas na internet. Se uma informação não estiver disponível, diga explicitamente 'não encontrado' ou 'sem dados disponíveis' — nunca invente ou suponha dados.            """,
            f"""
            🏢 DADOS DO ONBOARDING DA EMPRESA
            - Nome da empresa: {profile_data['business_name']}
            - Site da empresa: {profile_data['business_website']}
            - Nome da empresa: {profile_data['business_website']}

            - Descrição do negócio: {profile_data['business_description']}
            - Setor / nicho de mercado: {profile_data['specialization']}
            - Localização principal: {profile_data['business_location']}
            - Público-alvo: {profile_data['target_audience']}
            - Interesses do público: {profile_data['target_interests']}
            - Concorrentes conhecidos: {profile_data['main_competitors']}
            - Perfis de referência: {profile_data['reference_profiles']}

            ============================================================
            📌 TAREFA
            Realizar pesquisa online (via web.search) e gerar um
            **relatório factual, sintetizado e confiável**, com links das fontes.
            ============================================================
            ⚠️ INSTRUÇÕES RÍGIDAS
            1. Não fazer inferências ou suposições sem fonte real.
            2. Citar fontes em cada seção (preferir oficiais / mercado).
            3. Se algo não for encontrado → escrever: "sem dados disponíveis".
            4. Priorizar fontes brasileiras se a localização for {profile_data['business_location']} (BR).
            5. Manter linguagem neutra, objetiva e sem opiniões.

            ============================================================

            📤 ESTRUTURA DE SAÍDA (JSON)
            O resultado deve seguir EXATAMENTE este formato:

            {{
            "contexto_pesquisado":
              "mercado": {{
                "panorama": "Resumo factual do setor com dados e referências.",
                "tendencias": ["Tendência 1", "Tendência 2"],
                "desafios": ["Desafio 1", "Desafio 2"],
                "fontes": ["URL 1", "URL 2"]
              }},

              "concorrencia": {{
                "principais": ["Concorrente 1", "Concorrente 2"],
                "estrategias": "Síntese factual das abordagens observadas.",
                "oportunidades": "Possíveis diferenciais com base nos fatos.",
                "fontes": ["URL 1", "URL 2"]
              }},

              "publico": {{
                "perfil": "Descrição factual do público baseada em pesquisas.",
                "comportamento_online": "Principais hábitos e plataformas.",
                "interesses": ["Interesse 1", "Interesse 2"],
                "fontes": ["URL 1", "URL 2"]
              }},

              "tendencias": {{
                "temas_populares": ["Tema 1", "Tema 2"],
                "hashtags": ["#hashtag1", "#hashtag2"],
                "palavras_chave": ["keyword1", "keyword2"],
                "fontes": ["URL 1", "URL 2"]
              }},

              "sazonalidade": {{
                "datas_relevantes": ["Data 1", "Data 2"],
                "eventos_locais": ["Evento 1", "Evento 2"],
                "fontes": ["URL 1", "URL 2"]
              }},          

              "marca": {{
                "presenca_online": "Resumo factual das aparições online.",
                "reputacao": "Sentimento geral encontrado.",
                "tom_comunicacao_atual": "Descrição objetiva do tom atual.",
                "fontes": ["URL 1", "URL 2"]
              }}
            }}
            ============================================================

            📝 OBSERVAÇÕES FINAIS
            Geração deve ser 100% factual, objetiva e baseada em fontes.
            ============================================================

            """]

    def build_content_prompts(self, context: dict, posts_quantity: str) -> dict:
        """Build content generation prompts based on the user's creator profile."""
        profile_data = get_creator_profile_data(self.user)

        return [
            """
            Você é um estrategista de conteúdo e redator de marketing digital especializado em redes sociais. Sua função é criar posts para o Instagram totalmente personalizados, usando dados reais e verificados sobre a empresa, seu público e o mercado. Se alguma informação estiver ausente ou marcada como 'sem dados disponíveis', você deve ignorar essa parte sem criar suposições. Não invente dados, tendências, números ou nomes de concorrentes. Baseie todas as decisões de conteúdo nas informações recebidas do onboarding e no contexto pesquisado, sempre respeitando o tom e propósito da marca.
            """,
            f'''
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
            - Tipos de post desejados: {profile_data['desired_post_types']}
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
            '''
        ]

    def build_campaign_prompts(self, context: dict) -> dict:
        """Build campaign generation prompts based on the user's creator profile."""
        profile_data = get_creator_profile_data(self.user)

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

            O “post_text_feed” deve incluir:

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
              - Adicionar “Título do post” à “sugestão visual” é obrigatório       
              - Adicionar “Sub Título do post” à sugestão visual é facultativo. Você pode escolher de acordo com o conceito e estética desejados
              - Adicionar “Chamada para ação” à sugestão visual é facultativo. Você pode escolher de acordo com o conceito e estética desejados.
              - Nunca adicione o texto de “legenda completa” à sugestão visual.
              - Nunca adicione o texto de “Hashtags” à sugestão visual.

            4. **Hashtags recomendadas**:
              - Adicione as hashtags de tendências verificadas: {', '.join(context['tendencies_hashtags'])}
              - Não criar hashtags inventadas

            5. **CTA (chamada para ação)**
              - coerente com o conteúdo do post

            O “post_text_stories” deve incluir:
            - Roteiro diário para geração de stories baseados no contexto pesquisado.

            O “post_text_reels” deve incluir:
            - Roteiro diário para geração de um video de reels baseados no contexto pesquisado.
            - Roteiro deve ser escrito baseado no método de criação de conteúdo AIDA.

            ============================================================
            🧭 DIRETRIZES DE QUALIDADE E CONFIABILIDADE

            - Não inventar estatísticas, datas ou referências.  
            - Linguagem natural, persuasiva e compatível com {profile_data['voice_tone']}.  
            - Se faltar dados → focar na proposta de valor.  
            - Storytelling só quando houver base real.  
            - Nunca mencionar “sem dados disponíveis” no texto final.  
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
                "roteiro": "Roteiro do Stories”
              }},
              "post_text_reels": {{
                "titulo": "Igual ao título do feed",
                "roteiro": "Roteiro do Reels”
              }}
            }}

          """
        ]

    def semantic_analysis_prompt(self, post_text: str) -> str:
        """Prompt for semantic analysis of user input."""
        return [
            """
              Você é um analista de semântica e especialista em direção de arte para redes sociais. Sua função é interpretar textos publicitários e identificar seus elementos conceituais e visuais principais, transformando a mensagem escrita em diretrizes visuais e emocionais claras. Baseie suas respostas apenas no texto fornecido, sem adicionar interpretações não fundamentadas.
            """,
            f"""
              Analise o texto a seguir e extraia:

              1. Tema principal
              2. Conceitos visuais que o representam
              3. Emoções ou sensações associadas
              4. Elementos visuais sugeridos (objetos, cenários, cores)

              Texto: {post_text}

              A SAÍDA DEVE SER NO FORMATO:
              {{
                "analise_semantica":{{
                  "tema_principal": "",
                  "subtemas": [],
                  "conceitos_visuais": [],
                  "objetos_relevantes": [],
                  "contexto_visual_sugerido": "",
                  "emoções_associadas": [],
                  "tons_de_cor_sugeridos": [],
                  "ação_sugerida": "",
                  "sensação_geral": "",
                  "palavras_chave": []
                }}
              }}
            """
        ]

    def adapted_semantic_analysis_prompt(self, semantic_analysis: dict) -> str:
        """Prompt for semantic analysis adapted to creator profile."""
        profile_data = get_creator_profile_data(self.user)

        return [
            """
              Você é um Diretor de Arte Sênior de Inteligência Artificial. Sua tarefa é fundir uma análise semântica de conteúdo com um perfil de marca específico, garantindo que o resultado seja uma diretriz visual coesa, priorizando **integralmente** o estilo e a paleta de cores da marca, mesmo que os temas originais sejam de naturezas diferentes (ex: Café com estilo Futurista).
            """,
            f"""
              ### DADOS DE ENTRADA ####

              1. PERSONALIDADE DA MARCA (Emoções)
              {profile_data['brand_personality']}

              2. ANÁLISE SEMÂNTICA (Conteúdo e Mensagem
              {semantic_analysis}

              3. PERFIL DA MARCA (Estilo e Identidade)

              - Cores da Marca:
                {profile_data['color_palette']} - podem ser usadas variações mais escuras, mais claras e gradientes baseadas nas cores da marca.
              - Estilo visual: 
                {str(profile_data['visual_style']) if profile_data.get('visual_style') else 'Não definido'}


              ### INSTRUÇÕES PARA ADAPTAÇÃO
              1. **Prioridade Absoluta:**  
                O resultado final deve priorizar o **"Estilo Visual"** e as **"Cores da Marca"**.

              2. **Mapeamento Visual:**  
                Adapte os `objetos_relevantes` e o `contexto_visual_sugerido` da análise semântica 
                para o `Estilo Visual` da marca.  
                Exemplo: se o tema é *natureza* e o estilo é *3D Futurista*, 
                a natureza deve ser renderizada em 3D, com brilhos e linhas geométricas.

              3. **Mapeamento de Emoções:**  
                Use a `Personalidade da Marca` para refinar a `ação_sugerida` e as `emoções_associadas`.  
                Exemplo: uma marca *educadora* deve ter personagens em postura de clareza e acolhimento.

              4. **Paleta de Cores:**  
                Substitua os `tons_de_cor_sugeridos` originais pelas **Cores da Marca**.  
                Utilize as cores da marca para destaques, iluminação e elementos de fundo.

              5. **Geração:**  
                Gere o novo JSON final com a estrutura `analise_semantica_adaptada` abaixo, 
                refletindo as adaptações e a priorização do `Perfil da Marca`.



              ### SAÍDA REQUERIDA (APENAS RETORNE O NOVO JSON ADAPTADO, NADA MAIS)
              {{
                "analise_semantica": {{
                    "tema_principal": "[Tema principal adaptado ao contexto da marca]",
                    "subtemas": [],
                    "conceitos_visuais": ["[Conceitos reinterpretados no estilo da marca]"],
                    "objetos_relevantes": ["[Objetos descritos no estilo visual prioritário]"],
                    "contexto_visual_sugerido": "[Cenário com a estética e paleta da marca]",
                    "emoções_associadas": ["[Emoções alinhadas à personalidade da marca]"],
                    "tons_de_cor_sugeridos": ["[As Cores da Marca e seus usos]"],
                    "ação_sugerida": "[Ação que reflete a personalidade e estilo da marca]",
                    "sensação_geral": "[Sensação geral de acordo com a estética da marca]",
                    "palavras_chave": ["[Keywords que fundem tema e estilo (ex: Café 3D, Editorial Roxo)]"]
                }}
              }}
            """
        ]

    def image_generation_prompt(self, semantic_analysis: dict) -> str:
        """Prompt for AI image generation based on semantic analysis."""
        profile_data = get_creator_profile_data(self.user)

        def get_visual_style_info():
            visual_style = profile_data.get('visual_style', '')
            if isinstance(visual_style, str) and ' - ' in visual_style:
                parts = visual_style.split(' - ', 1)
                return {
                    'tipo_estilo': parts[0],
                    'descricao_completa': parts[1] if len(parts) > 1 else ''
                }
            elif isinstance(visual_style, dict):
                return {
                    'tipo_estilo': visual_style.get('tipo_estilo', ''),
                    'descricao_completa': visual_style.get('descricao_completa', '')
                }
            else:
                return {
                    'tipo_estilo': str(visual_style) if visual_style else '',
                    'descricao_completa': ''
                }

        visual_style_info = get_visual_style_info()

        return [
            f"""
          Crie uma imagem seguindo o estilo e contexto descritos abaixo.

          - Estilo visual:
            - Tipo estilo: {visual_style_info['tipo_estilo']},
            - Descrição completa: {visual_style_info['descricao_completa']},
          - Contexto e conteudo:
            - Contexto visual sugerido: {semantic_analysis['contexto_visual_sugerido']},
            - Elementos relevantes: {', '.join(semantic_analysis['objetos_relevantes'])},
            - Tema principal do post: {semantic_analysis['tema_principal']},
          - Emoção e estética:
            - Emoções associadas: {', '.join(semantic_analysis['emoções_associadas'])},
            - Sensação geral: {semantic_analysis['sensação_geral']},
            - Tons de cor sugeridos: {', '.join(semantic_analysis['tons_de_cor_sugeridos'])}

          - Restricoes:
            - Caso uma logomarca seja anexada, INCLUA a logomarca na imagem de forma harmoniosa e integrada ao design
            - Caso uma logomarca não seja anexada, NÃO gerar ou adicionar logomarca
            - Textos renderizados na imagem devem sempre ser escritos em português do Brasil (PT-BR)
        """
        ]
