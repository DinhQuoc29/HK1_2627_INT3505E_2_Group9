import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { AppRoutes } from '../../../App'
import { setAccessToken } from '../../api/client'

type Role = 'buyer' | 'seller' | 'admin'
const mkUser = (role: Role, id = 'me') => ({ id, email: `${role}@example.com`, full_name: `Tên ${role}`, role, created_at: '2026-01-01T00:00:00Z', providers: [] as string[], has_password: true, email_verified: true })
const json = (body: unknown, status = 200) => new Response(body === null ? null : JSON.stringify(body), { status })
const problem = (status: number, type: string, detail: string, extra: object = {}) =>
  new Response(JSON.stringify({ type: `/problems/${type}`, title: 't', status, detail, ...extra }), { status })
const session = (role: Role) => ({ access_token: 'tok', token_type: 'Bearer', expires_in: 900, user: mkUser(role) })
const shop = { id: 's1', name: 'Shop An', province: { code: '01', name: 'Hà Nội' }, created_at: '2026-01-01T00:00:00Z' }
const adminUser = (o: object = {}) => ({ id: 'u2', email: 'khach@example.com', full_name: 'Khách Hàng', role: 'buyer', status: 'active', created_at: '2026-02-01T00:00:00Z', has_shop: false, ...o })

type Call = { method: string; path: string; body?: unknown }
/** `restore`: phiên khôi phục từ cookie lúc tải trang (null = chưa đăng nhập). */
function setup(opts: { restore: Role | null; login?: Role | Response; route: (c: Call) => Response | undefined; initial?: string }) {
  const calls: Call[] = []
  vi.stubGlobal('fetch', vi.fn(async (url: string, init?: RequestInit) => {
    const call = { method: init?.method ?? 'GET', path: url.replace('/api/v1', ''), body: init?.body ? JSON.parse(String(init.body)) : undefined }
    calls.push(call)
    if (call.path === '/auth/tokens') return opts.restore ? json(session(opts.restore)) : problem(401, 'invalid-refresh-token', 'no')
    if (call.path === '/auth/sessions' && call.method === 'POST') {
      return opts.login instanceof Response ? opts.login : json(session(opts.login ?? 'buyer'), 201)
    }
    if (call.path === '/auth/sessions/current') return json(null, 204)
    return opts.route(call) ?? json(null, 500)
  }))
  render(<MemoryRouter initialEntries={[opts.initial ?? '/']}><AppRoutes /></MemoryRouter>)
  return calls
}

async function signIn() {
  await userEvent.type(await screen.findByLabelText('Email'), 'a@example.com')
  await userEvent.type(screen.getByLabelText('Mật khẩu'), 'Matkhau123')
  await userEvent.click(screen.getByRole('button', { name: 'Đăng nhập' }))
}

afterEach(() => { vi.unstubAllGlobals(); setAccessToken(null) })

describe('điều hướng theo vai trò sau đăng nhập', () => {
  it('buyer vào /account', async () => {
    setup({ restore: null, login: 'buyer', route: () => undefined })
    await signIn()
    expect(await screen.findByRole('heading', { name: /Xin chào, Tên buyer/ })).toBeInTheDocument()
  })

  it('seller vào /seller', async () => {
    setup({ restore: null, login: 'seller', route: (c) => (c.path === '/shops/me' ? json(shop) : undefined) })
    await signIn()
    expect(await screen.findByRole('heading', { name: 'Shop An' })).toBeInTheDocument()
  })

  it('admin vào /admin', async () => {
    setup({ restore: null, login: 'admin', route: (c) => (c.path.startsWith('/admin/users') ? json({ items: [adminUser()], next_cursor: null }) : undefined) })
    await signIn()
    expect(await screen.findByRole('heading', { name: 'Quản trị người dùng' })).toBeInTheDocument()
    expect(await screen.findByText('khach@example.com')).toBeInTheDocument()
  })

  it('đã đăng nhập mà vào /login thì về trang vai trò', async () => {
    setup({ restore: 'admin', initial: '/login', route: (c) => (c.path.startsWith('/admin/users') ? json({ items: [], next_cursor: null }) : undefined) })
    expect(await screen.findByRole('heading', { name: 'Quản trị người dùng' })).toBeInTheDocument()
  })

  it('chưa đăng nhập vào /admin: chuyển sang đăng nhập rồi quay lại /admin', async () => {
    setup({ restore: null, login: 'admin', initial: '/admin', route: (c) => (c.path.startsWith('/admin/users') ? json({ items: [], next_cursor: null }) : undefined) })
    await signIn()
    expect(await screen.findByRole('heading', { name: 'Quản trị người dùng' })).toBeInTheDocument()
  })

  it('tài khoản bị khóa: báo lỗi rõ ràng, ở lại trang đăng nhập', async () => {
    setup({ restore: null, login: problem(403, 'account-suspended', 'x'), route: () => undefined })
    await signIn()
    expect(await screen.findByRole('alert')).toHaveTextContent('tạm khóa')
    expect(screen.getByRole('button', { name: 'Đăng nhập' })).toBeInTheDocument()
  })
})

