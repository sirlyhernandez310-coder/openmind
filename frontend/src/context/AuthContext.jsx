import { useCallback, useEffect, useMemo, useState } from 'react'
import { authApi } from '../api/auth'
import { tokenStorage } from '../api/client'
import { AuthContext } from './auth-context'

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(() => Boolean(tokenStorage.get()))

  // si ya había sesión guardada la recuperamos
  useEffect(() => {
    if (!tokenStorage.get()) return
    authApi
      .me()
      .then(setUser)
      .catch(() => tokenStorage.clear())
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    const onExpired = () => setUser(null)
    window.addEventListener('auth:expired', onExpired)
    return () => window.removeEventListener('auth:expired', onExpired)
  }, [])

  const startSession = useCallback(({ access, refresh, user: sessionUser }) => {
    tokenStorage.set({ access, refresh })
    setUser(sessionUser)
    return sessionUser
  }, [])

  const login = useCallback(
    async (email, password) => startSession(await authApi.login(email, password)),
    [startSession],
  )

  // el registro no inicia sesión: primero hay que confirmar el correo
  const register = useCallback((data) => authApi.register(data), [])

  const logout = useCallback(async () => {
    const tokens = tokenStorage.get()
    try {
      if (tokens?.refresh) await authApi.logout(tokens.refresh)
    } catch {
      // igual se cierra la sesión local
    }
    tokenStorage.clear()
    setUser(null)
  }, [])

  const value = useMemo(
    () => ({ user, loading, isAuthenticated: Boolean(user), login, register, logout, startSession, updateUser: setUser }),
    [user, loading, login, register, logout, startSession],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
