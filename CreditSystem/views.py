from django.core.exceptions import ValidationError
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import AIModel, CreditPackage, CreditTransaction
from .serializers import (
    AIModelPreferencesSerializer,
    AIModelSerializer,
    CreditPackageSerializer,
    CreditTransactionSerializer,
    CreditUsageSerializer,
    ModelRecommendationSerializer,
    StripeCheckoutSerializer,
    UserCreditsSerializer,
)
from .services.credit_service import CreditService
from .services.stripe_service import StripeService


class CreditPackageListView(generics.ListAPIView):
    """
    Lista todos os pacotes de créditos disponíveis
    """
    queryset = CreditPackage.objects.filter(is_active=True)
    serializer_class = CreditPackageSerializer
    permission_classes = [IsAuthenticated]


class UserCreditsView(generics.RetrieveAPIView):
    """
    Obtém o saldo de créditos do usuário autenticado
    """
    serializer_class = UserCreditsSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        """Retorna os créditos do usuário autenticado"""
        return CreditService.get_or_create_user_credits(self.request.user)


class CreditTransactionListView(generics.ListAPIView):
    """
    Lista as transações de créditos do usuário autenticado
    """
    serializer_class = CreditTransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Retorna as transações do usuário autenticado"""
        return CreditTransaction.objects.filter(user=self.request.user)


class AIModelListView(generics.ListAPIView):
    """
    Lista todos os modelos de IA disponíveis
    """
    queryset = AIModel.objects.filter(is_active=True)
    serializer_class = AIModelSerializer
    permission_classes = [IsAuthenticated]


class StripeCheckoutView(APIView):
    """
    Cria uma sessão de checkout do Stripe para compra de créditos
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Cria sessão de checkout"""
        serializer = StripeCheckoutSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'success': False, 'errors': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            stripe_service = StripeService()
            checkout_data = stripe_service.create_checkout_session(
                package_id=serializer.validated_data['package_id'],
                success_url=serializer.validated_data['success_url'],
                cancel_url=serializer.validated_data['cancel_url'],
                user_email=request.user.email
            )

            return Response({
                'success': True,
                'data': checkout_data
            }, status=status.HTTP_200_OK)

        except ValidationError as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'success': False,
                'message': 'Erro interno do servidor',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CreditUsageView(APIView):
    """
    Verifica e calcula o custo de uso de créditos para um modelo de IA
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Calcula custo estimado de uso"""
        serializer = CreditUsageSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'success': False, 'errors': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            ai_model = serializer.validated_data['ai_model']
            estimated_tokens = serializer.validated_data['estimated_tokens']

            # Calcula o custo estimado
            estimated_cost = CreditService.calculate_usage_cost(
                ai_model, estimated_tokens)

            # Verifica se o usuário tem créditos suficientes
            has_sufficient = CreditService.has_sufficient_credits(
                request.user, estimated_cost
            )

            return Response({
                'success': True,
                'data': {
                    'ai_model': ai_model,
                    'estimated_tokens': estimated_tokens,
                    'estimated_cost': estimated_cost,
                    'has_sufficient_credits': has_sufficient,
                    'current_balance': CreditService.get_user_balance(request.user)
                }
            }, status=status.HTTP_200_OK)

        except ValidationError as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response({
                'success': False,
                'message': 'Erro interno do servidor'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CreditUsageSummaryView(APIView):
    """
    Obtém um resumo do uso de créditos do usuário
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Retorna resumo do uso de créditos"""
        try:
            summary = CreditService.get_credit_usage_summary(request.user)

            return Response({
                'success': True,
                'data': summary
            }, status=status.HTTP_200_OK)

        except Exception:
            return Response({
                'success': False,
                'message': 'Erro interno do servidor'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(APIView):
    """
    Endpoint para receber webhooks do Stripe
    """
    permission_classes = []  # Sem autenticação para webhooks

    def post(self, request):
        """Processa webhook do Stripe"""
        # Simple logging to file for debugging
        from datetime import datetime

        # Create a simple log file to track webhook attempts
        log_file = '/tmp/stripe_webhook_debug.log'
        try:
            with open(log_file, 'a') as f:
                timestamp = datetime.now().isoformat()
                print(f"=== WEBHOOK RECEIVED {timestamp} ===")
                print(f"Headers: {dict(request.META)}")
                print(f"Body length: {len(request.body)}")
                print(
                    f"Stripe signature present: {'HTTP_STRIPE_SIGNATURE' in request.META}")
                f.write(f"\n=== WEBHOOK RECEIVED {timestamp} ===\n")
                f.write(f"Headers: {dict(request.META)}\n")
                f.write(f"Body length: {len(request.body)}\n")
                f.write(
                    f"Stripe signature present: {'HTTP_STRIPE_SIGNATURE' in request.META}\n")
        except Exception as e:
            print(f"Logging error: {e}")

        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

        print(f"payload: {payload}")
        if not sig_header:
            return Response(
                {'success': False, 'message': 'Assinatura Stripe não fornecida'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            stripe_service = StripeService()
            result = stripe_service.process_webhook(payload, sig_header)
            print("Processing result:")
            print(result)

            if result.get('status') == 'success':
                return Response({
                    'success': True,
                    'message': 'Webhook processado com sucesso'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'message': result.get('error', 'Erro ao processar webhook')
                }, status=status.HTTP_400_BAD_REQUEST)

        except ValidationError as e:
            print(e)
            return Response({
                'success': False,
                'message': f'Webhook error: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response({
                'success': False,
                'message': 'Erro interno do servidor'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def deduct_credits_view(request):
    """
    Deduz créditos do usuário após uso de um modelo de IA
    """
    serializer = CreditUsageSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {'success': False, 'errors': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        ai_model = serializer.validated_data['ai_model']
        estimated_tokens = serializer.validated_data['estimated_tokens']
        description = serializer.validated_data['description']

        # Calcula o custo real
        actual_cost = CreditService.calculate_usage_cost(
            ai_model, estimated_tokens)

        # Deduz os créditos
        success = CreditService.deduct_credits(
            user=request.user,
            amount=actual_cost,
            ai_model=ai_model,
            description=description
        )

        if success:
            return Response({
                'success': True,
                'message': 'Créditos deduzidos com sucesso',
                'data': {
                    'credits_deducted': actual_cost,
                    'new_balance': CreditService.get_user_balance(request.user)
                }
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'message': 'Créditos insuficientes',
                'data': {
                    'required_credits': actual_cost,
                    'current_balance': CreditService.get_user_balance(request.user)
                }
            }, status=status.HTTP_402_PAYMENT_REQUIRED)

    except ValidationError as e:
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception:
        return Response({
            'success': False,
            'message': 'Erro interno do servidor'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AIModelPreferencesView(APIView):
    """
    Gerenciar preferências de modelos de IA do usuário
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Obter preferências do usuário"""
        try:
            # Import aqui para evitar circular import
            from IdeaBank.services.ai_model_service import AIModelService

            preferences = AIModelService.get_user_preferences(request.user)
            if not preferences:
                return Response({
                    'success': False,
                    'message': 'Preferências não encontradas'
                }, status=status.HTTP_404_NOT_FOUND)

            serializer = AIModelPreferencesSerializer(preferences)
            return Response({
                'success': True,
                'data': serializer.data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'success': False,
                'message': 'Erro interno do servidor',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request):
        """Atualizar preferências do usuário"""
        try:
            from IdeaBank.services.ai_model_service import AIModelService

            # Validar dados de entrada
            serializer = AIModelPreferencesSerializer(
                data=request.data, partial=True)
            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

            # Atualizar preferências
            success = AIModelService.update_user_preferences(
                request.user,
                serializer.validated_data
            )

            if success:
                # Retornar preferências atualizadas
                updated_prefs = AIModelService.get_user_preferences(
                    request.user)
                response_serializer = AIModelPreferencesSerializer(
                    updated_prefs)

                return Response({
                    'success': True,
                    'message': 'Preferências atualizadas com sucesso',
                    'data': response_serializer.data
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'message': 'Erro ao atualizar preferências'
                }, status=status.HTTP_400_BAD_REQUEST)

        except ValidationError as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'success': False,
                'message': 'Erro interno do servidor',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ModelRecommendationsView(APIView):
    """
    Obter recomendações de modelos de IA para o usuário
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Obter recomendações de modelos"""
        try:
            from IdeaBank.services.ai_model_service import AIModelService

            serializer = ModelRecommendationSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

            operation_type = serializer.validated_data['operation_type']
            estimated_tokens = serializer.validated_data['estimated_tokens']

            # Obter recomendações
            recommendations = AIModelService.get_model_recommendations(
                request.user,
                operation_type
            )

            # Selecionar modelo ótimo
            optimal_model = AIModelService.select_optimal_model(
                request.user,
                estimated_tokens,
                operation_type
            )

            return Response({
                'success': True,
                'data': {
                    'recommendations': recommendations,
                    'optimal_model': optimal_model,
                    'operation_type': operation_type,
                    'estimated_tokens': estimated_tokens
                }
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'success': False,
                'message': 'Erro interno do servidor',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def select_optimal_model_view(request):
    """
    Selecionar modelo ótimo para uma operação específica
    """
    try:
        from IdeaBank.services.ai_model_service import AIModelService

        # Validar parâmetros
        estimated_tokens = request.data.get('estimated_tokens', 1000)
        operation_type = request.data.get('operation_type', 'text_generation')
        preferred_provider = request.data.get('preferred_provider')

        if not isinstance(estimated_tokens, int) or estimated_tokens < 1:
            return Response({
                'success': False,
                'message': 'estimated_tokens deve ser um inteiro positivo'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Selecionar modelo ótimo
        optimal_model = AIModelService.select_optimal_model(
            user=request.user,
            estimated_tokens=estimated_tokens,
            operation_type=operation_type,
            preferred_provider=preferred_provider
        )

        if optimal_model:
            # Calcular custo estimado
            estimated_cost = AIModelService.calculate_cost(
                optimal_model, estimated_tokens)

            # Obter informações do modelo
            model_config = AIModelService.get_model_config(optimal_model)

            return Response({
                'success': True,
                'data': {
                    'selected_model': optimal_model,
                    'model_config': model_config,
                    'estimated_cost': estimated_cost,
                    'estimated_tokens': estimated_tokens,
                    'operation_type': operation_type
                }
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'message': 'Nenhum modelo disponível para os critérios especificados',
                'data': {
                    'user_balance': AIModelService.get_user_credit_balance(request.user),
                    'estimated_tokens': estimated_tokens
                }
            }, status=status.HTTP_402_PAYMENT_REQUIRED)

    except Exception as e:
        return Response({
            'success': False,
            'message': 'Erro interno do servidor',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
