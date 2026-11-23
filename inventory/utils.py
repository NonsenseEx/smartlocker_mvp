"""Utilidades compartidas para disponibilidad de equipos del pañol."""

from django.db.models import Count, Q, Sum

BLOQUES_HORARIOS = [
    "Lunes 08:00 - 10:00",
    "Lunes 10:00 - 12:00",
    "Lunes 14:00 - 16:00",
    "Martes 08:00 - 10:00",
    "Martes 10:00 - 12:00",
    "Martes 14:00 - 16:00",
    "Miércoles 08:00 - 10:00",
    "Miércoles 10:00 - 12:00",
    "Miércoles 14:00 - 16:00",
    "Jueves 08:00 - 10:00",
    "Jueves 10:00 - 12:00",
    "Jueves 14:00 - 16:00",
    "Viernes 08:00 - 10:00",
    "Viernes 10:00 - 12:00",
    "Viernes 14:00 - 16:00",
]


def formatear_rango(equipo):
    """Devuelve una etiqueta legible para el rango de fechas del equipo."""
    desde = equipo.disponible_desde
    hasta = equipo.disponible_hasta

    if desde and hasta:
        if desde == hasta:
            return f"Disponible el {desde.strftime('%d/%m/%Y')}"
        return f"{desde.strftime('%d/%m')} – {hasta.strftime('%d/%m/%Y')}"
    if desde:
        return f"Desde el {desde.strftime('%d/%m/%Y')}"
    if hasta:
        return f"Hasta el {hasta.strftime('%d/%m/%Y')}"
    return "Sin fecha definida"


def resumen_inventario(equipos):
    """Métricas agregadas para la vista de inventario."""
    datos = equipos.aggregate(
        total_equipos=Count("id"),
        stock_total=Sum("stock"),
        equipos_disponibles=Count("id", filter=Q(estado="disponible")),
        equipos_mantenimiento=Count("id", filter=Q(estado="mantenimiento")),
    )
    return {
        "total_equipos": datos["total_equipos"] or 0,
        "stock_total": datos["stock_total"] or 0,
        "equipos_disponibles": datos["equipos_disponibles"] or 0,
        "equipos_mantenimiento": datos["equipos_mantenimiento"] or 0,
    }


def calcular_disponibilidad(equipos):
    """
    Calcula, por equipo, los bloques horarios con stock libre.

    La regla replica la validación de crear_reserva: se descuentan las
    cantidades de reservas confirmadas para cada bloque.
    """
    from loans.models import Reserva

    resultado = {}
    equipos = list(equipos)

    if not equipos:
        return resultado

    ids = [equipo.id for equipo in equipos]
    reservas = (
        Reserva.objects.filter(
            equipo_id__in=ids,
            estado="confirmada",
            bloque_horario__in=BLOQUES_HORARIOS,
        )
        .values("equipo_id", "bloque_horario")
        .annotate(total=Sum("cantidad"))
    )
    ocupados = {
        (item["equipo_id"], item["bloque_horario"]): item["total"] or 0
        for item in reservas
    }

    for equipo in equipos:
        bloques = []
        for bloque in BLOQUES_HORARIOS:
            reservado = ocupados.get((equipo.id, bloque), 0)
            libres = max(equipo.stock - reservado, 0)
            bloques.append(
                {
                    "label": bloque,
                    "libres": libres,
                    "disponible": libres > 0,
                }
            )

        resultado[equipo.id] = {
            "rango": formatear_rango(equipo),
            "bloques": bloques,
            "bloques_libres": sum(1 for bloque in bloques if bloque["disponible"]),
            "total_bloques": len(bloques),
            "proximos_libres": [bloque["label"] for bloque in bloques if bloque["disponible"]][:3],
        }

    return resultado
