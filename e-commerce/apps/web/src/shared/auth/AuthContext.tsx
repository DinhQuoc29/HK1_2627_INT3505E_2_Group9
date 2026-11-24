import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { api, setAccessToken, type AuthPayload, type User } from '../api/client'

type Status = 'loading' | 'anonymous' | 'authenticated'

type AuthState = {
  status: Status
  user: User | null
  register: (b: { email: string; password: string; full_name: string }) => Promise<void>
  login: (b: { email: string; password: string }) => Promise<void>
  loginWithGoogle: (credential: string) => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthState | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<Status>('loading')
  const [user, setUser] = useState<User | null>(null)

  const accept = useCallback((p: AuthPayload) => {
    setAccessToken(p.access_token)
    setUser(p.user)
    setStatus('authenticated')
  }, [])

  // Khôi phục phiên khi tải trang: đổi cookie refresh lấy access token (nếu còn hiệu lực).
  useEffect(() => {
    let cancelled = false
    api.refresh().then(
      (p) => { if (!cancelled) accept(p) },
      () => { if (!cancelled) setStatus('anonymous') },
    )
    return () => { cancelled = true }
  }, [accept])

  const value = useMemo<AuthState>(() => ({
    status,
    user,
    register: async (b) => accept(await api.register(b)),
    login: async (b) => accept(await api.login(b)),
    loginWithGoogle: async (c) => accept(await api.loginWithGoogle(c)),
    logout: async () => {
      try { await api.logout() } finally {
        setAccessToken(null)
        setUser(null)
        setStatus('anonymous')
      }
    },
  }), [status, user, accept])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth phải nằm trong <AuthProvider>')
  return ctx
}
