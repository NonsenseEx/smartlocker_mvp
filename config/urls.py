from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views # Importamos las vistas de auth de Django

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Rutas de Autenticación (Django las trae hechas)
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    
    # Rutas de la app inventory (Catálogo)
    path('', include('inventory.urls')),
    path('prestamos/', include('loans.urls')), 
]