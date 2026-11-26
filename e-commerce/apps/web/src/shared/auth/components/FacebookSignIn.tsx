import { useEffect, useState } from 'react'
import { SOCIAL_FONT } from './socialStyle'

type FbAuthResponse = { authResponse?: { accessToken: string } | null; status?: string }
type FbSdk = {
  init: (o: { appId: string; cookie: boolean; xfbml: boolean; version: string }) => void
  login: (cb: (r: FbAuthResponse) => void, o: { scope: string }) => void
}
declare global {
  interface Window { FB?: FbSdk; fbAsyncInit?: () => void }
}

/** App ID đọc lúc chạy để dễ kiểm thử; rỗng nghĩa là Facebook chưa được cấu hình. */
export const facebookAppId = (): string => import.meta.env.VITE_FACEBOOK_APP_ID ?? ''

let sdk: Promise<FbSdk> | null = null
let initialized = false

/** Nạp Facebook JS SDK một lần (chỉ khi đã cấu hình App ID). */
export function loadFacebookSdk(appId: string): Promise<FbSdk> {
  const init = (fb: FbSdk) => {
    if (!initialized) { fb.init({ appId, cookie: false, xfbml: false, version: 'v21.0' }); initialized = true }
    return fb
  }
  if (window.FB) return Promise.resolve(init(window.FB))
  sdk ??= new Promise<FbSdk>((resolve, reject) => {
    window.fbAsyncInit = () => resolve(init(window.FB!))
    const s = document.createElement('script')
    s.src = 'https://connect.facebook.net/vi_VN/sdk.js'
    s.async = true
    s.onerror = () => { sdk = null; reject(new Error('Không tải được Facebook SDK')) }
    document.head.appendChild(s)
  })
  return sdk
}

export const FacebookMark = () => (
  <svg className="size-5" viewBox="0 0 24 24" aria-hidden fill="currentColor">
    <path d="M24 12.07C24 5.4 18.63 0 12 0S0 5.4 0 12.07C0 18.1 4.39 23.1 10.13 24v-8.44H7.08v-3.49h3.05V9.41c0-3.02 1.79-4.69 4.53-4.69 1.31 0 2.69.24 2.69.24v2.97h-1.51c-1.49 0-1.96.93-1.96 1.88v2.26h3.33l-.53 3.49h-2.8V24C19.61 23.1 24 18.1 24 12.07Z" />
  </svg>
)

const base = 'relative flex h-10 w-full items-center justify-center rounded-full text-sm font-medium transition'
const referenceClass = 'login-social-facebook relative flex h-10 w-full items-center justify-center gap-2 rounded-md border border-[#E4E4E7] bg-white px-3 text-[13px] font-medium text-[#18181B] transition hover:bg-stone-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#1877F2] disabled:cursor-not-allowed disabled:opacity-70'

/**
 * Nút "Tiếp tục với Facebook". SDK được nạp sẵn khi hiển thị để lệnh FB.login chạy ngay trong cú nhấp chuột
 * (trình duyệt chặn popup nếu gọi sau khi chờ bất đồng bộ). Người dùng đóng cửa sổ thì không báo lỗi.
 */
export function FacebookSignIn({
  onToken, onError, appId = facebookAppId(), label = 'Tiếp tục với Facebook', appearance = 'default',
}: { onToken: (accessToken: string) => void; onError: (message: string) => void; appId?: string; label?: string; appearance?: 'default' | 'reference' }) {
  const [ready, setReady] = useState(false)

  useEffect(() => {
    if (!appId) return
    let alive = true
    loadFacebookSdk(appId).then(
      () => alive && setReady(true),
      () => alive && onError('Không tải được Facebook. Kiểm tra kết nối mạng rồi tải lại trang.'),
    )
    return () => { alive = false }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [appId])

  if (!appId) {
    return (
      <div>
        <button type="button" disabled aria-label={appearance === 'reference' ? 'Facebook hiện chưa khả dụng' : undefined} style={appearance === 'reference' ? undefined : { fontFamily: SOCIAL_FONT }} className={appearance === 'reference' ? referenceClass : `${base} cursor-not-allowed border border-zinc-300 text-zinc-400 dark:border-zinc-700`}>
          <span className={appearance === 'reference' ? 'flex text-[#1877F2]' : 'absolute left-3 flex'}><FacebookMark /></span> {label}
        </button>
      </div>
    )
  }

  return (
    <button
      type="button"
      disabled={!ready}
      style={appearance === 'reference' ? undefined : { fontFamily: SOCIAL_FONT }}
      onClick={() =>
        window.FB?.login(
          (r) => { if (r.authResponse?.accessToken) onToken(r.authResponse.accessToken) },
          { scope: 'public_profile,email' },
        )
      }
      className={appearance === 'reference'
        ? referenceClass
        : `${base} bg-[#1877F2] text-white hover:bg-[#166fe0] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#1877F2] disabled:cursor-wait disabled:opacity-70`}
    >
      <span className={appearance === 'reference' ? 'flex text-[#1877F2]' : 'absolute left-3 flex'}><FacebookMark /></span> {label}
    </button>
  )
}
