import { loginSchema, registerSchema } from '../schemas'
import { describeError, safeRedirect } from '../errors'
import { ApiError } from '../../api/client'

const ok = { full_name: 'Nguyễn Văn An', email: 'AN@Example.com ', password: 'Matkhau123', confirm: 'Matkhau123' }

describe('registerSchema', () => {
  it('chấp nhận dữ liệu hợp lệ và chuẩn hóa email', () => {
    const r = registerSchema.safeParse(ok)
    expect(r.success).toBe(true)
    if (r.success) expect(r.data.email).toBe('AN@Example.com')
  })
  it.each([
    [{ password: 'short1', confirm: 'short1' }, 'password'],
    [{ password: 'chiCoChuCai', confirm: 'chiCoChuCai' }, 'password'],
    [{ password: '12345678', confirm: '12345678' }, 'password'],
    [{ confirm: 'Khac12345' }, 'confirm'],
    [{ email: 'khong-phai-email' }, 'email'],
    [{ full_name: '   ' }, 'full_name'],
  ])('từ chối %j', (patch, field) => {
    const r = registerSchema.safeParse({ ...ok, ...patch })
    expect(r.success).toBe(false)
    if (!r.success) expect(r.error.issues.map((i) => i.path[0])).toContain(field)
  })
  it('từ chối mật khẩu quá 72 byte', () => {
    const long = 'a1' + 'ệ'.repeat(40)
    expect(registerSchema.safeParse({ ...ok, password: long, confirm: long }).success).toBe(false)
  })
})

describe('loginSchema', () => {
  it('yêu cầu email và mật khẩu', () => {
    expect(loginSchema.safeParse({ email: '', password: '' }).success).toBe(false)
    expect(loginSchema.safeParse({ email: 'a@b.co', password: 'x' }).success).toBe(true)
  })
})

describe('describeError', () => {
  it('map 422 sang lỗi theo field', () => {
    const e = new ApiError(422, 'validation-error', 'x', [{ field: 'password', message: 'Sai' }])
    expect(describeError(e).fields).toEqual([{ field: 'password', message: 'Sai' }])
  })
  it('map 409 sang lỗi ở ô email', () => {
    expect(describeError(new ApiError(409, 'email-already-registered', 'x')).fields[0].field).toBe('email')
  })
  it('báo số phút khi bị khóa (429)', () => {
    expect(describeError(new ApiError(429, 'account-locked', 'x', [], 600)).message).toContain('10 phút')
  })
})

describe('safeRedirect', () => {
  it.each([['/orders', '/orders'], ['//evil.com', '/account'], ['https://evil.com', '/account'], [undefined, '/account']])(
    '%s -> %s', (input, out) => expect(safeRedirect(input)).toBe(out),
  )
})
