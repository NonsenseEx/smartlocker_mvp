from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Sum
from django.db import models
from django.conf import settings

from inventory.models import Equipo
from users.decorators import role_required
from .models import Reserva, Prestamo, ReporteIncidente
from .utils import enviar_correo_notificacion

@login_required
def crear_reserva(request, equipo_id):
    equipo = get_object_or_404(Equipo, id=equipo_id)
    
    # 1. REGLA DE NEGOCIO: Validar si el usuario tiene sanción
    if request.user.tiene_sancion_activa:
        if request.user.fecha_fin_sancion and request.user.fecha_fin_sancion < timezone.now():
            request.user.tiene_sancion_activa = False
            request.user.fecha_fin_sancion = None
            request.user.save()
        else:
            fecha_fin = request.user.fecha_fin_sancion.strftime('%d/%m/%Y') if request.user.fecha_fin_sancion else "indefinido"
            messages.error(request, f"Usuario Suspendido: No puedes reservar porque tienes una sanción activa hasta el {fecha_fin}.")
            return redirect('catalogo')
        
    # 2. Validar que el equipo esté disponible
    if equipo.estado != 'disponible':
        messages.warning(request, "El equipo no está disponible actualmente.")
        return redirect('catalogo')

    if request.method == 'POST':
        bloque_horario = request.POST.get('bloque_horario')
        cantidad_str = request.POST.get('cantidad', '1')
        
        try:
            cantidad_solicitada = int(cantidad_str)
        except ValueError:
            cantidad_solicitada = 1

        if bloque_horario:
            # 3. VALIDACIÓN DE STOCK POR BLOQUE HORARIO
            reservas_existentes = Reserva.objects.filter(
                equipo=equipo,
                bloque_horario=bloque_horario,
                estado='confirmada'
            ).aggregate(total=models.Sum('cantidad'))['total'] or 0
            
            stock_disponible = equipo.stock - reservas_existentes
            
            if cantidad_solicitada > stock_disponible:
                messages.error(request, f"No hay suficiente stock en este bloque. Solo quedan {stock_disponible} unidades de {equipo.nombre}.")
                return redirect('crear_reserva', equipo_id=equipo.id)
            
            # Creamos la reserva
            reserva = Reserva.objects.create(
                usuario=request.user,
                equipo=equipo,
                bloque_horario=bloque_horario,
                cantidad=cantidad_solicitada,
                estado='confirmada'
            )
            
            # Enviar correo de notificación
            enviar_correo_notificacion(
                asunto="SmartLocker - Reserva Confirmada",
                mensaje=f"Hola {request.user.username},\n\nTu reserva para {cantidad_solicitada} unidad(es) de {equipo.nombre} ha sido confirmada para el bloque: {bloque_horario}.\n\nSaludos,\nEl equipo de SmartLocker.",
                destinatario=request.user.email
            )
            
            messages.success(
                request,
                f"¡Reserva confirmada! Comprobante N° {reserva.id} para {cantidad_solicitada} {equipo.nombre}(s) en el bloque: {bloque_horario}."
            )
            return redirect('catalogo')
        else:
            messages.error(request, "Debes seleccionar un bloque horario.")
            
    return render(request, 'loans/crear_reserva.html', {'equipo': equipo})


@login_required
def registrar_devolucion(request, prestamo_id):
    prestamo = get_object_or_404(Prestamo, id=prestamo_id)
    
    if request.method == 'POST':
        estado_devuelto = request.POST.get('estado_equipo')
        
        if estado_devuelto:
            prestamo.fecha_devolucion_real = timezone.now()
            prestamo.estado_equipo_devuelto = estado_devuelto
            
            # Verificamos retraso
            if prestamo.fecha_devolucion_real > prestamo.fecha_limite:
                prestamo.tiene_retraso = True
                
                diferencia = prestamo.fecha_devolucion_real - prestamo.fecha_limite
                dias_retraso = diferencia.days if diferencia.days > 0 else 1
                prestamo.dias_retraso = dias_retraso
                
                usuario = prestamo.reserva.usuario
                usuario.tiene_sancion_activa = True
                
                if usuario.fecha_fin_sancion and usuario.fecha_fin_sancion > timezone.now():
                    usuario.fecha_fin_sancion += timezone.timedelta(days=dias_retraso)
                else:
                    usuario.fecha_fin_sancion = timezone.now() + timezone.timedelta(days=dias_retraso)
                
                usuario.save()
                messages.warning(request, f"Devolución con {dias_retraso} día(s) de retraso. Sanción aplicada hasta el {usuario.fecha_fin_sancion.strftime('%d/%m/%Y')}.")
            else:
                messages.success(request, "Devolución registrada a tiempo. ¡Gracias!")

            prestamo.save()
            
            # Sumamos el stock de vuelta
            equipo = prestamo.reserva.equipo
            equipo.stock += prestamo.reserva.cantidad
            if estado_devuelto == 'operativo':
                equipo.estado = 'disponible'
            else:
                equipo.estado = 'mantenimiento'
            equipo.save()
            
            return redirect('catalogo')
            
    return render(request, 'loans/registrar_devolucion.html', {'prestamo': prestamo})


