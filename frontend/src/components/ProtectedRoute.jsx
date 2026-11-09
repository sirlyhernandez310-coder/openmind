import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { homeForRole } from '../constants/roles'
import { useAuth } from '../context/auth-context'

export default function ProtectedRoute({ allowedRoles }) {
  const { user } = useAuth()
  const location = useLocation()

  if (!user) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />
  }

  // si la sección no es de su rol, lo enviamos a su propia interfaz
  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return (
      <Navigate
        to={homeForRole(user.role)}
        replace
        state={{ notice: 'No tienes permisos para acceder a esa sección.' }}
      />
    )
  }

  return <Outlet />
}
