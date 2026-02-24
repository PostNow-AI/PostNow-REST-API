"""
AIPromptService - Serviço de geração de prompts para IA.

Este módulo contém a classe AIPromptService e funções auxiliares para
geração de prompts estruturados enviados para modelos de IA.

=============================================================================
NOTA IMPORTANTE SOBRE ARQUITETURA (NÃO REFATORAR SEM LER)
=============================================================================

Os métodos desta classe contêm "repetição" proposital de dados do perfil
(nome do negócio, setor, público-alvo, tom de voz, etc.) em cada prompt.

ISSO NÃO É VIOLAÇÃO DE DRY. Motivos:

1. Cada prompt é enviado INDEPENDENTEMENTE para a IA
2. A IA não "lembra" de chamadas anteriores
3. Cada prompt PRECISA ter o contexto completo para funcionar
4. São dados de contexto, não lógica duplicada

Exemplo:
    - build_historical_analysis_prompt() → Chamada IA 1 (precisa do contexto)
    - build_automatic_post_prompt()      → Chamada IA 2 (precisa do contexto)

Se você extrair os dados do perfil para uma função auxiliar, o código fica
mais "organizado", mas os dados ainda precisarão aparecer em cada prompt.
A "repetição" é intencional e necessária.

DRY se aplica a: lógica de código, funções, algoritmos
DRY NÃO se aplica a: dados de contexto em prompts independentes

=============================================================================
"""

import logging

from services.color_extraction import format_colors_for_prompt
from services.format_weekly_context import format_weekly_context_output
from services.get_creator_profile_data import get_creator_profile_data
from services.prompt_logo import build_logo_section

logger = logging.getLogger(__name__)


