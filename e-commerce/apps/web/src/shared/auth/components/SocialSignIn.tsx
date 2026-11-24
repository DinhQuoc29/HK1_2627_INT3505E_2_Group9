import { FacebookSignIn } from './FacebookSignIn'
import { GoogleSignIn, type GoogleText } from './GoogleSignIn'

const wording: Record<'signin' | 'signup', { google: GoogleText; facebook: string }> = {
  signin: { google: 'signin_with', facebook: 'Đăng nhập bằng Facebook' },
  signup: { google: 'signup_with', facebook: 'Đăng ký bằng Facebook' },
}

/** Khối nút đăng nhập xã hội dùng chung; hai nút cùng rộng, cao, bo tròn và cùng cách đặt tên theo ngữ cảnh. */
export function SocialSignIn({
  mode, onGoogle, onFacebook, onError,
}: {
  mode: 'signin' | 'signup'
  onGoogle: (credential: string) => void
  onFacebook: (accessToken: string) => void
  onError: (message: string) => void
}) {
  const w = wording[mode]
  return (
    <div className="space-y-3">
      <GoogleSignIn text={w.google} onCredential={onGoogle} onError={() => onError('Không thể đăng nhập bằng Google. Vui lòng thử lại.')} />
      <FacebookSignIn label={w.facebook} onToken={onFacebook} onError={onError} />
    </div>
  )
}
