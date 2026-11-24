import { z } from 'zod'

/** Quy tắc khớp backend (accounts/schema.py). */
export const passwordRules = [
  { id: 'length', label: 'Tối thiểu 8 ký tự', test: (v: string) => v.length >= 8 },
  { id: 'letter', label: 'Có chữ cái', test: (v: string) => /\p{L}/u.test(v) },
  { id: 'digit', label: 'Có chữ số', test: (v: string) => /\d/.test(v) },
]

const email = z.string().trim().min(1, 'Vui lòng nhập email').max(255).pipe(z.email('Email không hợp lệ'))

export const loginSchema = z.object({
  email,
  password: z.string().min(1, 'Vui lòng nhập mật khẩu'),
})

export const registerSchema = z
  .object({
    full_name: z.string().trim().min(1, 'Vui lòng nhập họ tên').max(100, 'Họ tên tối đa 100 ký tự'),
    email,
    password: z
      .string()
      .min(8, 'Mật khẩu tối thiểu 8 ký tự')
      .refine((v) => new TextEncoder().encode(v).length <= 72, 'Mật khẩu tối đa 72 byte')
      .refine((v) => /\p{L}/u.test(v) && /\d/.test(v), 'Mật khẩu cần có cả chữ và số'),
    confirm: z.string().min(1, 'Vui lòng nhập lại mật khẩu'),
  })
  .refine((d) => d.password === d.confirm, { path: ['confirm'], message: 'Mật khẩu nhập lại không khớp' })

export type LoginValues = z.infer<typeof loginSchema>
export type RegisterValues = z.infer<typeof registerSchema>
