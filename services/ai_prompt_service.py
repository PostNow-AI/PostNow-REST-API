import logging
import random

from CreatorProfile.models import CreatorProfile, VisualStylePreference

logger = logging.getLogger(__name__)


class AIPromptService:
    def __init__(self):
        self.user = None

    def set_user(self, user) -> None:
        """Set the user for whom the prompts will be generated."""
        self.user = user

    def _get_creator_profile_data(self) -> dict:
        """Fetch and return the creator profile data for the current user."""
        if not self.user:
            raise ValueError("User is not set for PromptService.")

        profile = CreatorProfile.objects.filter(user=self.user).first()
        if not profile:
            raise CreatorProfile.DoesNotExist
        profile_data = {
            "business_name": profile.business_name,
            "business_phone": profile.business_phone,
            "business_website": profile.business_website,
            "business_instagram_handle": profile.business_instagram_handle,
            "specialization": profile.specialization,
            "business_description": profile.business_description,
            "business_purpose": profile.business_purpose,
            "brand_personality": profile.brand_personality,
            "products_services": profile.products_services,
            "business_location": profile.business_location,
            "target_audience": profile.target_audience,
            "target_interests": profile.target_interests,
            "main_competitors": profile.main_competitors,
            "reference_profiles": profile.reference_profiles,
            "voice_tone": profile.voice_tone,
            "visual_style": self._get_random_visual_style(profile),
            'color_palette': [] if not any([
                profile.color_1, profile.color_2,
                profile.color_3, profile.color_4, profile.color_5
            ]) else [
                profile.color_1, profile.color_2,
                profile.color_3, profile.color_4, profile.color_5
            ],
            'desired_post_types': ['Nenhum'],
        }

        return profile_data

    def _get_random_visual_style(self, profile) -> dict:
        """Randomly select and fetch one visual style from the user's visual_style_ids list."""
        if not profile.visual_style_ids or len(profile.visual_style_ids) == 0:
            return {"name": None, "description": None}

        random_style_id = random.choice(profile.visual_style_ids)

        try:
            visual_style = VisualStylePreference.objects.get(
                id=random_style_id)
            return f'{visual_style.name} - {visual_style.description}'
        except VisualStylePreference.DoesNotExist:
            logger.warning(
                f"VisualStylePreference with id {random_style_id} not found for user {self.user.id if self.user else 'unknown'}")
            return {"name": None, "description": None}

    def build_context_prompts(self) -> dict:
        """Build context prompts based on the user's creator profile."""
        profile_data = self._get_creator_profile_data()

        return [
            """
                Você é um analista de mercado especializado em marketing digital e pesquisa competitiva. Sua função é coletar informações atualizadas e factuais sobre empresas, setores e públicos, para gerar um contexto confiável usado na criação de conteúdo personalizado. Sempre que possível, baseie suas respostas em fontes verificáveis encontradas na internet. Se uma informação não estiver disponível, diga explicitamente 'não encontrado' ou 'sem dados disponíveis' — nunca invente ou suponha dados.
            """,
            f"""
            A seguir estão as informações coletadas no onboarding da empresa:
            - Nome da empresa: {profile_data['business_name']}
            - Descrição do negócio: {profile_data['business_description']}
            - Setor / nicho de mercado: {profile_data['specialization']}
            - Localização principal: {profile_data['business_location']}
            - Público-alvo: {profile_data['target_audience']}, interesses em {profile_data['target_interests']}
            - Concorrentes conhecidos: {profile_data['main_competitors']}
            - Perfis de referência: {profile_data['reference_profiles']}

            Com base nessas informações, realize uma pesquisa online (via web.search) e elabore um **relatório factual e sintetizado**, retornando apenas dados verificáveis. Inclua links das fontes quando possível.

            ---## INSTRUÇÕES RÍGIDAS

            1. Não faça inferências, previsões ou generalizações sem base em fontes reais.
            2. Cite as fontes em cada seção, preferindo domínios oficiais, publicações de mercado ou notícias recentes.
            3. Se alguma informação não puder ser encontrada, escreva: "sem dados disponíveis".
            4. Priorize fontes brasileiras se {profile_data['business_location']} for no Brasil; caso contrário, use fontes regionais relevantes.
            5. Mantenha linguagem neutra e objetiva, evitando opiniões ou suposições.

            ---## ESTRUTURA DE SAÍDA (JSON)

            {{
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
                  "comportamento_online": "Principais hábitos e plataformas com dados reais.",
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
                  "reputacao": "Sentimento geral encontrado em menções ou avaliações.",
                  "tom_comunicacao_atual": "Descrição objetiva do estilo de comunicação.",
                  "fontes": ["URL 1", "URL 2"]
              }}
            }}
            """]

    def build_content_prompts(self, context: dict, posts_quantity: str) -> dict:
        """Build content generation prompts based on the user's creator profile."""
        profile_data = self._get_creator_profile_data()

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
        profile_data = self._get_creator_profile_data()

        return [
            """
              Você é um Diretor de Arte Sênior de Inteligência Artificial. Sua tarefa é fundir uma análise semântica de conteúdo com um perfil de marca específico, garantindo que o resultado seja uma diretriz visual coesa, priorizando **integralmente** o estilo e a paleta de cores da marca, mesmo que os temas originais sejam de naturezas diferentes (ex: Café com estilo Futurista).
            """,
            f"""
              ### DADOS DE ENTRADA  ####
              1. ANÁLISE SEMÂNTICA (Conteúdo e Mensagem)
              {semantic_analysis}

              #### 2. PERFIL DA MARCA (Estilo e Identidade)
              // Cole o conteúdo do seu JSON "brand_profile" aqui.
              // Esta seção define COMO DEVE SER MOSTRADO (Estilo prioritário).

              {profile_data}

              ### INSTRUÇÕES PARA ADAPTAÇÃO
              1.  **Prioridade Absoluta:** O resultado final deve priorizar o **"Estilo Visual"** e as **"Cores da Marca"** definidos no `brand_profile`.
              2.  **Mapeamento Visual:** Adapte os `objetos_relevantes` e o `contexto_visual_sugerido` da análise semântica para o `Estilo Visual` da marca. Por exemplo, se o tema é 'natureza' e o estilo é '3D Futurista', a natureza deve ser renderizada em 3D, com brilhos e linhas geométricas.
              3.  **Mapeamento de Emoções:** Use a `Personalidade da Marca` para refinar a `ação_sugerida` e as `emoções_associadas`. (Ex: Uma marca 'educadora' deve ter personagens em postura de clareza e acolhimento).
              4.  **Paleta de Cores:** Substitua os `tons_de_cor_sugeridos` originais pelas **Cores da Marca** fornecidas. Use as cores da marca para destaques, iluminação e elementos de fundo, mantendo a consistência.
              5.  **Geração:** Gere o novo JSON final com a estrutura `analise_semantica` abaixo, refletindo as alterações e a priorização do `brand_profile`.

              ### SAÍDA REQUERIDA (NOVO JSON ADAPTADO)
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
        profile_data = self._get_creator_profile_data()

        return f"""
          Crie uma imagem em estilo {profile_data['visual_style']}.

          {semantic_analysis['contexto_visual_sugerido']}.

          Inclua elementos como {semantic_analysis['objetos_relevantes']}.

          Transmita as emoções de {semantic_analysis['emoções_associadas']} e a sensação geral de {semantic_analysis['sensação_geral']}.

          Use tons de {semantic_analysis['tons_de_cor_sugeridos']}.

          O post fala sobre: {semantic_analysis['tema_principal']}.

          A marca é {profile_data['business_name']}, cujo estilo é {profile_data['visual_style']} e paleta é {profile_data['color_palette']}.

          REGRAS/RESTRIÇÕES:
          NÃO GERE OU ADICIONE LOGOMARCAS OU MARCAS D'ÁGUA
        """
