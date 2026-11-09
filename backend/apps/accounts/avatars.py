"""Procesa la foto de perfil: valida, recorta al centro en cuadrado y comprime a WebP."""
from io import BytesIO

from PIL import Image, ImageOps, UnidentifiedImageError
from rest_framework import serializers

MAX_UPLOAD_MB = 5
SIZE = 400
ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}


def process_avatar(uploaded_file):
    if uploaded_file.size > MAX_UPLOAD_MB * 1024 * 1024:
        raise serializers.ValidationError(f"La foto no puede pesar más de {MAX_UPLOAD_MB} MB.")
    try:
        image = Image.open(uploaded_file)
        image_format = image.format
        image.load()
    except (UnidentifiedImageError, OSError):
        raise serializers.ValidationError("El archivo no es una imagen válida.")
    if image_format not in ALLOWED_FORMATS:
        raise serializers.ValidationError("Sube una imagen JPG, PNG o WEBP.")

    image = ImageOps.exif_transpose(image)  # respeta la orientación de las fotos del celular
    image = ImageOps.fit(image.convert("RGB"), (SIZE, SIZE), Image.Resampling.LANCZOS)
    output = BytesIO()
    image.save(output, format="WEBP", quality=82, method=6)
    return output.getvalue()
