import { useEffect, useState } from 'react'
import { ApiError } from '../shared/api/client'

type RequestState<T> =
  | { status: 'loading' }
  | { status: 'error'; error: unknown }
  | { status: 'ready'; data: T }

export function useBuyerRequest<T>(load: () => Promise<T>) {
  const [state, setState] = useState<RequestState<T>>({ status: 'loading' })
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    let current = true
    load().then(
      (data) => { if (current) setState({ status: 'ready', data }) },
      (error: unknown) => { if (current) setState({ status: 'error', error }) },
    )
    return () => { current = false }
  }, [load, attempt])

  const retry = () => {
    setState({ status: 'loading' })
    setAttempt((value) => value + 1)
  }

  return { state, retry }
}

export function buyerErrorMessage(error: unknown, fallback: string): string {
  return error instanceof ApiError ? error.message : fallback
}
