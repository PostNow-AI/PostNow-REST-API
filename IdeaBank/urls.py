from django.urls import path

from . import views

app_name = 'ideabank'

urlpatterns = [
    # Campaigns
    path('campaigns/', views.CampaignListView.as_view(), name='campaign-list'),
    path('campaigns/<int:pk>/', views.CampaignDetailView.as_view(),
         name='campaign-detail'),

    # Campaign ideas
    path('campaigns/<int:campaign_id>/ideas/',
         views.CampaignIdeaListView.as_view(), name='campaign-ideas'),
    path('ideas/', views.CampaignIdeaListView.as_view(), name='idea-list'),
    path('ideas/<int:pk>/', views.CampaignIdeaDetailView.as_view(), name='idea-detail'),
    path('ideas/<int:idea_id>/improve/',
         views.improve_idea, name='improve-idea'),

    # Campaign idea generation
    path('campaigns/generate/', views.generate_campaign_ideas,
         name='generate-campaign-ideas'),

    # Public idea generation (no authentication required)
    path('public/generate/', views.generate_public_ideas,
         name='generate-public-ideas'),
    path('public/options/', views.get_public_options, name='public-options'),

    # Statistics and options
    path('campaigns/stats/', views.get_campaign_stats, name='campaign-stats'),
    path('options/', views.get_available_options, name='available-options'),
]
