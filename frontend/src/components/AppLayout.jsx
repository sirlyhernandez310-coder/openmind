import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { ROLE_LABELS, homeForRole } from '../constants/roles'
import { useAuth } from '../context/auth-context'
import Alert from './Alert'
import Avatar from './Avatar'
import Icon from './Icon'
import Logo from './Logo'

const NAV_BY_ROLE = {
  PACIENTE: [
    { to: '/paciente', label: 'Inicio', icon: 'home', end: true },
    { to: '/paciente/evaluacion', label: 'Evaluación', icon: 'smile' },
    { to: '/paciente/historial', label: 'Mi historial', icon: 'chart' },
    { to: '/paciente/psicologos', label: 'Psicólogos', icon: 'users' },
    { to: '/paciente/sesiones', label: 'Mis sesiones', icon: 'calendar' },
    { to: '/paciente/emergencia', label: 'Chat de emergencia', icon: 'chat', urgent: true },
  ],
  PSICOLOGO: [
    { to: '/psicologo', label: 'Inicio', icon: 'home', end: true },
    { to: '/psicologo/agenda', label: 'Agenda', icon: 'calendar' },
    { to: '/psicologo/emergencias', label: 'Emergencias', icon: 'chat', urgent: true },
    { to: '/psicologo/perfil', label: 'Perfil profesional', icon: 'user' },
  ],
  ADMINISTRADOR: [
    { to: '/admin', label: 'Usuarios', icon: 'users', end: true },
    { to: '/admin/profesionales', label: 'Profesionales', icon: 'shield' },
  ],
}

export default function AppLayout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const notice = location.state?.notice

  const handleLogout = async () => {
    await logout()
    navigate('/login', { replace: true })
  }

  return (
    <div className="shell">
      <header className="topbar">
        <NavLink to={homeForRole(user.role)} className="topbar-logo" aria-label="Ir al inicio"><Logo size="sm" /></NavLink>
        <nav className="topbar-nav" aria-label="Menú principal">
          {NAV_BY_ROLE[user.role]?.map((item) => (
            <NavLink key={item.to} to={item.to} end={item.end}
              className={`nav-item ${item.urgent ? 'nav-item--urgent' : ''}`}>
              <Icon name={item.icon} size={18} />
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="topbar-user">
          <Avatar user={user} size={42} />
          <div className="topbar-user-info">
            <strong>{user.first_name}</strong>
            <span>{ROLE_LABELS[user.role]}</span>
          </div>
          <button type="button" className="btn btn--ghost btn--sm btn--icon" onClick={handleLogout} aria-label="Cerrar sesión">
            <Icon name="logout" size={18} />
            <span className="hide-sm">Salir</span>
          </button>
        </div>
      </header>
      <main className="content">
        {notice && <Alert type="info">{notice}</Alert>}
        <Outlet />
      </main>
    </div>
  )
}
