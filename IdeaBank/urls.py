from django.urls import path

from . import views

app_name = 'ideabank'

urlpatterns = [
    # Campaign ideas
    path('ideas/', views.CampaignIdeaListView.as_view(), name='idea-list'),
    path('ideas/<int:pk>/', views.CampaignIdeaDetailView.as_view(), name='idea-detail'),

    # Idea generation
    path('generate/', views.generate_ideas, name='generate-ideas'),

    # Statistics and options
    path('stats/', views.get_idea_stats, name='idea-stats'),
    path('options/', views.get_available_options, name='available-options'),
]
