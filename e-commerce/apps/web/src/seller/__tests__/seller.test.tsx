import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { AppRoutes } from '../../App'
import { setAccessToken } from '../../shared/api/client'

const mkUser = (role: string, verified = true) => ({ id: 'u1', email: 'an@example.com', full_name: 'An', role, created_at: '2026-01-01T00:00:00Z', providers: [], has_password: true, email_verified: verified })
const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status })
const problem = (status: number, type: string, detail: string, extra: object = {}) =>
  new Response(JSON.stringify({ type: `/problems/${type}`, title: 't', status, detail, ...extra }), { status })
const shop = { id: 's1', name: 'Shop An', province: { code: '01', name: 'Hà Nội' }, created_at: '2026-01-01T00:00:00Z' }
const application = (status: string, extra: object = {}) => ({ id: 'a1', shop_name: 'Shop An', province_code: '01', province_name: 'Hà Nội', status, reject_reason: null, created_at: '2026-01-01T00:00:00Z', reviewed_at: null, ...extra })

type Call = { url: string; method: string; body?: unknown }
function setup(
  user: ReturnType<typeof mkUser>,
  handler: (url: string, method: string) => Response | Promise<Response> | undefined,
  initialPath = '/seller/register',
) {
  const calls: Call[] = []
  vi.stubGlobal('fetch', vi.fn(async (url: string, init?: RequestInit) => {
    const method = init?.method ?? 'GET'
    calls.push({ url, method, body: init?.body ? JSON.parse(String(init.body)) : undefined })
    if (url.endsWith('/auth/tokens')) return json({ access_token: 't', token_type: 'Bearer', expires_in: 900, user })
    if (url.endsWith('/provinces')) return json([{ code: '01', name: 'Hà Nội' }, { code: '79', name: 'TP. Hồ Chí Minh' }])
    return handler(url, method) ?? json(null, 500)
  }))
  render(<MemoryRouter initialEntries={[initialPath]}><AppRoutes /></MemoryRouter>)
  return calls
}

afterEach(() => { vi.unstubAllGlobals(); setAccessToken(null) })

