from django.db import models

class Categoria(models.Model):
    nombre = models.CharField(max_length=100)
    
    def __str__(self):
        return self.nombre

class Equipo(models.Model):
    ESTADOS = (
        ('disponible', 'Disponible'),
        ('prestado', 'Prestado'),
        ('mantenimiento', 'En Mantenimiento'),
    )
    
    nombre = models.CharField(max_length=150)
    codigo = models.CharField(max_length=50, unique=True, help_text="Código único del equipo (ej. NOTE-001)")
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='disponible')
    stock = models.PositiveIntegerField(default=1, help_text="Cantidad total en el pañol")

    def __str__(self):
        return f"{self.codigo} - {self.nombre} ({self.get_estado_display()})"