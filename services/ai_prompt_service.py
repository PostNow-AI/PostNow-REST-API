import logging
from datetime import datetime

from format_weekly_context import format_weekly_context_output
from services.get_creator_profile_data import get_creator_profile_data
from services.prompt_utils import (
    get_json_schema,
    get_upcoming_holidays,
)

logger = logging.getLogger(__name__)


class AIPromptService:
    def __init__(self):
        self.user = None

    def set_user(self, user) -> None:
        """Set the user for whom the prompts will be generated."""
        self.user = user

    def _build_market_prompt(self, profile_data: dict, queries: dict) -> list:
        """Constrói prompt específico para análise de mercado."""
        # Unificando lógica de prompt para seções de conteúdo (Mercado, Tendências, Concorrência)
        # com Chain of Thought, Scoring Objetivo e Diversidade Forçada
        
        # Observação: esta função não recebe os snippets/URLs diretamente;
        # a restrição de uso de fontes é adicionada em `_build_synthesis_prompt` (append).
        return [
            """
            Você é um Editor-Chefe de Conteúdo Viral e Estrategista de Marketing (Estilo Opus Clip / BuzzSumo).
            Sua missão é MINERAR e MULTIPLICAR oportunidades de conteúdo a partir de fontes de dados.
            NÃO RESUMA. CRIE GANCHOS VIRAIS.
            """,
            f"""
            BUSCA: {queries['mercado']}
            
            Setor: {profile_data['specialization']}
            
            /// ROTEIRO DE PENSAMENTO (CHAIN OF THOUGHT) - SIGA ESTA SEQUÊNCIA ///
            
            1. ANÁLISE DE FATOS:
               - Leia cada fonte encontrada e extraia os 3 fatos ou conceitos principais.
            
            2. DIVERGÊNCIA CRIATIVA (OBRIGATÓRIO):
               - Para CADA fato, force a criação de ideias em 3 "Modos" diferentes:
                 a) MODO POLÊMICO (Jornalista): "O que aqui é controverso, injusto ou chocante?"
                 b) MODO EDUCATIVO (Professor): "O que é complexo e pode ser simplificado em passos?"
                 c) MODO FUTURISTA (Visionário): "Como isso muda o mercado daqui a 1 ano?"
               - O objetivo é extrair pelo menos 3 ideias distintas de CADA fonte.
            
            3. SCORING OBJETIVO (0-100) - SEJA RIGOROSO:
               Para cada ideia, calcule a nota somando os pontos:
               - [0-20] Viralidade: Desperta emoção forte (Raiva, Medo, Riso)?
               - [0-20] Urgência: É uma notícia de "AGORA" ou algo velho? (Velho = 0 pts)
               - [0-20] Hook (Gancho): O título faz a pessoa parar o scroll?
               - [0-20] Trend Match: Usa palavras-chave que estão em alta?
               - [0-20] Relevância: Impacta o bolso ou a vida do leitor?
               
               Nota Final = Soma dos pontos. (Ex: 85, 92, 45).
               NUNCA use decimais. Use APENAS inteiros.
            
            4. DIVERSIDADE FORÇADA:
               - Se a ideia 1 for "Educativo", a ideia 2 OBRIGATORIAMENTE deve ser outro tipo.
               - Garanta que na saída final haja variedade de tipos (Polêmica, Newsjacking, etc.).
            
            /// EXEMPLO DE SAÍDA (FEW-SHOT) ///
            {{
                "fontes_analisadas": [
                    {{
                        "url_original": "http://exemplo.com/noticia",
                        "titulo_original": "Nova Lei Trabalhista Aprovada",
                        "oportunidades": [
                            {{
                                "titulo_ideia": "Fim da CLT? O que a nova lei esconde de você",
                                "tipo": "Polêmica",
                                "score": 95,
                                "explicacao_score": "Alta polêmica e impacto financeiro direto.",
                                "texto_base_analisado": "A nova lei altera o artigo 5...",
                                "gatilho_criativo": "Faça um vídeo reagindo com cara de choque."
                            }},
                            {{
                                "titulo_ideia": "Guia Prático: 3 coisas que mudam no seu contrato hoje",
                                "tipo": "Educativo",
                                "score": 88,
                                "explicacao_score": "Utilidade pública imediata e alta procura.",
                                "texto_base_analisado": "Mudanças nos benefícios e férias...",
                                "gatilho_criativo": "Carrossel 'Antes x Depois'."
                            }}
                        ]
                    }}
                ],
                "fontes": ["http://exemplo.com/noticia"]
            }}
            
            SAÍDA FINAL (JSON ESTRUTURADO):
            {get_json_schema('mercado')}
            """
        ]
    
    def _build_competition_prompt(self, profile_data: dict, queries: dict) -> list:
        """Constrói prompt específico para análise de concorrência."""
        return [
            """
            Você é um Analista de Inteligência Competitiva focado em engenharia reversa de sucesso.
            """,
            f"""
            BUSCA: {queries['concorrencia']}
            
            Concorrentes/Benchmarks: {profile_data['main_competitors']} / {profile_data.get('benchmark_brands', '')}
            
            /// ROTEIRO DE PENSAMENTO ///
            
            1. IDENTIFICAÇÃO DE PADRÕES:
               - O que eles estão fazendo que está dando certo (ou errado)?
               - Procure por campanhas, lançamentos ou posicionamentos recentes.
            
            2. EXTRAÇÃO DE GANCHOS (Multi-Persona):
               a) ESTUDO DE CASO: "Como eles conseguiram X resultado?"
               b) CRÍTICA/ANÁLISE: "Por que a estratégia Y vai falhar?"
               c) NEWSJACKING: "Aproveite a onda do lançamento Z deles."
            
            3. SCORING (0-100):
               - [0-20] Sucesso Comprovado: A ação viralizou?
               - [0-20] Replicabilidade: É fácil copiar a estratégia?
               - [0-20] Hook: O título da análise é forte?
               - [0-20] Autoridade: Gera credibilidade falar sobre isso?
               - [0-20] Urgência.
            
            SAÍDA (JSON ESTRUTURADO):
            {get_json_schema('concorrencia')}
            """
        ]

    def _build_trends_prompt(self, profile_data: dict, queries: dict) -> list:
        """Constrói prompt específico para tendências."""
        return [
            """
            Você é um Caçador de Tendências (Coolhunter) e Analista de Dados.
            """,
            f"""
            BUSCA: {queries['tendencias']}
            
            Setor: {profile_data['specialization']}
            
            /// ROTEIRO DE PENSAMENTO ///
            
            1. DETECÇÃO DE SINAL:
               - Identifique tópicos que estão crescendo (Trending).
               - Ignore tendências mortas ou muito antigas (> 3 meses).
            
            2. CRIAÇÃO DE ÂNGULOS (Divergência):
               a) FUTURO/VISÃO: "Isso é o fim de X?" ou "O futuro de Y."
               b) POLÊMICA: "Por que todo mundo está errado sobre [Trend]."
               c) UTILIDADE: "Ferramentas para surfar na onda de [Trend]."
            
            3. SCORING (0-100):
               - [0-40] TREND MATCH (Peso Dobrado): O assunto está MUITO em alta?
               - [0-20] Hook.
               - [0-20] Emoção.
               - [0-20] Facilidade.
            
            SAÍDA (JSON ESTRUTURADO):
            {get_json_schema('tendencias')}
            """
        ]
    
    def _build_seasonality_prompt(self, profile_data: dict, queries: dict) -> list:
        """Constrói prompt específico para sazonalidade (Parser de Eventos)."""
        current_date_str = datetime.now().strftime("%d/%m/%Y")
        upcoming_holidays = get_upcoming_holidays(months=3)
        upcoming_holidays_text = "\n            ".join(upcoming_holidays)

        return [
            """
            Você é um 'Event API Parser' inteligente. 
            Sua função é extrair dados estruturados de eventos (Data, Nome, Local) a partir de snippets de busca.
            """,
            f"""
            INPUT DE BUSCA: {queries['sazonalidade']}
            
            CONTEXTO:
            - Hoje: {current_date_str}
            - Local: {profile_data['business_location']}
            - Setor: {profile_data['specialization']}
            
            TAREFA:
            1. Analise os resultados da busca (snippets) para encontrar eventos com DATAS FUTURAS e ESPECÍFICAS.
            2. Procure padrões como "Sáb, 20 Set", "15 de Outubro", "20/11".
            3. Extraia APENAS eventos que ainda não aconteceram.
            
            SAÍDA ESPERADA (JSON):
            {{
                "datas_relevantes": ["DD/MM - Nome do Evento (Local se houver) - Sugestão de ação"],
                "eventos_locais": [],
                "fontes": ["URL da fonte 1"]
            }}
            
            DATAS DE BACKUP (Use SE E SOMENTE SE a busca não retornar eventos de nicho futuros):
            {upcoming_holidays_text}
            
            REGRAS DE EXTRAÇÃO:
            - Priorize eventos de sites como Sympla, Eventbrite, Feiras do Brasil.
            - Se o snippet diz "Eventos em São Paulo - Sympla", e não tem data específica no título/snippet, NÃO invente uma data.
            - Se não encontrar NENHUM evento futuro específico nos snippets, use as DATAS DE BACKUP.
            - Formato final da string: "DD/MM - Nome do Evento - Dica rápida".
            
            CRÍTICO:
            - IGNORE eventos passados.
            - PROIBIDO criar eventos genéricos como "Eventos de Gestão (Remoto)" ou "Monitorar plataformas".
            - Se não tiver nome específico e data exata, NÃO inclua.
            - Se usar backup, mantenha as fontes da busca se forem relevantes, ou deixe vazio.
            """
        ]
    
    def _build_brand_prompt(self, profile_data: dict, queries: dict) -> list:
        """Constrói prompt específico para análise de marca."""
        return [
            """
            Você é um analista de reputação de marca.
            Faça UMA busca específica sobre menções e avaliações da marca.
            Use APENAS URLs retornadas pela busca.
            Se não encontrar menções, retorne 'Sem dados recentes'.
            """,
            f"""
            BUSCA ESPECÍFICA - PRESENÇA E REPUTAÇÃO DA MARCA
            
            Query: {queries['marca']}
            
            Marca: {profile_data['business_name']}
            Instagram: @{profile_data.get('business_instagram_handle', '')}
            Descrição: {profile_data.get('business_description', '')}
            
            TAREFA:
            1. Analise o "Mood Geral" do mercado com base nos resultados da busca (ex: Otimista, Cauteloso, Focado em Sustentabilidade).
            2. Cruze isso com o Tom de Voz da marca: "{profile_data.get('voice_tone', 'Profissional')}".
            3. Gere uma "Diretriz Editorial" para a semana.
               Ex: "O mercado está cauteloso. Sua marca é 'Divertida'. Sugestão: Use humor leve para quebrar o gelo, mas evite exageros."
            
            SAÍDA (JSON):
            {{
                "presenca_online": "Resumo do clima/mood do mercado esta semana.",
                "reputacao": "Neutro",
                "tom_comunicacao_atual": "Sua sugestão estratégica de tom para a semana.",
                "fontes": ["URL exata 1", "URL exata 2"]
            }}
            
            CRÍTICO: O campo "fontes" deve conter as URLs EXATAS retornadas pela busca.
            """
        ]

    def _build_synthesis_prompt(self, section_name: str, query: str, urls: list, profile_data: dict, excluded_topics: list = None, context_borrowed: list = None) -> list:
        """Constrói prompt para síntese de dados de busca."""
        
        # Formatar URLs para o prompt
        urls_text = "\\n".join([
            f"- [{item.get('title', 'Sem título')}]({item.get('url', '')})\\n  Resumo: {item.get('snippet', 'Sem resumo')}"
            for item in urls[:6]  # Top 6 URLs para garantir insumo
        ])
        
        # Formatar Contexto Emprestado (Cross-Context)
        borrowed_text = ""
        if context_borrowed:
            borrowed_text = "\\nCONTEXTO DE MERCADO E TENDÊNCIAS (Para Inferência):\\n" + "\\n".join([
                f"- {item.get('title', '')}: {item.get('snippet', '')}"
                for item in context_borrowed[:5]
            ])
        
        # Seletor de Prompts Especializados
        if section_name == 'mercado':
            prompts = self._build_market_prompt(profile_data, {'mercado': query})
            prompts.append(f"""
            FONTES REAIS (USE APENAS ISTO, NÃO INVENTE LINKS):
            {urls_text}

            REGRAS CRÍTICAS:
            - Para cada item em \"fontes_analisadas\", o campo \"url_original\" DEVE ser uma das URLs acima (exata).
            - Se você não conseguir associar a ideia a uma URL acima, NÃO inclua essa fonte.
            """)
            return prompts
        elif section_name == 'concorrencia':
            prompts = self._build_competition_prompt(profile_data, {'concorrencia': query})
            prompts.append(f"""
            FONTES REAIS (USE APENAS ISTO, NÃO INVENTE LINKS):
            {urls_text}

            REGRAS CRÍTICAS:
            - Para cada item em \"fontes_analisadas\", o campo \"url_original\" DEVE ser uma das URLs acima (exata).
            - Se você não conseguir associar a ideia a uma URL acima, NÃO inclua essa fonte.
            """)
            return prompts
        elif section_name == 'tendencias':
            prompts = self._build_trends_prompt(profile_data, {'tendencias': query})
            prompts.append(f"""
            FONTES REAIS (USE APENAS ISTO, NÃO INVENTE LINKS):
            {urls_text}

            REGRAS CRÍTICAS:
            - Para cada item em \"fontes_analisadas\", o campo \"url_original\" DEVE ser uma das URLs acima (exata).
            - Se você não conseguir associar a ideia a uma URL acima, NÃO inclua essa fonte.
            """)
            return prompts
        elif section_name == 'sazonalidade':
            return self._build_seasonality_prompt(profile_data, {'sazonalidade': query})
        elif section_name == 'marca':
            return self._build_brand_prompt(profile_data, {'marca': query})
        
        # Fallback para seções genéricas (ex: publico)
        
        # Contexto específico e Instruções por seção
        context_extra = ""
        specific_instructions = ""
        
        if section_name == 'publico':
            context_extra = f"Foque no público: {profile_data['target_audience']}."
            specific_instructions = f"""
            - Busque dados comportamentais recentes e interesses emergentes.
            
            - FALLBACK OBRIGATÓRIO (Se a lista 'FONTES REAIS' abaixo estiver vazia):
              1. Analise o 'CONTEXTO DE MERCADO E TENDÊNCIAS' fornecido acima.
              2. CRUZE essas notícias com a persona ({profile_data['target_audience']}).
              3. INFIRA: "Dado que o mercado fala de X, o público deve estar sentindo Y".
              4. Se não houver contexto emprestado, use seu conhecimento de Consultor de Persona.
              5. NUNCA retorne 'Sem dados'. Gere insights lógicos baseados no cenário.
            """

        # Instrução Anti-Repetição
        anti_repetition_text = ""
        if excluded_topics and section_name in ['mercado', 'tendencias']:
            topics_str = ", ".join(excluded_topics[:5])
            anti_repetition_text = f"\\n        EVITE REPETIR os seguintes temas já abordados recentemente: {topics_str}.\\n        Busque novidades ou ângulos diferentes."

        prompt = f"""
        Você é um estrategista de conteúdo sênior especializado em {section_name}.
        
        Sua tarefa é analisar os resultados de busca reais fornecidos abaixo e sintetizar um relatório JSON para um BRIEFING DE CONTEÚDO.
        
        QUERY ORIGINAL: "{query}"
        
        CONTEXTO ADICIONAL: {context_extra}
        {anti_repetition_text}
        
        INSTRUÇÕES ESPECÍFICAS:
        {specific_instructions}
        
        {borrowed_text}
        
        FONTES REAIS ENCONTRADAS (Use APENAS estas informações):
        {urls_text}
        
        REGRAS:
        1. Baseie sua análise EXCLUSIVAMENTE nos snippets e títulos acima (ou no contexto emprestado se indicado).
        2. Se os resultados forem insuficientes, admita "Sem dados suficientes" nos campos de texto ou retorne listas vazias.
        3. O campo "fontes" do JSON deve conter as URLs exatas usadas (escolha as 2-3 mais relevantes da lista acima).
        4. Retorne APENAS o JSON válido, sem markdown.
        5. Não inclua citações no formato [cite:...] ou [1] no texto final.
        
        FORMATO JSON ESPERADO:
        {get_json_schema(section_name)}
        """
        
        return [prompt]

    def build_content_prompts(self, context: dict, posts_quantity: str) -> list[str]:
        """Build content generation prompts based on the user's creator profile."""
        profile_data = get_creator_profile_data(self.user)

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
