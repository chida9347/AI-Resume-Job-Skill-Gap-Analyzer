import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import * as api from '../services/api.js'
import { AUTH_EXPIRED_EVENT } from '../services/api.js'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => api.tokenStore.getUser())
  const [loading, setLoading] = useState(() => Boolean(api.tokenStore.getAccess() || api.tokenStore.getRefresh()))

  useEffect(() => {
    let active = true

    async function bootstrap() {
      if (!api.tokenStore.getAccess() && !api.tokenStore.getRefresh()) {
        setLoading(false)
        return
      }
      try {
        const profile = await api.fetchMe()
        if (active) setUser(profile)
      } catch {
        if (active) {
          api.tokenStore.clear()
          setUser(null)
        }
      } finally {
        if (active) setLoading(false)
      }
    }

    bootstrap()
    const handleExpired = () => setUser(null)
    window.addEventListener(AUTH_EXPIRED_EVENT, handleExpired)
    return () => {
      active = false
      window.removeEventListener(AUTH_EXPIRED_EVENT, handleExpired)
    }
  }, [])

  const login = useCallback(async (credentials) => {
    const session = await api.login(credentials)
    setUser(session.user)
    return session
  }, [])

  const register = useCallback(async (payload) => {
    const session = await api.register(payload)
    setUser(session.user)
    return session
  }, [])

  const logout = useCallback(async () => {
    try {
      await api.logout()
    } finally {
      setUser(null)
    }
  }, [])

  const updateProfile = useCallback(async (payload) => {
    const profile = await api.updateProfile(payload)
    setUser(profile)
    return profile
  }, [])

  const deleteAccount = useCallback(async (password) => {
    const result = await api.deleteAccount(password)
    setUser(null)
    return result
  }, [])

  const value = useMemo(
    () => ({
      user,
      loading,
      isAuthenticated: Boolean(user),
      login,
      register,
      logout,
      updateProfile,
      deleteAccount,
      setUser,
    }),
    [user, loading, login, register, logout, updateProfile, deleteAccount],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used inside AuthProvider')
  return context
}
