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
from datetime import datetime

from services.color_extraction import format_colors_for_prompt
from services.format_weekly_context import format_weekly_context_output
from services.get_creator_profile_data import get_creator_profile_data
from services.prompt_logo import build_logo_section
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

    def build_context_prompts(self, discovered_trends: dict = None) -> list[str]:
        """Build context prompts based on the user's creator profile.

        Args:
            discovered_trends: Tendências pré-descobertas via Google Trends (opcional).
                              Quando fornecido, a IA DEVE usar EXCLUSIVAMENTE essas
                              tendências - NÃO pode inventar ou sugerir outras.
                              Isso garante que todo conteúdo seja baseado em dados reais.
        """
        profile_data = get_creator_profile_data(self.user)

        # Formatar tendências descobertas para inclusão no prompt
        trends_section = self._format_discovered_trends_for_prompt(discovered_trends)

        return [
            """
            Você é um 'Event API Parser' inteligente.
            Sua função é extrair dados estruturados de eventos (Data, Nome, Local) a partir de snippets de busca do Google.
            """,
            f"""
            🏢 DADOS DO ONBOARDING DA EMPRESA
            - Nome da empresa: {profile_data['business_name']}
            - Site da empresa: {profile_data['business_website']}

            - Descrição do negócio: {profile_data['business_description']}
            - Setor / nicho de mercado: {profile_data['specialization']}
            - Localização principal: {profile_data['business_location']}
            - Público-alvo: {profile_data['target_audience']}
            - Interesses do público: {profile_data['target_interests']}
            - Concorrentes conhecidos: {profile_data['main_competitors']}
            - Perfis de referência: {profile_data['reference_profiles']}
{trends_section}
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
            6. REGRA CRÍTICA - TENDÊNCIAS:
               - Se tendências pré-validadas foram fornecidas acima, você DEVE usar
                 SOMENTE essas tendências na seção "tendencias" do output.
               - NÃO invente temas novos. Use APENAS os temas da lista fornecida.
               - As fontes já estão validadas - use-as diretamente.
               - Se não houver tendências pré-validadas, pesquise normalmente.

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
                "temas_populares": [
                  {{"tema": "Tema 1", "trend_source": "tendência original da lista"}},
                  {{"tema": "Tema 2", "trend_source": "tendência original da lista"}}
                ],
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
            """
        ]

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

    def _format_discovered_trends_for_prompt(self, discovered_trends: dict = None) -> str:
        """
        Formata tendências descobertas para inclusão no prompt.

        Args:
            discovered_trends: Dict com tendências do TrendsDiscoveryService

        Returns:
            String formatada para inclusão no prompt, ou string vazia se não houver tendências
        """
        if not discovered_trends or discovered_trends.get('validated_count', 0) == 0:
            return ""

        sections = []
        sections.append("""
            ============================================================
            📊 TENDÊNCIAS PRÉ-VALIDADAS (Google Trends + fontes verificadas)

            ⚠️ REGRA OBRIGATÓRIA - LEIA COM ATENÇÃO:
            Você DEVE usar EXCLUSIVAMENTE as tendências listadas abaixo.
            NÃO invente ou sugira temas que não estejam nesta lista.
            Cada item da seção "tendencias" DEVE vir desta lista.
            Se precisar de mais temas, adapte os existentes ao contexto do setor.

            PROIBIDO: Criar temas novos que não estão na lista abaixo.
            ============================================================""")

        # Tendências gerais do Brasil
        general_trends = discovered_trends.get('general_trends', [])
        if general_trends:
            sections.append("\n            🌍 TENDÊNCIAS GERAIS DO BRASIL:")
            for trend in general_trends[:5]:
                topic = trend.get('topic', '')
                sources = trend.get('sources', [])
                relevance = trend.get('relevance_score', 0)
                sections.append(f"            - {topic} (relevância: {relevance}/100)")
                if sources:
                    source_urls = [s.get('url', '') for s in sources[:2] if s.get('url')]
                    if source_urls:
                        sections.append(f"              Fontes: {', '.join(source_urls)}")

        # Tendências específicas do setor
        sector_trends = discovered_trends.get('sector_trends', [])
        if sector_trends:
            sections.append("\n            🎯 TENDÊNCIAS DO SETOR:")
            for trend in sector_trends[:5]:
                topic = trend.get('topic', '')
                sources = trend.get('sources', [])
                relevance = trend.get('relevance_score', 0)
                sections.append(f"            - {topic} (relevância: {relevance}/100)")
                if sources:
                    source_urls = [s.get('url', '') for s in sources[:2] if s.get('url')]
                    if source_urls:
                        sections.append(f"              Fontes: {', '.join(source_urls)}")

        # Tópicos em crescimento
        rising_topics = discovered_trends.get('rising_topics', [])
        if rising_topics:
            sections.append("\n            📈 TÓPICOS EM CRESCIMENTO:")
            for trend in rising_topics[:5]:
                topic = trend.get('topic', '')
                growth = trend.get('growth_score', 0)
                sections.append(f"            - {topic} (crescimento: +{growth}%)")

        # Few-shot examples para guiar a IA
        sections.append("""
            ============================================================
            📚 EXEMPLOS DE COMO USAR AS TENDÊNCIAS (Few-shot):

            EXEMPLO 1:
            Tendência fornecida: "IA generativa empresas"
            Setor do usuário: "Marketing Digital"
            Resultado esperado:
            {
              "tema": "IA generativa no marketing digital",
              "trend_source": "IA generativa empresas"
            }

            EXEMPLO 2:
            Tendência fornecida: "ChatGPT"
            Setor do usuário: "Recursos Humanos"
            Resultado esperado:
            {
              "tema": "ChatGPT para recrutamento e seleção",
              "trend_source": "ChatGPT"
            }

            EXEMPLO 3:
            Tendência fornecida: "automação processos"
            Setor do usuário: "E-commerce"
            Resultado esperado:
            {
              "tema": "Automação de atendimento no e-commerce",
              "trend_source": "automação processos"
            }

            REGRA: Sempre adapte a tendência ao setor do usuário, mas o
            "trend_source" DEVE ser exatamente uma das tendências listadas acima.
            ============================================================""")

        sections.append("")  # Linha em branco no final

        return '\n'.join(sections)

    def _format_discovered_trends_for_prompt(self, discovered_trends: dict = None) -> str:
        """
        Formata tendências descobertas para inclusão no prompt.

        Args:
            discovered_trends: Dict com tendências do TrendsDiscoveryService

        Returns:
            String formatada para inclusão no prompt, ou string vazia se não houver tendências
        """
        if not discovered_trends or discovered_trends.get('validated_count', 0) == 0:
            return ""

        sections = []
        sections.append("""
            ============================================================
            📊 TENDÊNCIAS PRÉ-VALIDADAS (Google Trends + fontes verificadas)

            ⚠️ REGRA OBRIGATÓRIA - LEIA COM ATENÇÃO:
            Você DEVE usar EXCLUSIVAMENTE as tendências listadas abaixo.
            NÃO invente ou sugira temas que não estejam nesta lista.
            Cada item da seção "tendencias" DEVE vir desta lista.
            Se precisar de mais temas, adapte os existentes ao contexto do setor.

            PROIBIDO: Criar temas novos que não estão na lista abaixo.
            ============================================================""")

        # Tendências gerais do Brasil
        general_trends = discovered_trends.get('general_trends', [])
        if general_trends:
            sections.append("\n            🌍 TENDÊNCIAS GERAIS DO BRASIL:")
            for trend in general_trends[:5]:
                topic = trend.get('topic', '')
                sources = trend.get('sources', [])
                relevance = trend.get('relevance_score', 0)
                sections.append(f"            - {topic} (relevância: {relevance}/100)")
                if sources:
                    source_urls = [s.get('url', '') for s in sources[:2] if s.get('url')]
                    if source_urls:
                        sections.append(f"              Fontes: {', '.join(source_urls)}")

        # Tendências específicas do setor
        sector_trends = discovered_trends.get('sector_trends', [])
        if sector_trends:
            sections.append("\n            🎯 TENDÊNCIAS DO SETOR:")
            for trend in sector_trends[:5]:
                topic = trend.get('topic', '')
                sources = trend.get('sources', [])
                relevance = trend.get('relevance_score', 0)
                sections.append(f"            - {topic} (relevância: {relevance}/100)")
                if sources:
                    source_urls = [s.get('url', '') for s in sources[:2] if s.get('url')]
                    if source_urls:
                        sections.append(f"              Fontes: {', '.join(source_urls)}")

        # Tópicos em crescimento
        rising_topics = discovered_trends.get('rising_topics', [])
        if rising_topics:
            sections.append("\n            📈 TÓPICOS EM CRESCIMENTO:")
            for trend in rising_topics[:5]:
                topic = trend.get('topic', '')
                growth = trend.get('growth_score', 0)
                sections.append(f"            - {topic} (crescimento: +{growth}%)")

        # Few-shot examples para guiar a IA
        sections.append("""
            ============================================================
            📚 EXEMPLOS DE COMO USAR AS TENDÊNCIAS (Few-shot):

            EXEMPLO 1:
            Tendência fornecida: "IA generativa empresas"
            Setor do usuário: "Marketing Digital"
            Resultado esperado:
            {
              "tema": "IA generativa no marketing digital",
              "trend_source": "IA generativa empresas"
            }

            EXEMPLO 2:
            Tendência fornecida: "ChatGPT"
            Setor do usuário: "Recursos Humanos"
            Resultado esperado:
            {
              "tema": "ChatGPT para recrutamento e seleção",
              "trend_source": "ChatGPT"
            }

            EXEMPLO 3:
            Tendência fornecida: "automação processos"
            Setor do usuário: "E-commerce"
            Resultado esperado:
            {
              "tema": "Automação de atendimento no e-commerce",
              "trend_source": "automação processos"
            }

            REGRA: Sempre adapte a tendência ao setor do usuário, mas o
            "trend_source" DEVE ser exatamente uma das tendências listadas acima.
            ============================================================""")

        sections.append("")  # Linha em branco no final

        return '\n'.join(sections)

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

    def build_standalone_post_prompt(self, post_data: dict, context: dict) -> list[str]:
        """Build prompt for standalone post generation from opportunity or manual creation."""
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
        colors_formatted = format_colors_for_prompt(profile_data.get('color_palette', []))

        return [
            """
              Você é um Diretor de Arte Sênior de Inteligência Artificial. Sua tarefa é fundir uma análise semântica de conteúdo com um perfil de marca específico, garantindo que o resultado seja uma diretriz visual coesa, priorizando **integralmente** a paleta de cores e a personalidade da marca, mesmo que os temas originais sejam de naturezas diferentes (ex: Café com marca Futurista).
            """,
            f"""
              ### DADOS DE ENTRADA ####

              1. PERSONALIDADE DA MARCA (Emoções)
              {profile_data['brand_personality']}

              2. ANÁLISE SEMÂNTICA (Conteúdo e Mensagem)
              {semantic_analysis}

              3. PERFIL DA MARCA (Identidade)

              - Cores da Marca (use estes nomes descritivos, não códigos hex):
{colors_formatted}
                Podem ser usadas variações mais escuras, mais claras e gradientes baseadas nestas cores.

              - Nicho: {profile_data.get('specialization', '')}
              - Tom de voz: {profile_data.get('voice_tone', '')}


              ### INSTRUÇÕES PARA ADAPTAÇÃO
              1. **Prioridade Absoluta:**
                O resultado final deve priorizar as **Cores da Marca** e a **Personalidade da Marca**.

              2. **Mapeamento Visual:**
                Adapte os `objetos_relevantes` e o `contexto_visual_sugerido` da análise semântica
                para serem coerentes com o nicho e personalidade da marca.

              3. **Mapeamento de Emoções:**
                Use a `Personalidade da Marca` para refinar a `ação_sugerida` e as `emoções_associadas`.
                Exemplo: uma marca *educadora* deve ter personagens em postura de clareza e acolhimento.

              4. **Paleta de Cores:**
                Substitua os `tons_de_cor_sugeridos` originais pelas **Cores da Marca** (nomes descritivos acima).
                Utilize as cores da marca para destaques, iluminação e elementos de fundo.
                NUNCA use códigos hex (#FFFFFF) — use apenas nomes descritivos de cor.

              5. **Geração:**
                Gere o novo JSON final com a estrutura abaixo,
                refletindo as adaptações e a priorização do `Perfil da Marca`.



              ### SAÍDA REQUERIDA (APENAS RETORNE O NOVO JSON ADAPTADO, NADA MAIS)
              {{
                "analise_semantica": {{
                    "tema_principal": "[Tema principal adaptado ao contexto da marca]",
                    "subtemas": [],
                    "titulo_imagem": "[Título curto para renderizar NA imagem, max 4 palavras, PT-BR, SEM acentos (ã, ç, é, ô, ü). Ex: 'Vendas Digital' ao invés de 'Ação Digital'. Deve ser impactante e relacionado ao tema.]",
                    "conceitos_visuais": ["[Conceitos reinterpretados para o nicho da marca]"],
                    "objetos_relevantes": ["[Objetos descritos de forma coerente com a marca]"],
                    "contexto_visual_sugerido": "[Cenário com a estética e paleta da marca]",
                    "emoções_associadas": ["[Emoções alinhadas à personalidade da marca]"],
                    "tons_de_cor_sugeridos": ["[Cores da marca em nomes descritivos e seus usos]"],
                    "ação_sugerida": "[Ação que reflete a personalidade da marca]",
                    "sensação_geral": "[Sensação geral de acordo com a estética da marca]",
                    "palavras_chave": ["[Keywords que fundem tema e marca]"]
                }}
              }}
            """
        ]

    def image_generation_prompt(self, semantic_analysis: dict, generated_style=None) -> str:
        """
        Prompt for AI image generation based on semantic analysis and generated style.

        Args:
            semantic_analysis: Dict from semantic analysis step
            generated_style: GeneratedVisualStyle instance (if None, uses fallback)
        """
        profile_data = get_creator_profile_data(self.user)

        # Gera seção de logo com instruções detalhadas
        logo_section = build_logo_section(
            business_name=profile_data.get('business_name', ''),
            color_palette=profile_data.get('color_palette', [])
        )

        # Formata cores da paleta para o prompt (agora em memory colors)
        colors_formatted = format_colors_for_prompt(profile_data.get('color_palette', []))

        # Estilo: usa GeneratedVisualStyle ou fallback
        if generated_style and hasattr(generated_style, 'style_data'):
            style = generated_style.style_data
        else:
            style = self._fallback_style(semantic_analysis, profile_data)

        style_colors = style.get('colors', {})
        references = style.get('references', [])
        references_text = ', '.join(references) if references else 'professional social media design'

        return [
            f"""Professional Instagram feed post (4:5 vertical format, 1080x1350px)
for a {profile_data.get('specialization', 'business')} business.

STYLE:
{style.get('aesthetic', 'Clean professional design')}.
{style.get('lighting', 'Soft natural daylight, diffused and even')}.
Aesthetic references: {references_text}.

SUBJECT AND CONTEXT:
Main visual: {semantic_analysis.get('contexto_visual_sugerido', '')}.
Key elements: {', '.join(semantic_analysis.get('objetos_relevantes', []))}.
Theme: {semantic_analysis.get('tema_principal', '')}.
Mood: {style.get('mood', semantic_analysis.get('sensação_geral', 'professional'))}.

COLORS:
- Background: {style_colors.get('background', 'warm ivory')}
- Primary elements: {style_colors.get('primary', 'deep cobalt blue')}
- Accent details: {style_colors.get('accent', 'vivid coral')}
- Text color: {style_colors.get('text', 'dark charcoal')}
- Brand palette (prefer these):
{colors_formatted}

COMPOSITION:
{style.get('composition', 'Title upper third centered, main visual centered, logo bottom-right 8%')}.
Typography: {style.get('typography', 'modern bold sans-serif')}.
Safe margin of 10% on all edges — no important elements near borders.
Title text: "{semantic_analysis.get('titulo_imagem', semantic_analysis.get('tema_principal', ''))}" — render this exact text, centered in the upper third, in bold {style.get('typography', 'sans-serif')} font, {style_colors.get('text', 'dark charcoal')} color.
All rendered text must be in Brazilian Portuguese (PT-BR). Do NOT add accented characters (ã, ç, é, ô, ü) unless they appear in the title above.

{logo_section}

QUALITY:
Professional social media quality, optimized for mobile viewing.
Sharp focus on text, smooth gradients, clean edges, no artifacts.

AVOID:
- Watermarks, stock photo badges
- Distorted or misspelled text
- Colors outside the specified palette
- Cluttered background, too many competing elements
- Hashtags or hex codes rendered in the image
- Text in any language other than Brazilian Portuguese
- If no logo is attached, do NOT generate or add any logo
- Do NOT add decorative text on screens, dashboards, charts, or UI elements unless explicitly requested. If the image shows a laptop/phone screen, keep it blurred or show abstract shapes instead of readable text. Any visible text risks being misspelled.
- Do NOT add generic icons (rockets, lightbulbs, gears, targets) unless the content specifically mentions them. Prefer concrete imagery related to the actual topic.
"""
        ]

    def _fallback_style(self, semantic_analysis: dict, profile_data: dict = None) -> dict:
        """Estilo fallback quando GeneratedVisualStyle não está disponível."""
        return {
            "aesthetic": "Clean professional design suitable for social media",
            "colors": {
                "background": "warm ivory",
                "primary": "deep cobalt blue",
                "accent": "vivid coral",
                "text": "dark charcoal",
            },
            "lighting": "Soft natural daylight, diffused and even",
            "typography": "modern bold sans-serif",
            "composition": "Title upper third centered, main visual centered 40% of frame, logo bottom-right 8%",
            "mood": semantic_analysis.get('sensação_geral', 'professional'),
            "references": ["editorial magazine layout"],
        }

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
