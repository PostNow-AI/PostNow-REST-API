from django.urls import path

from . import views

app_name = 'ideabank'

urlpatterns = [
    # Campaign management
    path('campaigns/', views.CampaignListView.as_view(), name='campaign-list'),
    path('campaigns/<int:pk>/', views.CampaignDetailView.as_view(),
         name='campaign-detail'),
    path('campaigns/<int:campaign_id>/ideas/',
         views.CampaignIdeaListView.as_view(), name='campaign-ideas'),

    # AI-powered idea generation
    path('generate-ideas/', views.generate_campaign_ideas, name='generate-ideas'),
    path('public/generate-ideas/', views.generate_public_ideas,
         name='generate-public-ideas'),
    path('generate-single-idea/', views.generate_single_idea,
         name='generate-single-idea'),

    # AI model information and cost estimation
    path('ai-models/', views.get_available_models, name='available-models'),
    path('estimate-cost/', views.estimate_campaign_cost, name='estimate-cost'),

    # Campaign data and options
    path('campaigns-with-ideas/', views.campaigns_with_ideas,
         name='campaigns-with-ideas'),
    path('stats/', views.get_campaign_stats, name='campaign-stats'),
    path('options/', views.get_available_options, name='available-options'),

    # Individual idea management
    path('ideas/<int:idea_id>/improve/',
         views.improve_idea, name='improve-idea'),
    path('ideas/<int:pk>/', views.CampaignIdeaDetailView.as_view(), name='idea-detail'),
]
