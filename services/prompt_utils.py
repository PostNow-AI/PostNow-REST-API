"""
Utility functions for prompt service - non-prompt related helpers.
"""
from datetime import datetime, timedelta


def get_upcoming_holidays(months: int = 3) -> list:
    """Return a list of relevant Brazilian holidays in the next N months."""
    today = datetime.now()
    end_date = today + timedelta(days=months * 30)

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
            holiday_date = datetime(today.year, month, day)
            if today <= holiday_date <= end_date:
                upcoming.append(f"{day:02d}/{month:02d} - {name}")

            holiday_date_next = datetime(today.year + 1, month, day)
            if today <= holiday_date_next <= end_date:
                upcoming.append(f"{day:02d}/{month:02d} - {name}")
        except ValueError:
            continue

    return upcoming


def format_date_ptbr(date_obj) -> str:
    """Convert date object to 'DD de mês' format (e.g., '25 de dezembro')."""
    months = {
        1: 'janeiro', 2: 'fevereiro', 3: 'março', 4: 'abril',
        5: 'maio', 6: 'junho', 7: 'julho', 8: 'agosto',
        9: 'setembro', 10: 'outubro', 11: 'novembro', 12: 'dezembro'
    }
    return f"{date_obj.day} de {months[date_obj.month]}"


def build_optimized_search_queries(profile_data: dict) -> dict:
    """Build optimized search queries for each report section."""

    months_pt = {
        1: "janeiro", 2: "fevereiro", 3: "março", 4: "abril",
        5: "maio", 6: "junho", 7: "julho", 8: "agosto",
        9: "setembro", 10: "outubro", 11: "novembro", 12: "dezembro"
    }

    today = datetime.now()
    current_year = today.year
    next_year = current_year + 1
    time_context = f"{current_year} OR {next_year}"
    quality_filters = "-filetype:pdf -filetype:doc -filetype:docx"

    future_dates = []
    for i in range(3):
        future_month = today.month + i
        future_year = today.year

        if future_month > 12:
            future_month -= 12
            future_year += 1

        future_dates.append(f"{months_pt[future_month]} {future_year}")

    seasonality_dates_query = " OR ".join(future_dates)

    products_services = profile_data.get('products_services') or profile_data.get('business_description') or ''
    products_keywords = products_services.replace(',', ' OR ') if products_services else profile_data.get('specialization', '')

    target_interests = profile_data.get('target_interests') or ''
    audience_keywords = target_interests.replace(',', ' OR ') if target_interests else profile_data.get('specialization', '')

    location = (profile_data.get('business_location') or 'Brasil').lower()
    location_domain = 'br' if 'brasil' in location or 'br' in location else 'com'

    competitors = profile_data.get('main_competitors') or f"principais empresas {profile_data.get('specialization', '')}"
    competitors_query = competitors.replace(',', ' OR ')

    benchmarks = profile_data.get('benchmark_brands') or f"melhores {profile_data.get('specialization', '')} referência mundo brasil"
    benchmarks_query = benchmarks.replace(',', ' OR ')

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


def get_json_schema(section_name: str) -> str:
    """Return the expected JSON schema for each section."""

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
        'concorrencia': opportunities_schema,
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
