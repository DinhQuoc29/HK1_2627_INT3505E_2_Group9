import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import AccountPage from '../../../buyer/AccountPage'
import { api, setAccessToken } from '../../api/client'
import { AuthProvider } from '../AuthContext'
import { GuestOnly, ProtectedRoute } from '../ProtectedRoute'
import LoginPage from '../pages/LoginPage'

const baseUser = { id: 'u1', email: 'an@example.com', full_name: 'Nguyễn Văn An', role: 'buyer', created_at: '2026-01-01T00:00:00Z' }
const payload = (user: object, token = 'tok') => ({ access_token: token, token_type: 'Bearer', expires_in: 900, user })
const json = (status: number, body: unknown) => new Response(body === null ? null : JSON.stringify(body), { status })
const problem = (status: number, slug: string, detail = 'x') => json(status, { type: `/problems/${slug}`, title: 't', status, detail })

type Call = { method: string; url: string; auth?: string | null }
function mockApi(routes: (call: Call) => Response) {
  const calls: Call[] = []
  vi.stubGlobal('fetch', vi.fn(async (url: string, init?: RequestInit) => {
    const headers = (init?.headers ?? {}) as Record<string, string>
    const call = { method: init?.method ?? 'GET', url: url.replace('/api/v1', ''), auth: headers.Authorization ?? null }
    calls.push(call)
    return routes(call)
  }))
  return calls
}

afterEach(() => { vi.unstubAllGlobals(); setAccessToken(null) })

describe('api client: access token hết hạn', () => {
  it('tự refresh một lần rồi gọi lại yêu cầu ban đầu', async () => {
    setAccessToken('old')
    const calls = mockApi((c) => {
      if (c.url === '/auth/tokens') return json(200, payload({ ...baseUser, providers: [], has_password: true }, 'new'))
      return c.auth === 'Bearer new' ? json(200, { ...baseUser, providers: [], has_password: true }) : problem(401, 'token-expired')
    })
    const me = await api.me()
    expect(me.email).toBe('an@example.com')
    expect(calls.map((c) => `${c.method} ${c.url} ${c.auth ?? ''}`.trim())).toEqual([
      'GET /users/me Bearer old', 'POST /auth/tokens', 'GET /users/me Bearer new',
    ])
  })

  it('refresh thất bại thì báo hết phiên và không gọi lại vô hạn', async () => {
    setAccessToken('old')
    const calls = mockApi((c) => (c.url === '/auth/tokens' ? problem(401, 'invalid-refresh-token') : problem(401, 'token-expired')))
    await expect(api.me()).rejects.toMatchObject({ status: 401 })
    expect(calls.filter((c) => c.url === '/users/me')).toHaveLength(1)
  })
})

function renderAt(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <AuthProvider>
        <Routes>
          <Route element={<GuestOnly />}><Route path="/login" element={<LoginPage />} /></Route>
          <Route element={<ProtectedRoute />}><Route path="/account" element={<AccountPage />} /></Route>
        </Routes>
      </AuthProvider>
    </MemoryRouter>,
  )
}

describe('Trang tài khoản', () => {
  it('hiển thị phương thức đăng nhập và hủy liên kết Google', async () => {
    let linked = true
    const calls = mockApi((c) => {
      const user = { ...baseUser, providers: linked ? ['google'] : [], has_password: true }
      if (c.url === '/auth/tokens') return json(200, payload(user))
      if (c.method === 'DELETE' && c.url === '/users/me/identities/google') { linked = false; return json(204, null) }
      if (c.url === '/users/me') return json(200, user)
      return problem(404, 'not-found')
    })
    renderAt('/account')
    expect(await screen.findByText('Đã liên kết')).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Hủy liên kết Google' }))
    expect(await screen.findByText('Đã hủy liên kết Google.')).toBeInTheDocument()
    expect(screen.getAllByText('Chưa liên kết')).toHaveLength(2) // Google và Facebook
    expect(calls.some((c) => c.method === 'DELETE')).toBe(true)
  })

  it('không cho hủy liên kết khi Google là cách đăng nhập duy nhất', async () => {
    mockApi((c) => (c.url === '/auth/tokens'
      ? json(200, payload({ ...baseUser, providers: ['google'], has_password: false }))
      : problem(404, 'not-found')))
    renderAt('/account')
    expect(await screen.findByRole('button', { name: 'Hủy liên kết Google' })).toBeDisabled()
    expect(screen.getByText('Đây là cách đăng nhập duy nhất của bạn.')).toBeInTheDocument()
    expect(screen.getByText(/Chưa thiết lập/)).toBeInTheDocument()
  })

  it('hiện lỗi từ máy chủ khi hủy liên kết thất bại', async () => {
    mockApi((c) => {
      if (c.url === '/auth/tokens') return json(200, payload({ ...baseUser, providers: ['google'], has_password: true }))
      return problem(409, 'last-login-method', 'Đây là cách đăng nhập duy nhất của bạn nên không thể hủy liên kết.')
    })
    renderAt('/account')
    await userEvent.click(await screen.findByRole('button', { name: 'Hủy liên kết Google' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('không thể hủy liên kết')
  })

  it('phiên hết hạn giữa chừng thì về trang đăng nhập kèm thông báo', async () => {
    let revoked = false
    mockApi((c) => {
      if (c.url === '/auth/tokens') return revoked ? problem(401, 'invalid-refresh-token') : json(200, payload({ ...baseUser, providers: ['google'], has_password: true }))
      revoked = true
      return problem(401, 'session-ended')
    })
    renderAt('/account')
    await userEvent.click(await screen.findByRole('button', { name: 'Hủy liên kết Google' }))
    expect(await screen.findByRole('heading', { name: 'Chào mừng trở lại' })).toBeInTheDocument()
    await waitFor(() => expect(screen.getByRole('status')).toHaveTextContent('Phiên đăng nhập đã hết hạn'))
  })
})
