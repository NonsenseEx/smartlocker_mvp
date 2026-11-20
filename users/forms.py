from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import Usuario

class RegistroForm(UserCreationForm):
    class Meta:
        model = Usuario
        fields = ('username', 'first_name', 'last_name', 'email')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Agregamos clases de Bootstrap a los campos de contraseña automáticos
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

class EditarPerfilForm(UserChangeForm):
    password = None # Ocultamos el campo de contraseña aquí (para eso está el botón de cambiar contraseña)
    
    class Meta:
        model = Usuario
        fields = ('first_name', 'last_name', 'email')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

class AdminEditarUsuarioForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ['first_name', 'last_name', 'email', 'rol', 'tiene_sancion_activa', 'fecha_fin_sancion']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'rol': forms.Select(attrs={'class': 'form-select'}),
            'tiene_sancion_activa': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'fecha_fin_sancion': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }