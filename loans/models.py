from django.db import models
from django.conf import settings
from inventory.models import Equipo

class Reserva(models.Model):
    ESTADOS_RESERVA = (
        ('pendiente', 'Pendiente'),
        ('confirmada', 'Confirmada'),
        ('cancelada', 'Cancelada'),
    )
    
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    equipo = models.ForeignKey(Equipo, on_delete=models.CASCADE)
    bloque_horario = models.CharField(max_length=100, help_text="Ej: Lunes 10:00 - 12:00")
    fecha_reserva = models.DateField(null=True, blank=True, help_text="Día solicitado para el préstamo")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADOS_RESERVA, default='pendiente')
    cantidad = models.PositiveIntegerField(default=1)     

    def __str__(self):
        return f"Reserva {self.id} - {self.equipo.nombre} por {self.usuario.username}"


class Prestamo(models.Model):
    ESTADOS_DEVOLUCION = (
        ('operativo', 'Operativo'),
        ('danado', 'Dañado'),
        ('faltante', 'Faltante / Perdido'),
    )
    
    # Relacionamos la reserva con el préstamo físico
    reserva = models.OneToOneField(Reserva, on_delete=models.CASCADE)
    fecha_salida = models.DateTimeField(auto_now_add=True)
    fecha_limite = models.DateTimeField(help_text="Fecha y hora máxima de devolución")
    fecha_devolucion_real = models.DateTimeField(null=True, blank=True)
    estado_equipo_devuelto = models.CharField(max_length=20, choices=ESTADOS_DEVOLUCION, blank=True, null=True)
    
    
    # Lógica de atraso (RF-07)
    tiene_retraso = models.BooleanField(default=False)
    dias_retraso = models.PositiveIntegerField(default=0, help_text="Días de retraso al devolver")

    def __str__(self):
        return f"Préstamo {self.id} - {self.reserva.equipo.codigo}"

class ReporteIncidente(models.Model):
    TIPOS = (
        ('atraso', 'Atraso en devolución'),
        ('dano', 'Daño del equipo'),
        ('robo', 'Pérdida / Robo'),
        ('otro', 'Otro problema'),
    )
    prestamo = models.ForeignKey(Prestamo, on_delete=models.CASCADE, related_name='reportes')
    encargado = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    tipo = models.CharField(max_length=20, choices=TIPOS)
    descripcion = models.TextField()
    fecha_reporte = models.DateTimeField(auto_now_add=True)
    bloqueo_aplicado = models.BooleanField(default=False)

    def __str__(self):
        return f"Reporte {self.get_tipo_display()} - Préstamo {self.prestamo.id}"