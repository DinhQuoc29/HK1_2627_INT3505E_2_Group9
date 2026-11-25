import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import AccountPage from '../../../buyer/AccountPage'
import { setAccessToken } from '../../api/client'
import { AuthProvider } from '../AuthContext'
import { FacebookSignIn } from '../components/FacebookSignIn'
import { GuestOnly, ProtectedRoute } from '../ProtectedRoute'
import LoginPage from '../pages/LoginPage'
import RegisterPage from '../pages/RegisterPage'

type LoginCb = (r: { authResponse?: { accessToken: string } | null }) => void
const baseUser = { id: 'u1', email: 'an@example.com', full_name: 'Nguyễn Văn An', role: 'buyer', created_at: '2026-01-01T00:00:00Z' }
const payload = (user: object) => ({ access_token: 'tok', token_type: 'Bearer', expires_in: 900, user })
const json = (status: number, body: unknown) => new Response(body === null ? null : JSON.stringify(body), { status })
const problem = (status: number, slug: string, detail: string) => json(status, { type: `/problems/${slug}`, title: 't', status, detail })

function installFb(result: Parameters<LoginCb>[0]) {
  const fb = { init: vi.fn(), login: vi.fn((cb: LoginCb) => cb(result)) }
  window.FB = fb
  return fb
}

type Call = { method: string; url: string; body?: unknown }
function mockApi(routes: (c: Call) => Response) {
  const calls: Call[] = []
  vi.stubGlobal('fetch', vi.fn(async (url: string, init?: RequestInit) => {
    const call = { method: init?.method ?? 'GET', url: url.replace('/api/v1', ''), body: init?.body ? JSON.parse(init.body as string) : undefined }
    calls.push(call)
    return call.url === '/auth/tokens' ? problem(401, 'invalid-refresh-token', 'no session') : routes(call)
  }))
  return calls
}

afterEach(() => { vi.unstubAllGlobals(); vi.unstubAllEnvs(); delete window.FB; setAccessToken(null) })

describe('FacebookSignIn', () => {
  it('chưa cấu hình App ID thì nút bị vô hiệu kèm giải thích', () => {
    render(<FacebookSignIn appId="" onToken={vi.fn()} onError={vi.fn()} />)
    expect(screen.getByRole('button', { name: /Facebook/ })).toBeDisabled()
    expect(screen.getByText(/VITE_FACEBOOK_APP_ID/)).toBeInTheDocument()
  })

  it('xin quyền email và trả access token khi đăng nhập thành công', async () => {
    const fb = installFb({ authResponse: { accessToken: 'fb-token' } })
    const onToken = vi.fn()
    render(<FacebookSignIn appId="app-1" onToken={onToken} onError={vi.fn()} />)
    const btn = await screen.findByRole('button', { name: /Facebook/ })
    await waitFor(() => expect(btn).toBeEnabled())
    await userEvent.click(btn)
    expect(fb.login).toHaveBeenCalledWith(expect.any(Function), { scope: 'public_profile,email' })
    expect(onToken).toHaveBeenCalledWith('fb-token')
  })

  it('người dùng đóng cửa sổ Facebook thì không báo lỗi và không gọi API', async () => {
    installFb({ authResponse: null })
    const onToken = vi.fn()
    const onError = vi.fn()
    render(<FacebookSignIn appId="app-1" onToken={onToken} onError={onError} />)
    const btn = await screen.findByRole('button', { name: /Facebook/ })
    await waitFor(() => expect(btn).toBeEnabled())
    await userEvent.click(btn)
    expect(onToken).not.toHaveBeenCalled()
    expect(onError).not.toHaveBeenCalled()
  })
})

function renderAuth(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <AuthProvider>
        <Routes>
          <Route element={<GuestOnly />}>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
          </Route>
          <Route element={<ProtectedRoute />}><Route path="/account" element={<AccountPage />} /></Route>
        </Routes>
      </AuthProvider>
    </MemoryRouter>,
  )
}

