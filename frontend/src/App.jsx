import { useEffect, useState } from 'react'
import { Route, Routes } from 'react-router-dom'
import AppLayout from './components/AppLayout'
import ProtectedRoute from './components/ProtectedRoute'
import RoleRedirect from './components/RoleRedirect'
import Splash from './components/Splash'
import { ROLES } from './constants/roles'
import { useAuth } from './context/auth-context'
import AdminHomePage from './pages/admin/AdminHomePage'
import ProfessionalsPage from './pages/admin/ProfessionalsPage'
import CheckEmailPage from './pages/CheckEmailPage'
import ForgotPasswordPage from './pages/ForgotPasswordPage'
import LoginPage from './pages/LoginPage'
import EmergencyChatPage from './pages/paciente/EmergencyChatPage'
import EvaluationDetailPage from './pages/paciente/EvaluationDetailPage'
import EvaluationPage from './pages/paciente/EvaluationPage'
import BookingPage from './pages/paciente/BookingPage'
import MySessionsPage from './pages/paciente/MySessionsPage'
import PsychologistProfilePage from './pages/paciente/PsychologistProfilePage'
import PsychologistsPage from './pages/paciente/PsychologistsPage'
import HistoryPage from './pages/paciente/HistoryPage'
import PatientHomePage from './pages/paciente/PatientHomePage'
import ProfessionalRegisterPage from './pages/ProfessionalRegisterPage'
import AgendaPage from './pages/psicologo/AgendaPage'
import EmergencyQueuePage from './pages/psicologo/EmergencyQueuePage'
import ProfessionalProfilePage from './pages/psicologo/ProfessionalProfilePage'
import PsychologistHomePage from './pages/psicologo/PsychologistHomePage'
import RegisterPage from './pages/RegisterPage'
import ResetPasswordPage from './pages/ResetPasswordPage'
import VerifyEmailPage from './pages/VerifyEmailPage'

const SPLASH_KEY = 'openmind.splash'
const SPLASH_MS = 2600

// El logo animado se muestra una vez por sesión del navegador (y mientras se recupera la sesión)
function useSplash() {
  const [phase, setPhase] = useState(() => {
    try {
      return sessionStorage.getItem(SPLASH_KEY) ? 'done' : 'show'
    } catch {
      return 'show'
    }
  })
  useEffect(() => {
    if (phase === 'done') return undefined
    const reduce = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
    const leave = setTimeout(() => setPhase('leaving'), reduce ? 600 : SPLASH_MS)
    const done = setTimeout(() => {
      setPhase('done')
      try {
        sessionStorage.setItem(SPLASH_KEY, '1')
      } catch {
        // sin almacenamiento: se mostrará de nuevo, no pasa nada
      }
    }, (reduce ? 600 : SPLASH_MS) + 450)
    return () => {
      clearTimeout(leave)
      clearTimeout(done)
    }
  }, [phase])
  return phase
}

function App() {
  const { isAuthenticated, loading } = useAuth()
  const splash = useSplash()

  if (loading || splash !== 'done') {
    return <Splash leaving={!loading && splash === 'leaving'} />
  }

  return (
    <Routes>
      {/* Rutas públicas */}
      <Route path="/login" element={isAuthenticated ? <RoleRedirect /> : <LoginPage />} />
      <Route path="/registro" element={isAuthenticated ? <RoleRedirect /> : <RegisterPage />} />
      <Route path="/registro-profesional" element={isAuthenticated ? <RoleRedirect /> : <ProfessionalRegisterPage />} />
      <Route path="/verifica-tu-correo" element={<CheckEmailPage />} />
      <Route path="/verificar-correo" element={<VerifyEmailPage />} />
      <Route path="/recuperar-contrasena" element={<ForgotPasswordPage />} />
      <Route path="/restablecer-contrasena" element={<ResetPasswordPage />} />

      {/* Rutas protegidas: cada rol ve su propia interfaz */}
      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          <Route element={<ProtectedRoute allowedRoles={[ROLES.PACIENTE]} />}>
            <Route path="/paciente" element={<PatientHomePage />} />
            <Route path="/paciente/evaluacion" element={<EvaluationPage />} />
            <Route path="/paciente/historial" element={<HistoryPage />} />
            <Route path="/paciente/historial/:id" element={<EvaluationDetailPage />} />
            <Route path="/paciente/psicologos" element={<PsychologistsPage />} />
            <Route path="/paciente/psicologos/:id" element={<PsychologistProfilePage />} />
            <Route path="/paciente/psicologos/:id/reservar" element={<BookingPage />} />
            <Route path="/paciente/sesiones" element={<MySessionsPage />} />
            <Route path="/paciente/emergencia" element={<EmergencyChatPage />} />
          </Route>
          <Route element={<ProtectedRoute allowedRoles={[ROLES.PSICOLOGO]} />}>
            <Route path="/psicologo" element={<PsychologistHomePage />} />
            <Route path="/psicologo/agenda" element={<AgendaPage />} />
            <Route path="/psicologo/emergencias" element={<EmergencyQueuePage />} />
            <Route path="/psicologo/perfil" element={<ProfessionalProfilePage />} />
          </Route>
          <Route element={<ProtectedRoute allowedRoles={[ROLES.ADMINISTRADOR]} />}>
            <Route path="/admin" element={<AdminHomePage />} />
            <Route path="/admin/profesionales" element={<ProfessionalsPage />} />
          </Route>
        </Route>
      </Route>

      <Route path="*" element={<RoleRedirect />} />
    </Routes>
  )
}

export default App
