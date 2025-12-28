"""
URL patterns para o app Campaigns.
"""

from django.urls import path
from . import views

app_name = 'campaigns'

urlpatterns = [
    # CRUD de Campanhas
    path('', views.CampaignListView.as_view(), name='campaign-list'),
    path('<int:pk>/', views.CampaignDetailView.as_view(), name='campaign-detail'),
    
    # Drafts (Auto-save)
    path('drafts/', views.CampaignDraftListView.as_view(), name='draft-list'),
    path('drafts/save/', views.save_campaign_draft, name='save-draft'),
    path('drafts/<int:pk>/', views.CampaignDraftDetailView.as_view(), name='draft-detail'),
    
    # Operações de Campanha
    path('<int:pk>/generate/', views.generate_campaign_content, name='generate-content'),
    path('<int:pk>/approve/', views.approve_campaign, name='approve-campaign'),
    path('<int:pk>/reorganize/', views.reorganize_campaign_posts, name='reorganize-posts'),
    
    # Operações de Posts Individuais
    path('<int:campaign_id>/posts/<int:post_id>/approve/', 
         views.approve_campaign_post, name='approve-post'),
    path('<int:campaign_id>/posts/<int:post_id>/regenerate/',
         views.regenerate_campaign_post, name='regenerate-post'),
    
    # Weekly Context Integration
    path('<int:pk>/opportunities/', 
         views.get_weekly_context_opportunities, name='get-opportunities'),
    path('<int:pk>/opportunities/<int:opportunity_id>/add/',
         views.add_opportunity_to_campaign, name='add-opportunity'),
    
    # Análise e Métricas
    path('<int:pk>/harmony/', views.calculate_visual_harmony, name='calculate-harmony'),
    path('templates/', views.CampaignTemplateListView.as_view(), name='template-list'),
    path('templates/<int:pk>/', views.CampaignTemplateDetailView.as_view(), name='template-detail'),
    
    # Helper endpoints
    path('structures/', views.get_available_structures, name='available-structures'),
    path('visual-styles/', views.get_visual_styles, name='visual-styles'),
    path('suggest-briefing/', views.get_briefing_suggestion, name='suggest-briefing'),
]

