import { Navigate } from 'react-router-dom'
import { homeForRole } from '../constants/roles'
import { useAuth } from '../context/auth-context'

export default function RoleRedirect() {
  const { user } = useAuth()
  return <Navigate to={user ? homeForRole(user.role) : '/login'} replace />
}
