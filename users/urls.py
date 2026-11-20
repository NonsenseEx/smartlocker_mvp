from django.urls import path
from . import views

urlpatterns = [
    path('registro/', views.registro, name='registro'),
    path('perfil/', views.editar_perfil, name='editar_perfil'),
]