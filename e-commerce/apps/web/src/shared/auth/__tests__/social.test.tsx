import { render, screen } from '@testing-library/react'
import { SocialSignIn } from '../components/SocialSignIn'

describe('SocialSignIn: hai nút Google và Facebook đồng bộ', () => {
  it.each([
    ['signin', 'Đăng nhập bằng Facebook'],
    ['signup', 'Đăng ký bằng Facebook'],
  ] as const)('chế độ %s: nút Facebook đặt tên đúng ngữ cảnh', (mode, label) => {
    render(<SocialSignIn mode={mode} onGoogle={vi.fn()} onFacebook={vi.fn()} onError={vi.fn()} />)
    expect(screen.getByRole('button', { name: new RegExp(label) })).toBeInTheDocument()
  })

  it('hai nút (kể cả khi chưa cấu hình) cùng cao, cùng bo tròn và cùng kiểu chữ', () => {
    render(<SocialSignIn mode="signin" onGoogle={vi.fn()} onFacebook={vi.fn()} onError={vi.fn()} />)
    const [google, facebook] = screen.getAllByRole('button')
    for (const b of [google, facebook]) {
      expect(b.className).toContain('h-10')
      expect(b.className).toContain('rounded-full')
      expect(b.className).toContain('w-full')
      expect(b.style.fontFamily).toContain('Roboto')
    }
  })
})