class AIPromptService:
    def __init__(self):
        self.user = None

    def set_user(self, user) -> None:
        """Set the user for whom the prompts will be generated."""
        self.user = user

    def build_context_prompts(self) -> list[str]:
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

    def build_content_prompts(self, context: dict, posts_quantity: str) -> list[str]:
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

    def build_feed_prompts(self, context: dict) -> list[str]:
        """Build feed generation prompts based on the user's creator profile."""
        profile_data = get_creator_profile_data(self.user)

        formatted_context = format_weekly_context_output(context)
        return [
            """
            Você é um estrategista de conteúdo e redator de marketing digital especializado em redes sociais. Sua função é criar posts para o Instagram totalmente personalizados e criativos para esta empresa. Se alguma informação estiver ausente ou marcada como 'sem dados disponíveis', você deve ignorar essa parte sem criar suposições. Não invente dados, tendências, números ou nomes de concorrentes. Baseie o conteúdo dos posts no contexto pesquisado, sempre respeitando o tom de voz da marca, porém seja criativo e crie conteúdo engajador, utilizando o método AIDA. Usar também como referência a jornada do herói.            """,
            f"""
            ============================================================
            📊 CONTEXTO PESQUISADO (dados externos e verificados)
            → INPUT: {formatted_context}
            ============================================================
        
            🏢 INFORMAÇÕES DA EMPRESA (dados internos do onboarding)
        
            - Nome: {profile_data['business_name']}
            - Personalidade da marca: {profile_data['brand_personality']}
            - Público-alvo: {profile_data['target_audience']}
            ============================================================
            📌 TAREFA PRINCIPAL
        
            Criar **7 posts para o Instagram**, combinando:
            ✔ dados da empresa  
            ✔ contexto pesquisado
            
            Os 7 posts devem ser:
            
            - 7 posts para Feed (post_text_feed)

            O “post_text_feed” deve incluir:
        
            1. **Título curto e atrativo**
               - Entre 2 e 5 palavras  
               - Alinhado ao tom da marca
        
            2. **Legenda completa**
               - Baseada nos dados de contexto pesquisado, crie uma legenda criativa para o post
               - Ignorar itens sem dados disponíveis
               - Limite máximo de 600 caracteres
               - Pode citar fontes reais quando relevante
        
            3. **Hashtags recomendadas**:
               - Adicione as hashtags de tendências verificadas: {', '.join(context['tendencies_hashtags'])}
               - Não criar hashtags inventadas
        
            4. **CTA (chamada para ação)**
               - coerente com o conteúdo do post
        
           ============================================================
            🧭 DIRETRIZES DE QUALIDADE E CONFIABILIDADE
        
        
            - O conteúdo de cada um dos 7 posts gerados devem sempre ser sobre assuntos diferentes.
            - Manter linguagem natural sem grandes exageros.
            - Não exagerar na utilização de emojis, máximo de 5 por conteúdo gerado
            - Não inventar estatísticas, datas ou referências.  
            - Linguagem persuasiva que expresse o tom do texto do post
            - Se faltar dados → focar na proposta de valor.  
            - Storytelling só quando houver base real.  
            - Nunca mencionar “sem dados disponíveis” no texto final.  
            - Conteúdo deve soar autêntico e profissional.
            - Conteúdo deve sempre ser gerado em PT-BR
        
            ============================================================
            
            
            💬 FORMATO DE SAÍDA (JSON)
    
            [
                {{
                    “id”: 1,        
                    "titulo": "Título do post",
                    "sub_titulo": "Sub Título do post",
                    "legenda": "Texto completo da legenda",
                    "hashtags": ["#hashtag1", "#hashtag2", "#hashtag3"],
                    "cta": "Chamada para ação"
                }},     
                {{
                    “id”: 2,
                    "titulo": "Título do post",
                    "sub_titulo": "Sub Título do post",
                    "legenda": "Texto completo da legenda",
                    "hashtags": ["#hashtag1", "#hashtag2", "#hashtag3"],
                    "cta": "Chamada para ação"
                }}, 
                {{
                    “id”: 3,
                    "titulo": "Título do post",
                    "sub_titulo": "Sub Título do post",
                    "legenda": "Texto completo da legenda",
                    "hashtags": ["#hashtag1", "#hashtag2", "#hashtag3"],
                        "cta": "Chamada para ação"
                }}, 
                {{
                    “id”: 4,
                    "titulo": "Título do post",
                    "sub_titulo": "Sub Título do post",
                    "legenda": "Texto completo da legenda",
                    "hashtags": ["#hashtag1", "#hashtag2", "#hashtag3"],
                    "cta": "Chamada para ação"
                }}, 
                {{
                    “id”: 5,
                    "titulo": "Título do post",
                    "sub_titulo": "Sub Título do post",
                    "legenda": "Texto completo da legenda",
                    "hashtags": ["#hashtag1", "#hashtag2", "#hashtag3"],
                    "cta": "Chamada para ação"
                }}, 
                {{
                    “id”: 6,
                    "titulo": "Título do post",
                    "sub_titulo": "Sub Título do post",
                    "legenda": "Texto completo da legenda",
                    "hashtags": ["#hashtag1", "#hashtag2", "#hashtag3"],
                    "cta": "Chamada para ação"
                }}, 
                {{
                    “id”: 7,
                    "titulo": "Título do post",
                    "sub_titulo": "Sub Título do post",
                    "legenda": "Texto completo da legenda",
                    "hashtags": ["#hashtag1", "#hashtag2", "#hashtag3"],
                    "cta": "Chamada para ação"
                }}
            ]
            ============================================================


        """]

    def build_campaign_prompts(self, post_text_feed: dict) -> list[str]:
        """Build campaign generation prompts based on the user's creator profile."""
        profile_data = get_creator_profile_data(self.user)
        return [
            """
            Você é um estrategista de conteúdo e redator de marketing digital especializado em redes sociais. Sua função é criar 1 roteiro diário de videos de stories e 1 roteiro para video de Reels para o Instagram totalmente personalizados e criativos para esta empresa. Baseie o conteúdo dos roteiros no conteúdo do post de Feed enviado, sempre respeitando o tom de voz da marca. Seja criativo e crie conteúdo engajador, utilizando o método AIDA. Usar também como referência a jornada do herói.""",
            f"""
            ============================================================
            Conteúdo do post de Feed:
            → INPUT: {post_text_feed}
            ============================================================
        
            🏢 INFORMAÇÕES DA EMPRESA (dados internos do onboarding)
        
            - Nome: {profile_data['business_name']}
            - Personalidade da marca: {profile_data['brand_personality']}
            - Público-alvo: {profile_data['target_audience']}
            
            ============================================================
            📌 TAREFA PRINCIPAL
        
            Criar **2 conteúdos para o Instagram**, combinando:
            ✔ Conteúdo do post de Feed  
            ✔ Informações da empresaOs 2 conteúdos devem ser:- 5 ideais para Stories (post_text_stories)
            - 1 roteiro para vídeo de Reels entre 15 e 35 segundos (post_text_reels)
        
            O “post_text_stories” deve incluir:- As ideais dos stories devem ser complementares as ideias do post de Feed fornecido.
            - Sempre traga ideias para que o público engaje com o storie.
        
            O “post_text_reels” deve incluir:- Roteiro diário para geração de um video de reels baseados no post de Feed fornecido.
            - Roteiro deve ser escrito baseado no método de criação de conteúdo AIDA e na jornada do herói.
        
            ============================================================
            🧭 DIRETRIZES DE QUALIDADE E CONFIABILIDADE
        
            - Não inventar estatísticas, datas ou referências.  
            - Manter linguagem natural sem grandes exageros.
            - Linguagem persuasiva que expresse o tom do texto do post
            - Se faltar dados → focar na proposta de valor.  
            - Storytelling só quando houver base real.  
            - Nunca mencionar “sem dados disponíveis” no texto final.  
            - Conteúdo deve soar autêntico e profissional.
            - Conteúdo deve sempre ser gerado em PT-BR
        
            ============================================================
        
            💬 FORMATO DE SAÍDA (JSON)
        
            {{
                "post_text_stories": {{
                    "titulo": "Deve ter o mesmo título do post_text_feed",
                    "roteiro": "Roteiro para gravação de vídeo nos stories. Videos curtos com o mesmo tema do”
                }},
                "post_text_reels": {{
                    "titulo": "Deve ter o mesmo título do post_text_feed",
                    "roteiro": "Roteiro do Reels”
                }}
            }}
            ============================================================
            """
        ]

    def build_standalone_post_prompt(self, post_data: dict, context: dict) -> list[str]:
        """Build campaign generation prompts based on the user's creator profile."""
        profile_data = get_creator_profile_data(self.user)
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
               - Baseada nos dados de contexto pesquisado e dados inseridos pelo usuário (Assunto, objetivo e mais detalhes) , crie uma legenda criativa para o post
               - Ignorar itens sem dados disponíveis
               - Limite máximo de 600 caracteres
               - Pode citar fontes reais quando relevante
        
            3. **Hashtags recomendadas**:
               - Adicione as hashtags de tendências verificadas: {', '.join(context['tendencies_hashtags'])}
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
            - Nunca mencionar “sem dados disponíveis” no texto final.  
            - Conteúdo deve soar autêntico e profissional.
            - Conteúdo deve sempre ser gerado em PT-BR
        
            ============================================================
            
            
            💬 FORMATO DE SAÍDA (APENAS UM JSON)
    
            {{
                “id”: 1,        
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
        
            O Post para “STORY” deve incluir:
            - Baseados no Assunto, objetivo e mais detalhes fornecidos, combinando estes dados com o contexto pesquisados e as informações da empres.
            - Sempre traga ideias para que o público engaje com o storie.
        
            O Post para “Reels” deve incluir:
            - Baseados no Assunto, objetivo e mais detalhes fornecidos, combinando estes dados com o contexto pesquisados e as informações da empres.
            - Roteiro deve ser escrito baseado no método de criação de conteúdo AIDA e na jornada do herói.
        
            ============================================================
            🧭 DIRETRIZES DE QUALIDADE E CONFIABILIDADE
        
            - Não inventar estatísticas, datas ou referências.  
            - Manter linguagem natural sem grandes exageros.
            - Linguagem persuasiva que expresse o tom do texto do post
            - Se faltar dados → focar na proposta de valor.  
            - Storytelling só quando houver base real.  
            - Nunca mencionar “sem dados disponíveis” no texto final.  
            - Conteúdo deve soar autêntico e profissional.
            - Conteúdo deve sempre ser gerado em PT-BR
        
            ============================================================
        
            💬 FORMATO DE SAÍDA (APENAS UM JSON)
        
            {{               
                "titulo": "Título do post",
                "roteiro": "Roteiro do Reels ou Story”
            }}

            """
        ]

    def regenerate_standalone_post_prompt(self, post_data: dict, custom_prompt: str, context: dict) -> list[str]:
        """Build campaign generation prompts based on the user's creator profile."""
        profile_data = get_creator_profile_data(self.user)
        formatted_context = format_weekly_context_output(context)

        return [
            """
            Você é um estrategista de conteúdo e redator de marketing digital especializado em redes sociais. Sua função é re-criar um post para o Instagram totalmente personalizado e criativo para esta empresa. Caso o post seja de tipo "reels" ou "story", traga o conteúdo em formato de roteiro de reels ou story. Caso contrário, recrie o post apropriado para ser postado no feed do usuário. Se alguma informação estiver ausente ou marcada como 'sem dados disponíveis', você deve ignorar essa parte sem criar suposições. Não invente dados, tendências, números ou nomes de concorrentes.
             
             Caso um prompt de usuário esteja disponível, utilize-o como base principal para a criação do conteúdo.
             
             Baseie o conteúdo dos posts no contexto pesquisado, sempre respeitando o tom de voz da marca, porém seja criativo e crie conteúdo engajador, utilizando o método AIDA. Usar também como referência a jornada do herói.""",
            f"""
            ============================================================
            ### DADOS DE ENTRADA (Inseridos pelo usuário):
            - Assunto do post: {post_data['name']}
            - Objetivo do post: {post_data['objective']}
            - Tipo do post: {post_data['type']}
            - Mais detalhes: {post_data['further_details']}
            - Conteúdo anterior do post: {post_data['content']}

            ============================================================

            ### PROMPT PERSONALIZADO DO USUÁRIO:
            - Prompt personalizado: {custom_prompt}

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
               - Baseada nos dados de contexto pesquisado e dados inseridos pelo usuário (Assunto, objetivo e mais detalhes) , crie uma legenda criativa para o post
               - Ignorar itens sem dados disponíveis
               - Limite máximo de 600 caracteres
               - Pode citar fontes reais quando relevante

            3. **Hashtags recomendadas**:
               - Adicione as hashtags de tendências verificadas: {', '.join(context['tendencies_hashtags'])}
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
            - Nunca mencionar “sem dados disponíveis” no texto final.  
            - Conteúdo deve soar autêntico e profissional.
            - Conteúdo deve sempre ser gerado em PT-BR

            ============================================================


            💬 FORMATO DE SAÍDA (APENAS UM JSON)

            {{
                “id”: 1,        
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

            O Post para “STORY” deve incluir:
            - Baseados no Assunto, objetivo e mais detalhes fornecidos, combinando estes dados com o contexto pesquisados e as informações da empres.
            - Sempre traga ideias para que o público engaje com o storie.

            O Post para “Reels” deve incluir:
            - Baseados no Assunto, objetivo e mais detalhes fornecidos, combinando estes dados com o contexto pesquisados e as informações da empres.
            - Roteiro deve ser escrito baseado no método de criação de conteúdo AIDA e na jornada do herói.

            ============================================================
            🧭 DIRETRIZES DE QUALIDADE E CONFIABILIDADE

            - Não inventar estatísticas, datas ou referências.  
            - Manter linguagem natural sem grandes exageros.
            - Linguagem persuasiva que expresse o tom do texto do post
            - Se faltar dados → focar na proposta de valor.  
            - Storytelling só quando houver base real.  
            - Nunca mencionar “sem dados disponíveis” no texto final.  
            - Conteúdo deve soar autêntico e profissional.
            - Conteúdo deve sempre ser gerado em PT-BR

            ============================================================

            💬 FORMATO DE SAÍDA (APENAS UM JSON)

            {{               
                "titulo": "Título do post",
                "roteiro": "Roteiro do Reels ou Story”
            }}

            """
        ]

    def semantic_analysis_prompt(self, post_text: str) -> list[str]:
        """Prompt for semantic analysis of user input."""
        profile_data = get_creator_profile_data(self.user)

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
            
            Adapte a analise para se adequar as cores da marca.
            Crie uma sugestão visual para a imagem que será gerada a partir do post_text_feed
            
            A sugestão visual deve seguir as regras:
            - Descrição da imagem, layout, estilo  
            - Coerente com o propósito e valores da empresa.
            - Adicionar “Título do post” à “sugestão visual”  é obrigatório- Adicionar “Sub Título do post” à sugestão visual  é facultativo. Você pode escolher de acordo com o conceito e estética desejados
            - Adicionar “Chamada para ação” à sugestão visual é facultativo. Você pode escolher de acordo com o conceito e estética desejados.
            - Adicionar “tipografia” indicada para composição com a sugestão de imagem sugerida.
            - Nunca adicione o texto de “legenda completa” à sugestão visual.
            - Nunca adicione o texto de “Hashtags” à sugestão visual.
            
            Texto: {post_text}
            
            "Cores da marca": {profile_data['color_palette']}
            
            A SAÍDA DEVE SER NO FORMATO:
            {{
                "analise_semantica": {{
                    "tema_principal": "",
                    "subtemas": [],
                    "conceitos_visuais": [],
                    "objetos_relevantes": [],
                    "contexto_visual_sugerido": "",
                    "emoções_associadas": [],
                    "tons_de_cor_sugeridos": [],
                    "ação_sugerida": "",
                    "sensação_geral": "",
                    "palavras_chave": [],
                    "sugestao_visual": []
                }}
            }}
            """
        ]

    def image_generation_prompt(self, semantic_analysis: dict) -> list[str]:
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

        # Gera seção de logo com instruções detalhadas
        logo_section = build_logo_section(
            business_name=profile_data.get('business_name', ''),
            color_palette=profile_data.get('color_palette', [])
        )

        # Formata cores da paleta para o prompt
        colors_formatted = format_colors_for_prompt(profile_data.get('color_palette', []))

        return [
            f"""
            Crie uma imagem seguindo o estilo e contexto descritos abaixo.

            - Estilo visual:
                - Tipo estilo: {visual_style_info['tipo_estilo']},
                - Descrição completa: {visual_style_info['descricao_completa']}

            - Contexto e conteudo:
                - Contexto visual sugerido: {semantic_analysis['contexto_visual_sugerido']},
                - Elementos relevantes: {', '.join(semantic_analysis['objetos_relevantes'])},
                - Tema principal do post: {semantic_analysis['tema_principal']}

            - Emoção e estética:
                - Emoções associadas: {', '.join(semantic_analysis['emoções_associadas'])},
                - Sensação geral: {semantic_analysis['sensação_geral']},
                - Tons de cor sugeridos: {', '.join(semantic_analysis['tons_de_cor_sugeridos'])}

            - Paleta de cores da marca (use estas cores preferencialmente):
{colors_formatted}

            {logo_section}

            - Regras e Restrições:
                - Sempre renderize um texto na imagem com um título curto referente ao conteúdo do post.
                - Todas as imagens devem renderizar o texto do título do post na imagem.
                - Nunca renderize o texto das hashtags do post na imagem.
                - Nunca renderize códigos HEX de cores na imagem.
                - Textos renderizados na imagem devem sempre ser escritos em português do Brasil (PT-BR).
        """
        ]

    # =========================================================================
    # ANÁLISE HISTÓRICA E POSTS AUTOMÁTICOS
    # =========================================================================

    def build_historical_analysis_prompt(self, post_data: dict) -> list[str]:
        """
        Analisa posts anteriores para evitar conteúdo repetitivo.

        Este método gera um prompt que analisa o histórico de conteúdos
        anteriores e cria um novo direcionamento criativo inédito.

        Args:
            post_data: Dados do post (name, objective, further_details)

        Returns:
            Lista de prompts para análise histórica
        """
        profile_data = get_creator_profile_data(self.user)

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

    def build_automatic_post_prompt(self, analysis_data: dict = None) -> list[str]:
        """
        Gera post automático baseado em análise histórica.

        Este método usa o resultado da análise histórica para gerar
        conteúdo original que não repete posts anteriores.

        Args:
            analysis_data: Resultado do build_historical_analysis_prompt

        Returns:
            Lista de prompts para geração automática
        """
        profile_data = get_creator_profile_data(self.user)

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

    # =========================================================================
    # EDIÇÃO COM PRESERVAÇÃO
    # =========================================================================

    def build_content_edit_prompt(self, current_content: str, instructions: str = None) -> list[str]:
        """
        Prompt para edição de conteúdo preservando identidade.

        Diferente de regenerate_standalone_post_prompt que recria o post inteiro,
        este método edita APENAS o que foi solicitado, mantendo todo o resto.

        Args:
            current_content: Conteúdo original a ser editado
            instructions: Instruções específicas de edição (None para variação automática)

        Returns:
            Lista de prompts para edição
        """
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

    def build_image_edit_prompt(self, user_prompt: str = None) -> list[str]:
        """
        Prompt para edição de imagem preservando identidade visual.

        Diferente de image_generation_prompt que cria imagem nova, este método
        edita a imagem existente alterando APENAS o que foi solicitado.

        Args:
            user_prompt: Instruções do usuário para edição

        Returns:
            Lista de prompts para edição de imagem
        """
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
