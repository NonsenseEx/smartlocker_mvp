from django.urls import path
from . import views

urlpatterns = [
    # Rutas existentes (usuario)
    path('reservar/<int:equipo_id>/', views.crear_reserva, name='crear_reserva'),
    path('mis-prestamos/', views.mis_prestamos, name='mis_prestamos'),
    path('devolver-mi-equipo/<int:prestamo_id>/', views.devolver_mi_equipo, name='devolver_mi_equipo'),

    # Rutas para el Encargado
    path('encargado/', views.panel_encargado, name='panel_encargado'),
    path('encargado/entregar/<int:reserva_id>/', views.confirmar_entrega, name='confirmar_entrega'),
    path('encargado/prestados/', views.dispositivos_prestados, name='dispositivos_prestados'),
    path('encargado/cancelar/<int:reserva_id>/', views.cancelar_reserva_encargado, name='cancelar_reserva_encargado'),
    path('encargado/reportar/<int:prestamo_id>/', views.reportar_incidente, name='reportar_incidente'),
    
]