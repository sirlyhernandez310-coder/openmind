"""Fotos de perfil. Ejecutar: python manage.py test apps.accounts.test_avatars"""
from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from PIL import Image
from rest_framework.test import APITestCase

User = get_user_model()


def image_file(fmt="PNG", size=(900, 600), name="foto.png"):
    buffer = BytesIO()
    Image.new("RGB", size, (200, 150, 230)).save(buffer, format=fmt)
    return SimpleUploadedFile(name, buffer.getvalue(), content_type=f"image/{fmt.lower()}")


class AvatarTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="a@x.com", password="ClaveSegura#2026", first_name="Ana",
                                             last_name="Ríos", email_verified=True)
        self.client.force_authenticate(self.user)
        self.url = reverse("accounts:my-avatar")

    def test_subir_foto_la_recorta_y_comprime_en_webp(self):
        response = self.client.put(self.url, {"avatar": image_file()}, format="multipart")
        self.assertEqual(response.status_code, 200)
        avatar_url = response.data["avatar_url"]
        self.assertTrue(avatar_url.startswith("/api/auth/avatars/"))

        self.client.force_authenticate(None)  # la imagen se puede ver sin token (URL no adivinable)
        image_response = self.client.get(avatar_url)
        self.assertEqual(image_response["Content-Type"], "image/webp")
        image = Image.open(BytesIO(image_response.content))
        self.assertEqual(image.size, (400, 400))

    def test_cambiar_foto_cambia_la_url_y_quitar_la_borra(self):
        first = self.client.put(self.url, {"avatar": image_file()}, format="multipart").data["avatar_url"]
        second = self.client.put(self.url, {"avatar": image_file("JPEG", name="f.jpg")}, format="multipart").data["avatar_url"]
        self.assertNotEqual(first, second)
        self.assertEqual(self.client.get(first).status_code, 404)

        response = self.client.delete(self.url)
        self.assertIsNone(response.data["avatar_url"])
        self.assertEqual(self.client.get(second).status_code, 404)

    def test_archivo_invalido_o_vacio(self):
        fake = SimpleUploadedFile("x.png", b"no soy una imagen", content_type="image/png")
        self.assertEqual(self.client.put(self.url, {"avatar": fake}, format="multipart").status_code, 400)
        self.assertEqual(self.client.put(self.url, {}, format="multipart").status_code, 400)

    def test_formato_no_permitido(self):
        response = self.client.put(self.url, {"avatar": image_file("GIF", name="a.gif")}, format="multipart")
        self.assertEqual(response.status_code, 400)
        self.assertIn("JPG, PNG o WEBP", str(response.data["avatar"]))

    def test_foto_muy_pesada(self):
        from unittest import mock

        with mock.patch("apps.accounts.avatars.MAX_UPLOAD_MB", 0):
            response = self.client.put(self.url, {"avatar": image_file()}, format="multipart")
        self.assertIn("no puede pesar", str(response.data["avatar"]))

    def test_requiere_sesion(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.put(self.url, {"avatar": image_file()}, format="multipart").status_code, 401)
