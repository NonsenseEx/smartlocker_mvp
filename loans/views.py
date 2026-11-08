from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from inventory.models import Equipo
from .models import Reserva
from django.utils import timezone
from datetime import timedelta
from .models import Reserva, Prestamo


@login_required
def crear_reserva(request, equipo_id):
    equipo = get_object_or_404(Equipo, id=equipo_id)
    
    if request.user.tiene_sancion_activa:
        messages.error(request, "Usuario Suspendido: No puedes realizar reservas porque tienes una sanción activa.")
        return redirect('catalogo')
        
    #  Equipo está disponible ?
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
            
            # 1. Cambiamos el estado del equipo a prestado para la demo
            equipo.estado = 'prestado'
            equipo.save()
            
            # 2. Creamos el préstamo automáticamente con fecha límite de 24 horas
            Prestamo.objects.create(
                reserva=reserva,
                fecha_limite=timezone.now() + timezone.timedelta(days=1)
            )
        
            
            
            messages.success(request, f"¡Reserva confirmada! Comprobante N° {reserva.id} para {equipo.nombre} en el bloque: {bloque_horario}")
            return redirect('catalogo')
        else:
            messages.error(request, "Debes seleccionar un bloque horario.")
            
    return render(request, 'loans/crear_reserva.html', {'equipo': equipo})

@login_required
def registrar_devolucion(request, prestamo_id):
    # Buscamos el préstamo que está activo
    prestamo = get_object_or_404(Prestamo, id=prestamo_id)
    
    if request.method == 'POST':
        # Obtenemos el estado en que el Encargado recibió el equipo
        estado_devuelto = request.POST.get('estado_equipo')
        
        if estado_devuelto:
            # 1. Registramos la fecha de devolución actual
            prestamo.fecha_devolucion_real = timezone.now()
            prestamo.estado_equipo_devuelto = estado_devuelto
            
            # 2. Verificamos si hay retraso (RF-07)
            if prestamo.fecha_devolucion_real > prestamo.fecha_limite:
                prestamo.tiene_retraso = True
                # Aplicamos la sanción al usuario
                prestamo.reserva.usuario.tiene_sancion_activa = True
                prestamo.reserva.usuario.save()
                messages.warning(request, "Devolución registrada con retraso. Se ha aplicado una sanción al usuario.")
            else:
                messages.success(request, "Devolución registrada a tiempo. ¡Gracias!")

            prestamo.save()
            
            # 3. Actualizamos el estado del equipo físico (RF-06)
            equipo = prestamo.reserva.equipo
            if estado_devuelto == 'operativo':
                equipo.estado = 'disponible'
            else:
                equipo.estado = 'mantenimiento' # Si está dañado, va a mantenimiento
            equipo.save()
            
            return redirect('catalogo')
            
    return render(request, 'loans/registrar_devolucion.html', {'prestamo': prestamo})

# 1. Vista para que el usuario vea sus préstamos activos
@login_required
def mis_prestamos(request):
    # Buscamos los préstamos donde el usuario de la reserva sea el usuario logueado
    # y que aún no tengan fecha de devolución real (es decir, que estén activos)
    prestamos_activos = Prestamo.objects.filter(
        reserva__usuario=request.user, 
        fecha_devolucion_real__isnull=True
    )
    return render(request, 'loans/mis_prestamos.html', {'prestamos': prestamos_activos})

# 2. Vista para que el propio usuario procese la devolución
@login_required
def devolver_mi_equipo(request, prestamo_id):
    prestamo = get_object_or_404(Prestamo, id=prestamo_id, reserva__usuario=request.user)
    
    if request.method == 'POST':
        estado_devuelto = request.POST.get('estado_equipo')
        if estado_devuelto:
            prestamo.fecha_devolucion_real = timezone.now()
            prestamo.estado_equipo_devuelto = estado_devuelto
            
            # Lógica de retraso y sanción
            if prestamo.fecha_devolucion_real > prestamo.fecha_limite:
                prestamo.tiene_retraso = True
                prestamo.reserva.usuario.tiene_sancion_activa = True
                prestamo.reserva.usuario.save()
                messages.warning(request, "Has devuelto el equipo con retraso. Se ha aplicado una sanción a tu cuenta.")
            else:
                messages.success(request, "Devolución registrada a tiempo. ¡Gracias por cuidar el equipo!")

            prestamo.save()
            
            # Actualizamos el estado del equipo
            equipo = prestamo.reserva.equipo
            if estado_devuelto == 'operativo':
                equipo.estado = 'disponible'
            else:
                equipo.estado = 'mantenimiento'
            equipo.save()
            
            return redirect('catalogo')
            
    return render(request, 'loans/devolver_mi_equipo.html', {'prestamo': prestamo})