from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count

from inventory.models import Equipo
from users.decorators import role_required
from .models import Reserva, Prestamo
from .utils import enviar_correo_notificacion

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
        bloque_horario = request.POST.get('bloque_horario')
        
        if bloque_horario:
            # Creamos la reserva
            reserva = Reserva.objects.create(
                usuario=request.user,
                equipo=equipo,
                bloque_horario=bloque_horario,
                estado='confirmada'
            )
            
            #  Enviar correo de notificación ---
            enviar_correo_notificacion(
                asunto="SmartLocker - Reserva Confirmada",
                mensaje=f"Hola {request.user.username},\n\nTu reserva para el equipo {equipo.nombre} (Código: {equipo.codigo}) ha sido confirmada.\n\nAcércate al pañol en el bloque: {bloque_horario} para retirar tu equipo.\n\nSaludos,\nEl equipo de SmartLocker.",
                destinatario=request.user.email
            )
            # ---------------------------------------------

            messages.success(
                request,
                f"¡Reserva confirmada! Comprobante N° {reserva.id} para "
                f"{equipo.nombre} en el bloque: {bloque_horario}. "
                f"Acércate al pañol para retirar el equipo."
            )
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


@role_required('encargado', 'administrador')
def panel_encargado(request):
    """
    Vista principal del Encargado.
    Muestra las reservas confirmadas que aún NO tienen un préstamo asociado
    (es decir, equipos reservados pero pendientes de entrega física).
    """
    # Reservas confirmadas que no tienen préstamo creado todavía
    reservas_pendientes = Reserva.objects.filter(
        estado='confirmada',
        prestamo__isnull=True
    ).select_related('usuario', 'equipo').order_by('fecha_creacion')

    # Contador rápido de préstamos activos (para mostrar en el panel)
    total_prestamos_activos = Prestamo.objects.filter(
        fecha_devolucion_real__isnull=True
    ).count()

    context = {
        'reservas_pendientes': reservas_pendientes,
        'total_prestamos_activos': total_prestamos_activos,
    }
    return render(request, 'loans/panel_encargado.html', context)


@role_required('encargado', 'administrador')
def confirmar_entrega(request, reserva_id):
    """
    El Encargado confirma la entrega física de un equipo reservado.
    Crea el registro de Prestamo y cambia el estado del equipo a 'prestado'.
    """
    reserva = get_object_or_404(Reserva, id=reserva_id, estado='confirmada')

    # Verificar que la reserva no tenga ya un préstamo (evita duplicados)
    if hasattr(reserva, 'prestamo'):
        messages.warning(request, "Esta reserva ya fue entregada anteriormente.")
        return redirect('panel_encargado')

    if request.method == 'POST':
        # Crear el préstamo con fecha límite de 24 horas (ajustable)
        Prestamo.objects.create(
            reserva=reserva,
            fecha_limite=timezone.now() + timezone.timedelta(days=1)
        )

        # Cambiar estado del equipo a prestado
        equipo = reserva.equipo
        equipo.estado = 'prestado'
        equipo.save()

        # Notificar al alumno que se le entregó el equipo ---
        enviar_correo_notificacion(
            asunto="SmartLocker - Equipo Entregado",
            mensaje=f"Hola {reserva.usuario.username},\n\nSe te ha entregado el equipo {equipo.nombre}.\n\nTienes plazo hasta mañana a la misma hora para devolverlo.\n\nSaludos.",
            destinatario=reserva.usuario.email
        )
        # -------------------------------------------------------------

        messages.success(
            request,
            f"Entrega confirmada: {equipo.nombre} (código {equipo.codigo}) "
            f"entregado a {reserva.usuario.username}."
        )
        return redirect('panel_encargado')

    # GET: mostrar pantalla de confirmación
    return render(request, 'loans/confirmar_entrega.html', {'reserva': reserva})


@role_required('encargado', 'administrador')
def dispositivos_prestados(request):
    """
    Vista que muestra todos los préstamos activos (no devueltos aún),
    agrupando la información: equipo, cantidad, usuario solicitante y fechas.
    """
    prestamos_activos = Prestamo.objects.filter(
        fecha_devolucion_real__isnull=True
    ).select_related(
        'reserva__equipo',
        'reserva__usuario',
        'reserva__equipo__categoria'
    ).order_by('fecha_limite')  # Los que vencen primero, arriba

    # Resumen por equipo (cuántas unidades de cada equipo están prestadas)
    resumen_por_equipo = (
        Prestamo.objects.filter(fecha_devolucion_real__isnull=True)
        .values('reserva__equipo__nombre', 'reserva__equipo__codigo')
        .annotate(cantidad=Count('id'))
        .order_by('-cantidad')
    )

    # Marcar visualmente los préstamos vencidos (para el template)
    ahora = timezone.now()
    for p in prestamos_activos:
        p.esta_vencido = p.fecha_limite < ahora

    context = {
        'prestamos_activos': prestamos_activos,
        'resumen_por_equipo': resumen_por_equipo,
        'total_activos': prestamos_activos.count(),
    }
    return render(request, 'loans/dispositivos_prestados.html', context)