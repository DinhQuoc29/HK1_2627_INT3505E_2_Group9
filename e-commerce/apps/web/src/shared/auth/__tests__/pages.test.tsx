import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { AuthProvider } from '../AuthContext'
import { GuestOnly, ProtectedRoute } from '../ProtectedRoute'
import LoginPage from '../pages/LoginPage'
import RegisterPage from '../pages/RegisterPage'

const user = { id: 'u1', email: 'an@example.com', full_name: 'Nguyễn Văn An', role: 'buyer', created_at: '2026-01-01T00:00:00Z' }
const problem = (status: number, type: string, detail: string, extra: object = {}) =>
  new Response(JSON.stringify({ type: `/problems/${type}`, title: 't', status, detail, ...extra }), { status, headers: { 'Content-Type': 'application/problem+json' } })
const ok = (status = 201) => new Response(JSON.stringify({ access_token: 'tok', token_type: 'Bearer', expires_in: 900, user }), { status })

type Handler = (url: string, init?: RequestInit) => Response
function mockFetch(h: Handler) {
  const calls: { url: string; init?: RequestInit }[] = []
  vi.stubGlobal('fetch', vi.fn(async (url: string, init?: RequestInit) => {
    calls.push({ url, init })
    return url.endsWith('/auth/tokens') ? problem(401, 'invalid-refresh-token', 'no session') : h(url, init)
  }))
  return calls
}

function renderApp(initial = '/login') {
  return render(
    <MemoryRouter initialEntries={[initial]}>
      <AuthProvider>
        <Routes>
          <Route element={<GuestOnly />}>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
          </Route>
          <Route element={<ProtectedRoute />}>
            <Route path="/account" element={<h1>Tài khoản của tôi</h1>} />
          </Route>
        </Routes>
      </AuthProvider>
    </MemoryRouter>,
  )
}

afterEach(() => vi.unstubAllGlobals())

