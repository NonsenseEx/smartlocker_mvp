from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import RegistroForm, EditarPerfilForm

def registro(request):
    if request.user.is_authenticated:
        return redirect('catalogo')
        
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.rol = 'solicitante' # Forzamos a que todos los nuevos sean solicitantes
            user.save()
            
            # Iniciar sesión automáticamente después de registrarse
            login(request, user)
            messages.success(request, "¡Bienvenido a SmartLocker! Tu cuenta ha sido creada exitosamente.")
            return redirect('catalogo')
    else:
        form = RegistroForm()
    
    return render(request, 'users/registro.html', {'form': form})

@login_required
def editar_perfil(request):
    if request.method == 'POST':
        form = EditarPerfilForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Tus datos personales se han actualizado correctamente.")
            return redirect('editar_perfil')
    else:
        form = EditarPerfilForm(instance=request.user)
        
    return render(request, 'users/editar_perfil.html', {'form': form})

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .forms import AdminEditarUsuarioForm
from users.decorators import role_required
from .models import Usuario

@role_required('administrador')
def gestion_usuarios(request):
    # Traemos a todos los usuarios ordenados por rol
    usuarios = Usuario.objects.all().order_by('rol', 'username')
    return render(request, 'users/gestion_usuarios.html', {'usuarios': usuarios})

@role_required('administrador')
def editar_usuario_admin(request, user_id):
    usuario = get_object_or_404(Usuario, id=user_id)
    
    if request.method == 'POST':
        form = AdminEditarUsuarioForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()
            messages.success(request, f"El perfil de {usuario.username} ha sido actualizado.")
            return redirect('gestion_usuarios')
    else:
        form = AdminEditarUsuarioForm(instance=usuario)
        
    return render(request, 'users/editar_usuario_admin.html', {'form': form, 'usuario_editado': usuario})