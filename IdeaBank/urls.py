from django.urls import path

from . import views

app_name = 'ideabank'

urlpatterns = [
    # Campaign ideas
    path('ideas/', views.CampaignIdeaListView.as_view(), name='idea-list'),
    path('ideas/<int:pk>/', views.CampaignIdeaDetailView.as_view(), name='idea-detail'),
    path('ideas/<int:idea_id>/improve/',
         views.improve_idea, name='improve-idea'),

    # Idea generation
    path('generate/', views.generate_ideas, name='generate-ideas'),

    # Public idea generation (no authentication required)
    path('public/generate/', views.generate_public_ideas,
         name='generate-public-ideas'),
    path('public/options/', views.get_public_options, name='public-options'),

    # Statistics and options
    path('stats/', views.get_idea_stats, name='idea-stats'),
    path('options/', views.get_available_options, name='available-options'),
]
