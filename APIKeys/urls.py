from django.urls import path

from . import views

urlpatterns = [
    path('set/', views.set_api_key, name='set_api_key'),
    path('<str:provider>/status/', views.get_api_key_status,
         name='get_api_key_status'),
    path('<str:provider>/delete/', views.delete_api_key, name='delete_api_key'),
]