describe('Đăng nhập', () => {
  it('hiển thị lỗi kiểm tra ngay trên form và không gọi API', async () => {
    const calls = mockFetch(() => ok())
    renderApp()
    await screen.findByRole('button', { name: 'Đăng nhập' })
    await userEvent.type(screen.getByLabelText('Email'), 'sai-email')
    await userEvent.click(screen.getByRole('button', { name: 'Đăng nhập' }))
    expect(await screen.findByText('Email không hợp lệ')).toBeInTheDocument()
    expect(await screen.findByText('Vui lòng nhập mật khẩu')).toBeInTheDocument()
    expect(calls.filter((c) => c.url.endsWith('/auth/sessions'))).toHaveLength(0)
  })

  it('đăng nhập đúng thì vào trang tài khoản và gửi đúng body', async () => {
    const calls = mockFetch(() => ok())
    renderApp()
    await userEvent.type(await screen.findByLabelText('Email'), 'an@example.com')
    await userEvent.type(screen.getByLabelText('Mật khẩu'), 'Matkhau123')
    await userEvent.click(screen.getByRole('button', { name: 'Đăng nhập' }))
    expect(await screen.findByRole('heading', { name: 'Tài khoản của tôi' })).toBeInTheDocument()
    const call = calls.find((c) => c.url.endsWith('/auth/sessions'))!
    expect(JSON.parse(call.init!.body as string)).toEqual({ email: 'an@example.com', password: 'Matkhau123' })
  })

  it('sai mật khẩu hiện thông báo chung (role=alert)', async () => {
    mockFetch(() => problem(401, 'invalid-credentials', 'Email hoặc mật khẩu không đúng.'))
    renderApp()
    await userEvent.type(await screen.findByLabelText('Email'), 'an@example.com')
    await userEvent.type(screen.getByLabelText('Mật khẩu'), 'Sai12345')
    await userEvent.click(screen.getByRole('button', { name: 'Đăng nhập' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Email hoặc mật khẩu không đúng.')
  })

  it('nút hiện/ẩn mật khẩu hoạt động', async () => {
    mockFetch(() => ok())
    renderApp()
    const input = await screen.findByLabelText('Mật khẩu')
    expect(input).toHaveAttribute('type', 'password')
    await userEvent.click(screen.getByRole('button', { name: 'Hiện mật khẩu' }))
    expect(input).toHaveAttribute('type', 'text')
  })

  it('route cần đăng nhập chuyển về /login khi chưa có phiên', async () => {
    mockFetch(() => ok())
    renderApp('/account')
    expect(await screen.findByRole('heading', { name: 'Chào mừng trở lại' })).toBeInTheDocument()
  })
})

describe('Đăng ký', () => {
  it('hiện checklist mật khẩu theo thời gian thực', async () => {
    mockFetch(() => ok())
    renderApp('/register')
    const pw = await screen.findByLabelText('Mật khẩu')
    await userEvent.type(pw, 'abcdefgh')
    expect(screen.getByText(/Tối thiểu 8 ký tự/)).toHaveTextContent('đã đạt')
    expect(screen.getByText(/Có chữ số/)).toHaveTextContent('chưa đạt')
  })

  it('email đã tồn tại (409) hiện lỗi ở ô email', async () => {
    mockFetch(() => problem(409, 'email-already-registered', 'Email này đã được đăng ký.'))
    renderApp('/register')
    await userEvent.type(await screen.findByLabelText('Họ và tên'), 'Nguyễn Văn An')
    await userEvent.type(screen.getByLabelText('Email'), 'an@example.com')
    await userEvent.type(screen.getByLabelText('Mật khẩu'), 'Matkhau123')
    await userEvent.type(screen.getByLabelText('Nhập lại mật khẩu'), 'Matkhau123')
    await userEvent.click(screen.getByRole('button', { name: 'Tạo tài khoản' }))
    await waitFor(() => expect(screen.getByLabelText('Email')).toHaveAttribute('aria-invalid', 'true'))
    expect(screen.getByText('Email này đã được đăng ký.')).toBeInTheDocument()
  })

  it('đăng ký thành công không gửi trường confirm', async () => {
    const calls = mockFetch(() => ok())
    renderApp('/register')
    await userEvent.type(await screen.findByLabelText('Họ và tên'), 'Nguyễn Văn An')
    await userEvent.type(screen.getByLabelText('Email'), 'an@example.com')
    await userEvent.type(screen.getByLabelText('Mật khẩu'), 'Matkhau123')
    await userEvent.type(screen.getByLabelText('Nhập lại mật khẩu'), 'Matkhau123')
    await userEvent.click(screen.getByRole('button', { name: 'Tạo tài khoản' }))
    expect(await screen.findByRole('heading', { name: 'Tài khoản của tôi' })).toBeInTheDocument()
    const body = JSON.parse(calls.find((c) => c.url.endsWith('/users'))!.init!.body as string)
    expect(body).toEqual({ full_name: 'Nguyễn Văn An', email: 'an@example.com', password: 'Matkhau123' })
  })
})

describe('Khôi phục phiên', () => {
  it('gọi refresh đúng một lần dù StrictMode mount hai lần', async () => {
    const { StrictMode } = await import('react')
    const calls: string[] = []
    vi.stubGlobal('fetch', vi.fn(async (url: string) => {
      calls.push(url)
      await new Promise((r) => setTimeout(r, 20))
      return ok(200)
    }))
    render(
      <StrictMode>
        <MemoryRouter initialEntries={['/account']}>
          <AuthProvider>
            <Routes><Route element={<ProtectedRoute />}><Route path="/account" element={<h1>Tài khoản của tôi</h1>} /></Route></Routes>
          </AuthProvider>
        </MemoryRouter>
      </StrictMode>,
    )
    expect(await screen.findByRole('heading', { name: 'Tài khoản của tôi' })).toBeInTheDocument()
    expect(calls.filter((u) => u.endsWith('/auth/tokens'))).toHaveLength(1)
  })
})