describe('phân quyền route', () => {
  it('buyer vào /admin: trang 403, không gọi API quản trị', async () => {
    const calls = setup({ restore: 'buyer', initial: '/admin', route: () => undefined })
    expect(await screen.findByText('Bạn không có quyền truy cập trang này')).toBeInTheDocument()
    expect(calls.some((c) => c.path.startsWith('/admin'))).toBe(false)
  })

  it('seller vào /admin: trang 403', async () => {
    setup({ restore: 'seller', initial: '/admin', route: () => undefined })
    expect(await screen.findByText('Bạn không có quyền truy cập trang này')).toBeInTheDocument()
  })

  it('buyer vào /seller được chuyển sang đăng ký bán hàng', async () => {
    const calls = setup({ restore: 'buyer', initial: '/seller', route: (c) => (c.path === '/provinces' ? json([{ code: '01', name: 'Hà Nội' }]) : undefined) })
    expect(await screen.findByRole('heading', { name: 'Đăng ký bán hàng' })).toBeInTheDocument()
    expect(calls.some((c) => c.path === '/shops/me')).toBe(false)
  })

  it('khách vào /seller được đưa tới đăng nhập', async () => {
    const calls = setup({ restore: null, initial: '/seller', route: () => undefined })
    expect(await screen.findByRole('button', { name: 'Đăng nhập' })).toBeInTheDocument()
    expect(calls.some((c) => c.path === '/shops/me')).toBe(false)
  })

  it('admin vào /seller nhận trang 403', async () => {
    const calls = setup({ restore: 'admin', initial: '/seller', route: () => undefined })
    expect(await screen.findByRole('heading', { name: 'Bạn không có quyền truy cập trang này' })).toBeInTheDocument()
    expect(calls.some((c) => c.path === '/shops/me')).toBe(false)
  })

  it('admin không được đăng ký bán hàng (403)', async () => {
    setup({ restore: 'admin', initial: '/seller/register', route: () => undefined })
    expect(await screen.findByText('Bạn không có quyền truy cập trang này')).toBeInTheDocument()
  })

  it('menu người bán đánh dấu đúng trang hiện tại và có thể đăng xuất', async () => {
    setup({ restore: 'seller', initial: '/account', route: (c) => (c.path === '/shops/me' ? json(shop) : undefined) })
    const navName = 'Điều hướng kênh người bán'
    const accountNav = within(await screen.findByRole('navigation', { name: navName }))
    expect(accountNav.getAllByRole('link')).toHaveLength(2)
    expect(accountNav.getByRole('link', { name: 'Tài khoản' })).toHaveAttribute('aria-current', 'page')

    await userEvent.click(accountNav.getByRole('link', { name: 'Tổng quan' }))
    expect(await screen.findByRole('heading', { name: 'Shop An' })).toBeInTheDocument()
    const dashboardNav = within(screen.getByRole('navigation', { name: navName }))
    expect(dashboardNav.getByRole('link', { name: 'Tổng quan' })).toHaveAttribute('aria-current', 'page')

    await userEvent.click(dashboardNav.getByRole('link', { name: 'Tài khoản' }))
    expect(await screen.findByRole('heading', { name: 'Xin chào, Tên seller' })).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Đăng xuất' }))
    expect(await screen.findByRole('button', { name: 'Đăng nhập' })).toBeInTheDocument()
  })
})

