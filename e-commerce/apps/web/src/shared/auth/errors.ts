import { ApiError, type FieldError } from '../api/client'

export type Described = { message?: string; fields: FieldError[] }

/** Chuyển lỗi API thành thông điệp cho người dùng: lỗi theo field hoặc lỗi chung của form. */
export function describeError(err: unknown): Described {
  if (!(err instanceof ApiError)) return { message: 'Đã có lỗi xảy ra, vui lòng thử lại.', fields: [] }
  if (err.status === 422 && err.errors.length) return { fields: err.errors }
  if (err.slug === 'email-already-registered') return { fields: [{ field: 'email', message: 'Email này đã được đăng ký.' }] }
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
