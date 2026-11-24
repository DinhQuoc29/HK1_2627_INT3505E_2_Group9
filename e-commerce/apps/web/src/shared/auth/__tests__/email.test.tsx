import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { AppRoutes } from '../../../App'
import { setAccessToken } from '../../api/client'

const mkUser = (verified: boolean) => ({ id: 'u1', email: 'an@example.com', full_name: 'An', role: 'buyer', created_at: '2026-01-01T00:00:00Z', providers: [], has_password: true, email_verified: verified })
const json = (body: unknown, status = 200) => new Response(body === null ? null : JSON.stringify(body), { status })
const problem = (status: number, type: string, detail: string) => new Response(JSON.stringify({ type: `/problems/${type}`, title: 't', status, detail }), { status })

type Call = { path: string; method: string; body?: unknown }
function setup(initial: string, opts: { user?: ReturnType<typeof mkUser> | null; route?: (c: Call) => Response | undefined }) {
  const calls: Call[] = []
  vi.stubGlobal('fetch', vi.fn(async (url: string, init?: RequestInit) => {
    const c = { path: url.replace('/api/v1', ''), method: init?.method ?? 'GET', body: init?.body ? JSON.parse(String(init.body)) : undefined }
    calls.push(c)
    if (c.path === '/auth/tokens') return opts.user ? json({ access_token: 't', token_type: 'Bearer', expires_in: 900, user: opts.user }) : problem(401, 'invalid-refresh-token', 'no')
    return opts.route?.(c) ?? json(null, 500)
  }))
  render(<MemoryRouter initialEntries={[initial]}><AppRoutes /></MemoryRouter>)
  return calls
}

afterEach(() => { vi.unstubAllGlobals(); setAccessToken(null) })

