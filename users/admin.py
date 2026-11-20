from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario

@admin.register(Usuario)
class CustomUserAdmin(UserAdmin):
    # Añadimos el campo 'rol' y 'tiene_sancion_activa' a la vista de edición
    fieldsets = UserAdmin.fieldsets + (
        ('Información de SmartLocker', {'fields': ('rol', 'tiene_sancion_activa')}),
    )
    
    # Añadimos el campo 'rol' y 'tiene_sancion_activa' a la vista de creación (Add User)
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Información de SmartLocker', {'fields': ('rol', 'tiene_sancion_activa')}),
    )

    # Mostramos la columna 'rol' en la lista de usuarios
    list_display = ('username', 'email', 'rol', 'tiene_sancion_activa', 'is_staff')
    
    # Filtro lateral por rol
    list_filter = ('rol', 'tiene_sancion_activa', 'is_staff')