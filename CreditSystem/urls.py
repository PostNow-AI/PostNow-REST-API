from django.urls import path

from . import views

app_name = 'credit_system'

urlpatterns = [
    # Pacotes de créditos
    path('packages/', views.CreditPackageListView.as_view(), name='package-list'),

    # Créditos do usuário
    path('balance/', views.UserCreditsView.as_view(), name='user-credits'),
    path('summary/', views.CreditUsageSummaryView.as_view(), name='usage-summary'),
    path('monthly/', views.MonthlyCreditsView.as_view(), name='monthly-credits'),

    # Transações
    path('transactions/', views.CreditTransactionListView.as_view(),
         name='transaction-list'),

    # Modelos de IA
    path('ai-models/', views.AIModelListView.as_view(), name='ai-model-list'),

    # Preferências de IA
    path('ai-preferences/', views.AIModelPreferencesView.as_view(),
         name='ai-preferences'),
    path('ai-recommendations/', views.ModelRecommendationsView.as_view(),
         name='ai-recommendations'),
    path('ai-select-optimal/', views.select_optimal_model_view,
         name='ai-select-optimal'),

    # Stripe
    path('stripe/checkout/', views.StripeCheckoutView.as_view(),
         name='stripe-checkout'),
    path('stripe/webhook/', views.StripeWebhookView.as_view(), name='stripe-webhook'),

    # Uso de créditos
    path('usage/calculate/', views.CreditUsageView.as_view(), name='calculate-usage'),
    path('usage/deduct/', views.deduct_credits_view, name='deduct-credits'),

    # Subscription Plans
    path('plans/', views.SubscriptionPlanListView.as_view(),
         name='subscription-plan-list'),
    path('checkout/', views.CreateStripeCheckoutSessionView.as_view(),
         name='stripe-checkout-session'),
    path('webhook/subscription/', views.StripeSubscriptionWebhookView.as_view(),
         name='stripe-subscription-webhook'),

    # User subscription management
    path('subscription/current/', views.UserSubscriptionView.as_view(),
         name='user-subscription'),
    path('subscription/cancel/', views.UserSubscriptionCancelView.as_view(),
         name='subscription-cancel'),
    path('payment-status/', views.PaymentStatusView.as_view(),
         name='payment-status'),
]
