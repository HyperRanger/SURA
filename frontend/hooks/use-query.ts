"use client"

import { useCallback, useEffect, useState } from "react"
import { ApiError, toApiError } from "@/lib/api-error"

type Settled<T> = { key: string; data: T | null; error: ApiError | null }

export type QueryResult<T> = {
  data: T | null
  error: ApiError | null
  isLoading: boolean
  retry: () => void
  // swaps in fresh data without a refetch, e.g. after a write returns the new record
  setData: (data: T) => void
}

// loads data for a read screen. the args are the cache key: change them and it
// refetches, and a response for old args is dropped so filters never race.
// pass null to wait, e.g. until a route param is known
export function useQuery<A extends unknown[], T>(
  fetcher: (...args: A) => Promise<T>,
  args: A | null
): QueryResult<T> {
  const [attempt, setAttempt] = useState(0)
  const [settled, setSettled] = useState<Settled<T> | null>(null)
  const key = args === null ? null : `${attempt}:${JSON.stringify(args)}`

  useEffect(() => {
    if (key === null) return
    let current = true
    const parsed = JSON.parse(key.slice(key.indexOf(":") + 1)) as A

    fetcher(...parsed).then(
      (data) => current && setSettled({ key, data, error: null }),
      (cause) => {
        const error = toApiError(cause)
        if (current && error.kind !== "cancelled") setSettled({ key, data: null, error })
      }
    )
    return () => {
      current = false
    }
  }, [fetcher, key])

  const retry = useCallback(() => setAttempt((n) => n + 1), [])
  const setData = useCallback(
    (data: T) => setSettled((prev) => (prev ? { ...prev, data, error: null } : prev)),
    []
  )

  const fresh = settled !== null && settled.key === key
  return {
    data: fresh ? settled.data : null,
    error: fresh ? settled.error : null,
    isLoading: key !== null && !fresh,
    retry,
    setData,
  }
}
