"use client"

import { useCallback, useRef, useState } from "react"
import { ApiError, toApiError } from "@/lib/api-error"

export type MutationResult<T> = { ok: true; data: T } | { ok: false; error: ApiError }

type MutationState = {
  isPending: boolean
  error: ApiError | null
}

const duplicateCall = () =>
  new ApiError({ kind: "cancelled", message: "a request is already in progress." })

// wraps a write request with pending and error state. a second call while the first
// is still in flight is dropped, so a double tap can never send the request twice
export function useMutation<TArgs extends unknown[], TResult>(
  fn: (...args: TArgs) => Promise<TResult>
) {
  const [state, setState] = useState<MutationState>({ isPending: false, error: null })
  const inFlight = useRef(false)

  const mutate = useCallback(
    async (...args: TArgs): Promise<MutationResult<TResult>> => {
      if (inFlight.current) return { ok: false, error: duplicateCall() }

      inFlight.current = true
      setState({ isPending: true, error: null })
      try {
        const data = await fn(...args)
        setState({ isPending: false, error: null })
        return { ok: true, data }
      } catch (cause) {
        const error = toApiError(cause)
        setState({ isPending: false, error })
        return { ok: false, error }
      } finally {
        inFlight.current = false
      }
    },
    [fn]
  )

  const reset = useCallback(() => setState({ isPending: false, error: null }), [])

  return { mutate, reset, ...state }
}
