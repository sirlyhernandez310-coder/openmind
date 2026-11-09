# OpenMind 🫧

Plataforma de **psicología y gestión emocional** — Proyecto final de Ingeniería de Software II, I.U. Pascual Bravo.

| Carpeta     | Qué es                                                        | Tecnología                          |
|-------------|---------------------------------------------------------------|-------------------------------------|
| `backend/`  | API REST: usuarios, roles, autenticación, recuperación        | Python · Django · DRF · JWT · Swagger |
| `frontend/` | Aplicación web para pacientes, psicólogos y administradores   | React · Vite · React Router         |

Base de datos: **SQLite** en desarrollo y **PostgreSQL** en producción (solo cambia la variable `DATABASE_URL`).

---

## 🚀 Cómo ejecutarlo en Windows (paso a paso)

Necesitas tener instalado **Python 3.12 o superior** y **Node.js 20.19 o superior**.
Puedes comprobarlo en una terminal con `python --version` y `node --version`.

### 1. Backend (Terminal 1)

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1          # en CMD: .venv\Scripts\activate.bat
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py seed_users         # usuarios de prueba por rol + historial de ejemplo
python manage.py runserver
```

> Si PowerShell no deja activar el entorno, ejecuta una sola vez:
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

Abre **http://localhost:8000** → portada de la API · **http://localhost:8000/api/docs/** → Swagger.

### 2. Frontend (Terminal 2)

```powershell
cd frontend
copy .env.example .env
npm install
npm run dev
```

Abre **http://localhost:5173**.

### 3. Usuarios de prueba

| Rol           | Correo                    | Contraseña      |
|---------------|---------------------------|-----------------|
| Paciente      | `paciente@openmind.com`   | `OpenMind#2026` |
| Psicólogo     | `psicologo@openmind.com`  | `OpenMind#2026` |
| Administrador | `admin@openmind.com`      | `OpenMind#2026` |
| Psicóloga (extra) | `lucia@openmind.com`  | `OpenMind#2026` |
| Psicólogo (extra) | `camilo@openmind.com` | `OpenMind#2026` |

El administrador también puede entrar a **http://localhost:8000/admin/**.
Los psicólogos de prueba ya están **verificados** y tienen un **horario semanal de atención** para poder reservar citas. La paciente tiene 4 evaluaciones de ejemplo para ver la gráfica del historial.

> Si ya tenías la base de datos de un sprint anterior, solo corre `python manage.py migrate` y `python manage.py seed_users` otra vez.

### 4. Probar los correos sin configurar nada