@login_required
def mis_prestamos(request):
    prestamos_activos = Prestamo.objects.filter(
        reserva__usuario=request.user, 
        fecha_devolucion_real__isnull=True
    )
    return render(request, 'loans/mis_prestamos.html', {'prestamos': prestamos_activos})


@login_required
def devolver_mi_equipo(request, prestamo_id):
    prestamo = get_object_or_404(Prestamo, id=prestamo_id, reserva__usuario=request.user)
    
    if request.method == 'POST':
        estado_devuelto = request.POST.get('estado_equipo')
        if estado_devuelto:
            prestamo.fecha_devolucion_real = timezone.now()
            prestamo.estado_equipo_devuelto = estado_devuelto
            
            if prestamo.fecha_devolucion_real > prestamo.fecha_limite:
                prestamo.tiene_retraso = True
                
                diferencia = prestamo.fecha_devolucion_real - prestamo.fecha_limite
                dias_retraso = diferencia.days if diferencia.days > 0 else 1
                prestamo.dias_retraso = dias_retraso
                
                usuario = prestamo.reserva.usuario
                usuario.tiene_sancion_activa = True
                
                if usuario.fecha_fin_sancion and usuario.fecha_fin_sancion > timezone.now():
                    usuario.fecha_fin_sancion += timezone.timedelta(days=dias_retraso)
                else:
                    usuario.fecha_fin_sancion = timezone.now() + timezone.timedelta(days=dias_retraso)
                
                usuario.save()
                messages.warning(request, f"Has devuelto el equipo con {dias_retraso} día(s) de retraso. Sanción aplicada hasta el {usuario.fecha_fin_sancion.strftime('%d/%m/%Y')}.")
            else:
                messages.success(request, "Devolución registrada a tiempo. ¡Gracias por cuidar el equipo!")

            prestamo.save()
            
            equipo = prestamo.reserva.equipo
            equipo.stock += prestamo.reserva.cantidad
            if estado_devuelto == 'operativo':
                equipo.estado = 'disponible'
            else:
                equipo.estado = 'mantenimiento'
            equipo.save()
            
            return redirect('catalogo')
            
    return render(request, 'loans/devolver_mi_equipo.html', {'prestamo': prestamo})


@role_required('encargado', 'administrador')
def panel_encargado(request):
    reservas_pendientes = Reserva.objects.filter(
        estado='confirmada',
        prestamo__isnull=True
    ).select_related('usuario', 'equipo').order_by('fecha_creacion')

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
    reserva = get_object_or_404(Reserva, id=reserva_id, estado='confirmada')

    if hasattr(reserva, 'prestamo'):
        messages.warning(request, "Esta reserva ya fue entregada anteriormente.")
        return redirect('panel_encargado')

    if request.method == 'POST':
        Prestamo.objects.create(
            reserva=reserva,
            fecha_limite=timezone.now() + timezone.timedelta(days=1)
        )

        # DESCONTAR STOCK
        equipo = reserva.equipo
        equipo.stock -= reserva.cantidad
        if equipo.stock <= 0:
            equipo.estado = 'prestado'
        equipo.save()

        enviar_correo_notificacion(
            asunto="SmartLocker - Equipo Entregado",
            mensaje=f"Hola {reserva.usuario.username},\n\nSe te ha entregado {reserva.cantidad} unidad(es) de {equipo.nombre}.\n\nTienes plazo hasta mañana a la misma hora para devolverlo.\n\nSaludos.",
            destinatario=reserva.usuario.email
        )

        messages.success(
            request,
            f"Entrega confirmada: {reserva.cantidad} {equipo.nombre}(s) entregado(s) a {reserva.usuario.username}."
        )
        return redirect('panel_encargado')

    return render(request, 'loans/confirmar_entrega.html', {'reserva': reserva})


