import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { api, setAccessToken, setSessionHandlers, type AuthPayload, type Provider, type User } from '../api/client'

type Status = 'loading' | 'anonymous' | 'authenticated'

type AuthState = {
  status: Status
  user: User | null
  /** Thông báo hiển thị ở trang đăng nhập (vd phiên hết hạn). */
  notice: string | null
  clearNotice: () => void
  linkIdentity: (provider: Provider, credential: string) => Promise<void>
  unlinkIdentity: (provider: Provider) => Promise<void>
  register: (b: { email: string; password: string; full_name: string }) => Promise<void>
  login: (b: { email: string; password: string }) => Promise<void>
  loginWithGoogle: (credential: string) => Promise<void>
  loginWithFacebook: (accessToken: string) => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthState | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<Status>('loading')
  const [user, setUser] = useState<User | null>(null)
  const [notice, setNotice] = useState<string | null>(null)

  const accept = useCallback((p: AuthPayload) => {
    setAccessToken(p.access_token)
    setUser(p.user)
    setStatus('authenticated')
    setNotice(null)
  }, [])

  // Phiên hết hạn hoặc bị thu hồi giữa chừng: đưa về trạng thái chưa đăng nhập kèm thông báo.
  useEffect(() => {
    setSessionHandlers({
      onRefreshed: accept,
      onExpired: () => {
        setAccessToken(null)
        setUser(null)
        setStatus('anonymous')
        setNotice('Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.')
      },
    })
    return () => setSessionHandlers(null)
  }, [accept])

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
    notice,
    clearNotice: () => setNotice(null),
    linkIdentity: async (p, c) => { setUser(await api.linkIdentity(p, c)) },
    unlinkIdentity: async (p) => { await api.unlinkIdentity(p); setUser(await api.me()) },
    register: async (b) => accept(await api.register(b)),
    login: async (b) => accept(await api.login(b)),
    loginWithGoogle: async (c) => accept(await api.loginWithGoogle(c)),
    loginWithFacebook: async (t) => accept(await api.loginWithFacebook(t)),
    logout: async () => {
      try { await api.logout() } finally {
        setAccessToken(null)
        setUser(null)
        setStatus('anonymous')
      }
    },
  }), [status, user, notice, accept])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth phải nằm trong <AuthProvider>')
  return ctx
}
