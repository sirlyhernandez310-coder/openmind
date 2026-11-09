# OpenMind · Frontend

React 19 + Vite + React Router. Se comunica con la API usando JWT (Bearer token).

## Estructura

```
src/
├── api/            # cliente HTTP (refresca el token solo) y llamadas de auth
├── components/     # AuthLayout, FormField, Blob, ProtectedRoute, AppLayout…
├── constants/      # roles y la ruta de inicio de cada rol
├── context/        # AuthContext: sesión del usuario
├── pages/
│   ├── LoginPage, RegisterPage, ForgotPasswordPage, ResetPasswordPage
│   ├── paciente/   # interfaz del paciente
│   ├── psicologo/  # interfaz del psicólogo
│   └── admin/      # interfaz del administrador
└── index.css       # sistema de diseño OpenMind
```

## Ejecutar

```powershell
copy .env.example .env     # VITE_API_URL=http://localhost:8000/api
npm install
npm run dev                # http://localhost:5173
```

## Rutas

| Ruta | Quién |
|---|---|
| `/login`, `/registro` | Público |
| `/recuperar-contrasena`, `/restablecer-contrasena?uid=…&token=…` | Público |
| `/registro-profesional` | Público |
| `/paciente`, `/paciente/evaluacion`, `/paciente/historial`, `/paciente/historial/:id`, `/paciente/emergencia` | Solo pacientes |
| `/psicologo`, `/psicologo/emergencias`, `/psicologo/perfil` | Solo psicólogos |
| `/admin`, `/admin/profesionales` | Solo administradores |

Si alguien entra a una ruta que no es de su rol, se le envía a su propio panel con un aviso.

## Despliegue en Vercel

1. Importa el repositorio y elige `frontend` como *Root Directory*.
2. Variable de entorno: `VITE_API_URL=https://openmind-api.onrender.com/api`
3. `vercel.json` ya redirige todas las rutas a `index.html` para que funcionen al recargar.
