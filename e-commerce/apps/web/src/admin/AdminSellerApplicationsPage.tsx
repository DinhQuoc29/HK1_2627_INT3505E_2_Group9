import { zodResolver } from '@hookform/resolvers/zod'
import { useCallback, useEffect, useState } from 'react'
import { useForm } from 'react-hook-form'
import { api, type AdminSellerApplication, type ApplicationStatus } from '../shared/api/client'
import { Alert, Spinner } from '../shared/auth/components/ui'
import { describeError } from '../shared/auth/errors'
import { rejectSchema } from '../shared/auth/schemas'
import { AppShell } from '../shared/layout/AppShell'

const statusLabel: Record<ApplicationStatus, string> = { pending: 'Chờ duyệt', approved: 'Đã duyệt', rejected: 'Đã từ chối' }
const statusTone: Record<ApplicationStatus, string> = {
  pending: 'bg-amber-50 text-amber-800 dark:bg-amber-950/40 dark:text-amber-200',
  approved: 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300',
  rejected: 'bg-red-50 text-red-700 dark:bg-red-950/40 dark:text-red-300',
}
const btn = 'rounded-lg border border-zinc-300 px-2.5 py-1.5 text-xs font-medium transition hover:bg-zinc-50 disabled:cursor-not-allowed disabled:opacity-50 dark:border-zinc-700 dark:hover:bg-zinc-800'

function RejectForm({ onSubmit, onCancel, busy }: { onSubmit: (reason: string) => void; onCancel: () => void; busy: boolean }) {
  const { register, handleSubmit, formState: { errors } } = useForm<{ reason: string }>({ resolver: zodResolver(rejectSchema), defaultValues: { reason: '' } })
  return (
    <form onSubmit={handleSubmit((v) => onSubmit(v.reason))} noValidate className="mt-3 flex flex-wrap items-start gap-2">
      <div className="min-w-56 flex-1">
        <input aria-label="Lý do từ chối" placeholder="Lý do từ chối (gửi cho người nộp)" maxLength={500}
          className="h-9 w-full rounded-lg border border-zinc-300 bg-white px-3 text-sm dark:border-zinc-700 dark:bg-zinc-900" {...register('reason')} />
        {errors.reason && <p className="mt-1 text-xs text-red-600">{errors.reason.message}</p>}
      </div>
      <button type="submit" disabled={busy} className={`${btn} border-red-300 text-red-700`}>Xác nhận từ chối</button>
      <button type="button" onClick={onCancel} className={btn}>Hủy</button>
    </form>
  )
}

/** Admin duyệt hồ sơ người bán: duyệt (tạo shop, nâng seller) hoặc từ chối kèm lý do. */
export default function AdminSellerApplicationsPage() {
  const [status, setStatus] = useState<ApplicationStatus | ''>('pending')
  const [items, setItems] = useState<AdminSellerApplication[]>([])
  const [next, setNext] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [busyId, setBusyId] = useState<string>()
  const [rejectingId, setRejectingId] = useState<string>()
  const [message, setMessage] = useState<{ tone: 'error' | 'success'; text: string }>()

  const load = useCallback(async (st: ApplicationStatus | '', cursor: string | undefined) => {
    setLoading(true)
    try {
      const page = await api.adminApplications({ status: st, cursor, limit: 20 })
      setItems((cur) => (cursor ? [...cur, ...page.items] : page.items))
      setNext(page.next_cursor)
    } catch (e) { setMessage({ tone: 'error', text: describeError(e).message ?? 'Không tải được danh sách.' }) } finally { setLoading(false) }
  }, [])

  useEffect(() => { void load(status, undefined) }, [status, load])

  const decide = async (a: AdminSellerApplication, action: () => Promise<AdminSellerApplication>, ok: string) => {
    setBusyId(a.id)
    setMessage(undefined)
    try {
      const saved = await action()
      // Đang xem danh sách lọc theo trạng thái: hồ sơ đã xử lý rời khỏi danh sách "Chờ duyệt".
      setItems((cur) => (status ? cur.filter((x) => x.id !== saved.id) : cur.map((x) => (x.id === saved.id ? saved : x))))
      setRejectingId(undefined)
      setMessage({ tone: 'success', text: ok })
    } catch (e) {
      setMessage({ tone: 'error', text: describeError(e).message ?? 'Không thực hiện được.' })
    } finally { setBusyId(undefined) }
  }

  return (
    <AppShell width="max-w-5xl">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Duyệt người bán</h1>
        <p className="mt-1 text-sm text-zinc-500">Duyệt hồ sơ sẽ tạo shop và nâng người nộp lên người bán; kết quả được gửi qua email.</p>
      </div>
      <select aria-label="Lọc theo trạng thái hồ sơ" value={status} onChange={(e) => setStatus(e.target.value as ApplicationStatus | '')}
        className="h-10 rounded-xl border border-zinc-300 bg-white px-3 text-sm dark:border-zinc-700 dark:bg-zinc-900">
        <option value="pending">Chờ duyệt</option>
        <option value="approved">Đã duyệt</option>
        <option value="rejected">Đã từ chối</option>
        <option value="">Tất cả</option>
      </select>
      {message && <Alert tone={message.tone}>{message.text}</Alert>}

      <ul className="space-y-3">
        {items.map((a) => (
          <li key={a.id} className="rounded-2xl border border-zinc-200 bg-white p-5 shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="font-semibold">{a.shop_name} <span className={`ml-2 rounded-full px-2.5 py-1 text-xs font-medium ${statusTone[a.status]}`}>{statusLabel[a.status]}</span></p>
                <p className="text-sm text-zinc-500">{a.province_name} · nộp ngày {new Date(a.created_at).toLocaleDateString('vi-VN')}</p>
                <p className="mt-1 text-sm">{a.applicant_name} · <span className="text-zinc-500">{a.applicant_email}</span></p>
                {a.status === 'rejected' && <p className="mt-1 text-sm text-red-700 dark:text-red-300">Lý do: {a.reject_reason}</p>}
              </div>
              {a.status === 'pending' && (
                <div className="flex gap-2">
                  <button type="button" className={`${btn} border-emerald-300 text-emerald-700`} disabled={busyId === a.id} aria-label={`Duyệt hồ sơ ${a.shop_name}`}
                    onClick={() => decide(a, () => api.approveApplication(a.id), `Đã duyệt shop "${a.shop_name}".`)}>Duyệt</button>
                  <button type="button" className={btn} disabled={busyId === a.id} aria-label={`Từ chối hồ sơ ${a.shop_name}`}
                    onClick={() => setRejectingId(rejectingId === a.id ? undefined : a.id)}>Từ chối</button>
                </div>
              )}
            </div>
            {rejectingId === a.id && (
              <RejectForm busy={busyId === a.id} onCancel={() => setRejectingId(undefined)}
                onSubmit={(reason) => decide(a, () => api.rejectApplication(a.id, reason), `Đã từ chối hồ sơ "${a.shop_name}".`)} />
            )}
          </li>
        ))}
      </ul>
      {!loading && items.length === 0 && <p className="py-8 text-center text-sm text-zinc-500">Không có hồ sơ nào.</p>}
      <div className="flex justify-center">
        {loading ? <Spinner label="Đang tải…" /> : next && <button type="button" className={`${btn} px-4 py-2 text-sm`} onClick={() => load(status, next)}>Tải thêm</button>}
      </div>
    </AppShell>
  )
}
