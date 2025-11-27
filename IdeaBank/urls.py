"""
URL patterns for new Post-based IdeaBank system.
"""

from django.urls import path

from . import views

app_name = 'ideabank'

urlpatterns = [
    # Post management endpoints
    path('posts/', views.PostListView.as_view(), name='post-list'),
    path('posts/<int:pk>/', views.PostDetailView.as_view(), name='post-detail'),
    path('posts/<int:pk>/with-ideas/',
         views.PostWithIdeasView.as_view(), name='post-with-ideas'),

    # Post Ideas management
    path('posts/<int:post_id>/ideas/',
         views.PostIdeaListView.as_view(), name='post-idea-list'),
    path('ideas/<int:pk>/', views.PostIdeaDetailView.as_view(),
         name='post-idea-detail'),

    # AI-powered generation endpoints
    path('generate/post-idea/', views.generate_post_idea,
         name='generate-post-idea'),
    path('ideas/<int:idea_id>/generate-image/',
         views.generate_image_for_idea, name='generate-image-for-idea'),
    path('ideas/<int:idea_id>/edit/',
         views.edit_post_idea, name='edit-post-idea'),
    path('ideas/<int:idea_id>/regenerate-image/',
         views.regenerate_image_for_idea, name='regenerate-image-for-idea'),

    # Helper endpoints
    path('options/', views.get_post_options, name='post-options'),
    path('posts/all-with-ideas/', views.get_user_posts_with_ideas,
         name='all-posts-with-ideas'),
    path('stats/', views.get_post_stats, name='post-stats'),

    # Cron endpoints
    path('cron/daily-content-generation/', views.vercel_cron_daily_content_generation,
         name='vercel_cron_daily_generation'),
    path('cron/retry-failed-users/', views.vercel_cron_retry_failed_users,
         name='vercel_cron_retry_failed_users'),
    path('admin/manual-daily-generation/', views.manual_trigger_daily_generation,
         name='manual_daily_generation'),
    path('admin/manual-retry-failed/', views.manual_trigger_retry_failed,
         name='manual_retry_failed'),
    path('cron/mail-automatic-posts/',
         views.mail_all_generated_content, name='mail_automatic_posts'),
    path('cron/mail-daily-errors/',
         views.mail_all_user_errors, name='mail_daily_errors'),
]