describe('Đăng nhập bằng Facebook', () => {
  it.each(['/login', '/register'])('%s: gửi access token tới API rồi vào trang tài khoản', async (path) => {
    vi.stubEnv('VITE_FACEBOOK_APP_ID', 'app-1')
    installFb({ authResponse: { accessToken: 'fb-token' } })
    const calls = mockApi((c) => (c.url === '/auth/sessions/facebook' ? json(201, payload({ ...baseUser, providers: ['facebook'], has_password: false })) : problem(404, 'not-found', 'x')))
    renderAuth(path)
    const btn = await screen.findByRole('button', { name: /Facebook/ })
    await waitFor(() => expect(btn).toBeEnabled())
    await userEvent.click(btn)
    expect(await screen.findByRole('heading', { name: /Xin chào, Nguyễn Văn An/ })).toBeInTheDocument()
    expect(calls.find((c) => c.url === '/auth/sessions/facebook')?.body).toEqual({ access_token: 'fb-token' })
  })

  it('email Facebook đã có tài khoản (409) hiện hướng dẫn thay vì tự gộp', async () => {
    vi.stubEnv('VITE_FACEBOOK_APP_ID', 'app-1')
    installFb({ authResponse: { accessToken: 'fb-token' } })
    mockApi(() => problem(409, 'account-exists', 'Email của Facebook đã có tài khoản. Hãy đăng nhập bằng mật khẩu hoặc Google, rồi liên kết Facebook trong trang tài khoản.'))
    renderAuth('/login')
    const btn = await screen.findByRole('button', { name: /Facebook/ })
    await waitFor(() => expect(btn).toBeEnabled())
    await userEvent.click(btn)
    expect(await screen.findByRole('alert')).toHaveTextContent('liên kết Facebook trong trang tài khoản')
  })
})

describe('Liên kết Facebook ở trang tài khoản', () => {
  it('liên kết rồi hiện trạng thái đã liên kết', async () => {
    vi.stubEnv('VITE_FACEBOOK_APP_ID', 'app-1')
    installFb({ authResponse: { accessToken: 'fb-token' } })
    let providers: string[] = []
    const calls: Call[] = []
    vi.stubGlobal('fetch', vi.fn(async (url: string, init?: RequestInit) => {
      const c = { method: init?.method ?? 'GET', url: url.replace('/api/v1', ''), body: init?.body ? JSON.parse(init.body as string) : undefined }
      calls.push(c)
      if (c.url === '/auth/tokens') return json(200, payload({ ...baseUser, providers, has_password: true }))
      if (c.method === 'POST' && c.url === '/users/me/identities') { providers = ['facebook']; return json(201, { ...baseUser, providers, has_password: true }) }
      return problem(404, 'not-found', 'x')
    }))
    renderAuth('/account')
    const btn = await screen.findByRole('button', { name: /Tiếp tục với Facebook/ })
    await waitFor(() => expect(btn).toBeEnabled())
    await userEvent.click(btn)
    expect(await screen.findByText('Đã liên kết tài khoản Facebook.')).toBeInTheDocument()
    expect(calls.find((c) => c.url === '/users/me/identities')?.body).toEqual({ provider: 'facebook', credential: 'fb-token' })
    expect(screen.getByRole('button', { name: 'Hủy liên kết Facebook' })).toBeEnabled()
  })

  it('cho hủy một nhà cung cấp khi còn nhà cung cấp khác dù chưa có mật khẩu', async () => {
    vi.stubGlobal('fetch', vi.fn(async (url: string) => (url.endsWith('/auth/tokens')
      ? json(200, payload({ ...baseUser, providers: ['facebook', 'google'], has_password: false }))
      : problem(404, 'not-found', 'x'))))
    renderAuth('/account')
    expect(await screen.findByRole('button', { name: 'Hủy liên kết Facebook' })).toBeEnabled()
    expect(screen.getByRole('button', { name: 'Hủy liên kết Google' })).toBeEnabled()
  })
})
