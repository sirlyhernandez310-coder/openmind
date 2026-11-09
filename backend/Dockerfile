# =========================
# 1) BUILDER STAGE
# Instala las librerías de Python (algunas necesitan compilarse)
# =========================
FROM python:3.13-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

COPY requirements.txt .
# Se instalan en una carpeta aparte para copiarlas limpias a la etapa final
RUN pip install --prefix=/install -r requirements.txt


# =========================
# 2) PRODUCTION STAGE
# Imagen final liviana: solo Python, las librerías ya instaladas y el código
# =========================
FROM python:3.13-slim AS production

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_DEBUG=False

WORKDIR /app

# Copiar las librerías desde el builder
COPY --from=builder /install /usr/local

# Copiar el código del backend
COPY . .

# Archivos estáticos (admin y Swagger) servidos con WhiteNoise
RUN python manage.py collectstatic --noinput

# Por seguridad la app no corre como administrador (root)
RUN useradd --create-home openmind && chown -R openmind /app
USER openmind

EXPOSE 8000

# Aplica migraciones y enciende el servidor de producción (gunicorn)
CMD ["sh", "-c", "python manage.py migrate --noinput && gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 2"]
