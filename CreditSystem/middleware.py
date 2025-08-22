import json

from django.http import JsonResponse

from .services.credit_service import CreditService


class CreditCheckMiddleware:
    """
    Middleware para verificar se o usuário possui créditos suficientes
    antes de permitir o uso de modelos de IA
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        """Processa a requisição"""
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        """
        Processa a view antes da execução para verificar créditos
        """
        # Lista de endpoints que requerem verificação de créditos
        credit_required_endpoints = [
            '/api/v1/ideabank/generate-idea/',
            '/api/v1/ideabank/improve-idea/',
            '/api/v1/ideabank/generate-campaign/',
            # Adicione outros endpoints que usam IA aqui
        ]

        # Verifica se a requisição é para um endpoint que requer créditos
        if request.path in credit_required_endpoints and request.user.is_authenticated:
            return self._check_credits_for_ai_usage(request, view_func)

        return None

    def _check_credits_for_ai_usage(self, request, view_func):
        """
        Verifica se o usuário possui créditos suficientes para usar IA
        """
        try:
            # Obtém o saldo atual do usuário
            current_balance = CreditService.get_user_balance(request.user)

            # Se o usuário não tem créditos, bloqueia a requisição
            if current_balance <= 0:
                return JsonResponse({
                    'success': False,
                    'message': 'Créditos insuficientes para usar modelos de IA',
                    'error_code': 'INSUFFICIENT_CREDITS',
                    'data': {
                        'current_balance': current_balance,
                        'required_action': 'purchase_credits'
                    }
                }, status=402)

            # Se tem créditos, permite a requisição continuar
            return None

        except Exception:
            # Em caso de erro, permite a requisição continuar
            # (não queremos bloquear usuários por problemas técnicos)
            return None

    def _estimate_ai_usage_cost(self, request):
        """
        Estima o custo de uso de IA baseado na requisição
        """
        try:
            # Tenta obter dados da requisição para estimar custo
            if request.method == 'POST':
                body = request.body.decode('utf-8')
                if body:
                    data = json.loads(body)

                    # Estima tokens baseado no tamanho do input
                    input_text = data.get('prompt', '') + \
                        data.get('context', '')
                    # Estimativa aproximada
                    estimated_tokens = len(input_text.split()) * 1.3

                    # Para endpoints específicos, usa estimativas mais precisas
                    if 'generate-idea' in request.path:
                        estimated_tokens = 150  # Estimativa para geração de ideias
                    elif 'improve-idea' in request.path:
                        estimated_tokens = 200  # Estimativa para melhoria de ideias
                    elif 'generate-campaign' in request.path:
                        estimated_tokens = 300  # Estimativa para campanhas

                    return estimated_tokens

            # Estimativa padrão se não conseguir calcular
            return 100

        except (json.JSONDecodeError, KeyError, AttributeError):
            # Em caso de erro, retorna estimativa padrão
            return 100
