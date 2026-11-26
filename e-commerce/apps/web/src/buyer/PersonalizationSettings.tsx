import { useState } from 'react'
import { api } from '../shared/api/client'
import { Alert, Spinner } from '../shared/auth/components/ui'
import { BuyerRequestError } from './BuyerFeedback'
import { buyerErrorMessage, useBuyerRequest } from './useBuyerRequest'

export function PersonalizationSettings() {
  const { state, retry } = useBuyerRequest(api.privacyPreference)

  return (
    <section id="personalization" aria-labelledby="personalization-title" className="space-y-4 rounded-2xl border border-zinc-200 bg-white p-4 shadow-sm sm:p-6 dark:border-zinc-800 dark:bg-zinc-900">
      <h2 id="personalization-title" className="text-lg font-semibold tracking-tight">Cá nhân hóa gợi ý</h2>
      <div className="space-y-2 rounded-xl bg-zinc-50 p-4 text-sm leading-6 text-zinc-700 dark:bg-zinc-950 dark:text-zinc-300">
        <h3 className="font-semibold text-zinc-900 dark:text-zinc-100">Thông báo theo dõi</h3>
        <p>Khi có gợi ý cá nhân hóa, E-Market có thể dùng hoạt động mua sắm như lượt xem hoặc tìm kiếm sản phẩm để chọn gợi ý phù hợp. Hiện E-Market chưa thu thập hoạt động cho mục đích này.</p>
        <p>Tùy chọn được lưu theo tài khoản và áp dụng trên mọi thiết bị đã đăng nhập. Khi tắt, hoạt động của bạn sẽ không được ghi hoặc dùng để cá nhân hóa. Bạn vẫn có thể tìm sản phẩm, mua hàng và xem đơn.</p>
      </div>
      {state.status === 'loading' && <Spinner label="Đang tải tùy chọn cá nhân hóa…" />}
      {state.status === 'error' && (
        <BuyerRequestError message={buyerErrorMessage(state.error, 'Không tải được tùy chọn cá nhân hóa.')} retry={retry} />
      )}
      {state.status === 'ready' && <PersonalizationSwitch initial={state.data.personalization_enabled} />}
    </section>
  )
}

function PersonalizationSwitch({ initial }: { initial: boolean }) {
  const [enabled, setEnabled] = useState(initial)
  const [saving, setSaving] = useState(false)
  const [result, setResult] = useState<{ tone: 'success' | 'error'; message: string }>()

  async function save(next: boolean) {
    if (saving) return
    setSaving(true)
    setResult(undefined)
    try {
      const confirmed = await api.setPrivacyPreference(next)
      setEnabled(confirmed.personalization_enabled)
      setResult({
        tone: 'success',
        message: confirmed.personalization_enabled ? 'Đã bật cá nhân hóa cho tài khoản.' : 'Đã tắt cá nhân hóa cho tài khoản.',
      })
    } catch (error) {
      const current = await api.privacyPreference().catch(() => null)
      if (current) setEnabled(current.personalization_enabled)
      setResult({
        tone: 'error',
        message: buyerErrorMessage(error, 'Chưa xác nhận được thay đổi. Vui lòng thử lại.'),
      })
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="space-y-3">
      <label className="flex min-h-12 flex-wrap items-center justify-between gap-x-4 gap-y-2 rounded-xl border border-zinc-200 px-3.5 py-2.5 dark:border-zinc-700">
        <span className="min-w-0">
          <span className="block text-sm font-semibold" id="personalization-switch-label">Cá nhân hóa gợi ý sản phẩm</span>
          <span className="block text-sm text-zinc-600 dark:text-zinc-400" id="personalization-switch-status" aria-live="polite">
            {saving ? 'Đang lưu…' : enabled ? 'Đang bật' : 'Đang tắt'}
          </span>
        </span>
        <input
          type="checkbox"
          role="switch"
          aria-labelledby="personalization-switch-label"
          aria-describedby="personalization-switch-status"
          checked={enabled}
          disabled={saving}
          onChange={(event) => void save(event.target.checked)}
          className="peer sr-only"
        />
        <span aria-hidden className="relative h-6 w-11 shrink-0 rounded-full bg-zinc-400 transition after:absolute after:left-0.5 after:top-0.5 after:size-5 after:rounded-full after:bg-white after:transition peer-checked:bg-brand-700 peer-checked:after:translate-x-5 peer-focus-visible:outline-2 peer-focus-visible:outline-offset-4 peer-focus-visible:outline-brand-500 peer-disabled:opacity-60 dark:bg-zinc-600" />
      </label>
      {result && <Alert tone={result.tone}>{result.message}</Alert>}
    </div>
  )
}
