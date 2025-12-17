import logging
import random
from datetime import datetime, timedelta

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
            # "benchmark_brands": profile.benchmark_brands,
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

            # Telemetria: registra a escolha de estilo (base pronta p/ bandit futuramente)
            try:
                from Analytics.models import Decision

                if self.user:
                    Decision.objects.create(
                        decision_type="visual_style",
                        action=str(random_style_id),
                        policy_id="visual_style_random_v0",
                        user=self.user,
                        resource_type="User",
                        resource_id=str(self.user.id),
                        context={
                            "styles_count": len(profile.visual_style_ids),
                            "source": "ai_prompt_service",
                        },
                        properties={},
                    )
            except Exception:
                # Nunca quebrar geração por causa de analytics
                pass

            return f'{visual_style.name} - {visual_style.description}'
        except VisualStylePreference.DoesNotExist:
            logger.warning(
                f"VisualStylePreference with id {random_style_id} not found for user {self.user.id if self.user else 'unknown'}")
            return {"name": None, "description": None}

    def _get_upcoming_holidays(self, months: int = 3) -> list:
        """Retorna uma lista de feriados brasileiros relevantes nos próximos N meses."""
        today = datetime.now()
        end_date = today + timedelta(days=months * 30)
        
        # Principais feriados e datas comemorativas fixas (Mês, Dia, Nome)
        fixed_holidays = [
            (1, 1, "Ano Novo / Confraternização Universal"),
            (1, 25, "Aniversário de São Paulo (Regional)"),
            (2, 14, "Dia de São Valentim / Valentine's Day (Internacional)"),
            (3, 8, "Dia Internacional da Mulher"),
            (3, 15, "Dia do Consumidor"),
            (4, 1, "Dia da Mentira"),
            (4, 21, "Tiradentes"),
            (5, 1, "Dia do Trabalhador"),
            (5, 12, "Dia das Mães (2024/2025 aprox - 2º domingo)"),
            (6, 12, "Dia dos Namorados (Brasil)"),
            (6, 24, "Dia de São João / Festas Juninas"),
            (7, 26, "Dia dos Avós"),
            (8, 11, "Dia dos Pais (2024/2025 aprox - 2º domingo)"),
            (9, 7, "Independência do Brasil"),
            (9, 15, "Dia do Cliente"),
            (10, 12, "Dia das Crianças / N. Sra. Aparecida"),
            (10, 31, "Halloween / Dia das Bruxas"),
            (11, 2, "Finados"),
            (11, 15, "Proclamação da República"),
            (11, 20, "Dia da Consciência Negra"),
            (11, 29, "Black Friday (2024 - Data Móvel fim nov)"),
            (12, 25, "Natal"),
            (12, 31, "Véspera de Ano Novo"),
        ]
        
        upcoming = []
        
        for month, day, name in fixed_holidays:
            try:
                # Tentar ano atual
                holiday_date = datetime(today.year, month, day)
                if today <= holiday_date <= end_date:
                    upcoming.append(f"{day:02d}/{month:02d} - {name}")
                
                # Tentar próximo ano (se estivermos no fim do ano)
                holiday_date_next = datetime(today.year + 1, month, day)
                if today <= holiday_date_next <= end_date:
                    upcoming.append(f"{day:02d}/{month:02d} - {name}")
            except ValueError:
                continue 

        return upcoming
    
    def _build_optimized_search_queries(self, profile_data: dict) -> dict:
        """Constrói queries de busca otimizadas para cada seção do relatório."""
        
        # --- Helper para Datas Dinâmicas ---
        months_pt = {
            1: "janeiro", 2: "fevereiro", 3: "março", 4: "abril",
            5: "maio", 6: "junho", 7: "julho", 8: "agosto",
            9: "setembro", 10: "outubro", 11: "novembro", 12: "dezembro"
        }
        
        today = datetime.now()
        current_year = today.year
        next_year = current_year + 1
        
        # Contexto temporal para forçar conteúdo recente (este ano ou próximo)
        time_context = f"{current_year} OR {next_year}"
        
        # Filtros Universais de Qualidade (Remove lixo acadêmico e PDFs estáticos)
        quality_filters = "-filetype:pdf -filetype:doc -filetype:docx"
        
        # Calcular próximos 3 meses para Sazonalidade
        future_dates = []
        for i in range(3):
            # i=0 (mês atual), i=1 (próximo), i=2 (seguinte)
            future_month = today.month + i
            future_year = today.year
            
            # Ajuste de ano
            if future_month > 12:
                future_month -= 12
                future_year += 1
                
            future_dates.append(f"{months_pt[future_month]} {future_year}")
            
        seasonality_dates_query = " OR ".join(future_dates)
        
        # Extrair palavras-chave dos produtos/serviços (com fallback)
        products_services = profile_data.get('products_services') or profile_data.get('business_description') or ''
        products_keywords = products_services.replace(',', ' OR ') if products_services else profile_data.get('specialization', '')
        
        # Extrair interesses do público (com fallback)
        target_interests = profile_data.get('target_interests') or ''
        audience_keywords = target_interests.replace(',', ' OR ') if target_interests else profile_data.get('specialization', '')
        
        # Domínio do país baseado na localização
        location = (profile_data.get('business_location') or 'Brasil').lower()
        location_domain = 'br' if 'brasil' in location or 'br' in location else 'com'
        
        # Concorrentes (com fallback)
        competitors = profile_data.get('main_competitors') or f"principais empresas {profile_data.get('specialization', '')}"
        competitors_query = competitors.replace(',', ' OR ')
        
        # Benchmarks (Top Players)
        benchmarks = profile_data.get('benchmark_brands') or f"melhores {profile_data.get('specialization', '')} referência mundo brasil"
        benchmarks_query = benchmarks.replace(',', ' OR ')

        # Instagram handle (com fallback)
        instagram_raw = profile_data.get('business_instagram_handle') or ''
        instagram = instagram_raw.strip('@') if instagram_raw else profile_data.get('business_name', '')
        
        queries = {
            'mercado': f"""
                {products_keywords} {profile_data['specialization']}
                {profile_data['business_location']}
                {time_context}
                (notícia OR lei OR mudança OR novidade OR lançamento OR regulamentação)
                site:{location_domain} {quality_filters} -site:medium.com -site:pinterest.* -site:slideshare.net
            """.strip(),

            'concorrencia': f"""
                ({competitors_query} OR {benchmarks_query})
                {products_keywords}
                (case de sucesso OR campanha viral OR estratégia de marketing OR lançamento inovador OR "analise de campanha")
                site:meioemensagem.com.br OR site:b9.com.br OR site:adnews.com.br OR site:propmark.com.br OR site:exame.com OR site:linkedin.com OR site:{location_domain} {quality_filters} -site:medium.com -site:pinterest.*
            """.strip(),

            'publico': f"""
                "{profile_data['target_audience']}"
                ({audience_keywords})
                comportamento tendências desejos dores {time_context}
                (pesquisa OR estudo OR relatório OR dados OR estatística) {quality_filters} -site:pinterest.* -site:slideshare.net
            """.strip(),

            'tendencias': f"""
                {profile_data['specialization']} {products_keywords}
                (polêmica OR debate OR discussão OR mudança OR "nova regra" OR opinião OR futuro OR desafio)
                {time_context}
                ("em alta" OR viral OR trend OR "hot topic")
                (site:linkedin.com OR site:{location_domain}) {quality_filters} -site:pinterest.* -site:slideshare.net
            """.strip(),

            'sazonalidade': f"""
                eventos conferências workshops
                {profile_data['specialization']} {products_keywords}
                {profile_data['business_location']}
                ({seasonality_dates_query} OR eventos {current_year})
                (site:sympla.com.br OR site:eventbrite.com.br OR site:feirasdobrasil.com.br OR site:e-inscricao.com OR site:linkedin.com OR agenda OR calendário)
                {quality_filters}
            """.strip(),

            'marca': f"""
                {profile_data['specialization']} "comportamento do consumidor" "sentimento" {current_year}
                (tendência de comportamento OR mood do mercado OR clima cultural) {quality_filters} -site:pinterest.*
            """.strip()
        }
        
        return queries
    
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
            {self._get_json_schema('mercado')}
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
            {self._get_json_schema('concorrencia')}
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
            {self._get_json_schema('tendencias')}
            """
        ]
    
    def _build_seasonality_prompt(self, profile_data: dict, queries: dict) -> list:
        """Constrói prompt específico para sazonalidade (Parser de Eventos)."""
        current_date_str = datetime.now().strftime("%d/%m/%Y")
        upcoming_holidays = self._get_upcoming_holidays(months=3)
        upcoming_holidays_text = "\n            ".join(upcoming_holidays)

        return [
            """
            Você é um 'Event API Parser' inteligente. 
            Sua função é extrair dados estruturados de eventos (Data, Nome, Local) a partir de snippets de busca do Google.
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
            Você é um analista de reputação de marca com acesso ao Google Search.
            Faça UMA busca específica sobre menções e avaliações da marca.
            Use APENAS URLs retornadas pela ferramenta google_search.
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

    def _format_date_ptbr(self, date_obj) -> str:
        """Converte objeto date em string 'DD de mês' (ex: '25 de dezembro')."""
        months = {
            1: 'janeiro', 2: 'fevereiro', 3: 'março', 4: 'abril',
            5: 'maio', 6: 'junho', 7: 'julho', 8: 'agosto',
            9: 'setembro', 10: 'outubro', 11: 'novembro', 12: 'dezembro'
        }
        return f"{date_obj.day} de {months[date_obj.month]}"

    def _get_json_schema(self, section_name: str) -> str:
        """Retorna o schema JSON esperado para cada seção."""
        
        # Schema padronizado para oportunidades com múltiplos ângulos e scoring
        opportunities_schema = """
        {
            "fontes_analisadas": [
                {
                    "url_original": "URL exata da fonte analisada",
                    "titulo_original": "Título da matéria original",
                    "oportunidades": [
                        {
                            "titulo_ideia": "Título criativo e engajador para o post",
                            "tipo": "Escolha um: Polêmica, Educativo, Newsjacking, Entretenimento, Estudo de Caso, Futuro",
                            "score": 85,
                            "explicacao_score": "Por que recebeu essa nota? (ex: Alta polêmica + Urgência)",
                            "texto_base_analisado": "Trecho ou resumo do parágrafo que inspirou esta ideia",
                            "gatilho_criativo": "Instrução rápida de como executar (ex: Faça um vídeo reagindo...)"
                        }
                    ]
                }
            ],
                  "fontes": ["URL 1", "URL 2"]
        }
        """

        schemas = {
            'mercado': opportunities_schema,
            'tendencias': opportunities_schema,
            'concorrencia': opportunities_schema, # Unificando estrutura para simplificar agregação
            'publico': """
            {
                "perfil": "Dados demográficos ou comportamentais recentes",
                "comportamento_online": "Onde estão engajando agora",
                  "interesses": ["Interesse 1", "Interesse 2"],
                  "fontes": ["URL 1", "URL 2"]
            }
            """,
            'sazonalidade': """
            {
                "datas_relevantes": [
                    { "data": "YYYY-MM-DD", "evento": "Nome do Evento", "sugestao": "Sugestão de ação" }
                ],
                "eventos_locais": ["Nome do Evento (Local) - Data"],
                "fontes": ["URL do calendário/evento"]
            }
            """,
            'marca': """
            {
                "presenca_online": "Resumo do que foi encontrado",
                "reputacao": "Sentimento geral",
                "tom_comunicacao_atual": "Análise do tom",
                  "fontes": ["URL 1", "URL 2"]
            }
            """
        }
        return schemas.get(section_name, "{}")

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
        {self._get_json_schema(section_name)}
        """
        
        return [prompt]

    def build_content_prompts(self, context: dict, posts_quantity: str) -> list[str]:
        """Build content generation prompts based on the user's creator profile."""
        profile_data = self._get_creator_profile_data()

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
              - As de {context.get('tendencies_hashtags', [])}
              - As tendências verificadas em {context.get('tendencies_popular_themes', [])}
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
            """,
        ]

    def semantic_analysis_prompt(self, post_text: str) -> list[str]:
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

    def adapted_semantic_analysis_prompt(self, semantic_analysis: dict) -> list[str]:
        """Prompt for semantic analysis adapted to creator profile."""
        profile_data = self._get_creator_profile_data()

        return [
            """
              Você é um Diretor de Arte Sênior de Inteligência Artificial. Sua tarefa é fundir uma análise semântica de conteúdo com um perfil de marca específico, garantindo que o resultado seja uma diretriz visual coesa, priorizando **integralmente** o estilo e a paleta de cores da marca, mesmo que os temas originais sejam de naturezas diferentes (ex: Café com estilo Futurista).
            """,
            f"""
            ### DADOS DE ENTRADA ####
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
