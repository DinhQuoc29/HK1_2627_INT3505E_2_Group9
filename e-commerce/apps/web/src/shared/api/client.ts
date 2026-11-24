/** Client gọi API /api/v1. Access token chỉ giữ trong bộ nhớ; refresh token là cookie HttpOnly. */

export type User = {
  id: string
  email: string
  full_name: string
  role: 'buyer' | 'seller' | 'admin'
  created_at: string
  providers: string[] // nhà cung cấp OAuth đã liên kết
  has_password: boolean // false: tài khoản chỉ đăng nhập bằng Google
}
export type Provider = 'google' | 'facebook'
export type AuthPayload = { access_token: string; token_type: 'Bearer'; expires_in: number; user: User }
export type FieldError = { field: string; message: string }

/** Lỗi problem+json (RFC 9457) từ backend, hoặc lỗi mạng (status = 0). */
export class ApiError extends Error {
  constructor(
    public status: number,
    public slug: string,
    message: string,
    public errors: FieldError[] = [],
    public retryAfter?: number,
  ) {
    super(message)
  }
}

let accessToken: string | null = null
export const setAccessToken = (t: string | null) => { accessToken = t }
export const getAccessToken = () => accessToken

const BASE = '/api/v1'

async function parse(res: Response): Promise<unknown> {
  if (res.status === 204) return null
  const text = await res.text()
  return text ? JSON.parse(text) : null
}

async function request<T>(method: string, path: string, body?: unknown, auth = false): Promise<T> {
  let res: Response
  try {
    res = await fetch(BASE + path, {
      method,
      credentials: 'same-origin',
      headers: {
        ...(body !== undefined ? { 'Content-Type': 'application/json' } : {}),
        ...(auth && accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
      },
      body: body !== undefined ? JSON.stringify(body) : undefined,
    })
  } catch {
    throw new ApiError(0, 'network', 'Không kết nối được máy chủ. Kiểm tra mạng và thử lại.')
  }
  const data = (await parse(res).catch(() => null)) as Record<string, unknown> | null
  if (res.ok) return data as T
  const retry = Number(res.headers.get('Retry-After'))
  throw new ApiError(
    res.status,
    String(data?.type ?? '').replace('/problems/', '') || 'error',
    String(data?.detail ?? 'Đã có lỗi xảy ra, vui lòng thử lại.'),
    (data?.errors as FieldError[] | undefined) ?? [],
    Number.isFinite(retry) && retry > 0 ? retry : undefined,
  )
}

// Refresh token bị xoay vòng nên các lần gọi đồng thời phải dùng chung MỘT request
// (nếu không, request thứ hai mang token cũ sẽ bị từ chối và xóa cookie mới).
let refreshInFlight: Promise<AuthPayload> | null = null
const refreshOnce = () => {
  refreshInFlight ??= request<AuthPayload>('POST', '/auth/tokens').finally(() => { refreshInFlight = null })
  return refreshInFlight
}

// AuthContext đăng ký để biết khi nào token được làm mới hoặc phiên hết hạn hẳn.
type SessionHandlers = { onRefreshed: (p: AuthPayload) => void; onExpired: () => void }
let handlers: SessionHandlers | null = null
export const setSessionHandlers = (h: SessionHandlers | null) => { handlers = h }

const RECOVERABLE = new Set(['token-expired', 'missing-token', 'invalid-token'])

/** Gọi API cần đăng nhập: access token hết hạn (15 phút) thì tự refresh một lần rồi thử lại. */
async function authed<T>(method: string, path: string, body?: unknown): Promise<T> {
  try {
    return await request<T>(method, path, body, true)
  } catch (e) {
    if (!(e instanceof ApiError) || e.status !== 401) throw e
    if (!RECOVERABLE.has(e.slug)) { handlers?.onExpired(); throw e } // vd phiên đã bị thu hồi
    let payload: AuthPayload
    try { payload = await refreshOnce() } catch { handlers?.onExpired(); throw e }
    setAccessToken(payload.access_token)
    handlers?.onRefreshed(payload)
    return request<T>(method, path, body, true)
  }
}

export const api = {
  register: (b: { email: string; password: string; full_name: string }) => request<AuthPayload>('POST', '/users', b),
  login: (b: { email: string; password: string }) => request<AuthPayload>('POST', '/auth/sessions', b),
  loginWithGoogle: (credential: string) => request<AuthPayload>('POST', '/auth/sessions/google', { credential }),
  loginWithFacebook: (access_token: string) => request<AuthPayload>('POST', '/auth/sessions/facebook', { access_token }),
  refresh: refreshOnce,
  logout: () => request<null>('DELETE', '/auth/sessions/current', undefined, true),
  me: () => authed<User>('GET', '/users/me'),
  linkIdentity: (provider: Provider, credential: string) => authed<User>('POST', '/users/me/identities', { provider, credential }),
  unlinkIdentity: (provider: Provider) => authed<null>('DELETE', `/users/me/identities/${provider}`),
}
