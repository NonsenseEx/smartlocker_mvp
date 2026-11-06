from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from inventory.models import Equipo, Categoria
from .models import Reserva

Usuario = get_user_model()

class ReservaTestCase(TestCase):
    def setUp(self):
        # 1. Preparamos los datos de prueba (se ejecuta antes de cada test)
        self.categoria = Categoria.objects.create(nombre="Notebooks")
        self.equipo = Equipo.objects.create(
            nombre="Lenovo Thinkpad", 
            codigo="NOTE-01", 
            categoria=self.categoria, 
            estado='disponible'
        )
        # Creamos un usuario normal
        self.user_normal = Usuario.objects.create_user(
            username='estudiante', 
            password='password123',
            rol='solicitante',
            tiene_sancion_activa=False
        )
        # Creamos un usuario sancionado
        self.user_sancionado = Usuario.objects.create_user(
            username='infractor', 
            password='password123',
            rol='solicitante',
            tiene_sancion_activa=True
        )

    def test_usuario_normal_puede_reservar(self):
        """Prueba que un usuario sin sanciones puede hacer una reserva exitosa."""
        self.client.login(username='estudiante', password='password123')
        
        # Simulamos que el usuario envía el formulario de reserva
        response = self.client.post(reverse('crear_reserva', args=[self.equipo.id]), {
            'bloque_horario': 'Lunes 08:00 - 10:00'
        })
        
        # Verificamos que la reserva se creó en la base de datos
        self.assertEqual(Reserva.objects.count(), 1)
        # Verificamos que el equipo cambió a estado 'prestado'
        self.equipo.refresh_from_db()
        self.assertEqual(self.equipo.estado, 'prestado')

    def test_usuario_sancionado_no_puede_reservar(self):
        """Prueba que el sistema bloquea a un usuario con sanción (RF-04)."""
        self.client.login(username='infractor', password='password123')
        
        # Intentamos reservar
        response = self.client.post(reverse('crear_reserva', args=[self.equipo.id]), {
            'bloque_horario': 'Lunes 08:00 - 10:00'
        })
        
        # Verificamos que NO se creó la reserva
        self.assertEqual(Reserva.objects.count(), 0)
        # Verificamos que el equipo sigue 'disponible'
        self.equipo.refresh_from_db()
        self.assertEqual(self.equipo.estado, 'disponible')