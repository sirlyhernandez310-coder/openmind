import { useEffect, useState } from 'react'
import { useLocation } from 'react-router-dom'
import { emergencyApi } from '../../api/emergency'
import Alert from '../../components/Alert'
import FeatureCard from '../../components/FeatureCard'
import PageHeader from '../../components/PageHeader'
import PhotoCard from '../../components/PhotoCard'
import { useAuth } from '../../context/auth-context'

export default function PsychologistHomePage() {
  const { user } = useAuth()
  const location = useLocation()
  const [waiting, setWaiting] = useState(null)

  useEffect(() => {
    if (!user.is_verified) return
    emergencyApi.chats('ESPERANDO').then((list) => setWaiting(list.length)).catch(() => {})
  }, [user.is_verified])

  return (
    <div className="stack">
      {location.state?.welcome && (
        <Alert type="success">¡Tu correo fue confirmado y tu perfil profesional está creado! Bienvenido a Open Mind.</Alert>
      )}
      <PageHeader eyebrow="Panel profesional" title={`Hola, ${user.first_name}`} mood="calma">
        Desde aquí acompañarás a tus pacientes y atenderás las solicitudes de emergencia.
      </PageHeader>

      {!user.is_verified && (
        <Alert type="info">
          Tu perfil está <strong>pendiente de verificación</strong>. Un administrador revisará tu tarjeta profesional;
          mientras tanto puedes completar tu perfil.
        </Alert>
      )}

      <section className="features">
        <FeatureCard icon="chat" title="Emergencias" tone="coral" to="/psicologo/emergencias"
          cta={waiting ? `${waiting} esperando` : 'Ver fila'} highlight={Boolean(waiting)}>
          Recibe y responde los chats de emergencia de los pacientes.
        </FeatureCard>
        <FeatureCard icon="user" title="Perfil profesional" tone="sun" to="/psicologo/perfil" cta="Ver perfil">
          Tu especialidad, experiencia, tarjeta profesional y descripción.
        </FeatureCard>
        <FeatureCard icon="calendar" title="Agenda" tone="white" to="/psicologo/agenda" cta="Ver agenda">
          Tus próximas sesiones y tu horario semanal de atención.
        </FeatureCard>
      </section>

      <PhotoCard hint="Los pacientes verán tu foto en el directorio de psicólogos y en el chat." />
    </div>
  )
}
