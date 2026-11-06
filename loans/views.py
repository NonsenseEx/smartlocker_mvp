from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from inventory.models import Equipo
from .models import Reserva

@login_required
def crear_reserva(request, equipo_id):
    equipo = get_object_or_404(Equipo, id=equipo_id)
    
    # 1. REGLA DE NEGOCIO: Validar si el usuario tiene sanción (RF-04)
    if request.user.tiene_sancion_activa:
        messages.error(request, "Usuario Suspendido: No puedes realizar reservas porque tienes una sanción activa.")
        return redirect('catalogo')
        
    # 2. Validar que el equipo esté disponible
    if equipo.estado != 'disponible':
        messages.warning(request, "El equipo no está disponible actualmente.")
        return redirect('catalogo')

    if request.method == 'POST':
        # Obtenemos el bloque horario del formulario
        bloque_horario = request.POST.get('bloque_horario')
        
        if bloque_horario:
            # Creamos la reserva en la base de datos
            reserva = Reserva.objects.create(
                usuario=request.user,
                equipo=equipo,
                bloque_horario=bloque_horario,
                estado='confirmada'
            )
            
            # (Opcional MVP) Cambiamos el estado del equipo a prestado para la demo
            # En un sistema real, el equipo cambia a prestado recién cuando el Encargado lo entrega físicamente.
            equipo.estado = 'prestado'
            equipo.save()
            
            messages.success(request, f"¡Reserva confirmada! Comprobante N° {reserva.id} para {equipo.nombre} en el bloque: {bloque_horario}")
            return redirect('catalogo')
        else:
            messages.error(request, "Debes seleccionar un bloque horario.")
            
    return render(request, 'loans/crear_reserva.html', {'equipo': equipo})