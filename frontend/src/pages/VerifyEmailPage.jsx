import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { authApi } from '../api/auth'
import Alert from '../components/Alert'
import AuthLayout from '../components/AuthLayout'
import { homeForRole } from '../constants/roles'
import { useAuth } from '../context/auth-context'

// Página a la que llega el usuario desde el enlace del correo
export default function VerifyEmailPage() {
  const [params] = useSearchParams()
  const navigate = useNavigate()
  const { startSession } = useAuth()
  const token = params.get('token') ?? ''
  const [error, setError] = useState(token ? '' : 'El enlace de verificación no es válido.')
  const started = useRef(false)

  useEffect(() => {
    if (!token || started.current) return
    started.current = true
    authApi
      .verifyEmail(token)
      .then((session) => {
        const user = startSession(session)
        navigate(homeForRole(user.role), { replace: true, state: { welcome: true } })
      })
      .catch((err) => setError(err.fieldErrors?.token || err.message))
  }, [token, navigate, startSession])

  if (error) {
    return (
      <AuthLayout title="No pudimos confirmar tu correo" mood="sleepy" footer={<Link to="/login">← Ir a iniciar sesión</Link>}>
        <Alert>{error}</Alert>
        <Link to="/verifica-tu-correo" className="btn btn--primary btn--block">Pedir un nuevo enlace</Link>
      </AuthLayout>
    )
  }

  return (
    <AuthLayout title="Confirmando tu correo…" mood="thinking">
      <p className="muted">Un momento, estamos activando tu cuenta.</p>
    </AuthLayout>
  )
}
