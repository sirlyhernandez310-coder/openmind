import { useCallback, useEffect, useRef, useState } from 'react'
import { emergencyApi } from '../api/emergency'
import { formatTime } from '../format'
import usePolling from '../hooks/usePolling'
import Alert from './Alert'
import Avatar from './Avatar'
import Icon from './Icon'

const STATUS_TEXT = {
  ESPERANDO: 'Esperando a que un psicólogo se una…',
  ACTIVA: 'En conversación',
  CERRADA: 'Conversación finalizada',
}

/**
 * Ventana de chat compartida por paciente y psicólogo.
 * Consulta los mensajes nuevos cada 3 segundos (polling).
 */
export default function ChatWindow({ chat, onChange, headerAction }) {
  const [messages, setMessages] = useState([])
  const [text, setText] = useState('')
  const [error, setError] = useState('')
  const [sending, setSending] = useState(false)
  const listRef = useRef(null)
  const lastId = messages.length ? messages[messages.length - 1].id : null
  const isOpen = chat.status !== 'CERRADA'

  const appendNew = useCallback((incoming) => {
    if (!incoming.length) return
    setMessages((current) => {
      const seen = new Set(current.map((m) => m.id))
      return [...current, ...incoming.filter((m) => !seen.has(m.id))]
    })
  }, [])

  useEffect(() => {
    setMessages([])
    emergencyApi.messages(chat.id).then(setMessages).catch((err) => setError(err.message))
  }, [chat.id])

  const refresh = useCallback(async () => {
    try {
      appendNew(await emergencyApi.messages(chat.id, lastId))
      const updated = await emergencyApi.chat(chat.id)
      if (updated.status !== chat.status) onChange?.(updated)
    } catch {
      // se reintenta en el siguiente ciclo
    }
  }, [appendNew, chat.id, chat.status, lastId, onChange])

  usePolling(refresh, 3000, isOpen)

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages.length])

  const send = async (event) => {
    event.preventDefault()
    const clean = text.trim()
    if (!clean) return
    setSending(true)
    setError('')
    try {
      appendNew([await emergencyApi.send(chat.id, clean)])
      setText('')
    } catch (err) {
      setError(err.fieldErrors?.text || err.message)
    } finally {
      setSending(false)
    }
  }

  const onKeyDown = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) send(event)
  }

  const other = chat.viewerRole === 'PSICOLOGO' ? chat.patient : chat.psychologist
  return (
    <section className="chat">
      <header className="chat-head">
        {other ? <Avatar user={other} size={52} /> : <span className="chat-head-waiting" aria-hidden="true"><Icon name="chat" size={24} /></span>}
        <div className="chat-head-text">
          <strong>{headerTitle(chat)}</strong>
          <span className={`chat-status chat-status--${chat.status.toLowerCase()}`}>
            <span className="chat-status-dot" aria-hidden="true" /> {STATUS_TEXT[chat.status]}
            {chat.status === 'ACTIVA' && chat.viewerRole !== 'PSICOLOGO' && chat.psychologist?.specialty ? ` · ${chat.psychologist.specialty}` : ''}
          </span>
        </div>
        {headerAction}
      </header>

      <ol className="chat-messages" ref={listRef} aria-live="polite">
        {messages.map((m) => (
          <li
            key={m.id}
            className={`msg ${m.is_system ? 'msg--system' : m.is_mine ? 'msg--mine' : 'msg--theirs'}`}
          >
            {!m.is_system && (
              <Avatar user={{ id: m.sender, full_name: m.sender_name, avatar_url: m.sender_avatar }} size={34} className="msg-avatar" />
            )}
            <div className="msg-bubble">
              {!m.is_system && !m.is_mine && <span className="msg-author">{m.sender_name}</span>}
              <p>{m.text}</p>
              <time dateTime={m.created_at}>{formatTime(m.created_at)}</time>
            </div>
          </li>
        ))}
        {chat.status === 'ESPERANDO' && (
          <li className="msg msg--system typing" aria-hidden="true"><div className="msg-bubble"><span /><span /><span /></div></li>
        )}
      </ol>

      <Alert>{error}</Alert>
      {isOpen ? (
        <form className="chat-form" onSubmit={send}>
          <textarea
            rows={1}
            placeholder="Escribe tu mensaje…"
            value={text}
            maxLength={2000}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={onKeyDown}
            aria-label="Mensaje"
            disabled={!chat.can_write}
          />
          <button type="submit" className="btn btn--primary btn--round" aria-label="Enviar mensaje" disabled={sending || !text.trim() || !chat.can_write}>
            <Icon name="send" size={20} />
          </button>
        </form>
      ) : (
        <p className="chat-closed muted">Esta conversación finalizó{chat.closed_at ? ` a las ${formatTime(chat.closed_at)}` : ''}.</p>
      )}
    </section>
  )
}

function headerTitle(chat) {
  if (chat.viewerRole === 'PSICOLOGO') return `Chat con ${chat.patient.full_name}`
  return chat.psychologist ? `Chat con ${chat.psychologist.full_name}` : 'Chat de emergencia'
}
