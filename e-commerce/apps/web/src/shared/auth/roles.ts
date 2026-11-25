import type { Role } from '../api/client'

export const roleLabel: Record<Role, string> = { buyer: 'Người mua', seller: 'Người bán', admin: 'Quản trị viên' }

/** Trang chủ của từng vai trò: nơi chuyển tới sau khi đăng nhập. */
export function homeFor(role: Role): string {
  return role === 'admin' ? '/admin' : role === 'seller' ? '/seller' : '/'
}
