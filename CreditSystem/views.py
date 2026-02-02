# Manual cancel view for users
import os

import stripe
from AuditSystem.services import AuditService
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from dotenv import load_dotenv
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    AIModel,
    CreditPackage,
    CreditTransaction,
    SubscriptionPlan,
    UserSubscription,
)
from .serializers import (
    AIModelPreferencesSerializer,
    AIModelSerializer,
    CreditPackageSerializer,
    CreditTransactionSerializer,
    CreditUsageSerializer,
    ModelRecommendationSerializer,
    StripeCheckoutSerializer,
    SubscriptionPlanSerializer,
    UserCreditsSerializer,
    UserSubscriptionSerializer,
)
from .services.credit_service import CreditService
from .services.stripe_service import StripeService
from .services.subscription_service import SubscriptionService

stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', None)


class UserSubscriptionCancelView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        sub = UserSubscription.objects.filter(
            user=user, status='active').order_by('-start_date').first()
        if not sub:
            # Log failed cancellation attempt - no active subscription
            AuditService.log_subscription_operation(
                user=user,
                action='subscription_cancelled',
                status='failure',
                error_message='No active subscription found',
                details={
                    'attempted_action': 'cancellation',
                    'reason': 'no_active_subscription'
                }
            )
            return Response({'success': False, 'message': 'Nenhuma assinatura ativa encontrada.'}, status=status.HTTP_404_NOT_FOUND)

        # Handle different subscription types
        try:
            # Case 1: Lifetime subscription (no Stripe subscription to cancel)
            if sub.plan.interval == 'lifetime':
                sub.status = 'cancelled'
                if not sub.end_date:
                    from django.utils import timezone
                    sub.end_date = timezone.now()
                sub.save()

                # Log lifetime subscription cancellation
                AuditService.log_subscription_operation(
                    user=user,
                    action='subscription_cancelled',
                    status='success',
                    details={
                        'plan_name': sub.plan.name,
                        'plan_interval': sub.plan.interval,
                        'cancellation_type': 'lifetime_manual'
                    }
                )

                return Response({
                    'success': True,
                    'message': 'Assinatura vitalícia cancelada com sucesso.'
                }, status=status.HTTP_200_OK)

            # Case 2: Recurring subscription - use webhook-first approach
            if sub.stripe_subscription_id:
                # Check if subscription exists in Stripe before trying to cancel
                try:
                    # First, try to retrieve the subscription to see if it exists
                    stripe_sub = stripe.Subscription.retrieve(
                        sub.stripe_subscription_id)

                    # If it exists and is active, cancel it in Stripe
                    # The webhook will handle local database updates
                    if stripe_sub.status in ['active', 'trialing']:
                        stripe.Subscription.delete(sub.stripe_subscription_id)

                        # Log Stripe subscription cancellation request
                        AuditService.log_subscription_operation(
                            user=user,
                            action='subscription_cancelled',
                            status='success',
                            details={
                                'plan_name': sub.plan.name,
                                'plan_interval': sub.plan.interval,
                                'stripe_subscription_id': sub.stripe_subscription_id,
                                'cancellation_type': 'stripe_webhook_pending'
                            }
                        )

                        return Response({
                            'success': True,
                            'message': 'Cancelamento enviado para o Stripe. A assinatura será cancelada em breve.',
                            'webhook_pending': True
                        }, status=status.HTTP_200_OK)
                    else:
                        # Stripe subscription is already cancelled, just update locally
                        sub.status = 'cancelled'
                        if not sub.end_date:
                            from django.utils import timezone
                            sub.end_date = timezone.now()
                        sub.save()

                        # Log local subscription cancellation
                        AuditService.log_subscription_operation(
                            user=user,
                            action='subscription_cancelled',
                            status='success',
                            details={
                                'plan_name': sub.plan.name,
                                'plan_interval': sub.plan.interval,
                                'stripe_subscription_id': sub.stripe_subscription_id,
                                'cancellation_type': 'local_update_already_cancelled'
                            }
                        )

                        return Response({
                            'success': True,
                            'message': 'Assinatura já estava cancelada no Stripe. Status local atualizado.'
                        }, status=status.HTTP_200_OK)

                except stripe.error.InvalidRequestError as e:
                    # Subscription doesn't exist in Stripe (maybe it's a test subscription)
                    if 'No such subscription' in str(e):
                        # Cancel locally for test subscriptions
                        sub.status = 'cancelled'
                        if not sub.end_date:
                            from django.utils import timezone
                            sub.end_date = timezone.now()
                        sub.save()

                        # Log test subscription cancellation
                        AuditService.log_subscription_operation(
                            user=user,
                            action='subscription_cancelled',
                            status='success',
                            details={
                                'plan_name': sub.plan.name,
                                'plan_interval': sub.plan.interval,
                                'stripe_subscription_id': sub.stripe_subscription_id,
                                'cancellation_type': 'test_subscription_local'
                            }
                        )

                        return Response({
                            'success': True,
                            'message': 'Assinatura de teste cancelada localmente.'
                        }, status=status.HTTP_200_OK)
                    else:
                        # Re-raise if it's a different error
                        raise e
            else:
                # No Stripe ID - cancel locally
                sub.status = 'cancelled'
                if not sub.end_date:
                    from django.utils import timezone
                    sub.end_date = timezone.now()
                sub.save()

                # Log local subscription cancellation
                AuditService.log_subscription_operation(
                    user=user,
                    action='subscription_cancelled',
                    status='success',
                    details={
                        'plan_name': sub.plan.name,
                        'plan_interval': sub.plan.interval,
                        'cancellation_type': 'local_no_stripe_id'
                    }
                )

                return Response({
                    'success': True,
                    'message': 'Assinatura cancelada localmente.'
                }, status=status.HTTP_200_OK)

        except stripe.error.StripeError as e:
            # Log Stripe error during cancellation
            AuditService.log_subscription_operation(
                user=user,
                action='subscription_cancelled',
                status='failure',
                error_message=str(e),
                details={
                    'stripe_error': True,
                    'error_type': type(e).__name__,
                    'plan_name': sub.plan.name if sub else None,
                    'stripe_subscription_id': sub.stripe_subscription_id if sub else None
                }
            )
            # If there's a Stripe error, provide helpful feedback but don't cancel locally
            return Response({
                'success': False,
                'message': f'Erro ao cancelar no Stripe: {str(e)}. Tente novamente ou entre em contato com o suporte.',
                'stripe_error': True
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # Log general error during cancellation
            AuditService.log_subscription_operation(
                user=user,
                action='subscription_cancelled',
                status='failure',
                error_message=str(e),
                details={
                    'error_type': type(e).__name__,
                    'plan_name': sub.plan.name if sub else None,
                    'unexpected_error': True
                }
            )
            return Response({
                'success': False,
                'message': f'Erro interno: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# --- Subscription Views ---

class UserSubscriptionView(generics.RetrieveAPIView):
    """
    Get the current user's active subscription
    """
    serializer_class = UserSubscriptionSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        """Return the user's active subscription or None"""
        try:
            return UserSubscription.objects.filter(
                user=self.request.user,
                status='active'
            ).order_by('-start_date').first()
        except UserSubscription.DoesNotExist:
            return None

    def retrieve(self, request, *args, **kwargs):
        """Override to handle case when user has no subscription"""
        instance = self.get_object()
        if instance is None:
            return Response(
                {'detail': 'No active subscription found'},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


# --- Stripe Webhook for Subscriptions ---
@method_decorator(csrf_exempt, name='dispatch')
class StripeSubscriptionWebhookView(APIView):
    """
    Endpoint para receber webhooks do Stripe e criar UserSubscription
    """
    permission_classes = []  # Sem autenticação para webhooks

    def post(self, request):
        """Processa webhook do Stripe para assinaturas"""
        # Simple logging to file for debugging
        from datetime import datetime

        # Create a simple log file to track webhook attempts
        log_file = '/tmp/stripe_subscription_webhook_debug.log'
        try:
            with open(log_file, 'a') as f:
                timestamp = datetime.now().isoformat()
                f.write(
                    f"\n=== SUBSCRIPTION WEBHOOK RECEIVED {timestamp} ===\n")
                f.write(f"Headers: {dict(request.META)}\n")
                f.write(f"Body length: {len(request.body)}\n")
                f.write(
                    f"Stripe signature present: {'HTTP_STRIPE_SIGNATURE' in request.META}\n")
        except Exception as e:
            print(f"Logging error: {e}")

        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

        if not sig_header:
            # Log missing signature error
            AuditService.log_system_operation(
                user=None,
                action='webhook_received',
                status='failure',
                error_message='Missing Stripe signature',
                resource_type='StripeWebhook',
                details={
                    'webhook_type': 'subscription',
                    'error_type': 'missing_signature',
                    'headers_present': bool(request.META),
                    'body_length': len(request.body)
                }
            )
            return Response(
                {'success': False, 'message': 'Assinatura Stripe não fornecida'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            subscription_service = SubscriptionService()
            result = subscription_service.process_webhook(payload, sig_header)

            if result.get('status') == 'success':
                # Log successful webhook processing
                AuditService.log_system_operation(
                    user=None,
                    action='webhook_processed',
                    status='success',
                    resource_type='StripeWebhook',
                    details={
                        'webhook_type': 'subscription',
                        'subscription_id': result.get('subscription_id'),
                        'user_id': result.get('user_id'),
                        'plan_name': result.get('plan_name'),
                        'message': result.get('message')
                    }
                )
                return Response({
                    'success': True,
                    'message': result.get('message', 'Webhook processado com sucesso'),
                    'data': {
                        'subscription_id': result.get('subscription_id'),
                        'user_id': result.get('user_id'),
                        'plan_name': result.get('plan_name')
                    }
                }, status=status.HTTP_200_OK)
            elif result.get('status') == 'warning':
                # Log webhook processing with warning
                AuditService.log_system_operation(
                    user=None,
                    action='webhook_processed',
                    status='success',
                    resource_type='StripeWebhook',
                    details={
                        'webhook_type': 'subscription',
                        'warning': True,
                        'message': result.get('message'),
                        'subscription_id': result.get('subscription_id'),
                        'user_id': result.get('user_id')
                    }
                )
                return Response({
                    'success': True,
                    'message': result.get('message', 'Webhook processado com alerta'),
                    'warning': True
                }, status=status.HTTP_200_OK)
            elif result.get('status') == 'ignored':
                # Log ignored webhook
                AuditService.log_system_operation(
                    user=None,
                    action='webhook_processed',
                    status='success',
                    resource_type='StripeWebhook',
                    details={
                        'webhook_type': 'subscription',
                        'ignored': True,
                        'message': result.get('message')
                    }
                )
                return Response({
                    'success': True,
                    'message': result.get('message', 'Evento ignorado')
                }, status=status.HTTP_200_OK)
            else:
                # Log webhook processing failure
                AuditService.log_system_operation(
                    user=None,
                    action='webhook_processed',
                    status='failure',
                    error_message=result.get(
                        'message', 'Erro ao processar webhook'),
                    resource_type='StripeWebhook',
                    details={
                        'webhook_type': 'subscription',
                        'processing_error': True
                    }
                )
                return Response({
                    'success': False,
                    'message': result.get('message', 'Erro ao processar webhook')
                }, status=status.HTTP_400_BAD_REQUEST)

        except ValidationError as e:
            # Log validation error in webhook processing
            AuditService.log_system_operation(
                user=None,
                action='webhook_processed',
                status='failure',
                error_message=str(e),
                resource_type='StripeWebhook',
                details={
                    'webhook_type': 'subscription',
                    'error_type': 'validation_error',
                    'body_length': len(request.body)
                }
            )
            return Response({
                'success': False,
                'message': f'Webhook error: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # Log general error in webhook processing
            AuditService.log_system_operation(
                user=None,
                action='webhook_processed',
                status='failure',
                error_message=str(e),
                resource_type='StripeWebhook',
                details={
                    'webhook_type': 'subscription',
                    'error_type': 'unexpected_error',
                    'body_length': len(request.body)
                }
            )
            return Response({
                'success': False,
                'message': 'Erro interno do servidor',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SubscriptionPlanListView(generics.ListAPIView):
    queryset = SubscriptionPlan.objects.filter(is_active=True).exclude(interval='legacy')
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [permissions.AllowAny]


class CreateStripeCheckoutSessionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        plan_id = request.data.get('plan_id')

        # Validate plan_id
        if not plan_id:
            # Log missing plan_id error
            AuditService.log_subscription_operation(
                user=request.user,
                action='subscription_created',
                status='failure',
                error_message='Missing plan_id parameter',
                details={
                    'error_type': 'missing_plan_id',
                    'request_data': request.data
                }
            )
            return Response({
                'success': False,
                'message': 'plan_id é obrigatório'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            plan = SubscriptionPlan.objects.get(id=plan_id, is_active=True)
        except SubscriptionPlan.DoesNotExist:
            # Log plan not found error
            AuditService.log_subscription_operation(
                user=request.user,
                action='subscription_created',
                status='failure',
                error_message='Plan not found or inactive',
                details={
                    'error_type': 'plan_not_found',
                    'requested_plan_id': plan_id
                }
            )
            return Response({
                'success': False,
                'message': 'Plano não encontrado ou inativo'
            }, status=status.HTTP_404_NOT_FOUND)

        user = request.user

        # Check if plan has Stripe price ID
        if not plan.stripe_price_id:
            # Log plan unavailable error
            AuditService.log_subscription_operation(
                user=user,
                action='subscription_created',
                status='failure',
                error_message='Plan unavailable - no Stripe price ID',
                details={
                    'error_type': 'plan_unavailable',
                    'plan_name': plan.name,
                    'plan_interval': plan.interval
                }
            )
            return Response({
                'success': False,
                'message': 'Este plano está temporariamente indisponível. Entre em contato com o suporte.'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        # Check for existing active subscription and support upgrade flow
        existing_sub = UserSubscription.objects.filter(
            user=user, status='active').select_related('plan').first()
        if existing_sub:
            # If same plan requested, just short‑circuit
            if existing_sub.plan_id == plan.id:
                # Log same plan request
                AuditService.log_subscription_operation(
                    user=user,
                    action='subscription_updated',
                    status='success',
                    details={
                        'action': 'same_plan_requested',
                        'plan_name': existing_sub.plan.name
                    }
                )

                return Response({
                    'success': True,
                    'message': 'Você já está neste plano',
                    'already_on_plan': True,
                    'plan': existing_sub.plan.name
                }, status=status.HTTP_200_OK)

            # If lifetime already, prevent upgrading/downgrading
            if existing_sub.plan.interval == 'lifetime':
                # Log lifetime upgrade attempt
                AuditService.log_subscription_operation(
                    user=user,
                    action='subscription_updated',
                    status='failure',
                    details={
                        'action': 'lifetime_upgrade_prevented',
                        'current_plan': existing_sub.plan.name,
                        'requested_plan': plan.name
                    }
                )

                return Response({
                    'success': False,
                    'message': 'Você já possui um plano vitalício ativo. Não é possível mudar de plano.',
                    'lifetime_active': True
                }, status=status.HTTP_400_BAD_REQUEST)

            # If target plan is lifetime but user has a recurring plan, instruct separate lifetime purchase flow
            if plan.interval == 'lifetime':
                return Response({
                    'success': False,
                    'message': 'Para migrar para o plano vitalício cancele a assinatura atual primeiro.',
                    'requires_manual_action': True
                }, status=status.HTTP_400_BAD_REQUEST)

            upgrade_requested = str(request.data.get('upgrade', 'false')).lower() in [
                '1', 'true', 'yes']
            if not upgrade_requested:
                return Response({
                    'success': False,
                    'message': 'Você já possui uma assinatura ativa. Envie "upgrade": true para alterar o plano.',
                    'upgrade_available': True,
                    'current_plan': existing_sub.plan.name,
                    'requested_plan': plan.name
                }, status=status.HTTP_409_CONFLICT)

            # Perform in-place upgrade via Stripe if subscription has a Stripe ID
            if existing_sub.stripe_subscription_id:
                try:
                    stripe_sub = stripe.Subscription.retrieve(
                        existing_sub.stripe_subscription_id)
                    # Locate the subscription item that matches current plan price (fallback to first item)
                    items = stripe_sub.get('items', {}).get('data', [])
                    sub_item_id = None
                    for it in items:
                        if it.get('price', {}).get('id') == existing_sub.plan.stripe_price_id:
                            sub_item_id = it.get('id')
                            break
                    if not sub_item_id and items:
                        sub_item_id = items[0].get('id')

                    if not sub_item_id:
                        return Response({
                            'success': False,
                            'message': 'Não foi possível localizar o item da assinatura para upgrade.'
                        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

                    updated_sub = stripe.Subscription.modify(
                        existing_sub.stripe_subscription_id,
                        cancel_at_period_end=False,
                        proration_behavior='create_prorations',
                        items=[{
                            'id': sub_item_id,
                            'price': plan.stripe_price_id,
                            'quantity': 1
                        }],
                        metadata={
                            'user_id': str(user.id),
                            'upgraded_from_plan': existing_sub.plan.interval,
                            'upgraded_to_plan': plan.interval
                        }
                    )

                    previous_plan = existing_sub.plan
                    # Update local subscription to new plan
                    existing_sub.plan = plan
                    existing_sub.save(update_fields=['plan'])

                    # Optionally trigger credit recalculation/reset immediately
                    try:
                        CreditService.check_and_reset_monthly_credits(user)
                    except Exception:
                        pass

                    # Log successful subscription upgrade
                    AuditService.log_subscription_operation(
                        user=user,
                        action='subscription_updated',
                        status='success',
                        details={
                            'action': 'plan_upgraded',
                            'previous_plan': previous_plan.name,
                            'new_plan': plan.name,
                            'upgrade_type': 'stripe_in_place'
                        }
                    )

                    return Response({
                        'success': True,
                        'message': 'Upgrade de assinatura realizado com sucesso.',
                        'upgraded': True,
                        'previous_plan': previous_plan.name,
                        'new_plan': plan.name,
                        'proration_invoice_id': updated_sub.get('latest_invoice'),
                        'subscription_id': existing_sub.id
                    }, status=status.HTTP_200_OK)
                except stripe.error.StripeError as e:
                    # Log Stripe error during upgrade
                    AuditService.log_subscription_operation(
                        user=user,
                        action='subscription_updated',
                        status='failure',
                        error_message=str(e),
                        details={
                            'error_type': 'stripe_upgrade_error',
                            'action': 'plan_upgraded',
                            'current_plan': existing_sub.plan.name,
                            'target_plan': plan.name,
                            'stripe_subscription_id': existing_sub.stripe_subscription_id,
                            'stripe_error_type': type(e).__name__
                        }
                    )
                    return Response({
                        'success': False,
                        'message': f'Erro no Stripe ao realizar upgrade: {str(e)}'
                    }, status=status.HTTP_400_BAD_REQUEST)
                except Exception as e:
                    # Log general error during upgrade
                    AuditService.log_subscription_operation(
                        user=user,
                        action='subscription_updated',
                        status='failure',
                        error_message=str(e),
                        details={
                            'error_type': 'upgrade_error',
                            'action': 'plan_upgraded',
                            'current_plan': existing_sub.plan.name,
                            'target_plan': plan.name,
                            'error_type_name': type(e).__name__
                        }
                    )
                    return Response({
                        'success': False,
                        'message': f'Erro interno ao realizar upgrade: {str(e)}'
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                # Local-only subscription (edge case) – require manual cancellation then new checkout
                return Response({
                    'success': False,
                    'message': 'Assinatura local ativa. Cancele antes de criar um novo checkout.',
                    'requires_cancellation': True
                }, status=status.HTTP_409_CONFLICT)

        try:
            # Check if this is a test price ID
            if plan.stripe_price_id.startswith('price_test_'):
                # Log test environment error
                AuditService.log_subscription_operation(
                    user=user,
                    action='subscription_created',
                    status='failure',
                    error_message='Test environment - real payments not available',
                    details={
                        'error_type': 'test_environment',
                        'plan_name': plan.name,
                        'stripe_price_id': plan.stripe_price_id
                    }
                )
                return Response({
                    'success': False,
                    'message': 'Este é um ambiente de desenvolvimento. Os pagamentos reais não estão disponíveis.',
                    'is_test_environment': True
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

            # Load environment variables and get frontend URL
            load_dotenv()
            frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')

            # Configure discounts based on plan interval
            discounts = []
            if plan.interval == 'monthly':
                # 50% off first month only
                # Replace with actual Stripe coupon ID
                discounts = [{'coupon': 'monthly_first_50_off'}]
            elif plan.interval == 'semester':
                # 25% off all months forever
                # Replace with actual Stripe coupon ID
                discounts = [{'coupon': 'semester_25_off'}]
            elif plan.interval == 'yearly':
                # 50% off all months forever
                # Replace with actual Stripe coupon ID
                discounts = [{'coupon': 'yearly_50_off'}]
            # Lifetime plans have no discounts (one-time payment)

            # Configure subscription data with trial period for non-lifetime plans
            subscription_data = None
            if plan.interval != 'lifetime':
                subscription_data = {
                    'metadata': {
                        'user_id': str(user.id),
                        'plan_id': str(plan.id),
                    },
                    'trial_period_days': 7  # 7-day free trial
                }

            checkout_session = stripe.checkout.Session.create(
                customer_email=user.email,
                payment_method_types=['card'],
                line_items=[{
                    'price': plan.stripe_price_id,
                    'quantity': 1,
                }],
                allow_promotion_codes=True,  # Allow for coupons
                mode='subscription' if plan.interval != 'lifetime' else 'payment',
                success_url=f'{frontend_url}/subscription/success?session_id={{CHECKOUT_SESSION_ID}}',
                cancel_url=f'{frontend_url}/subscription/cancel',
                metadata={
                    'user_id': str(user.id),
                    'plan_id': str(plan.id),
                },
                subscription_data=subscription_data
            )

            # Log successful checkout session creation
            AuditService.log_subscription_operation(
                user=user,
                action='subscription_created',
                status='success',
                details={
                    'plan_name': plan.name,
                    'plan_interval': plan.interval,
                    'checkout_session_id': checkout_session.id,
                    'mode': 'subscription' if plan.interval != 'lifetime' else 'payment'
                }
            )

            return Response({
                'success': True,
                'checkout_url': checkout_session.url
            }, status=status.HTTP_200_OK)
        except stripe.error.StripeError as e:
            # Log Stripe error during checkout creation
            AuditService.log_subscription_operation(
                user=user,
                action='subscription_created',
                status='failure',
                error_message=str(e),
                details={
                    'error_type': 'stripe_error',
                    'plan_name': plan.name,
                    'plan_interval': plan.interval,
                    'stripe_price_id': plan.stripe_price_id,
                    'stripe_error_type': type(e).__name__
                }
            )
            return Response({
                'success': False,
                'message': f'Erro no Stripe: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # Log general error during checkout creation
            AuditService.log_subscription_operation(
                user=user,
                action='subscription_created',
                status='failure',
                error_message=str(e),
                details={
                    'error_type': 'unexpected_error',
                    'plan_name': plan.name,
                    'plan_interval': plan.interval,
                    'error_type_name': type(e).__name__
                }
            )
            return Response({
                'success': False,
                'message': f'Erro interno: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
            # Log validation error in credit checkout
            AuditService.log_subscription_operation(
                user=request.user,
                action='credit_purchased',
                status='failure',
                error_message='Serializer validation failed',
                details={
                    'error_type': 'validation_error',
                    'validation_errors': serializer.errors
                }
            )
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

            # Log credit purchase checkout creation
            AuditService.log_subscription_operation(
                user=request.user,
                action='credit_purchased',
                status='success',
                details={
                    'package_id': serializer.validated_data['package_id'],
                    'checkout_session_id': checkout_data.get('id'),
                    # Convert from cents
                    'amount': checkout_data.get('amount_total', 0) / 100
                }
            )

            return Response({
                'success': True,
                'data': checkout_data
            }, status=status.HTTP_200_OK)

        except ValidationError as e:
            # Log ValidationError in credit checkout
            AuditService.log_subscription_operation(
                user=request.user,
                action='credit_purchased',
                status='failure',
                error_message=str(e),
                details={
                    'error_type': 'validation_error',
                    'package_id': serializer.validated_data.get('package_id') if serializer.is_valid() else None
                }
            )
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # Log general error in credit checkout
            AuditService.log_subscription_operation(
                user=request.user,
                action='credit_purchased',
                status='failure',
                error_message=str(e),
                details={
                    'error_type': 'unexpected_error',
                    'package_id': serializer.validated_data.get('package_id') if serializer.is_valid() else None,
                    'error_type_name': type(e).__name__
                }
            )
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
    Obtém um resumo do uso de créditos do usuário (includes monthly status)
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

        except Exception as e:
            return Response({
                'success': False,
                'message': 'Erro interno do servidor',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MonthlyCreditsView(APIView):
    """
    Obtém o status dos créditos mensais do usuário
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Retorna status dos créditos mensais"""
        try:
            # Get monthly credit status
            monthly_status = CreditService.get_monthly_credit_status(
                request.user)

            # Get current subscription info
            subscription = UserSubscription.objects.filter(
                user=request.user,
                status='active'
            ).select_related('plan').first()

            # Get subscription validation status
            has_active_subscription = CreditService.validate_user_subscription(
                request.user)

            # Get fixed pricing info
            fixed_prices = {
                'text_generation': float(CreditTransaction.get_fixed_price('text_generation')),
                'image_generation': float(CreditTransaction.get_fixed_price('image_generation'))
            }

            # Calculate what user can do with remaining credits
            remaining_credits = monthly_status['monthly_remaining']
            capabilities = {
                'text_generations_possible': int(remaining_credits / fixed_prices['text_generation']) if fixed_prices['text_generation'] > 0 else 0,
                'image_generations_possible': int(remaining_credits / fixed_prices['image_generation']) if fixed_prices['image_generation'] > 0 else 0
            }

            response_data = {
                'monthly_status': monthly_status,
                'subscription_info': {
                    'has_active_subscription': has_active_subscription,
                    'plan_name': subscription.plan.name if subscription else None,
                    'plan_interval': subscription.plan.interval if subscription else None,
                    'monthly_credits_allocation': float(subscription.plan.monthly_credits) if subscription else 0.0,
                    'allows_extra_purchase': subscription.plan.allow_credit_purchase if subscription else False
                },
                'pricing_info': {
                    'fixed_prices': fixed_prices,
                    'capabilities': capabilities
                },
                'usage_tips': {
                    'efficient_usage': f"Com {remaining_credits:.2f} créditos restantes, você pode fazer:",
                    'text_operations': f"{capabilities['text_generations_possible']} gerações de texto",
                    'image_operations': f"{capabilities['image_generations_possible']} gerações de imagem"
                }
            }

            return Response({
                'success': True,
                'data': response_data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'success': False,
                'message': 'Erro interno do servidor',
                'error': str(e)
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
                f.write(f"\n=== WEBHOOK RECEIVED {timestamp} ===\n")
                f.write(f"Headers: {dict(request.META)}\n")
                f.write(f"Body length: {len(request.body)}\n")
                f.write(
                    f"Stripe signature present: {'HTTP_STRIPE_SIGNATURE' in request.META}\n")
        except Exception as e:
            print(f"Logging error: {e}")

        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

        if not sig_header:
            # Log missing signature error for credit webhook
            AuditService.log_system_operation(
                user=None,
                action='webhook_received',
                status='failure',
                error_message='Missing Stripe signature',
                resource_type='StripeWebhook',
                details={
                    'webhook_type': 'credit',
                    'error_type': 'missing_signature',
                    'headers_present': bool(request.META),
                    'body_length': len(request.body)
                }
            )
            return Response(
                {'success': False, 'message': 'Assinatura Stripe não fornecida'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            stripe_service = StripeService()
            result = stripe_service.process_webhook(payload, sig_header)

            if result.get('status') == 'success':
                # Log successful credit webhook processing
                AuditService.log_system_operation(
                    user=None,
                    action='webhook_processed',
                    status='success',
                    resource_type='StripeWebhook',
                    details={
                        'webhook_type': 'credit',
                        'message': 'Webhook processado com sucesso'
                    }
                )
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
            # Log validation error for credit webhook
            AuditService.log_system_operation(
                user=None,
                action='webhook_processed',
                status='failure',
                error_message=f'Validation error in credit webhook: {str(e)}',
                resource_type='StripeWebhook',
                details={
                    'webhook_type': 'credit',
                    'error_type': 'validation_error',
                    'validation_errors': str(e)
                }
            )
            return Response({
                'success': False,
                'message': f'Webhook error: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            # Log general exception for credit webhook
            AuditService.log_system_operation(
                user=None,
                action='webhook_processed',
                status='failure',
                error_message='Unexpected error processing credit webhook',
                resource_type='StripeWebhook',
                details={
                    'webhook_type': 'credit',
                    'error_type': 'unexpected_error',
                    'has_signature': bool(sig_header),
                    'body_length': len(payload) if payload else 0
                }
            )
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
            # Log successful credit deduction
            AuditService.log_subscription_operation(
                user=request.user,
                action='credit_used',
                status='success',
                details={
                    'ai_model': ai_model,
                    'credits_deducted': actual_cost,
                    'description': description,
                    'estimated_tokens': estimated_tokens
                }
            )

            return Response({
                'success': True,
                'message': 'Créditos deduzidos com sucesso',
                'data': {
                    'credits_deducted': actual_cost,
                    'new_balance': CreditService.get_user_balance(request.user)
                }
            }, status=status.HTTP_200_OK)
        else:
            # Log failed credit deduction (insufficient funds)
            AuditService.log_subscription_operation(
                user=request.user,
                action='credit_used',
                status='failure',
                error_message='Insufficient credits',
                details={
                    'ai_model': ai_model,
                    'required_credits': actual_cost,
                    'current_balance': CreditService.get_user_balance(request.user),
                    'description': description
                }
            )

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
