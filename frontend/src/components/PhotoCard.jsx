import { useRef, useState } from 'react'
import { authApi } from '../api/auth'
import { useAuth } from '../context/auth-context'
import Alert from './Alert'
import Avatar from './Avatar'
import LoopPattern from './LoopPattern'

const MAX_MB = 5

// Tarjeta para subir, cambiar o quitar la foto de perfil
export default function PhotoCard({ hint }) {
  const { user, updateUser } = useAuth()
  const input = useRef(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const upload = async (event) => {
    const file = event.target.files?.[0]
    event.target.value = ''
    if (!file) return
    if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) {
      setError('Sube una imagen JPG, PNG o WEBP.')
      return
    }
    if (file.size > MAX_MB * 1024 * 1024) {
      setError(`La foto no puede pesar más de ${MAX_MB} MB.`)
      return
    }
    setBusy(true)
    setError('')
    try {
      updateUser(await authApi.uploadAvatar(file))
    } catch (err) {
      setError(err.fieldErrors?.avatar || err.message)
    } finally {
      setBusy(false)
    }
  }

  const remove = async () => {
    setBusy(true)
    try {
      updateUser(await authApi.removeAvatar())
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  const hasPhoto = Boolean(user.avatar_url)
  return (
    <section className="photo-card panel-lilac">
      <LoopPattern variant="small" width={26} />
      <button type="button" className="photo-card-pic" onClick={() => input.current?.click()} disabled={busy}
        aria-label={hasPhoto ? 'Cambiar mi foto' : 'Subir mi foto'}>
        {hasPhoto ? <Avatar user={user} size={104} /> : (
          <span className="photo-card-empty">
            <svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" aria-hidden="true"><circle cx="12" cy="8" r="4" /><path d="M4 21c1-4 4-6 8-6s7 2 8 6" /></svg>
            Tu foto
          </span>
        )}
        <span className="photo-card-badge" aria-hidden="true">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M4 8h3l2-3h6l2 3h3v11H4z" /><circle cx="12" cy="13" r="3.5" /></svg>
        </span>
      </button>
      <div className="photo-card-text">
        <strong>{hasPhoto ? 'Tu foto de perfil' : 'Agrega tu foto'}</strong>
        <p>{hint}</p>
        <Alert>{error}</Alert>
        <div className="photo-card-actions">
          <button type="button" className="btn btn--primary btn--sm" onClick={() => input.current?.click()} disabled={busy}>
            {busy ? 'Guardando…' : hasPhoto ? 'Cambiar foto' : 'Subir foto'}
          </button>
          {hasPhoto && (
            <button type="button" className="btn btn--ghost btn--sm" onClick={remove} disabled={busy}>Quitar</button>
          )}
        </div>
      </div>
      <input ref={input} type="file" accept="image/jpeg,image/png,image/webp" onChange={upload} hidden />
    </section>
  )
}
