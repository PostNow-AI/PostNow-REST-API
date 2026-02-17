"""Mapeamento centralizado JSON -> Model fields para ClientContext."""

CONTEXT_FIELD_MAPPING = {
    'mercado': {
        'panorama': ('market_panorama', ''),
        'tendencias': ('market_tendencies', []),
        'desafios': ('market_challenges', []),
        'fontes': ('market_sources', []),
    },
    'concorrencia': {
        'principais': ('competition_main', []),
        'estrategias': ('competition_strategies', ''),
        'oportunidades': ('competition_opportunities', ''),
        'fontes': ('competition_sources', []),
    },
    'publico': {
        'perfil': ('target_audience_profile', ''),
        'comportamento_online': ('target_audience_behaviors', ''),
        'interesses': ('target_audience_interests', []),
        'fontes': ('target_audience_sources', []),
    },
    'tendencias': {
        'temas_populares': ('tendencies_popular_themes', []),
        'hashtags': ('tendencies_hashtags', []),
        'keywords': ('tendencies_keywords', []),
        'fontes': ('tendencies_sources', []),
    },
    'sazonalidade': {
        'datas_relevantes': ('seasonal_relevant_dates', []),
    },
    'sazonal': {
        'eventos_locais': ('seasonal_local_events', []),
        'fontes': ('seasonal_sources', []),
    },
    'marca': {
        'presenca_online': ('brand_online_presence', ''),
        'reputacao': ('brand_reputation', ''),
        'tom_comunicacao_atual': ('brand_communication_style', ''),
        'fontes': ('brand_sources', []),
    },
}
