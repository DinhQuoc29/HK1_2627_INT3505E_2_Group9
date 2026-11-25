/** Client gọi API /api/v1. Access token chỉ giữ trong bộ nhớ; refresh token là cookie HttpOnly. */

export type User = {
  id: string
  email: string
  full_name: string
  role: 'buyer' | 'seller' | 'admin'
  created_at: string
  providers: string[] // nhà cung cấp OAuth đã liên kết
  has_password: boolean // false: tài khoản chỉ đăng nhập bằng Google
  email_verified: boolean // cần để đăng ký bán hàng
}
export type Provider = 'google' | 'facebook'
export type AuthPayload = { access_token: string; token_type: 'Bearer'; expires_in: number; user: User }
export type Province = { code: string; name: string }
export type ApplicationStatus = 'pending' | 'approved' | 'rejected'
export type SellerApplication = {
  id: string; shop_name: string; province_code: string; province_name: string
  status: ApplicationStatus; reject_reason: string | null; created_at: string; reviewed_at: string | null
}
export type AdminSellerApplication = SellerApplication & { applicant_id: string; applicant_email: string; applicant_name: string }
export type AdminSellerApplicationPage = { items: AdminSellerApplication[]; next_cursor: string | null }
export type Shop = { id: string; name: string; province: Province; created_at: string }
export type ShopStatistics = {
  total_orders: number
  orders_by_status: Record<OrderStatus, number>
  captured_orders: number
  recorded_revenue_vnd: string
}
export type ProductCategory = { id: string; name: string; parent_name: string }
export type ProductStatus = 'active' | 'inactive'
export type ProductInput = {
  name: string
  brand: string | null
  description: string
  category_id: string
  price: number
  quantity: number
  images: string[]
}
export type SellerProduct = Omit<ProductInput, 'description'> & {
  id: string
  description: string | null
  category_name: string
  status: ProductStatus
}
export type SellerProductPage = { items: SellerProduct[]; has_more: boolean }
export type OrderStatus = 'pending_payment' | 'paid' | 'shipping' | 'completed' | 'cancelled'
export type SellerOrder = {
  id: string
  checkout_id: string
  shop: { id: string; name: string }
  status: OrderStatus
  total_amount: number
  shipping: { name: string; phone: string; address: string }
  items: {
    id: string
    product_id: string
    product_name: string
    unit_price: number
    quantity: number
    line_total: number
    has_review: boolean
  }[]
  created_at: string
  paid_at: string | null
  shipped_at: string | null
  completed_at: string | null
  cancelled_at: string | null
  cancelled_by: 'buyer' | 'seller' | null
}
export type SellerOrderPage = { items: SellerOrder[]; next_cursor: string | null }
export type Role = User['role']
export type AdminUser = { id: string; email: string; full_name: string; role: Role; status: 'active' | 'suspended'; created_at: string; has_shop: boolean }
export type AdminUserPage = { items: AdminUser[]; next_cursor: string | null }
export type AdminUserQuery = { q?: string; role?: Role | ''; status?: 'active' | 'suspended' | ''; cursor?: string; limit?: number }
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
  provinces: () => request<Province[]>('GET', '/provinces'),
  applySeller: (b: { name: string; province_code: string }) => authed<SellerApplication>('POST', '/seller-applications', b),
  myApplication: () => authed<SellerApplication>('GET', '/seller-applications/me'),
  adminApplications: (query: { status?: ApplicationStatus | ''; cursor?: string; limit?: number }) => {
    const qs = new URLSearchParams(Object.entries(query).filter(([, v]) => v !== undefined && v !== '').map(([k, v]) => [k, String(v)]))
    return authed<AdminSellerApplicationPage>('GET', `/admin/seller-applications${qs.size ? `?${qs}` : ''}`)
  },
  approveApplication: (id: string) => authed<AdminSellerApplication>('POST', `/admin/seller-applications/${id}/approval`),
  rejectApplication: (id: string, reason: string) => authed<AdminSellerApplication>('POST', `/admin/seller-applications/${id}/rejection`, { reason }),
  resendVerification: () => authed<{ status: string }>('POST', '/auth/email-verifications'),
  confirmEmail: (token: string) => request<null>('POST', '/auth/email-verifications/confirmation', { token }),
  forgotPassword: (email: string) => request<{ status: string }>('POST', '/auth/password-resets', { email }),
  resetPassword: (token: string, new_password: string) => request<null>('POST', '/auth/password-resets/confirmation', { token, new_password }),
  myShop: () => authed<Shop>('GET', '/shops/me'),
  updateMyShop: (body: { name: string; province_code: string }) => authed<Shop>('PUT', '/shops/me', body),
  shopStatistics: () => authed<ShopStatistics>('GET', '/shops/me/statistics'),
  sellerProductCategories: () => authed<ProductCategory[]>('GET', '/shops/me/product-categories'),
  sellerProducts: ({ q, status, page }: { q: string; status: ProductStatus | ''; page: number }) => {
    const query = new URLSearchParams({ page: String(page) })
    if (q) query.set('q', q)
    if (status) query.set('status', status)
    return authed<SellerProductPage>('GET', `/shops/me/products?${query}`)
  },
  addSellerProduct: (product: ProductInput) => authed<SellerProduct>('POST', '/shops/me/products', product),
  updateSellerProduct: (id: string, product: ProductInput) => authed<SellerProduct>('PUT', `/shops/me/products/${encodeURIComponent(id)}`, product),
  changeSellerProductStatus: (id: string, status: ProductStatus) =>
    authed<SellerProduct>('PATCH', `/shops/me/products/${encodeURIComponent(id)}/status`, { status }),
  sellerOrders: ({ status, cursor }: { status?: OrderStatus; cursor?: string } = {}) => {
    const query = new URLSearchParams()
    if (status) query.set('status', status)
    if (cursor) query.set('cursor', cursor)
    return authed<SellerOrderPage>('GET', `/shops/me/orders${query.size ? `?${query}` : ''}`)
  },
  sellerOrder: (id: string) => authed<SellerOrder>('GET', `/orders/${encodeURIComponent(id)}`),
  shipSellerOrder: (id: string) => authed<SellerOrder>('POST', `/orders/${encodeURIComponent(id)}/shipment`),
  completeSellerOrder: (id: string) => authed<SellerOrder>('POST', `/orders/${encodeURIComponent(id)}/completion`),
  changePassword: (b: { current_password?: string; new_password: string }) => authed<null>('PUT', '/users/me/password', b),
  adminUsers: (query: AdminUserQuery) => {
    const qs = new URLSearchParams(Object.entries(query).filter(([, v]) => v !== undefined && v !== '').map(([k, v]) => [k, String(v)]))
    return authed<AdminUserPage>('GET', `/admin/users${qs.size ? `?${qs}` : ''}`)
  },
  adminUpdateUser: (id: string, b: { role?: 'buyer' | 'admin'; status?: 'active' | 'suspended' }) => authed<AdminUser>('PATCH', `/admin/users/${id}`, b),
  unlinkIdentity: (provider: Provider) => authed<null>('DELETE', `/users/me/identities/${provider}`),
}
