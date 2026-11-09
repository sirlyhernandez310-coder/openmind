# OpenMind · Backend (API REST)

Django + Django REST Framework + JWT (SimpleJWT) + Swagger (drf-spectacular).

## Estructura

```
backend/
├── config/                 # configuración del proyecto (settings, urls)
├── apps/
│   ├── accounts/           # usuarios, roles, login, registro y recuperación (Sprint 1)
│   ├── evaluations/        # evaluación emocional e historial (Sprint 2)
│   │   └── scoring.py      # cómo se calcula el resultado
│   ├── professionals/      # registro y verificación de psicólogos (Sprint 2)
│   └── emergency/          # chat de emergencia (Sprint 2)
├── .env.example
├── Dockerfile
├── build.sh                # build para Render
└── requirements.txt
```

## Ejecutar en local (Windows)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py seed_users
python manage.py runserver
```

- Portada: http://localhost:8000
- Swagger: http://localhost:8000/api/docs/
- Admin: http://localhost:8000/admin/

### Probar endpoints protegidos en Swagger

1. Ejecuta `POST /api/auth/login/` con un usuario de prueba.
2. Copia el valor de `access`.
3. Pulsa **Authorize** y pégalo. Swagger lo enviará como `Bearer <token>`.

## Pruebas

```powershell
python manage.py test
coverage run manage.py test
coverage report        # en consola
coverage html          # reporte navegable en htmlcov/index.html
```

## Correos: verificación de cuenta y recuperación de contraseña

Los dos correos usan la misma configuración. Hay tres modos según `EMAIL_BACKEND`:

| Modo | Dónde usarlo | Configuración |
|---|---|---|
| Consola (por defecto) | Desarrollo | Nada: el enlace sale en la terminal con 🔑 |
| Gmail (SMTP) | Tu PC | Ver abajo |
| Brevo (API HTTP) | Render gratis (bloquea SMTP) | `EMAIL_BACKEND=apps.accounts.email_backends.BrevoEmailBackend` y `BREVO_API_KEY` |

### Correo real (Gmail)

1. Activa la verificación en dos pasos en tu cuenta de Google.
2. Crea una **contraseña de aplicación** en https://myaccount.google.com/apppasswords
3. En `backend/.env`:

```
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=tucorreo@gmail.com
EMAIL_HOST_PASSWORD=la-contraseña-de-aplicación
DEFAULT_FROM_EMAIL=OpenMind <tucorreo@gmail.com>
```

Si el correo no se puede enviar, la API responde `503` con un mensaje claro y el error queda en la terminal.

## Despliegue en Render

1. Crea una base de datos **PostgreSQL** en Render y copia su *Internal Database URL*.
2. Crea un **Web Service** apuntando a tu repositorio, con *Root Directory* `backend`.
   - Build Command: `./build.sh`
   - Start Command: `gunicorn config.wsgi:application`
3. Variables de entorno:

| Variable | Ejemplo |
|---|---|
| `DJANGO_SECRET_KEY` | una clave larga y aleatoria |
| `DJANGO_DEBUG` | `False` |
| `DJANGO_ALLOWED_HOSTS` | `openmind-api.onrender.com` |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | `https://openmind-api.onrender.com` |
| `DATABASE_URL` | la URL de PostgreSQL |
| `CORS_ALLOWED_ORIGINS` | `https://openmind.vercel.app` |
| `FRONTEND_URL` | `https://openmind.vercel.app` |
| `EMAIL_*` | los datos de Gmail de arriba |

4. Para crear el administrador en producción usa la *Shell* de Render: `python manage.py createsuperuser`.

## Docker

```bash
docker build -t openmind-api .
docker run -p 8000:8000 --env-file .env openmind-api
```

## Preguntas de la evaluación

Las 12 preguntas se crean con la migración `evaluations/0002_seed_questions.py` y el administrador puede
editarlas o desactivarlas en `/admin/` → *Preguntas*. La escala y los niveles están en `evaluations/models.py`
y `evaluations/scoring.py`.

## Líneas de atención del chat

Por defecto se muestran la Línea 106 (nacional), la Línea Amiga Saludable de Medellín y el 123
(`emergency/service_info.py`). Puedes cambiarlas definiendo `EMERGENCY_LINES` en `settings.py`.

## Correos en Render con Brevo (gratis)

Render, en su plan gratis, bloquea los puertos SMTP (25, 465 y 587), así que Gmail no funciona allá.
Brevo envía por HTTPS y su plan gratis permite 300 correos al día.

1. Crea una cuenta gratis en https://www.brevo.com.
2. En **Senders, domains & dedicated IPs → Senders**, agrega y verifica el correo remitente (puede ser tu Gmail).
3. En **SMTP & API → API keys**, crea una API key y cópiala.
4. En las variables de entorno de Render (o en tu `.env`):

```
EMAIL_BACKEND=apps.accounts.email_backends.BrevoEmailBackend
BREVO_API_KEY=xkeysib-...
DEFAULT_FROM_EMAIL=OpenMind <el-correo-que-verificaste@gmail.com>
```