describe('quản trị người dùng', () => {
  const list = (items: object[], next: string | null = null) => json({ items, next_cursor: next })

  it('khóa người dùng rồi cập nhật dòng; không tự khóa chính mình', async () => {
    const calls = setup({
      restore: 'admin', initial: '/admin',
      route: (c) => {
        if (c.path.startsWith('/admin/users?') || c.path === '/admin/users') return list([adminUser({ id: 'me', email: 'admin@example.com', role: 'admin' }), adminUser()])
        if (c.method === 'PATCH') return json(adminUser({ status: 'suspended' }))
      },
    })
    await screen.findByText('khach@example.com')
    expect(screen.getByRole('button', { name: 'Khóa admin@example.com' })).toBeDisabled()
    await userEvent.click(screen.getByRole('button', { name: 'Khóa khach@example.com' }))
    expect(await screen.findByText('Đã khóa tài khoản.')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Mở khóa khach@example.com' })).toBeInTheDocument()
    expect(calls.find((c) => c.method === 'PATCH')).toMatchObject({ path: '/admin/users/u2', body: { status: 'suspended' } })
  })

  it('cấp quyền admin; người bán không có nút đổi vai trò', async () => {
    const calls = setup({
      restore: 'admin', initial: '/admin',
      route: (c) => {
        if (c.method === 'PATCH') return json(adminUser({ role: 'admin' }))
        if (c.path.startsWith('/admin/users')) return list([adminUser(), adminUser({ id: 'u3', email: 'banhang@example.com', role: 'seller', has_shop: true })])
      },
    })
    await screen.findByText('banhang@example.com')
    expect(screen.queryByRole('button', { name: /quyền admin của banhang@example.com/ })).not.toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Cấp quyền admin của khach@example.com' }))
    expect(await screen.findByText('Đã cấp quyền admin.')).toBeInTheDocument()
    expect(calls.find((c) => c.method === 'PATCH')?.body).toEqual({ role: 'admin' })
  })

  it('lọc và tải thêm theo cursor', async () => {
    const calls = setup({
      restore: 'admin', initial: '/admin',
      route: (c) => {
        if (!c.path.startsWith('/admin/users')) return undefined
        return c.path.includes('cursor=abc') ? list([adminUser({ id: 'u9', email: 'trang2@example.com' })]) : list([adminUser()], 'abc')
      },
    })
    await screen.findByText('khach@example.com')
    await userEvent.click(screen.getByRole('button', { name: 'Tải thêm' }))
    expect(await screen.findByText('trang2@example.com')).toBeInTheDocument()
    expect(screen.getByText('khach@example.com')).toBeInTheDocument()
    await userEvent.selectOptions(screen.getByLabelText('Lọc theo vai trò'), 'seller')
    await waitFor(() => expect(calls.some((c) => c.path.includes('role=seller'))).toBe(true))
  })

  it('hiện lỗi khi API từ chối', async () => {
    setup({
      restore: 'admin', initial: '/admin',
      route: (c) => {
        if (c.method === 'PATCH') return problem(409, 'seller-has-shop', 'Người bán đang có shop nên không đổi vai trò được.')
        if (c.path.startsWith('/admin/users')) return list([adminUser()])
      },
    })
    await userEvent.click(await screen.findByRole('button', { name: 'Khóa khach@example.com' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Người bán đang có shop')
  })
})

describe('đổi mật khẩu', () => {
  const fill = async (cur: string, next: string, confirm = next) => {
    if (cur) await userEvent.type(screen.getByLabelText('Mật khẩu hiện tại'), cur)
    await userEvent.type(screen.getByLabelText('Mật khẩu mới'), next)
    await userEvent.type(screen.getByLabelText('Nhập lại mật khẩu mới'), confirm)
    await userEvent.click(screen.getByRole('button', { name: 'Đổi mật khẩu' }))
  }

  it('kiểm tra form trước khi gọi API', async () => {
    const calls = setup({ restore: 'buyer', initial: '/account', route: () => undefined })
    await screen.findByLabelText('Mật khẩu hiện tại')
    await fill('Matkhau123', 'yeu', 'khac')
    expect(await screen.findByText('Mật khẩu tối thiểu 8 ký tự')).toBeInTheDocument()
    expect(calls.some((c) => c.path === '/users/me/password')).toBe(false)
  })

  it('đổi thành công và báo các thiết bị khác bị đăng xuất', async () => {
    const calls = setup({ restore: 'buyer', initial: '/account', route: (c) => (c.path === '/users/me/password' ? json(null, 204) : c.path === '/users/me' ? json(mkUser('buyer')) : undefined) })
    await screen.findByLabelText('Mật khẩu hiện tại')
    await fill('Matkhau123', 'MatkhauMoi1')
    expect(await screen.findByText(/Đã đổi mật khẩu/)).toBeInTheDocument()
    expect(calls.find((c) => c.path === '/users/me/password')).toMatchObject({ method: 'PUT', body: { current_password: 'Matkhau123', new_password: 'MatkhauMoi1' } })
  })

  it('hiện lỗi ngay tại ô mật khẩu hiện tại khi sai', async () => {
    setup({
      restore: 'buyer', initial: '/account',
      route: (c) => (c.path === '/users/me/password'
        ? problem(422, 'validation-error', 'x', { errors: [{ field: 'current_password', message: 'Mật khẩu hiện tại không đúng.' }] })
        : undefined),
    })
    await screen.findByLabelText('Mật khẩu hiện tại')
    await fill('SaiMatKhau1', 'MatkhauMoi1')
    expect(await screen.findByText('Mật khẩu hiện tại không đúng.')).toBeInTheDocument()
  })
})