describe('Quên mật khẩu', () => {
  it('đăng nhập có liên kết "Quên mật khẩu?"', async () => {
    setup('/login', { user: null })
    await userEvent.click(await screen.findByRole('link', { name: 'Quên mật khẩu?' }))
    expect(await screen.findByRole('heading', { name: 'Quên mật khẩu' })).toBeInTheDocument()
  })

  it('kiểm tra email rồi gửi yêu cầu và hiện thông báo trung tính', async () => {
    const calls = setup('/forgot-password', { user: null, route: (c) => (c.path === '/auth/password-resets' ? json({ status: 'accepted' }, 202) : undefined) })
    await userEvent.type(await screen.findByLabelText('Email'), 'sai-email')
    await userEvent.click(screen.getByRole('button', { name: 'Gửi liên kết đặt lại' }))
    expect(await screen.findByText('Email không hợp lệ')).toBeInTheDocument()
    expect(calls.some((c) => c.path === '/auth/password-resets')).toBe(false)
    await userEvent.clear(screen.getByLabelText('Email'))
    await userEvent.type(screen.getByLabelText('Email'), 'an@example.com')
    await userEvent.click(screen.getByRole('button', { name: 'Gửi liên kết đặt lại' }))
    expect(await screen.findByRole('status')).toHaveTextContent('Nếu an@example.com đã đăng ký')
    expect(calls.find((c) => c.path === '/auth/password-resets')?.body).toEqual({ email: 'an@example.com' })
  })

  it('đặt lại mật khẩu bằng token trong link rồi về đăng nhập', async () => {
    const calls = setup('/reset-password?token=' + 'a'.repeat(30), { user: null, route: (c) => (c.path === '/auth/password-resets/confirmation' ? json(null, 204) : undefined) })
    await userEvent.type(await screen.findByLabelText('Mật khẩu mới'), 'yeu')
    await userEvent.type(screen.getByLabelText('Nhập lại mật khẩu mới'), 'khac')
    await userEvent.click(screen.getByRole('button', { name: 'Đổi mật khẩu' }))
    expect(await screen.findByText('Mật khẩu tối thiểu 8 ký tự')).toBeInTheDocument()
    await userEvent.clear(screen.getByLabelText('Mật khẩu mới'))
    await userEvent.clear(screen.getByLabelText('Nhập lại mật khẩu mới'))
    await userEvent.type(screen.getByLabelText('Mật khẩu mới'), 'MatkhauMoi9')
    await userEvent.type(screen.getByLabelText('Nhập lại mật khẩu mới'), 'MatkhauMoi9')
    await userEvent.click(screen.getByRole('button', { name: 'Đổi mật khẩu' }))
    expect(await screen.findByText(/Đã đổi mật khẩu/)).toBeInTheDocument()
    expect(calls.find((c) => c.path === '/auth/password-resets/confirmation')?.body).toEqual({ token: 'a'.repeat(30), new_password: 'MatkhauMoi9' })
  })

  it('token hết hạn: báo lỗi và gợi ý yêu cầu liên kết mới', async () => {
    setup('/reset-password?token=' + 'b'.repeat(30), { user: null, route: (c) => (c.path === '/auth/password-resets/confirmation' ? problem(400, 'invalid-reset-token', 'x') : undefined) })
    await userEvent.type(await screen.findByLabelText('Mật khẩu mới'), 'MatkhauMoi9')
    await userEvent.type(screen.getByLabelText('Nhập lại mật khẩu mới'), 'MatkhauMoi9')
    await userEvent.click(screen.getByRole('button', { name: 'Đổi mật khẩu' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('không hợp lệ hoặc đã hết hạn')
    expect(screen.getByRole('link', { name: 'Yêu cầu liên kết mới' })).toHaveAttribute('href', '/forgot-password')
  })

  it('thiếu token trong link', async () => {
    setup('/reset-password', { user: null })
    expect(await screen.findByRole('alert')).toHaveTextContent('Liên kết không hợp lệ')
  })
})

describe('Xác minh email', () => {
  it('link trong email xác minh thành công đúng một lần (kể cả khi chưa đăng nhập)', async () => {
    const calls = setup('/verify-email?token=' + 'c'.repeat(30), { user: null, route: (c) => (c.path === '/auth/email-verifications/confirmation' ? json(null, 204) : undefined) })
    expect(await screen.findByText(/đã được xác minh/)).toBeInTheDocument()
    expect(calls.filter((c) => c.path === '/auth/email-verifications/confirmation')).toHaveLength(1)
    expect(calls.find((c) => c.path === '/auth/email-verifications/confirmation')?.body).toEqual({ token: 'c'.repeat(30) })
  })

  it('token sai: báo lỗi', async () => {
    setup('/verify-email?token=' + 'd'.repeat(30), { user: null, route: (c) => (c.path === '/auth/email-verifications/confirmation' ? problem(400, 'invalid-email-token', 'x') : undefined) })
    expect(await screen.findByRole('alert')).toHaveTextContent('không hợp lệ hoặc đã hết hạn')
  })

  it('đã đăng nhập: xác minh xong thì biểu ngữ biến mất', async () => {
    let verified = false
    setup('/verify-email?token=' + 'e'.repeat(30), {
      user: mkUser(false),
      route: (c) => {
        if (c.path === '/auth/email-verifications/confirmation') { verified = true; return json(null, 204) }
        if (c.path === '/users/me') return json(mkUser(verified))
      },
    })
    await screen.findByText(/đã được xác minh/)
    await waitFor(() => expect(verified).toBe(true))
  })

  it('biểu ngữ nhắc xác minh và gửi lại email', async () => {
    const calls = setup('/account', { user: mkUser(false), route: (c) => (c.path === '/auth/email-verifications' ? json({ status: 'sent' }, 202) : undefined) })
    await userEvent.click(await screen.findByRole('button', { name: 'Gửi lại email xác minh' }))
    expect(await screen.findByText(/Đã gửi email xác minh/)).toBeInTheDocument()
    expect(calls.some((c) => c.path === '/auth/email-verifications' && c.method === 'POST')).toBe(true)
  })

  it('gửi lại quá nhanh: hiện lỗi từ server', async () => {
    setup('/account', { user: mkUser(false), route: (c) => (c.path === '/auth/email-verifications' ? problem(429, 'rate-limited', 'Bạn vừa yêu cầu gửi email.') : undefined) })
    await userEvent.click(await screen.findByRole('button', { name: 'Gửi lại email xác minh' }))
    expect(await screen.findByRole('alert')).toBeInTheDocument()
  })

  it('đã xác minh thì không có biểu ngữ', async () => {
    setup('/account', { user: mkUser(true) })
    await screen.findByRole('heading', { name: /Xin chào/ })
    expect(screen.queryByRole('button', { name: 'Gửi lại email xác minh' })).not.toBeInTheDocument()
  })
})
