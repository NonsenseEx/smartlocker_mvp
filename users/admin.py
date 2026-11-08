from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario

class UsuarioAdmin(UserAdmin):
    # Agregamos nuestros campos a la vista de edición
    fieldsets = UserAdmin.fieldsets + (
        ('Información SmartLocker', {'fields': ('rol', 'tiene_sancion_activa')}),
    )
    # Agregamos nuestros campos a la vista de creación
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Información SmartLocker', {'fields': ('rol', 'tiene_sancion_activa')}),
    )
    # Mostramos las columnas en la lista de usuarios
    list_display = ('username', 'email', 'rol', 'tiene_sancion_activa', 'is_staff')

admin.site.register(Usuario, UsuarioAdmin)