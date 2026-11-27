import { useEffect, useState } from 'react'
import { ApiError } from '../shared/api/client'

type RequestState<T> =
  | { status: 'loading' }
  | { status: 'error'; error: unknown }
  | { status: 'ready'; data: T }

export function useBuyerRequest<T>(load: () => Promise<T>) {
  const [result, setResult] = useState<{ load: () => Promise<T>; state: RequestState<T> }>()
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    let current = true
    load().then(
      (data) => { if (current) setResult({ load, state: { status: 'ready', data } }) },
      (error: unknown) => { if (current) setResult({ load, state: { status: 'error', error } }) },
    )
    return () => { current = false }
  }, [load, attempt])

  const retry = () => {
    setResult(undefined)
    setAttempt((value) => value + 1)
  }

  const state: RequestState<T> = result?.load === load ? result.state : { status: 'loading' }
  return { state, retry }
}

export function buyerErrorMessage(error: unknown, fallback: string): string {
  return error instanceof ApiError ? error.message : fallback
}