describe('Đăng ký người bán (nộp hồ sơ, chờ duyệt)', () => {
  it('kiểm tra form trước khi gọi API', async () => {
    const calls = setup(mkUser('buyer'), (url) => (url.endsWith('/seller-applications/me') ? problem(404, 'application-not-found', 'x') : undefined))
    await userEvent.click(await screen.findByRole('button', { name: 'Gửi hồ sơ' }))
    expect(await screen.findByText('Tên shop tối thiểu 3 ký tự')).toBeInTheDocument()
    expect(screen.getByText('Vui lòng chọn tỉnh/thành')).toBeInTheDocument()
    expect(calls.some((c) => c.method === 'POST' && c.url.endsWith('/seller-applications'))).toBe(false)
  })

  it('nộp hồ sơ thành công thì hiện trạng thái chờ duyệt', async () => {
    const calls = setup(mkUser('buyer'), (url, method) => {
      if (url.endsWith('/seller-applications/me')) return problem(404, 'application-not-found', 'x')
      if (url.endsWith('/seller-applications') && method === 'POST') return json(application('pending'), 201)
    })
    await userEvent.type(await screen.findByLabelText('Tên shop'), 'Shop An')
    await userEvent.selectOptions(screen.getByLabelText('Tỉnh/thành (nơi bán)'), '01')
    await userEvent.click(screen.getByRole('button', { name: 'Gửi hồ sơ' }))
    expect(await screen.findByRole('status', { name: 'Hồ sơ đang chờ duyệt' })).toHaveTextContent('Shop An')
    expect(calls.find((c) => c.method === 'POST' && c.url.endsWith('/seller-applications'))?.body).toEqual({ name: 'Shop An', province_code: '01' })
  })

  it('đã có hồ sơ chờ duyệt thì không hiện form', async () => {
    setup(mkUser('buyer'), (url) => (url.endsWith('/seller-applications/me') ? json(application('pending')) : undefined))
    expect(await screen.findByRole('status', { name: 'Hồ sơ đang chờ duyệt' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Gửi hồ sơ' })).not.toBeInTheDocument()
  })

  it('kiểm tra hồ sơ đã được duyệt rồi vào kênh người bán', async () => {
    let reviewed = false
    setup(mkUser('buyer'), (url) => {
      if (url.endsWith('/seller-applications/me')) return json(application(reviewed ? 'approved' : 'pending'))
      if (url.endsWith('/users/me')) return json(mkUser('seller'))
      if (url.endsWith('/shops/me')) return json(shop)
    })
    const check = await screen.findByRole('button', { name: 'Kiểm tra trạng thái' })
    reviewed = true
    await userEvent.click(check)
    expect(await screen.findByRole('heading', { name: 'Shop An' })).toBeInTheDocument()
  })

  it('bị từ chối: hiện lý do và cho nộp lại', async () => {
    setup(mkUser('buyer'), (url) => (url.endsWith('/seller-applications/me') ? json(application('rejected', { reject_reason: 'Tên shop vi phạm' })) : undefined))
    expect(await screen.findByRole('alert')).toHaveTextContent('Tên shop vi phạm')
    expect(screen.getByRole('button', { name: 'Gửi hồ sơ' })).toBeEnabled()
  })

  it('chưa xác minh email: khóa nút gửi và nhắc xác minh', async () => {
    setup(mkUser('buyer', false), (url) => (url.endsWith('/seller-applications/me') ? problem(404, 'application-not-found', 'x') : undefined))
    expect(await screen.findByRole('button', { name: 'Gửi hồ sơ' })).toBeDisabled()
    expect(screen.getByText(/cần xác minh email/)).toBeInTheDocument()
  })

  it('hiện lỗi từ server khi đã có hồ sơ chờ', async () => {
    setup(mkUser('buyer'), (url, method) => {
      if (url.endsWith('/seller-applications/me')) return problem(404, 'application-not-found', 'x')
      if (method === 'POST') return problem(409, 'application-pending', 'x')
    })
    await userEvent.type(await screen.findByLabelText('Tên shop'), 'Shop An')
    await userEvent.selectOptions(screen.getByLabelText('Tỉnh/thành (nơi bán)'), '79')
    await userEvent.click(screen.getByRole('button', { name: 'Gửi hồ sơ' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('đang chờ duyệt')
  })

  it('seller vào trang đăng ký thì được chuyển tới trang shop', async () => {
    setup(mkUser('seller'), (url) => (url.endsWith('/shops/me') ? json(shop) : undefined))
    expect(await screen.findByRole('heading', { name: 'Shop An' })).toBeInTheDocument()
  })
})

describe('Tổng quan shop', () => {
  it.each(['lỗi mạng', 'lỗi máy chủ'])('tải lại thông tin shop sau %s', async (failure) => {
    let resolveShop!: (response: Response) => void
    const pendingShop = new Promise<Response>((resolve) => { resolveShop = resolve })
    let attempts = 0
    setup(mkUser('seller'), (url) => {
      if (!url.endsWith('/shops/me')) return
      attempts += 1
      if (attempts === 2) return pendingShop
      if (failure === 'lỗi mạng') return Promise.reject(new Error('Offline'))
      return problem(503, 'unavailable', 'Máy chủ đang bận.')
    }, '/seller')

    expect(await screen.findByRole('alert')).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Thử lại' }))
    expect(await screen.findByRole('status')).toHaveTextContent('Đang tải shop')
    expect(screen.getByRole('link', { name: 'Tài khoản' })).toBeInTheDocument()

    resolveShop(json(shop))
    expect(await screen.findByRole('heading', { name: 'Shop An' })).toBeInTheDocument()
    expect(screen.getByText('Hà Nội')).toBeInTheDocument()
    expect(screen.getByText('1 thg 1, 2026')).toHaveAttribute('datetime', shop.created_at)
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
    expect(attempts).toBe(2)
  })

  it('hướng dẫn liên hệ quản trị viên khi tài khoản chưa có shop liên kết', async () => {
    setup(mkUser('seller'), (url) => (
      url.endsWith('/shops/me') ? problem(404, 'shop-not-found', 'Bạn chưa có shop.') : undefined
    ), '/seller')

    expect(await screen.findByRole('alert')).toHaveTextContent('Vui lòng liên hệ quản trị viên.')
    expect(screen.queryByRole('button', { name: 'Thử lại' })).not.toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Tài khoản' })).toBeInTheDocument()
  })
})
