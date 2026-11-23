from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Equipo, Categoria
from .forms import EquipoForm
from .utils import calcular_disponibilidad, resumen_inventario
from users.decorators import role_required

# Vista actual del catálogo (ya la tienes)
@login_required 
def catalogo_view(request):
    equipos = Equipo.objects.all().order_by('nombre')
    disponibilidad = calcular_disponibilidad(equipos)
    for equipo in equipos:
        equipo.disponibilidad = disponibilidad.get(equipo.id)
    return render(request, 'inventory/catalogo.html', {
        'equipos': equipos,
        'resumen': resumen_inventario(equipos),
    })


@role_required('encargado', 'administrador')
def gestion_inventario(request):
    """Vista de consulta para Encargados y Administradores"""
    equipos = Equipo.objects.all().order_by('nombre')
    disponibilidad = calcular_disponibilidad(equipos)
    for equipo in equipos:
        equipo.disponibilidad = disponibilidad.get(equipo.id)
    return render(request, 'inventory/gestion_inventario.html', {
        'equipos': equipos,
        'resumen': resumen_inventario(equipos),
    })

@role_required('administrador')
def crear_equipo(request):
    """Solo el Administrador puede crear equipos"""
    if request.method == 'POST':
        form = EquipoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Equipo agregado al catálogo exitosamente.")
            return redirect('gestion_inventario')
    else:
        form = EquipoForm()
    return render(request, 'inventory/form_equipo.html', {'form': form, 'titulo': 'Agregar Nuevo Equipo'})

@role_required('administrador')
def editar_equipo(request, equipo_id):
    """Solo el Administrador puede editar equipos"""
    equipo = get_object_or_404(Equipo, id=equipo_id)
    if request.method == 'POST':
        form = EquipoForm(request.POST, request.FILES, instance=equipo)
        if form.is_valid():
            form.save()
            messages.success(request, "Equipo actualizado correctamente.")
            return redirect('gestion_inventario')
    else:
        form = EquipoForm(instance=equipo)
    return render(request, 'inventory/form_equipo.html', {'form': form, 'titulo': 'Editar Equipo'})

@role_required('administrador')
def eliminar_equipo(request, equipo_id):
    """Solo el Administrador puede eliminar equipos"""
    equipo = get_object_or_404(Equipo, id=equipo_id)
    if request.method == 'POST':
        equipo.delete()
        messages.warning(request, "Equipo eliminado del catálogo.")
        return redirect('gestion_inventario')
    return render(request, 'inventory/eliminar_equipo.html', {'equipo': equipo})

@role_required('encargado', 'administrador')
def equipos_defectuosos(request):
    # Buscamos los equipos que estén en mantenimiento
    equipos = Equipo.objects.filter(estado='mantenimiento').order_by('nombre')
    return render(request, 'inventory/equipos_defectuosos.html', {'equipos': equipos})