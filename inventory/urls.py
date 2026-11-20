from django.urls import path
from . import views

from django.urls import path
from . import views

urlpatterns = [
    path('', views.catalogo_view, name='catalogo'),
    path('inventario/', views.gestion_inventario, name='gestion_inventario'),
    path('inventario/crear/', views.crear_equipo, name='crear_equipo'),
    path('inventario/editar/<int:equipo_id>/', views.editar_equipo, name='editar_equipo'),
    path('inventario/eliminar/<int:equipo_id>/', views.eliminar_equipo, name='eliminar_equipo'),
    path('inventario/defectuosos/', views.equipos_defectuosos, name='equipos_defectuosos'),
]