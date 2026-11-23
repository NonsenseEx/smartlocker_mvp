from io import BytesIO
from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

Usuario = get_user_model()


def crear_imagen():
    buffer = BytesIO()
    Image.new("RGB", (40, 40), "#e30513").save(buffer, format="PNG")
    return SimpleUploadedFile("perfil.png", buffer.getvalue(), content_type="image/png")


class PerfilTestCase(TestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            username="perfil_test", password="pass12345", rol="solicitante"
        )

    def test_perfil_acepta_foto_opcional(self):
        self.client.force_login(self.usuario)
        response = self.client.get(reverse("editar_perfil"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "enctype=\"multipart/form-data\"")
        self.assertContains(response, "foto_perfil")

    def test_guardar_foto_de_perfil(self):
        with TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                self.client.force_login(self.usuario)
                response = self.client.post(
                    reverse("editar_perfil"),
                    {
                        "first_name": "Ana",
                        "last_name": "Pérez",
                        "email": "ana@test.cl",
                        "foto_perfil": crear_imagen(),
                    },
                )
                self.assertEqual(response.status_code, 302)
                self.usuario.refresh_from_db()
                self.assertTrue(self.usuario.foto_perfil.name.startswith("perfiles/"))

                response = self.client.get(reverse("editar_perfil"))
                self.assertContains(response, self.usuario.foto_perfil.url)

    def test_foto_no_es_obligatoria(self):
        self.client.force_login(self.usuario)
        response = self.client.post(
            reverse("editar_perfil"),
            {
                "first_name": "Solo",
                "last_name": "Nombre",
                "email": "solo@test.cl",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.usuario.refresh_from_db()
        self.assertFalse(self.usuario.foto_perfil)
