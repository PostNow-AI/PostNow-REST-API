from django.urls import path

from . import views

app_name = 'global_options'

urlpatterns = [
    # Endpoints para buscar opções
    path('professions/', views.get_all_professions, name='get_all_professions'),
    path('professions/<int:profession_id>/specializations/',
         views.get_profession_specializations, name='get_profession_specializations'),
    path('fonts/', views.get_all_fonts, name='get_all_fonts'),

    # Endpoints para criar opções customizadas
    path('professions/create/', views.create_custom_profession,
         name='create_custom_profession'),
    path('specializations/create/', views.create_custom_specialization,
         name='create_custom_specialization'),
    path('specializations/create-for-profession/', views.create_custom_specialization_for_profession,
         name='create_custom_specialization_for_profession'),
    path('fonts/create/', views.create_custom_font, name='create_custom_font'),
]
