import { GoogleLogin } from '@react-oauth/google'

export const GOOGLE_ENABLED = Boolean(import.meta.env.VITE_GOOGLE_CLIENT_ID)

/** Nút Google (Google Identity Services). Chưa cấu hình Client ID thì hiển thị nút bị vô hiệu kèm giải thích. */
export function GoogleSignIn({ onCredential, onError }: { onCredential: (credential: string) => void; onError: () => void }) {
  if (!GOOGLE_ENABLED) {
    return (
      <div>
        <button
          type="button"
          disabled
          className="flex h-11 w-full cursor-not-allowed items-center justify-center gap-2.5 rounded-xl border border-zinc-300 text-sm font-medium text-zinc-400 dark:border-zinc-700"
        >
          <GoogleMark /> Tiếp tục với Google
        </button>
        <p className="mt-1.5 text-center text-xs text-zinc-500">Chưa cấu hình VITE_GOOGLE_CLIENT_ID.</p>
      </div>
    )
  }
  return (
    <div className="flex justify-center">
      <GoogleLogin
        onSuccess={(r) => (r.credential ? onCredential(r.credential) : onError())}
        onError={onError}
        text="continue_with"
        shape="pill"
        size="large"
        width="380"
        theme="outline"
      />
    </div>
  )
}

function GoogleMark() {
  return (
    <svg className="size-5" viewBox="0 0 48 48" aria-hidden>
      <path fill="#EA4335" d="M24 9.5c3.5 0 6.6 1.2 9.1 3.6l6.8-6.8C35.8 2.4 30.3 0 24 0 14.6 0 6.5 5.4 2.6 13.2l7.9 6.1C12.4 13.6 17.7 9.5 24 9.5z" />
      <path fill="#4285F4" d="M46.5 24.5c0-1.6-.1-3.1-.4-4.5H24v9h12.7c-.6 3-2.3 5.5-4.8 7.2l7.6 5.9c4.4-4.1 7-10.1 7-17.6z" />
      <path fill="#FBBC05" d="M10.5 28.7a14.5 14.5 0 0 1 0-9.4l-7.9-6.1a24 24 0 0 0 0 21.6l7.9-6.1z" />
      <path fill="#34A853" d="M24 48c6.5 0 11.9-2.1 15.9-5.8l-7.6-5.9c-2.1 1.4-4.9 2.3-8.3 2.3-6.3 0-11.6-4.1-13.5-9.8l-7.9 6.1C6.5 42.6 14.6 48 24 48z" />
    </svg>
  )
}
