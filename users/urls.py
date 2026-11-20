from django.urls import path
from . import views

urlpatterns = [
    path('registro/', views.registro, name='registro'),
    path('perfil/', views.editar_perfil, name='editar_perfil'),
    path('admin-usuarios/', views.gestion_usuarios, name='gestion_usuarios'),
    path('admin-usuarios/editar/<int:user_id>/', views.editar_usuario_admin, name='editar_usuario_admin'),
]