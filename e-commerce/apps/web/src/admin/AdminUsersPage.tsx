import { useCallback, useEffect, useState } from 'react'
import { api, type AdminUser, type AdminUserQuery } from '../shared/api/client'
import { useAuth } from '../shared/auth/AuthContext'
import { Alert, Spinner } from '../shared/auth/components/ui'
import { describeError } from '../shared/auth/errors'
import { roleLabel } from '../shared/auth/roles'
import { AppShell } from '../shared/layout/AppShell'

const PAGE = 20
const btn = 'rounded-lg border border-zinc-300 px-2.5 py-1.5 text-xs font-medium transition hover:bg-zinc-50 disabled:cursor-not-allowed disabled:opacity-50 dark:border-zinc-700 dark:hover:bg-zinc-800'
const field = 'h-10 rounded-xl border border-zinc-300 bg-white px-3 text-sm dark:border-zinc-700 dark:bg-zinc-900'

/** Quản trị người dùng: tìm kiếm, lọc, khóa/mở khóa, cấp/thu quyền admin. */
export default function AdminUsersPage() {
  const { user: me } = useAuth()
  const [filters, setFilters] = useState<Pick<AdminUserQuery, 'q' | 'role' | 'status'>>({ q: '', role: '', status: '' })
  const [items, setItems] = useState<AdminUser[]>([])
  const [next, setNext] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [busyId, setBusyId] = useState<string>()
  const [message, setMessage] = useState<{ tone: 'error' | 'success'; text: string }>()

  const load = useCallback(async (query: AdminUserQuery, append: boolean) => {
    setLoading(true)
    try {
      const page = await api.adminUsers({ ...query, limit: PAGE })
      setItems((cur) => (append ? [...cur, ...page.items] : page.items))
      setNext(page.next_cursor)
      if (!append) setMessage(undefined)
    } catch (e) {
      setMessage({ tone: 'error', text: describeError(e).message ?? 'Không tải được danh sách.' })
    } finally { setLoading(false) }
  }, [])

  // Tìm kiếm: chờ người dùng gõ xong một nhịp rồi mới gọi API.
  useEffect(() => {
    const t = setTimeout(() => { void load(filters, false) }, 250)
    return () => clearTimeout(t)
  }, [filters, load])

  const update = async (u: AdminUser, change: Parameters<typeof api.adminUpdateUser>[1], ok: string) => {
    setBusyId(u.id)
    setMessage(undefined)
    try {
      const saved = await api.adminUpdateUser(u.id, change)
      setItems((cur) => cur.map((x) => (x.id === saved.id ? saved : x)))
      setMessage({ tone: 'success', text: ok })
    } catch (e) {
      setMessage({ tone: 'error', text: describeError(e).message ?? 'Không thực hiện được.' })
    } finally { setBusyId(undefined) }
  }

  return (
    <AppShell width="max-w-5xl">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Quản trị người dùng</h1>
        <p className="mt-1 text-sm text-zinc-500">Khóa tài khoản sẽ đăng xuất người dùng ngay lập tức.</p>
      </div>

      <div className="flex flex-wrap gap-3">
        <input
          type="search" aria-label="Tìm người dùng" placeholder="Tìm theo email hoặc tên…" maxLength={100}
          className={`${field} min-w-64 flex-1`} value={filters.q}
          onChange={(e) => setFilters((f) => ({ ...f, q: e.target.value }))}
        />
        <select aria-label="Lọc theo vai trò" className={field} value={filters.role} onChange={(e) => setFilters((f) => ({ ...f, role: e.target.value as AdminUserQuery['role'] }))}>
          <option value="">Mọi vai trò</option>
          {(['buyer', 'seller', 'admin'] as const).map((r) => <option key={r} value={r}>{roleLabel[r]}</option>)}
        </select>
        <select aria-label="Lọc theo trạng thái" className={field} value={filters.status} onChange={(e) => setFilters((f) => ({ ...f, status: e.target.value as AdminUserQuery['status'] }))}>
          <option value="">Mọi trạng thái</option>
          <option value="active">Đang hoạt động</option>
          <option value="suspended">Đã khóa</option>
        </select>
      </div>

      {message && <Alert tone={message.tone}>{message.text}</Alert>}

      <div className="overflow-x-auto rounded-2xl border border-zinc-200 bg-white shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
        <table className="w-full text-left text-sm">
          <caption className="sr-only">Danh sách người dùng</caption>
          <thead className="border-b border-zinc-200 text-xs uppercase tracking-wide text-zinc-500 dark:border-zinc-800">
            <tr><th className="px-4 py-3">Người dùng</th><th className="px-4 py-3">Vai trò</th><th className="px-4 py-3">Trạng thái</th><th className="px-4 py-3 text-right">Thao tác</th></tr>
          </thead>
          <tbody className="divide-y divide-zinc-200 dark:divide-zinc-800">
            {items.map((u) => {
              const self = u.id === me?.id
              const busy = busyId === u.id
              const suspended = u.status === 'suspended'
              return (
                <tr key={u.id}>
                  <td className="px-4 py-3"><p className="font-medium">{u.full_name}{self && <span className="ml-2 text-xs text-zinc-500">(bạn)</span>}</p><p className="text-zinc-500">{u.email}</p></td>
                  <td className="px-4 py-3">{roleLabel[u.role]}</td>
                  <td className="px-4 py-3">
                    <span className={`rounded-full px-2.5 py-1 text-xs font-medium ${suspended ? 'bg-red-50 text-red-700 dark:bg-red-950/40 dark:text-red-300' : 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300'}`}>
                      {suspended ? 'Đã khóa' : 'Hoạt động'}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex justify-end gap-2">
                      {u.role !== 'seller' && (
                        <button type="button" className={btn} disabled={self || busy} aria-label={`${u.role === 'admin' ? 'Thu quyền admin' : 'Cấp quyền admin'} của ${u.email}`}
                          onClick={() => update(u, { role: u.role === 'admin' ? 'buyer' : 'admin' }, u.role === 'admin' ? 'Đã thu quyền admin.' : 'Đã cấp quyền admin.')}>
                          {u.role === 'admin' ? 'Thu quyền admin' : 'Cấp quyền admin'}
                        </button>
                      )}
                      <button type="button" className={btn} disabled={self || busy} aria-label={`${suspended ? 'Mở khóa' : 'Khóa'} ${u.email}`}
                        onClick={() => update(u, { status: suspended ? 'active' : 'suspended' }, suspended ? 'Đã mở khóa tài khoản.' : 'Đã khóa tài khoản.')}>
                        {suspended ? 'Mở khóa' : 'Khóa'}
                      </button>
                    </div>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
        {!loading && items.length === 0 && <p className="px-4 py-8 text-center text-sm text-zinc-500">Không có người dùng phù hợp.</p>}
      </div>

      <div className="flex justify-center">
        {loading ? <Spinner label="Đang tải…" /> : next && (
          <button type="button" className={`${btn} px-4 py-2 text-sm`} onClick={() => load({ ...filters, cursor: next }, true)}>Tải thêm</button>
        )}
      </div>
    </AppShell>
  )
}
