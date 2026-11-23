from datetime import date, timedelta
from io import BytesIO
from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from loans.calendar_utils import DIAS_LABORABLES
from loans.models import Prestamo, ReporteIncidente, Reserva
from .forms import EquipoForm
from .models import Categoria, Equipo
from .utils import BLOQUES_HORARIOS, calcular_disponibilidad, formatear_rango, resumen_inventario

Usuario = get_user_model()


def proximo_laborable():
    fecha = date.today() + timedelta(days=1)
    while fecha.weekday() >= 5:
        fecha += timedelta(days=1)
    return fecha


def bloque_de_fecha(fecha):
    return f"{DIAS_LABORABLES[fecha.weekday()]} 08:00 - 10:00"


def crear_imagen():
    buffer = BytesIO()
    Image.new("RGB", (40, 40), "#e30513").save(buffer, format="PNG")
    return SimpleUploadedFile("prueba.png", buffer.getvalue(), content_type="image/png")


class InventarioTestCase(TestCase):
    def setUp(self):
        self.categoria = Categoria.objects.create(nombre="Notebooks")
        self.admin = Usuario.objects.create_user(
            username="admin_test", password="pass12345", rol="administrador"
        )
        self.encargado = Usuario.objects.create_user(
            username="encargado_test", password="pass12345", rol="encargado"
        )
        self.estudiante = Usuario.objects.create_user(
            username="alumno_test", password="pass12345", rol="solicitante", email="alumno@test.cl"
        )
        hoy = date.today()
        self.equipo = Equipo.objects.create(
            nombre="Laptop de prueba",
            codigo="TEST-01",
            categoria=self.categoria,
            stock=3,
            estado="disponible",
            disponible_desde=hoy - timedelta(days=2),
            disponible_hasta=hoy + timedelta(days=10),
        )

    def test_formatear_rango_con_fechas_y_sin_fechas(self):
        self.assertEqual(
            formatear_rango(self.equipo),
            f"{self.equipo.disponible_desde.strftime('%d/%m')} – {self.equipo.disponible_hasta.strftime('%d/%m/%Y')}",
        )
        self.equipo.disponible_desde = None
        self.equipo.disponible_hasta = None
        self.assertEqual(formatear_rango(self.equipo), "Sin fecha definida")

    def test_resumen_inventario_calcula_stock_y_estados(self):
        Equipo.objects.create(
            nombre="Equipo mantenimiento",
            codigo="TEST-MANT",
            categoria=self.categoria,
            stock=5,
            estado="mantenimiento",
        )
        resumen = resumen_inventario(Equipo.objects.all())
        self.assertEqual(resumen["total_equipos"], 2)
        self.assertEqual(resumen["stock_total"], 8)
        self.assertEqual(resumen["equipos_disponibles"], 1)
        self.assertEqual(resumen["equipos_mantenimiento"], 1)

    def test_disponibilidad_descuenta_reservas_confirmadas(self):
        Reserva.objects.create(
            usuario=self.estudiante,
            equipo=self.equipo,
            bloque_horario=BLOQUES_HORARIOS[0],
            cantidad=2,
            estado="confirmada",
        )
        Reserva.objects.create(
            usuario=self.estudiante,
            equipo=self.equipo,
            bloque_horario=BLOQUES_HORARIOS[1],
            cantidad=3,
            estado="pendiente",
        )
        disponibilidad = calcular_disponibilidad(Equipo.objects.filter(id=self.equipo.id))
        datos = disponibilidad[self.equipo.id]
        self.assertEqual(datos["bloques"][0]["libres"], 1)
        self.assertEqual(datos["bloques"][1]["libres"], 3)
        self.assertEqual(datos["bloques_libres"], 15)
        self.assertEqual(datos["total_bloques"], 15)

    def test_catalogo_y_gestion_muestran_stock_y_fechas(self):
        self.client.force_login(self.estudiante)
        response = self.client.get(reverse("catalogo"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "unidades en el pañol")
        self.assertContains(response, "bloques libres")
        self.assertContains(response, self.equipo.disponible_hasta.strftime("%d/%m/%Y"))

        self.client.force_login(self.encargado)
        response = self.client.get(reverse("gestion_inventario"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Stock total")
        self.assertContains(response, "Disponibilidad")
        self.assertContains(response, self.equipo.codigo)

    def test_crear_equipo_guarda_imagen_y_fechas(self):
        with TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                self.client.force_login(self.admin)
                response = self.client.post(
                    reverse("crear_equipo"),
                    {
                        "nombre": "Nuevo equipo",
                        "codigo": "TEST-02",
                        "categoria": self.categoria.id,
                        "estado": "disponible",
                        "stock": 2,
                        "imagen": crear_imagen(),
                        "disponible_desde": (date.today() + timedelta(days=1)).isoformat(),
                        "disponible_hasta": (date.today() + timedelta(days=5)).isoformat(),
                    },
                )
                self.assertEqual(response.status_code, 302)
                equipo = Equipo.objects.get(codigo="TEST-02")
                self.assertTrue(equipo.imagen.name.startswith("equipos/"))
                self.assertEqual(equipo.disponible_desde, date.today() + timedelta(days=1))

    def test_formulario_acepta_campos_de_fecha(self):
        form = EquipoForm(data={
            "nombre": "Con fechas",
            "codigo": "TEST-03",
            "categoria": self.categoria.id,
            "estado": "disponible",
            "stock": 1,
            "disponible_desde": "2026-11-20",
            "disponible_hasta": "2026-12-20",
        })
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["disponible_desde"], date(2026, 11, 20))


class FlujoPrestamoTestCase(TestCase):
    def setUp(self):
        categoria = Categoria.objects.create(nombre="Tablets")
        self.equipo = Equipo.objects.create(
            nombre="Tablet flujo",
            codigo="FLU-01",
            categoria=categoria,
            stock=2,
            estado="disponible",
        )
        self.encargado = Usuario.objects.create_user(
            username="encargado_flujo", password="pass12345", rol="encargado"
        )
        self.estudiante = Usuario.objects.create_user(
            username="alumno_flujo",
            password="pass12345",
            rol="solicitante",
            email="flujo@test.cl",
        )

    def test_flujo_reserva_entrega_devolucion_y_reporte(self):
        fecha = proximo_laborable()
        bloque = bloque_de_fecha(fecha)
        self.client.force_login(self.estudiante)
        response = self.client.post(
            reverse("crear_reserva", args=[self.equipo.id]),
            {"fecha_reserva": fecha.isoformat(), "bloque_horario": bloque, "cantidad": 2},
        )
        self.assertEqual(response.status_code, 302)
        reserva = Reserva.objects.get()
        self.assertEqual(reserva.estado, "confirmada")
        self.assertEqual(reserva.fecha_reserva, fecha)

        # No se puede exceder el stock del bloque
        self.client.force_login(self.estudiante)
        response = self.client.post(
            reverse("crear_reserva", args=[self.equipo.id]),
            {"fecha_reserva": fecha.isoformat(), "bloque_horario": bloque, "cantidad": 1},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Reserva.objects.count(), 1)

        self.client.force_login(self.encargado)
        response = self.client.get(reverse("confirmar_entrega", args=[reserva.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Confirmar entrega")

        response = self.client.post(reverse("confirmar_entrega", args=[reserva.id]))
        self.assertEqual(response.status_code, 302)
        self.equipo.refresh_from_db()
        reserva.refresh_from_db()
        self.assertEqual(self.equipo.estado, "prestado")
        self.assertEqual(reserva.estado, "confirmada")
        self.assertEqual(Prestamo.objects.count(), 1)

        prestamo = Prestamo.objects.get()
        # La devolución por parte del alumno usa la ruta devolver_mi_equipo.
        self.client.force_login(self.estudiante)
        response = self.client.post(
            reverse("devolver_mi_equipo", args=[prestamo.id]),
            {"estado_equipo": "operativo"},
        )
        self.assertEqual(response.status_code, 302)
        self.client.force_login(self.encargado)
        prestamo.refresh_from_db()
        self.equipo.refresh_from_db()
        self.assertIsNotNone(prestamo.fecha_devolucion_real)
        self.assertEqual(self.equipo.estado, "disponible")

        response = self.client.post(
            reverse("reportar_incidente", args=[prestamo.id]),
            {
                "tipo": "dano",
                "descripcion": "Pantalla rayada",
                "aplicar_bloqueo": "on",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(ReporteIncidente.objects.count(), 1)
        self.estudiante.refresh_from_db()
        self.assertTrue(self.estudiante.tiene_sancion_activa)

    def test_panel_encargado_y_reportes_renderizan(self):
        self.client.force_login(self.encargado)
        for nombre in ["panel_encargado", "dispositivos_prestados", "registro_reportes"]:
            response = self.client.get(reverse(nombre))
            self.assertEqual(response.status_code, 200, nombre)

    def test_usuario_sancionado_no_puede_reservar(self):
        self.estudiante.tiene_sancion_activa = True
        self.estudiante.fecha_fin_sancion = timezone.now() + timedelta(days=10)
        self.estudiante.save()
        self.client.force_login(self.estudiante)
        fecha = proximo_laborable()
        response = self.client.post(
            reverse("crear_reserva", args=[self.equipo.id]),
            {"fecha_reserva": fecha.isoformat(), "bloque_horario": bloque_de_fecha(fecha)},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Reserva.objects.count(), 0)


class HealthEndpointTests(TestCase):
    def test_health_responde_sin_autenticacion(self):
        for path in ("/health", "/health/"):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json(), {"status": "ok"})
