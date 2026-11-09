import { useCallback, useEffect, useState } from 'react'
import { emergencyApi } from '../../api/emergency'
import Alert from '../../components/Alert'
import Blob from '../../components/Blob'
import ChatWindow from '../../components/ChatWindow'
import PageHeader from '../../components/PageHeader'
import { useAuth } from '../../context/auth-context'
import { formatTime } from '../../format'
import usePolling from '../../hooks/usePolling'

export default function EmergencyQueuePage() {
  const { user } = useAuth()
  const [chats, setChats] = useState([])
  const [selectedId, setSelectedId] = useState(null)
  const [error, setError] = useState('')
  const [loaded, setLoaded] = useState(false)

  const load = useCallback(async () => {
    try {
      setChats(await emergencyApi.chats())
      setError('')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoaded(true)
    }
  }, [])

  useEffect(() => {
    if (user.is_verified) load()
  }, [load, user.is_verified])

  usePolling(load, 5000, Boolean(user.is_verified))

  if (!user.is_verified) {
    return (
      <>
        <PageHeader eyebrow="Emergencias" title="Atención de emergencias" mood="sleepy" />
        <Alert type="info">
          Tu perfil profesional está pendiente de verificación. Cuando un administrador valide tu tarjeta profesional
          podrás atender chats de emergencia.
        </Alert>
      </>
    )
  }

  const waiting = chats.filter((c) => c.status === 'ESPERANDO')
  const mine = chats.filter((c) => c.status !== 'ESPERANDO' && c.psychologist?.id === user.id)
  const selected = chats.find((c) => c.id === selectedId)

  const replace = (updated) => setChats((list) => list.map((c) => (c.id === updated.id ? updated : c)))

  const take = async (id) => {
    try {
      const updated = await emergencyApi.take(id)
      replace(updated)
      setSelectedId(id)
    } catch (err) {
      setError(err.message)
      load()
    }
  }

  const close = async (id) => {
    if (!window.confirm('¿Finalizar esta conversación?')) return
    try {
      replace(await emergencyApi.close(id))
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <>
      <PageHeader eyebrow="Emergencias" title="Fila de atención" mood="thinking">
        Los pacientes que piden ayuda aparecen aquí en tiempo real. Atiende el primero de la fila.
      </PageHeader>
      <Alert>{error}</Alert>

      <div className="queue-layout">
        <aside className="queue">
          <h2>En espera <span className="count">{waiting.length}</span></h2>
          {loaded && !waiting.length && <p className="muted tiny">No hay pacientes esperando. 🌿</p>}
          <ul>
            {waiting.map((c) => (
              <li key={c.id}>
                <button type="button" className={`queue-item ${selectedId === c.id ? 'queue-item--active' : ''}`} onClick={() => setSelectedId(c.id)}>
                  <span className="queue-pulse" aria-hidden="true" />
                  <span>
                    <strong>{c.patient.full_name}</strong>
                    <span className="tiny muted">Esperando desde las {formatTime(c.created_at)}</span>
                  </span>
                </button>
              </li>
            ))}
          </ul>

          <h2>Mis conversaciones</h2>
          {loaded && !mine.length && <p className="muted tiny">Aún no has atendido conversaciones.</p>}
          <ul>
            {mine.map((c) => (
              <li key={c.id}>
                <button type="button" className={`queue-item ${selectedId === c.id ? 'queue-item--active' : ''}`} onClick={() => setSelectedId(c.id)}>
                  <span className={`queue-state queue-state--${c.status.toLowerCase()}`} aria-hidden="true" />
                  <span>
                    <strong>{c.patient.full_name}</strong>
                    <span className="tiny muted">{c.status_display}</span>
                  </span>
                </button>
              </li>
            ))}
          </ul>
        </aside>

        <div className="queue-chat">
          {selected ? (
            <ChatWindow
              key={selected.id}
              chat={{ ...selected, viewerRole: 'PSICOLOGO', can_write: selected.psychologist?.id === user.id }}
              onChange={replace}
              headerAction={
                selected.status === 'ESPERANDO' ? (
                  <button type="button" className="btn btn--primary btn--sm" onClick={() => take(selected.id)}>
                    Atender
                  </button>
                ) : selected.status === 'ACTIVA' ? (
                  <button type="button" className="btn btn--ghost btn--sm" onClick={() => close(selected.id)}>Finalizar</button>
                ) : null
              }
            />
          ) : (
            <section className="card empty">
              <Blob mood="calm" size={90} />
              <p className="muted">Selecciona una conversación para verla.</p>
            </section>
          )}
        </div>
      </div>
    </>
  )
}