En desarrollo los correos (**verificación de cuenta** y **recuperación de contraseña**) **no se envían de verdad**:
se imprimen en la Terminal 1 (la del backend). Busca la línea que empieza con `🔑 ENLACE DE VERIFICACIÓN` o
`🔑 ENLACE DE RECUPERACIÓN`, cópiala y ábrela en el navegador. Para enviar correos reales mira [backend/README.md](backend/README.md#correo-real-gmail).

### 5. Correr las pruebas

```powershell
cd backend
python manage.py test                          # 134 pruebas (Sprints 1, 2 y 3)
coverage run manage.py test; coverage report   # cobertura (99 %)
```

---

## ✅ Sprint 1 · Gestión de usuarios

### OM3-9 · Registro de usuario (5 pts)

| Criterio | Cómo se cumple | Prueba |
|---|---|---|
| CA1 Ingresar datos requeridos | Formulario con nombres, apellidos, correo, contraseña y confirmación (teléfono y fecha de nacimiento opcionales) → `POST /api/auth/register/` | `test_ca1_ca5_registro_exitoso…` |
| CA2 Validar obligatorios | Validación en el frontend y en la API: *"Este campo es obligatorio."* | `test_ca2_campos_obligatorios_vacios`, `test_ca2_campos_en_blanco` |
| CA3 Formato de correo | Regex en el frontend + `EmailField` en la API | `test_ca3_correo_con_formato_invalido` |
| CA4 Correo ya registrado | Búsqueda sin distinguir mayúsculas; mensaje y enlace a iniciar sesión | `test_ca4_correo_ya_registrado…` |
| CA5 Acceder tras registrarse | Se envía un correo de verificación; al abrir el enlace la cuenta se activa y el usuario entra directo a su panel | `test_ca5_al_confirmar_el_correo_accede…` |
| Extra · Verificación de correo | Sin confirmar el correo no se puede iniciar sesión (403 `email_not_verified`); se puede reenviar el enlace. Si el correo no se puede enviar, la cuenta no se crea | `EmailVerificationTests`, `test_si_el_correo_no_se_puede_enviar…` |

### OM3-10 · Inicio de sesión (8 pts)

| Criterio | Cómo se cumple | Prueba |
|---|---|---|
| CA1 Ingresar correo y contraseña | Formulario de login → `POST /api/auth/login/` | `test_ca1_correo_y_contrasena_son_obligatorios` |
| CA2 Validar credenciales | Django `authenticate` contra la contraseña encriptada (PBKDF2) | `test_ca2_ca3_credenciales_correctas…` |
| CA3 Permitir acceso | Tokens JWT `access` + `refresh` (Bearer) | `test_ca2_ca3_credenciales_correctas…` |
| CA4 Mensaje de error | *"Correo o contraseña incorrectos."* (401) | `test_ca4_contrasena_incorrecta…`, `test_ca4_correo_inexistente…` |
| CA5 Interfaz según el rol | El rol viaja en la respuesta y en el token; el frontend redirige a `/paciente`, `/psicologo` o `/admin` y bloquea las rutas de otros roles | `test_ca5_identifica_el_tipo_de_usuario`, `test_control_de_roles…` |

### OM3-11 · Recuperación de contraseña (13 pts)

| Criterio | Cómo se cumple | Prueba |
|---|---|---|
| Solicitar con el correo | Pantalla *¿Olvidaste tu contraseña?* → `POST /api/auth/password-reset/` | `test_ca1_ca3_solicitud_envia_correo…` |
| Verificar que esté registrado | Si no existe responde 404: *"No encontramos una cuenta registrada con este correo."* | `test_ca2_correo_no_registrado` |
| Recibir instrucciones | Correo HTML con botón y enlace seguro que vence en 1 hora | `test_ca1_ca3_solicitud_envia_correo…` |
| Establecer nueva contraseña | Pantalla *Crea una nueva contraseña* → `POST /api/auth/password-reset/confirm/`; el enlace queda inválido después de usarse | `test_ca4_establece_nueva_contrasena…`, `test_el_enlace_solo_sirve_una_vez` |

**Extras de seguridad:** contraseñas encriptadas, validación de contraseñas débiles, límite de intentos
(10 logins/min y 5 solicitudes de recuperación/min), refresh token con lista negra al cerrar sesión.

## ✅ Sprint 2 · Bienestar emocional

### OM3-12 · Realizar evaluación emocional

| Criterio | Cómo se cumple | Prueba |
|---|---|---|
| CA1 Iniciar evaluación | Pantalla de inicio con duración y botón *Iniciar evaluación* | `test_ca1_ca2_iniciar_muestra_preguntas…` |
| CA2 Mostrar preguntas | `GET /api/evaluations/questions/`: 12 preguntas de 4 dimensiones (ánimo, ansiedad, estrés, sueño y energía) con escala 0-3, una por pantalla con barra de progreso | `test_ca1_ca2_iniciar_muestra_preguntas…` |
| CA3 Responder las requeridas | No deja avanzar sin responder; la API rechaza respuestas incompletas, repetidas o fuera de rango | `test_ca3_debe_responder_todas…`, `test_respuesta_fuera_de_rango` |
| CA4 Procesar respuestas | `scoring.py`: puntaje total y por dimensión, porcentaje y nivel (estable, leve, moderado, alto). Una pregunta de alerta activa la recomendación de apoyo | `test_ca4_ca5_procesa…`, `test_pregunta_de_alerta…` |
| CA5 Mostrar resultado | Nivel, índice de malestar, barras por dimensión, recomendaciones y acceso al chat si se necesita apoyo | `test_ca4_ca5_procesa…`, `test_malestar_alto_recomienda_apoyo` |

### OM3-13 · Consultar historial emocional

| Criterio | Cómo se cumple | Prueba |
|---|---|---|
| CA1 Acceder al historial | Menú *Mi historial* → `GET /api/evaluations/` | `test_ca1_ca2_ca3_muestra_evaluaciones…` |
| CA2 Evaluaciones anteriores | Lista de la más reciente a la más antigua + gráfica de evolución | `test_ca1_ca2_ca3_muestra_evaluaciones…` |
| CA3 Fecha de cada registro | Fecha y hora en cada fila y en el eje de la gráfica | `test_ca1_ca2_ca3_muestra_evaluaciones…` |
| CA4 Resultado de cada una | Cada fila abre su resultado completo con las respuestas dadas | `test_ca4_consultar_resultado…` |
| CA5 Solo para su usuario | La consulta siempre filtra por el usuario del token; otro usuario recibe 404; psicólogos y admin, 403 | `test_ca5_historial_solo_del_usuario…`, `test_ca5_admin_y_psicologo…` |

### OM3-21 · Registro profesional

| Criterio | Cómo se cumple | Prueba |
|---|---|---|
| CA1 Datos profesionales | Formulario `/registro-profesional` → `POST /api/professionals/register/` crea el usuario PSICOLOGO y su perfil en una sola transacción | `test_ca1_a_ca5_registro_completo` |
| CA2 Especialidad | Lista de 8 especialidades | `test_ca2_especialidad_invalida` |
| CA3 Experiencia | Años (0-60) y texto opcional de experiencia | `test_ca3_experiencia_invalida` |
| CA4 Licencia profesional | Tarjeta profesional única, normalizada en mayúsculas | `test_ca4_licencia_duplicada_o_invalida` |
| CA5 Descripción | Mínimo 30 y máximo 1000 caracteres | `test_ca5_descripcion_muy_corta` |

**Regla de negocio:** el perfil queda *pendiente de verificación*. El administrador lo revisa en **Profesionales** y lo verifica; solo los psicólogos verificados atienden emergencias.

### OM3-19 · Chat de emergencia

| Criterio | Cómo se cumple | Prueba |
|---|---|---|
| CA1 Acceder desde la plataforma | Menú *Chat de emergencia*, botón en el inicio y en resultados con malestar alto | `test_ca1_paciente_inicia_el_chat…` |
| CA2 Enviar mensajes | `POST /api/emergency/chats/{id}/messages/` (Enter para enviar) | `test_ca2_ca3_enviar_y_ver_mensajes` |
| CA3 Mensajes enviados y recibidos | Burbujas propias y del psicólogo; se actualiza cada 3 s | `test_psicologo_ve_la_fila_toma_el_chat_y_responde` |
| CA4 Asociada al usuario | Cada chat pertenece a un paciente; solo él y el psicólogo que lo toma lo ven | `test_ca4_conversacion_asociada…`, `test_otro_psicologo_no_puede_tomar…` |
| CA5 Información del servicio | Panel con cómo funciona, privacidad, líneas 106, Línea Amiga de Medellín y 123, y aviso de que no reemplaza urgencias | `test_ca5_informacion_clara_del_servicio` |

**Flujo:** el paciente abre el chat → queda *Esperando psicólogo* → un psicólogo verificado lo ve en su **Fila de atención** y pulsa *Atender* → conversan → cualquiera de los dos lo finaliza.
El chat usa consultas periódicas (polling) cada 3 segundos, que funcionan en cualquier hosting gratuito sin servicios extra.

---

## ✅ Sprint 3 · Citas con psicólogos

Nueva app `backend/apps/appointments`. Cada psicólogo define su **horario semanal** (por ejemplo lunes de 8:00 a 12:00).
Con ese horario el sistema arma los espacios de **1 hora** de los próximos **14 días**. Quita los que ya pasaron, los que empiezan en menos de 1 hora y los que ya están reservados.
Una restricción única en la base de datos impide que dos personas reserven el mismo horario, aunque lo intenten al mismo tiempo.

### OM3-14 · Buscar psicólogos

| Criterio | Cómo se cumple | Prueba |
|---|---|---|
| CA1 Acceder al listado | Menú *Psicólogos* → `GET /api/professionals/directory/` | `test_om3_14_listado_muestra_solo_profesionales…` |
| CA2 Profesionales disponibles | Solo aparecen psicólogos **verificados y activos**, con su *próximo horario libre* | ídem |
| CA3 Información básica | Foto, nombre, especialidad, años de experiencia y mini descripción. Buscador por nombre o especialidad (`?q=`) | `test_om3_14_buscar_por_nombre_o_especialidad` |
| CA4 Coincide con el perfil | Se lee directamente del perfil profesional registrado | `test_om3_14_la_info_corresponde_al_perfil_registrado` |

### OM3-15 · Consultar perfil del psicólogo

| Criterio | Cómo se cumple | Prueba |
|---|---|---|
| CA1 Seleccionar psicólogo | Clic en la tarjeta → `/paciente/psicologos/{id}` | `test_om3_15_perfil_muestra…` |
| CA2 Especialidad | Etiqueta y fila *Especialidad* | ídem |
| CA3 Experiencia | Años de experiencia y texto de experiencia | ídem |
| CA4 Información profesional | Universidad, tarjeta verificada, descripción y próximo horario | ídem; `test_om3_15_perfil_de_psicologo_no_verificado_no_existe` |
| CA5 Opción de reservar | Botón **Reservar sesión** en el perfil | prueba en navegador |

### OM3-16 · Consultar disponibilidad

| Criterio | Cómo se cumple | Prueba |
|---|---|---|
| CA1 Consultar horarios | `GET /api/appointments/psychologists/{id}/slots/` agrupados por día | `test_ca1_ca2_muestra_solo_horarios_futuros_y_libres` |
| CA2 Solo horarios disponibles | No se envían horarios pasados ni reservados | ídem, `test_parametros_from_y_days` |
| CA3 Ocupados no seleccionables | No aparecen en pantalla y el backend rechaza reservarlos | `test_ca3_un_horario_ocupado_no_se_puede_seleccionar` |
| CA4 Seleccionar horario | Pestañas por día + botones de hora | prueba en navegador |

### OM3-17 · Reservar cita

| Criterio | Cómo se cumple | Prueba |
|---|---|---|
| CA1 Seleccionar psicólogo | Desde el perfil | `test_ca1_ca2_psicologo_y_horario_obligatorios` |
| CA2 Fecha y hora disponibles | Paso 1 día, paso 2 hora | ídem, `test_horario_fuera_de_la_agenda_o_en_el_pasado` |
| CA3 Confirmación | Pantalla *¡Tu sesión quedó agendada!* | `test_ca1_a_ca5_reserva_confirmada…` |
| CA4 Cita registrada | `POST /api/appointments/` crea la cita *Programada* | ídem |
| CA5 Deja de estar disponible | El horario desaparece de la lista. Si dos personas reservan a la vez, solo una lo logra | ídem, `test_dos_reservas_simultaneas_solo_pasa_una` |

### OM3-18 · Consultar mis sesiones

| Criterio | Cómo se cumple | Prueba |
|---|---|---|
| CA1 Acceder a sesiones | Menú *Mis sesiones* y tarjeta *Tu próxima sesión* en el inicio | `test_ca1_a_ca4_ve_sus_citas…` |
| CA2 Citas programadas | Pestañas *Próximas* y *Pasadas* (`?scope=upcoming\|past\|all`) | `test_citas_pasadas_y_canceladas_van_al_historial` |
| CA3 Fecha y hora | Día, fecha y rango de hora | `test_ca1_a_ca4_ve_sus_citas…` |
| CA4 Identificar al psicólogo | Foto, nombre y especialidad | ídem; `test_cada_paciente_ve_solo_sus_citas` |

**Lado del psicólogo:** en *Agenda* (`/psicologo/agenda`) ve sus próximas sesiones (solo consulta) y edita su horario semanal. Cancelar o marcar como realizada queda para *OM3-23 Gestionar sesiones* (Sprint 4).

---

## 🎨 Identidad visual (Sprint 2.5)

- **Logo:** isotipo de medio cerebro + medio corazón unidos por una línea, con "Open Mind" en **Kaushan Script**.
- **Tipografías:** Montserrat (textos) y Kaushan Script (solo logo). Ambas con licencia libre OFL e incluidas en el proyecto (`@fontsource`), así funcionan sin internet y en producción.
- **Colores:** lila `#D6B4EC` con líneas en bucle `#E3CAF3`, textos ciruela `#4A1858`, acentos sol, menta y coral.
- **Personajes:** nubes de emociones (Alegría, Calma, Ansiedad, Tristeza, Enojo) en `frontend/src/components/Blob.jsx`. El resultado de la evaluación muestra la nube que corresponde.
- **Logo animado** al abrir la app (una vez por sesión) e ilustración cerebro-corazón en las pantallas de acceso.

### Fotos de perfil y directorio de psicólogos

| Método | Ruta | Acceso | Descripción |
|---|---|---|---|
| PUT | `/api/auth/me/avatar/` | JWT | Subir o cambiar la foto (multipart, campo `avatar`; JPG, PNG o WEBP, máx. 5 MB) |
| DELETE | `/api/auth/me/avatar/` | JWT | Quitar la foto |
| GET | `/api/auth/avatars/{clave}/` | Público | La imagen (WebP 400×400). La clave es aleatoria y cambia con cada foto |
| GET | `/api/professionals/directory/` | JWT | Psicólogos verificados con foto, especialidad y mini descripción |
| GET | `/api/professionals/directory/{id}/` | JWT | Perfil de un psicólogo |

Las fotos se recortan y comprimen y se guardan **dentro de la base de datos**, para que no se pierdan en hostings con disco temporal como Render.

## 🔌 Endpoints

| Método | Ruta | Acceso | Descripción |
|---|---|---|---|
| POST | `/api/auth/register/` | Público | Registro de paciente |
| POST | `/api/auth/login/` | Público | Inicio de sesión |
| POST | `/api/auth/refresh/` | Público | Renovar token |
| POST | `/api/auth/logout/` | JWT | Cerrar sesión |
| GET  | `/api/auth/me/` | JWT | Perfil propio |
| GET  | `/api/auth/users/` | Administrador | Lista de usuarios (`?role=PACIENTE`) |
| POST | `/api/auth/verify-email/` | Público | Confirmar correo (devuelve la sesión) |
| POST | `/api/auth/verify-email/resend/` | Público | Reenviar enlace de confirmación |
| POST | `/api/auth/password-reset/` | Público | Solicitar recuperación |
| POST | `/api/auth/password-reset/validate/` | Público | Validar enlace |
| POST | `/api/auth/password-reset/confirm/` | Público | Nueva contraseña |
| GET  | `/api/evaluations/questions/` | Paciente | Preguntas y escala |
| POST | `/api/evaluations/` | Paciente | Enviar respuestas → resultado |
| GET  | `/api/evaluations/` | Paciente | Historial |
| GET  | `/api/evaluations/{id}/` | Dueño | Resultado detallado |
| POST | `/api/professionals/register/` | Público | Registro de psicólogo |
| GET  | `/api/professionals/specialties/` | Público | Especialidades |
| GET/PATCH | `/api/professionals/me/` | Psicólogo | Mi perfil profesional |
| GET  | `/api/professionals/` | Administrador | Profesionales (`?verified=false`) |
| POST | `/api/professionals/{id}/verify/` | Administrador | Verificar profesional |
| GET  | `/api/emergency/info/` | Público | Información del servicio |
| GET/POST | `/api/emergency/chats/` | Paciente / Psicólogo verificado | Mis chats o fila · iniciar chat |
| POST | `/api/emergency/chats/{id}/take/` | Psicólogo verificado | Atender chat |
| GET/POST | `/api/emergency/chats/{id}/messages/` | Participantes | Leer (`?after=`) y enviar |
| POST | `/api/emergency/chats/{id}/close/` | Participantes | Finalizar chat |
| GET  | `/api/professionals/directory/` | JWT | Psicólogos verificados (`?q=` buscar) |
| GET  | `/api/professionals/directory/{id}/` | JWT | Perfil de un psicólogo |
| GET  | `/api/appointments/psychologists/{id}/slots/` | JWT | Horarios libres (`?from=AAAA-MM-DD&days=14`) |
| GET/POST | `/api/appointments/` | Paciente (POST) · Paciente o Psicólogo | Mis sesiones (`?scope=`) · reservar cita |
| GET  | `/api/appointments/{id}/` | Participantes | Detalle de una cita |
| GET/PUT | `/api/appointments/availability/` | Psicólogo | Mi horario semanal |

Documentación interactiva: `/api/docs/` (Swagger) y `/api/redoc/`.

### Roles

| Rol | Cómo se crea | Interfaz |
|---|---|---|
| `PACIENTE` | Registro público | `/paciente` |
| `PSICOLOGO` | *Registro profesional* en `/registro-profesional` (luego lo verifica el administrador) | `/psicologo` |
| `ADMINISTRADOR` | `python manage.py createsuperuser` | `/admin` |

---

## 🌿 Flujo de ramas y commits

- `main`: código estable. `develop`: integración del sprint.
- `feature/<historia>` por cada historia, por ejemplo `feature/OM3-9-registro`, `feature/OM3-12-evaluacion-emocional`, `feature/OM3-19-chat-emergencia`, `feature/OM3-17-reservar-cita`.
- Pull Request de la feature hacia `develop`; al cerrar el sprint, PR de `develop` a `main`.

Commits con **Conventional Commits**: `feat(auth): add password reset endpoint`, `test(auth): cover login errors`, `docs: update README`.
El archivo `.commitlintrc.json` define las reglas y el CI revisa los mensajes de cada Pull Request.

## 🐳 Docker

El proyecto está dockerizado con **Dockerfiles multi-stage** (dos etapas):

| Archivo | Etapa 1 · `builder` | Etapa 2 · `production` |
|---|---|---|
| `backend/Dockerfile` | Instala las librerías de Python | Imagen liviana con el código, usuario sin permisos de administrador, migraciones y gunicorn en el puerto 8000 |
| `frontend/Dockerfile` | `npm ci` + `npm run build` con Node 22 | **Nginx** sirve los archivos compilados en el puerto 80 (sin Node) |

`docker-compose.yml` enciende todo junto: **PostgreSQL + API + frontend**.

```powershell
docker compose up --build                                  # enciende todo
docker compose exec backend python manage.py seed_users    # usuarios de prueba
docker compose down                                        # apaga (los datos quedan en el volumen pgdata)
```

Página: http://localhost:5173 · API: http://localhost:8000/api/docs/

> Docker Desktop necesita mínimo 8 GB de RAM. Si tu PC no los tiene, el CI de GitHub construye y prueba las imágenes por ti.

## ⚙️ Calidad y CI/CD

`.github/workflows/ci_cd.yml` se ejecuta en cada push a `main`, `develop` o `feature/**` y en cada Pull Request:

1. **Commits:** revisa que los mensajes sigan Conventional Commits (en los PR).
2. **Backend:** `check`, migraciones al día, pruebas y cobertura mínima de 60 %.
3. **Frontend:** lint y build.
4. **Docker:** construye las dos imágenes y prueba `docker compose up` de verdad (la API responde y se cargan los usuarios de prueba).
5. **Despliegue (CD):** al llegar a `main`, avisa a Render para publicar la nueva versión. Se configura con el secreto `RENDER_DEPLOY_HOOK` del repositorio.

- `sonar-project.properties`: listo para conectar el repositorio a SonarCloud.

## ☁️ Despliegue

Ver la sección de despliegue en [backend/README.md](backend/README.md#despliegue-en-render) (API en Render con PostgreSQL)
y [frontend/README.md](frontend/README.md#despliegue-en-vercel) (frontend en Vercel).
