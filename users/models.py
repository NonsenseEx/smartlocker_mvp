from django.db import models
from django.contrib.auth.models import AbstractUser

class Usuario(AbstractUser):
    ROLES = (
        ('solicitante', 'Solicitante (Estudiante / Docente)'),
        ('encargado', 'Encargado del Centro de Préstamos'),
        ('administrador', 'Administrador del Sistema'),
    )
    rol = models.CharField(max_length=20, choices=ROLES, default='solicitante')
    
    tiene_sancion_activa = models.BooleanField(default=False)
    
    # --- NUEVO CAMPO ---
    fecha_fin_sancion = models.DateTimeField(null=True, blank=True, help_text="Fecha hasta la que el usuario está suspendido")
    foto_perfil = models.ImageField(upload_to='perfiles/', null=True, blank=True, help_text="Foto de perfil (opcional)")

    def __str__(self):
        return f"{self.username} - {self.get_rol_display()}"