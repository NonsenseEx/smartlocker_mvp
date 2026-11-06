from django.contrib.auth.models import AbstractUser
from django.db import models

class Usuario(AbstractUser):
    # Definimos los roles que pediste en la Parte 1 (RF-01)
    ROLES = (
        ('solicitante', 'Solicitante (Estudiante / Docente)'),
        ('encargado', 'Encargado del Centro de Préstamos'),
        ('administrador', 'Administrador del Sistema'),
    )
    rol = models.CharField(max_length=20, choices=ROLES, default='solicitante')
    
    # Para la sanción lógica (RF-04)
    tiene_sancion_activa = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.username} - {self.get_rol_display()}"