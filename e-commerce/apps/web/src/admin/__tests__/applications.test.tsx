import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { AppRoutes } from '../../App'
import { setAccessToken } from '../../shared/api/client'

const admin = { id: 'ad', email: 'admin@example.com', full_name: 'Admin', role: 'admin', created_at: '2026-01-01T00:00:00Z', providers: [], has_password: true, email_verified: true }
const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status })
const problem = (status: number, type: string, detail: string, extra: object = {}) =>
  new Response(JSON.stringify({ type: `/problems/${type}`, title: 't', status, detail, ...extra }), { status })
const app = (o: object = {}) => ({
  id: 'a1', shop_name: 'Shop Hoa', province_code: '01', province_name: 'Hà Nội', status: 'pending', reject_reason: null,
  created_at: '2026-02-01T00:00:00Z', reviewed_at: null, applicant_id: 'u2', applicant_email: 'hoa@example.com', applicant_name: 'Chị Hoa', ...o,
})

type Call = { url: string; method: string; body?: unknown }
function setup(handler: (c: Call) => Response | undefined) {
  const calls: Call[] = []
  vi.stubGlobal('fetch', vi.fn(async (url: string, init?: RequestInit) => {
    const call = { url: url.replace('/api/v1', ''), method: init?.method ?? 'GET', body: init?.body ? JSON.parse(String(init.body)) : undefined }
    calls.push(call)
    if (call.url === '/auth/tokens') return json({ access_token: 't', token_type: 'Bearer', expires_in: 900, user: admin })
    return handler(call) ?? json(null, 500)
  }))
  render(<MemoryRouter initialEntries={['/admin/sellers']}><AppRoutes /></MemoryRouter>)
  return calls
}
const list = (items: object[], next: string | null = null) => json({ items, next_cursor: next })

afterEach(() => { vi.unstubAllGlobals(); setAccessToken(null) })

describe('Admin duyệt người bán', () => {
  it('mặc định chỉ tải hồ sơ chờ duyệt', async () => {
    const calls = setup((c) => (c.url.startsWith('/admin/seller-applications') ? list([app()]) : undefined))
    expect(await screen.findByText('Shop Hoa')).toBeInTheDocument()
    expect(screen.getByText(/hoa@example.com/)).toBeInTheDocument()
    expect(calls.find((c) => c.url.startsWith('/admin/seller-applications'))?.url).toContain('status=pending')
  })

  it('duyệt hồ sơ: gọi API, hồ sơ rời khỏi danh sách chờ', async () => {
    const calls = setup((c) => {
      if (c.method === 'POST' && c.url.startsWith('/admin')) return json(app({ status: 'approved' }))
      if (c.url.startsWith('/admin/seller-applications')) return list([app()])
    })
    await userEvent.click(await screen.findByRole('button', { name: 'Duyệt hồ sơ Shop Hoa' }))
    expect(await screen.findByText('Đã duyệt shop "Shop Hoa".')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Duyệt hồ sơ Shop Hoa' })).not.toBeInTheDocument()
    expect(calls.find((c) => c.method === 'POST' && c.url.startsWith('/admin'))?.url).toBe('/admin/seller-applications/a1/approval')
  })

  it('từ chối cần lý do hợp lệ rồi gửi lý do lên API', async () => {
    const calls = setup((c) => {
      if (c.method === 'POST' && c.url.startsWith('/admin')) return json(app({ status: 'rejected', reject_reason: 'Tên shop vi phạm' }))
      if (c.url.startsWith('/admin/seller-applications')) return list([app()])
    })
    await userEvent.click(await screen.findByRole('button', { name: 'Từ chối hồ sơ Shop Hoa' }))
    await userEvent.click(screen.getByRole('button', { name: 'Xác nhận từ chối' }))
    expect(await screen.findByText('Lý do tối thiểu 3 ký tự')).toBeInTheDocument()
    expect(calls.some((c) => c.method === 'POST' && c.url.startsWith('/admin'))).toBe(false)
    await userEvent.type(screen.getByLabelText('Lý do từ chối'), 'Tên shop vi phạm')
    await userEvent.click(screen.getByRole('button', { name: 'Xác nhận từ chối' }))
    expect(await screen.findByText('Đã từ chối hồ sơ "Shop Hoa".')).toBeInTheDocument()
    expect(calls.find((c) => c.method === 'POST' && c.url.startsWith('/admin'))).toMatchObject({ url: '/admin/seller-applications/a1/rejection', body: { reason: 'Tên shop vi phạm' } })
  })

  it('hiện lỗi khi hồ sơ đã được admin khác xử lý', async () => {
    setup((c) => {
      if (c.method === 'POST' && c.url.startsWith('/admin')) return problem(409, 'application-not-pending', 'x')
      if (c.url.startsWith('/admin/seller-applications')) return list([app()])
    })
    await userEvent.click(await screen.findByRole('button', { name: 'Duyệt hồ sơ Shop Hoa' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('đã được xử lý')
  })

  it('đổi bộ lọc và tải thêm', async () => {
    const calls = setup((c) => {
      if (!c.url.startsWith('/admin/seller-applications')) return undefined
      if (c.url.includes('cursor=abc')) return list([app({ id: 'a2', shop_name: 'Shop Trang Hai' })])
      if (c.url.includes('status=rejected')) return list([app({ id: 'a3', status: 'rejected', shop_name: 'Shop Bi Tu Choi', reject_reason: 'Sai thông tin' })])
      return list([app()], 'abc')
    })
    await screen.findByText('Shop Hoa')
    await userEvent.click(screen.getByRole('button', { name: 'Tải thêm' }))
    expect(await screen.findByText('Shop Trang Hai')).toBeInTheDocument()
    await userEvent.selectOptions(screen.getByLabelText('Lọc theo trạng thái hồ sơ'), 'rejected')
    expect(await screen.findByText('Shop Bi Tu Choi')).toBeInTheDocument()
    expect(screen.getByText(/Sai thông tin/)).toBeInTheDocument()
    expect(calls.some((c) => c.url.includes('status=rejected'))).toBe(true)
  })
})
