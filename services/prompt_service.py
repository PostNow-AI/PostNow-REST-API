import logging

from CreatorProfile.models import CreatorProfile

logger = logging.getLogger(__name__)


class PromptService:
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
            'target_age_range': 'Todos' if profile.target_age_group == 'all' else profile.target_age_group,
            'target_interests': 'Nenhum' if not profile.target_interests else profile.target_interests,
            'target_location': 'Nenhum' if not profile.target_location else profile.target_location,
            'voice_tone': profile.voice_tone,
            'color_palette': [profile.color_1, profile.color_2,
                              profile.color_3, profile.color_4, profile.color_5],
            'competition': ['Nenhum' if not profile.competition else profile.competition],
            'references': ['Nenhum' if not profile.references else profile.references],
        }
        return profile_data

    def build_context_prompts(self) -> dict:
        """Build context prompts based on the user's creator profile."""
        profile_data = self._get_creator_profile_data()

        return {
            'prompt_1': """
                Você é um analista de mercado especializado em marketing digital e pesquisa competitiva. Sua função é coletar informações atualizadas e factuais sobre empresas, setores e públicos, para gerar um contexto confiável usado na criação de conteúdo personalizado. Sempre que possível, baseie suas respostas em fontes verificáveis encontradas na internet. Se uma informação não estiver disponível, diga explicitamente 'não encontrado' ou 'sem dados disponíveis' — nunca invente ou suponha dados.
            """,
            'prompt_2': f"""
            A seguir estão as informações coletadas no onboarding da empresa:
            - Nome da empresa: {profile_data['company_name']}
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
            4. Priorize fontes brasileiras se {{localizacao}} for no Brasil; caso contrário, use fontes regionais relevantes.
            5. Mantenha linguagem neutra e objetiva, evitando opiniões ou suposições.
            
            ---## ESTRUTURA DE SAÍDA (JSON)
            
            {{
                "mercado": {
                "panorama": "Resumo factual do setor com dados e referências.",
                  "tendencias": ["Tendência 1", "Tendência 2"],
                  "desafios": ["Desafio 1", "Desafio 2"],
                  "fontes": ["URL 1", "URL 2"]
                },
                "concorrencia": {
                "principais": ["Concorrente 1", "Concorrente 2"],
                  "estrategias": "Síntese factual das abordagens observadas.",
                  "oportunidades": "Possíveis diferenciais com base nos fatos.",
                  "fontes": ["URL 1", "URL 2"]
                },
                "publico": {
                "perfil": "Descrição factual do público baseada em pesquisas.",
                  "comportamento_online": "Principais hábitos e plataformas com dados reais.",
                  "interesses": ["Interesse 1", "Interesse 2"],
                  "fontes": ["URL 1", "URL 2"]
                },
                "tendencias": {
                "temas_populares": ["Tema 1", "Tema 2"],
                  "hashtags": ["#hashtag1", "#hashtag2"],
                  "palavras_chave": ["keyword1", "keyword2"],
                  "fontes": ["URL 1", "URL 2"]
                },
                "sazonalidade": {
                "datas_relevantes": ["Data 1", "Data 2"],
                  "eventos_locais": ["Evento 1", "Evento 2"],
                  "fontes": ["URL 1", "URL 2"]
                },
                "marca": {
                "presenca_online": "Resumo factual das aparições online.",
                  "reputacao": "Sentimento geral encontrado em menções ou avaliações.",
                  "tom_comunicacao_atual": "Descrição objetiva do estilo de comunicação.",
                  "fontes": ["URL 1", "URL 2"]
              }
            }}
            """}
