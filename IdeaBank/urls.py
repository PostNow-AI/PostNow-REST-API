from django.urls import path

from . import views

app_name = 'ideabank'

urlpatterns = [
    # Campaigns
    path('campaigns/', views.CampaignListView.as_view(), name='campaign-list'),
    path('campaigns/<int:pk>/', views.CampaignDetailView.as_view(),
         name='campaign-detail'),
    path('campaigns-with-ideas/', views.campaigns_with_ideas,
         name='campaigns-with-ideas'),

    # Ideas
    path('ideas/', views.CampaignIdeaListView.as_view(), name='idea-list'),
    path('ideas/<int:pk>/', views.CampaignIdeaDetailView.as_view(), name='idea-detail'),
    path('ideas/<int:idea_id>/improve/',
         views.improve_idea, name='improve-idea'),

    # Add idea to campaign
    path('campaigns/<int:campaign_id>/ideas/',
         views.add_idea_to_campaign, name='add-idea-to-campaign'),

    # Generate single idea with AI
    path('campaigns/<int:campaign_id>/generate-idea/',
         views.generate_single_idea, name='generate-single-idea'),

    # Generation
    path('campaigns/generate/', views.generate_campaign_ideas,
         name='generate-campaign-ideas'),

    # Stats
    path('campaigns/stats/', views.get_campaign_stats, name='campaign-stats'),

    # Options
    path('options/', views.get_available_options, name='available-options'),

    # Public options (no authentication required)
    path('public/options/', views.get_public_options, name='public-options'),
    path('public/generate/', views.generate_public_ideas, name='public-generate'),
]
