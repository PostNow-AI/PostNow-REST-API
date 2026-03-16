"""
Prompts para descoberta de contexto (mercado, concorrência, tendências, sazonalidade, marca).

Extraído de ai_prompt_service.py para separação de responsabilidades.
"""

import logging
from datetime import datetime

from services.get_creator_profile_data import get_creator_profile_data
from services.prompt_utils import (
    get_json_schema,
    get_upcoming_holidays,
)

logger = logging.getLogger(__name__)


def build_context_prompts(user, discovered_trends: dict = None) -> list[str]:
    """Build context prompts based on the user's creator profile.

    Args:
        user: Django User instance
        discovered_trends: Tendências pré-descobertas via Google Trends (opcional).
    """
    profile_data = get_creator_profile_data(user)
    trends_section = format_discovered_trends_for_prompt(discovered_trends)

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


def _build_market_prompt(profile_data: dict, queries: dict) -> list:
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


def _build_competition_prompt(profile_data: dict, queries: dict) -> list:
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


def _build_trends_prompt(profile_data: dict, queries: dict) -> list:
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


def _build_seasonality_prompt(profile_data: dict, queries: dict) -> list:
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


def _build_brand_prompt(profile_data: dict, queries: dict) -> list:
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


def build_synthesis_prompt(section_name: str, query: str, urls: list, user, excluded_topics: list = None, context_borrowed: list = None) -> list:
    """Constrói prompt para síntese de dados de busca."""
    profile_data = get_creator_profile_data(user)

    urls_text = "\\n".join([
        f"- [{item.get('title', 'Sem título')}]({item.get('url', '')})\\n  Resumo: {item.get('snippet', 'Sem resumo')}"
        for item in urls[:6]
    ])

    borrowed_text = ""
    if context_borrowed:
        borrowed_text = "\\nCONTEXTO DE MERCADO E TENDÊNCIAS (Para Inferência):\\n" + "\\n".join([
            f"- {item.get('title', '')}: {item.get('snippet', '')}"
            for item in context_borrowed[:5]
        ])

    _sources_append = f"""
            FONTES REAIS (USE APENAS ISTO, NÃO INVENTE LINKS):
            {urls_text}

            REGRAS CRÍTICAS:
            - Para cada item em \"fontes_analisadas\", o campo \"url_original\" DEVE ser uma das URLs acima (exata).
            - Se você não conseguir associar a ideia a uma URL acima, NÃO inclua essa fonte.
            """

    if section_name == 'mercado':
        prompts = _build_market_prompt(profile_data, {'mercado': query})
        prompts.append(_sources_append)
        return prompts
    elif section_name == 'concorrencia':
        prompts = _build_competition_prompt(profile_data, {'concorrencia': query})
        prompts.append(_sources_append)
        return prompts
    elif section_name == 'tendencias':
        prompts = _build_trends_prompt(profile_data, {'tendencias': query})
        prompts.append(_sources_append)
        return prompts
    elif section_name == 'sazonalidade':
        return _build_seasonality_prompt(profile_data, {'sazonalidade': query})
    elif section_name == 'marca':
        return _build_brand_prompt(profile_data, {'marca': query})

    # Fallback para seções genéricas (ex: publico)
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


def format_discovered_trends_for_prompt(discovered_trends: dict = None) -> str:
    """Formata tendências descobertas para inclusão no prompt."""
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

    rising_topics = discovered_trends.get('rising_topics', [])
    if rising_topics:
        sections.append("\n            📈 TÓPICOS EM CRESCIMENTO:")
        for trend in rising_topics[:5]:
            topic = trend.get('topic', '')
            growth = trend.get('growth_score', 0)
            sections.append(f"            - {topic} (crescimento: +{growth}%)")

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

    sections.append("")
    return '\n'.join(sections)
