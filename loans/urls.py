from django.urls import path
from . import views

urlpatterns = [
    path('reservar/<int:equipo_id>/', views.crear_reserva, name='crear_reserva'),
    # Rutas nuevas:
    path('mis-prestamos/', views.mis_prestamos, name='mis_prestamos'),
    path('devolver-mi-equipo/<int:prestamo_id>/', views.devolver_mi_equipo, name='devolver_mi_equipo'),
]