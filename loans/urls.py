from django.urls import path
from . import views

urlpatterns = [
    path('reservar/<int:equipo_id>/', views.crear_reserva, name='crear_reserva'),
]