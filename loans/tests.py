from datetime import date, timedelta

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from inventory.models import Equipo, Categoria
from .calendar_utils import BLOQUES_POR_DIA, calendario_reservas, cupo_disponible, validar_fecha_reserva
from .models import Reserva

Usuario = get_user_model()


def proximo_laborable():
    fecha = timezone.localdate() + timedelta(days=1)
    while fecha.weekday() >= 5:
        fecha += timedelta(days=1)
    return fecha

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
        fecha = proximo_laborable()
        dia = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes'][fecha.weekday()]
        response = self.client.post(reverse('crear_reserva', args=[self.equipo.id]), {
            'fecha_reserva': fecha.isoformat(),
            'bloque_horario': f'{dia} 08:00 - 10:00'
        })
        
        # Verificamos que la reserva se creó en la base de datos
        self.assertEqual(Reserva.objects.count(), 1)
        reserva = Reserva.objects.get()
        self.assertEqual(reserva.estado, 'confirmada')
        self.assertEqual(reserva.fecha_reserva, fecha)
        # El equipo sigue disponible hasta que el encargado confirme la entrega
        self.equipo.refresh_from_db()
        self.assertEqual(self.equipo.estado, 'disponible')

    def test_usuario_sancionado_no_puede_reservar(self):
        """Prueba que el sistema bloquea a un usuario con sanción (RF-04)."""
        self.client.login(username='infractor', password='password123')
        
        # Intentamos reservar
        fecha = proximo_laborable()
        dia = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes'][fecha.weekday()]
        response = self.client.post(reverse('crear_reserva', args=[self.equipo.id]), {
            'fecha_reserva': fecha.isoformat(),
            'bloque_horario': f'{dia} 08:00 - 10:00'
        })
        
        # Verificamos que NO se creó la reserva
        self.assertEqual(Reserva.objects.count(), 0)
        # Verificamos que el equipo sigue 'disponible'
        self.equipo.refresh_from_db()
        self.assertEqual(self.equipo.estado, 'disponible')


class CalendarioReservaTestCase(TestCase):
    def setUp(self):
        self.categoria = Categoria.objects.create(nombre="Proyectores")
        self.equipo = Equipo.objects.create(
            nombre="Proyector calendario",
            codigo="CAL-01",
            categoria=self.categoria,
            stock=2,
            estado="disponible",
        )
        self.usuario = Usuario.objects.create_user(
            username="calendario", password="pass12345", rol="solicitante"
        )

    def test_calendario_contiene_solo_dias_laborables_y_tres_bloques(self):
        calendario = calendario_reservas(self.equipo)
        for clave, info in calendario["dias"].items():
            fecha = date.fromisoformat(clave)
            self.assertLess(fecha.weekday(), 5)
            self.assertEqual(len(info["slots"]), 3)
            self.assertEqual(
                [slot["hora"] for slot in info["slots"]],
                [bloque.split(" ", 1)[1] for bloque in BLOQUES_POR_DIA[info["dia"]]],
            )

    def test_cupo_y_calendario_se_actualizan_con_reservas_confirmadas(self):
        fecha = proximo_laborable()
        bloque = f"{['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes'][fecha.weekday()]} 08:00 - 10:00"
        self.assertEqual(cupo_disponible(self.equipo, fecha, bloque), 2)

        Reserva.objects.create(
            usuario=self.usuario,
            equipo=self.equipo,
            fecha_reserva=fecha,
            bloque_horario=bloque,
            cantidad=2,
            estado="confirmada",
        )
        self.assertEqual(cupo_disponible(self.equipo, fecha, bloque), 0)
        calendario = calendario_reservas(self.equipo)
        slot = calendario["dias"][fecha.isoformat()]["slots"][0]
        self.assertEqual(slot["libres"], 0)
        self.assertFalse(slot["disponible"])

    def test_validacion_rechaza_fin_de_semana_y_fechas_pasadas(self):
        hoy = timezone.localdate()
        sabado = hoy + timedelta(days=(5 - hoy.weekday()) % 7)
        fecha, error = validar_fecha_reserva(self.equipo, sabado.isoformat())
        self.assertIsNone(fecha)
        self.assertIn("laborables", error)

        fecha, error = validar_fecha_reserva(self.equipo, (hoy - timedelta(days=1)).isoformat())
        self.assertIsNone(fecha)
        self.assertIn("pasadas", error)

    def test_get_crear_reserva_entrega_calendario_al_navegador(self):
        self.client.force_login(self.usuario)
        response = self.client.get(reverse("crear_reserva", args=[self.equipo.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "sl-calendario-data")
        self.assertContains(response, "slCalendarGrid")
        self.assertContains(response, "id_cantidad")