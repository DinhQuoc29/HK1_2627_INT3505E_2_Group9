import { ApiError, type FieldError } from '../api/client'

export type Described = { message?: string; fields: FieldError[] }

/** Chuyển lỗi API thành thông điệp cho người dùng: lỗi theo field hoặc lỗi chung của form. */
export function describeError(err: unknown): Described {
  if (!(err instanceof ApiError)) return { message: 'Đã có lỗi xảy ra, vui lòng thử lại.', fields: [] }
  if (err.status === 422 && err.errors.length) return { fields: err.errors }
  if (err.slug === 'email-already-registered') return { fields: [{ field: 'email', message: 'Email này đã được đăng ký.' }] }
  if (err.slug === 'account-suspended') return { message: 'Tài khoản của bạn đã bị tạm khóa. Vui lòng liên hệ quản trị viên.', fields: [] }
  if (err.slug === 'email-not-verified') return { message: 'Hãy xác minh email trước khi đăng ký bán hàng.', fields: [] }
  if (err.slug === 'application-pending') return { message: 'Bạn đã có hồ sơ đang chờ duyệt.', fields: [] }
  if (err.slug === 'application-not-pending') return { message: 'Hồ sơ này đã được xử lý trước đó.', fields: [] }
  if (err.slug === 'invalid-email-token') return { message: 'Liên kết xác minh không hợp lệ hoặc đã hết hạn.', fields: [] }
  if (err.slug === 'invalid-reset-token') return { message: 'Liên kết đặt lại mật khẩu không hợp lệ hoặc đã hết hạn.', fields: [] }
  if (err.slug === 'email-already-verified') return { message: 'Email của bạn đã được xác minh.', fields: [] }
  if (err.slug === 'shop-already-exists') return { message: 'Bạn đã có shop rồi.', fields: [] }
  if (err.slug === 'rate-limited') {
    return { message: `Bạn thao tác quá nhanh. Vui lòng thử lại sau ${err.retryAfter ?? 60} giây.`, fields: [] }
  }
  if (err.status === 429) {
    const mins = err.retryAfter ? Math.max(1, Math.ceil(err.retryAfter / 60)) : null
    return { message: `Bạn đăng nhập sai quá nhiều lần. ${mins ? `Vui lòng thử lại sau khoảng ${mins} phút.` : 'Vui lòng thử lại sau.'}`, fields: [] }
  }
  return { message: err.message, fields: [] }
}

/** Chỉ cho phép quay lại đường dẫn nội bộ (chống open redirect). */
export function safeRedirect(from: unknown, fallback = '/account'): string {
  return typeof from === 'string' && /^\/(?!\/)/.test(from) ? from : fallback
}
