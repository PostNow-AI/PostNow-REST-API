import logging

from CreatorProfile.models import CreatorProfile

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
            "professional_name": profile.professional_name,
            "profession": profile.profession,
            "whatsapp_number": profile.whatsapp_number,
            "business_name": profile.business_name,
            'specialization': profile.specialization,
            'business_description': 'Nenhum' if not profile.business_description else profile.business_description,
            'target_gender': 'Todos' if profile.target_gender == 'all' else profile.target_gender(),
            'target_age_range': 'Todos' if profile.target_age_range == 'all' else profile.target_age_range,
            'target_interests': 'Nenhum' if not profile.target_interests else profile.target_interests,
            'target_location': 'Nenhum' if not profile.target_location else profile.target_location,
            'voice_tone': profile.voice_tone,
            'color_palette': [profile.color_1, profile.color_2,
                              profile.color_3, profile.color_4, profile.color_5],
            'competition': ['Nenhum'],
            'references': ['Nenhum'],
            'purpose': 'Nenhum' if not profile.business_description else profile.business_description,
            'values_personality': 'Nenhum' if not profile.voice_tone else profile.voice_tone,
            'main_goal': 'Nenhum' if not profile.business_description else profile.business_description,
            'desired_post_types': ['Nenhum'],
        }
        return profile_data

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
            - Localização principal: {profile_data['target_location']}
            - Público-alvo: {profile_data['target_gender']}, {profile_data['target_age_range']}, interesses em {profile_data['target_interests']}
            - Concorrentes conhecidos: {profile_data['competition']}
            - Perfis de referência: {profile_data['references']}
            
            Com base nessas informações, realize uma pesquisa online (via web.search) e elabore um **relatório factual e sintetizado**, retornando apenas dados verificáveis. Inclua links das fontes quando possível.
            
            ---## INSTRUÇÕES RÍGIDAS
            
            1. Não faça inferências, previsões ou generalizações sem base em fontes reais.
            2. Cite as fontes em cada seção, preferindo domínios oficiais, publicações de mercado ou notícias recentes.
            3. Se alguma informação não puder ser encontrada, escreva: "sem dados disponíveis".
            4. Priorize fontes brasileiras se {profile_data['target_location']} for no Brasil; caso contrário, use fontes regionais relevantes.
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
            - Propósito: {profile_data['purpose']}
            - Valores e personalidade: {profile_data['values_personality']}
            - Tom de voz: {profile_data['voice_tone']}
            - Público-alvo:  {profile_data['target_gender']}, {profile_data['target_age_range']}, interesses em {profile_data['target_interests']}
            - Interesses do Público: {profile_data['target_interests']}
            - Tipos de post desejados: {profile_data['desired_post_types']}
            - Objetivo principal: {profile_data['main_goal']}
            - Produtos ou serviços prioritários: {profile_data['specialization'], profile_data['business_description']}
            
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
            5. **CTA (chamada para ação)**, relevante e consistente com o objetivo {profile_data['main_goal']}.
            
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
