import { Link } from 'react-router-dom'
import Icon from '../components/Icon'
import Logo from '../components/Logo'
import LoopPattern from '../components/LoopPattern'
import { useAuth } from '../context/auth-context'

const WHO_SEES = [
  ['Tus datos de cuenta (nombre, correo, teléfono)', 'Tú y el administrador', 'Los psicólogos ven solo tu nombre y foto en tus citas y chats'],
  ['Tus evaluaciones emocionales e historial', 'Solo tú', 'Ningún psicólogo ni administrador las puede abrir'],
  ['Tus citas y videollamadas', 'Tú y el psicólogo de esa cita', 'Las videollamadas no se graban'],
  ['Tus chats de emergencia', 'Tú y el psicólogo que te atiende', '—'],
  ['Perfil del psicólogo (foto, especialidad, descripción)', 'Pacientes con sesión iniciada', 'Nunca su correo, teléfono ni tarjeta profesional'],
  ['Estadísticas de la plataforma', 'Solo el administrador', 'Son totales: no identifican a nadie'],
]

const RIGHTS = [
  ['Conocer, actualizar y rectificar', 'tus datos cuando quieras.'],
  ['Solicitar prueba', 'de la autorización que nos diste al registrarte.'],
  ['Ser informado', 'sobre el uso que se les da a tus datos.'],
  ['Revocar la autorización o pedir que se eliminen', 'tus datos, cuando no haya un deber legal de conservarlos.'],
  ['Acceder gratis', 'a tus datos personales.'],
  ['Presentar quejas', 'ante la Superintendencia de Industria y Comercio (SIC).'],
]

// OM3-26: política de tratamiento de datos personales (Ley 1581 de 2012 y Decreto 1377 de 2013)
export default function PrivacyPage() {
  const { isAuthenticated } = useAuth()
  return (
    <div className="privacy">
      <header className="privacy-hero panel-lilac">
        <LoopPattern variant="wide" />
        <Link to={isAuthenticated ? '/' : '/login'} aria-label="Ir a OpenMind"><Logo size="md" /></Link>
        <div>
          <span className="eyebrow"><Icon name="lock" size={16} /> Protección de datos</span>
          <h1>Política de privacidad y tratamiento de datos personales</h1>
          <p>Cómo cuidamos tu información, según la Ley 1581 de 2012 de Colombia.</p>
        </div>
      </header>

      <main className="privacy-body">
        <section className="card">
          <h2>1. ¿Quién es el responsable?</h2>
          <p>
            OpenMind es una plataforma de bienestar emocional desarrollada como proyecto académico de Ingeniería de Software II
            en la Institución Universitaria Pascual Bravo (Medellín). El equipo del proyecto es responsable del tratamiento de los
            datos que se registran en ella.
          </p>
        </section>

        <section className="card">
          <h2>2. ¿Qué datos recogemos y para qué?</h2>
          <ul className="privacy-list">
            <li><strong>Datos de cuenta:</strong> nombre, correo, teléfono, fecha de nacimiento y foto (opcionales los tres últimos), para crear tu cuenta, iniciar sesión y recuperar tu contraseña.</li>
            <li><strong>Datos profesionales del psicólogo:</strong> especialidad, experiencia, universidad y tarjeta profesional, para verificar su idoneidad y mostrar su perfil a los pacientes.</li>
            <li><strong>Datos de bienestar emocional:</strong> respuestas y resultados de tus evaluaciones, para mostrarte tu historial y recomendarte apoyo cuando lo necesites.</li>
            <li><strong>Citas, chats y videollamadas:</strong> para conectarte con tu psicólogo.</li>
          </ul>
          <p className="privacy-note">
            <Icon name="shield" size={18} /> Las evaluaciones emocionales son <strong>datos sensibles</strong> (relacionados con la salud).
            Responderlas es voluntario: no estás obligado a hacerlo para usar la plataforma.
          </p>
        </section>

        <section className="card">
          <h2>3. ¿Quién puede ver tu información?</h2>
          <div className="table-wrap">
            <table>
              <thead><tr><th>Información</th><th>Quién la ve</th><th>Nota</th></tr></thead>
              <tbody>
                {WHO_SEES.map(([what, who, note]) => <tr key={what}><td>{what}</td><td>{who}</td><td>{note}</td></tr>)}
              </tbody>
            </table>
          </div>
        </section>

        <section className="card">
          <h2>4. ¿Cómo la protegemos?</h2>
          <ul className="privacy-list">
            <li>Las contraseñas se guardan cifradas (PBKDF2 con SHA-256); nadie puede leerlas, ni siquiera el administrador.</li>
            <li>Cada función revisa tu rol (paciente, psicólogo o administrador) y solo te deja ver lo que te corresponde.</li>
            <li>Toda la comunicación viaja cifrada por HTTPS y las sesiones usan tokens JWT que vencen.</li>
            <li>Las videollamadas van cifradas directamente entre los dos navegadores y no se graban.</li>
            <li>Las fotos de perfil se sirven con enlaces aleatorios que no se pueden adivinar.</li>
            <li>Las acciones de los administradores sobre las cuentas quedan registradas.</li>
          </ul>
        </section>

        <section className="card">
          <h2>5. Tus derechos como titular</h2>
          <ul className="rights-grid">
            {RIGHTS.map(([title, text]) => (
              <li key={title}><Icon name="check" size={18} /><span><strong>{title}</strong> {text}</span></li>
            ))}
          </ul>
          <p>
            Puedes actualizar tus datos desde tu perfil. Para cualquier otra solicitud (consulta, rectificación, supresión o
            revocatoria), escríbele al administrador de la plataforma; responderemos en los plazos de la ley (10 días hábiles
            para consultas y 15 para reclamos).
          </p>
        </section>

        <section className="card">
          <h2>6. Vigencia</h2>
          <p>
            Tus datos se conservan mientras tengas una cuenta activa o hasta que solicites su eliminación. Al registrarte aceptas
            esta política; guardamos la fecha de tu autorización.
          </p>
        </section>

        <p className="center">
          <Link to={isAuthenticated ? '/' : '/registro'} className="btn btn--primary">
            {isAuthenticated ? 'Volver a OpenMind' : 'Volver al registro'}
          </Link>
        </p>
      </main>
    </div>
  )
}
