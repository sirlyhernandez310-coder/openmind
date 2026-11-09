import { useEffect, useState } from 'react'
import { emergencyApi } from '../../api/emergency'
import Alert from '../../components/Alert'
import Blob from '../../components/Blob'
import ChatWindow from '../../components/ChatWindow'
import ServiceInfo from '../../components/ServiceInfo'

export default function EmergencyChatPage() {
  const [info, setInfo] = useState(null)
  const [chat, setChat] = useState(undefined) // undefined = cargando, null = sin chat abierto
  const [error, setError] = useState('')
  const [starting, setStarting] = useState(false)

  useEffect(() => {
    emergencyApi.info().then(setInfo).catch(() => {})
    emergencyApi
      .chats()
      .then((chats) => setChat(chats.find((c) => c.status !== 'CERRADA') ?? null))
      .catch((err) => {
        setError(err.message)
        setChat(null)
      })
  }, [])

  const start = async () => {
    setStarting(true)
    setError('')
    try {
      setChat(await emergencyApi.open())
    } catch (err) {
      setError(err.message)
    } finally {
      setStarting(false)
    }
  }

  const close = async () => {
    if (!window.confirm('¿Quieres finalizar la conversación?')) return
    try {
      setChat(await emergencyApi.close(chat.id))
    } catch (err) {
      setError(err.message)
    }
  }

  if (chat === undefined) return <p className="muted">Cargando…</p>

  return (
    <div className="emergency">
      <Alert>{error}</Alert>
      {chat ? (
        <div className="emergency-layout">
          <div className="emergency-chat">
            <ChatWindow
              chat={{ ...chat, viewerRole: 'PACIENTE', can_write: true }}
              onChange={setChat}
              headerAction={
                chat.status === 'CERRADA' ? (
                  <button type="button" className="btn btn--primary btn--sm" onClick={start} disabled={starting}>
                    Nuevo chat
                  </button>
                ) : (
                  <button type="button" className="btn btn--ghost btn--sm" onClick={close}>Finalizar</button>
                )
              }
            />
          </div>
          <ServiceInfo info={info} compact />
        </div>
      ) : (
        <div className="emergency-layout">
          <section className="card emergency-start">
            <Blob mood="calm" size={110} className="float" />
            <span className="eyebrow">Chat de emergencia</span>
            <h1>Estamos aquí para escucharte</h1>
            <p className="muted">
              Habla en tiempo real con un psicólogo de OpenMind. Tu conversación es privada.
            </p>
            <button type="button" className="btn btn--primary" onClick={start} disabled={starting}>
              {starting ? 'Conectando…' : 'Iniciar chat ahora'}
            </button>
          </section>
          <ServiceInfo info={info} />
        </div>
      )}
    </div>
  )
}
