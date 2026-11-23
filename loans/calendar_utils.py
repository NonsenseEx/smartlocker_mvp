"""Calendario laborable y cálculo de cupos por fecha para las reservas."""

import calendar
from datetime import date, timedelta

from django.db.models import Sum
from django.utils import timezone

from inventory.utils import BLOQUES_HORARIOS

DIAS_LABORABLES = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]
MESES_ES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]
MESES_VENTANA = 3

BLOQUES_POR_DIA = {
    dia: [bloque for bloque in BLOQUES_HORARIOS if bloque.startswith(dia)]
    for dia in DIAS_LABORABLES
}


def fin_ventana(hoy=None):
    """Último día del tercer mes desde la fecha indicada."""
    hoy = hoy or timezone.localdate()
    anio, mes = hoy.year, hoy.month
    for _ in range(MESES_VENTANA - 1):
        mes += 1
        if mes == 13:
            anio += 1
            mes = 1
    return date(anio, mes, calendar.monthrange(anio, mes)[1])


def inicio_ventana(equipo, hoy=None):
    hoy = hoy or timezone.localdate()
    if equipo.disponible_desde and equipo.disponible_desde > hoy:
        return equipo.disponible_desde
    return hoy


def cupo_disponible(equipo, fecha, bloque):
    """Unidades libres de un equipo para una fecha y bloque concretos."""
    from .models import Reserva

    reservado = (
        Reserva.objects.filter(
            equipo=equipo,
            fecha_reserva=fecha,
            bloque_horario=bloque,
            estado="confirmada",
        ).aggregate(total=Sum("cantidad"))["total"]
        or 0
    )
    return max(equipo.stock - reservado, 0)


def validar_fecha_reserva(equipo, fecha_texto, hoy=None):
    """Valida la fecha solicitada. Devuelve (fecha, error)."""
    hoy = hoy or timezone.localdate()
    try:
        fecha = date.fromisoformat(fecha_texto)
    except (TypeError, ValueError):
        return None, "Selecciona una fecha válida."

    if fecha < hoy:
        return None, "No se pueden reservar fechas pasadas."
    if fecha.weekday() >= 5:
        return None, "Solo se pueden reservar días laborables (lunes a viernes)."
    if fecha > fin_ventana(hoy):
        return None, "Solo se pueden reservar fechas de los próximos 3 meses."
    if equipo.disponible_desde and fecha < equipo.disponible_desde:
        return None, "El equipo aún no está disponible en esa fecha."
    if equipo.disponible_hasta and fecha > equipo.disponible_hasta:
        return None, "El equipo no está disponible en esa fecha."

    return fecha, None


def bloques_del_dia(fecha):
    return BLOQUES_POR_DIA.get(DIAS_LABORABLES[fecha.weekday()], [])


def calendario_reservas(equipo, hoy=None):
    """
    Genera los días laborables de los próximos 3 meses con sus horarios libres.

    La información se serializa en la plantilla para que el calendario y la
    barra de cantidad funcionen sin depender de peticiones adicionales.
    """
    from .models import Reserva

    hoy = hoy or timezone.localdate()
    inicio = inicio_ventana(equipo, hoy)
    fin = fin_ventana(hoy)
    if equipo.disponible_hasta and equipo.disponible_hasta < fin:
        fin = equipo.disponible_hasta
    if inicio > fin:
        return {"dias": {}, "meses": [], "stock": equipo.stock}

    reservas = (
        Reserva.objects.filter(
            equipo=equipo,
            estado="confirmada",
            fecha_reserva__range=[inicio, fin],
        )
        .values("fecha_reserva", "bloque_horario")
        .annotate(total=Sum("cantidad"))
    )
    ocupados = {
        (item["fecha_reserva"], item["bloque_horario"]): item["total"] or 0
        for item in reservas
    }

    dias = {}
    fecha = inicio
    while fecha <= fin:
        if fecha.weekday() < 5:
            nombre_dia = DIAS_LABORABLES[fecha.weekday()]
            slots = []
            for bloque in BLOQUES_POR_DIA[nombre_dia]:
                reservado = ocupados.get((fecha, bloque), 0)
                libres = max(equipo.stock - reservado, 0)
                slots.append({
                    "bloque": bloque,
                    "hora": bloque.split(" ", 1)[1],
                    "libres": libres,
                    "disponible": libres > 0,
                })
            dias[fecha.isoformat()] = {
                "fecha": fecha.isoformat(),
                "numero": fecha.day,
                "dia": nombre_dia,
                "mes": MESES_ES[fecha.month - 1],
                "anio": fecha.year,
                "slots": slots,
                "hay_horas": any(slot["disponible"] for slot in slots),
            }
        fecha += timedelta(days=1)

    meses = []
    anio, mes = inicio.year, inicio.month
    while (anio, mes) <= (fin.year, fin.month):
        meses.append({
            "anio": anio,
            "mes": mes,
            "label": f"{MESES_ES[mes - 1]} {anio}".capitalize(),
        })
        mes += 1
        if mes == 13:
            anio += 1
            mes = 1

    return {
        "dias": dias,
        "meses": meses,
        "stock": equipo.stock,
        "hoy": hoy.isoformat(),
    }