# --- NUEVAS VISTAS ---

@role_required('encargado', 'administrador')
def cancelar_reserva_encargado(request, reserva_id):
    reserva = get_object_or_404(Reserva, id=reserva_id, estado='confirmada')
    
    if request.method == 'POST':
        reserva.estado = 'cancelada'
        reserva.save()
        
        # --- NUEVO: Enviar correo de notificación de cancelación ---
        enviar_correo_notificacion(
            asunto="SmartLocker - Reserva Cancelada",
            mensaje=f"Hola {reserva.usuario.username},\n\nLamentamos informarte que tu reserva para {reserva.cantidad} {reserva.equipo.nombre}(s) en el bloque {reserva.bloque_horario} ha sido cancelada por el Encargado del pañol.\n\nPor favor, acércate a ventanilla para más detalles.\n\nSaludos,\nEl equipo de SmartLocker.",
            destinatario=reserva.usuario.email
        )
        messages.warning(request, f"La reserva de {reserva.cantidad} {reserva.equipo.nombre}(s) para {reserva.usuario.username} ha sido cancelada.")
        return redirect('panel_encargado')
        
    return render(request, 'loans/cancelar_reserva_encargado.html', {'reserva': reserva})


@role_required('encargado', 'administrador')
def reportar_incidente(request, prestamo_id):
    prestamo = get_object_or_404(Prestamo, id=prestamo_id)
    
    if request.method == 'POST':
        tipo = request.POST.get('tipo')
        descripcion = request.POST.get('descripcion')
        aplicar_bloqueo = request.POST.get('aplicar_bloqueo') == 'on'
        
        reporte = ReporteIncidente.objects.create(
            prestamo=prestamo,
            encargado=request.user,
            tipo=tipo,
            descripcion=descripcion,
            bloqueo_aplicado=aplicar_bloqueo
        )
        
        if aplicar_bloqueo:
            usuario = prestamo.reserva.usuario
            usuario.tiene_sancion_activa = True
            usuario.fecha_fin_sancion = timezone.now() + timezone.timedelta(days=30)
            usuario.save()
            
            # --- NUEVO: Enviar correo de notificación de suspensión ---
            enviar_correo_notificacion(
                asunto="SmartLocker - Cuenta Suspendida",
                mensaje=f"Hola {usuario.username},\n\nTu cuenta ha sido suspendida por un período de 30 días debido a un incidente reportado con el equipo {prestamo.reserva.equipo.nombre}.\n\nMotivo: {descripcion}\n\nNo podrás realizar nuevas reservas hasta que la sanción expire.\n\nSaludos,\nEl equipo de SmartLocker.",
                destinatario=usuario.email
            )
            # -----------------------------------------------------------
            
            messages.error(request, f"Incidente reportado y usuario {usuario.username} bloqueado por 30 días.")
        else:
            messages.info(request, "Incidente reportado (sin bloqueo).")
            
        return redirect('dispositivos_prestados')
        
    return render(request, 'loans/reportar_incidente.html', {'prestamo': prestamo})


@role_required('encargado', 'administrador')
def dispositivos_prestados(request):
    prestamos_activos = Prestamo.objects.filter(
        fecha_devolucion_real__isnull=True
    ).select_related(
        'reserva__equipo',
        'reserva__usuario',
        'reserva__equipo__categoria'
    ).order_by('fecha_limite')

    resumen_por_equipo = (
        Prestamo.objects.filter(fecha_devolucion_real__isnull=True)
        .values('reserva__equipo__nombre', 'reserva__equipo__codigo')
        .annotate(cantidad=Count('id'))
        .order_by('-cantidad')
    )

    ahora = timezone.now()
    for p in prestamos_activos:
        p.esta_vencido = p.fecha_limite < ahora

    context = {
        'prestamos_activos': prestamos_activos,
        'resumen_por_equipo': resumen_por_equipo,
        'total_activos': prestamos_activos.count(),
    }
    return render(request, 'loans/dispositivos_prestados.html', context)