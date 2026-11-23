from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views 
from django.conf import settings
from django.conf.urls.static import static

from .views import health

urlpatterns = [
    path('health', health, name='health'),
    path('health/', health, name='health_trailing_slash'),
    path('admin/', admin.site.urls),
    
    # Rutas de Autenticación (Django las trae hechas)
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    
    # Rutas de la app inventory (Catálogo)
    path('', include('inventory.urls')),
    path('prestamos/', include('loans.urls')), 
    path('usuarios/', include('users.urls')), # Rutas de la app users
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
