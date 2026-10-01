"use client"

import { useSyncExternalStore } from "react"

const subscribe = () => () => {}

// false during the server render and hydration, true afterwards. use it to tell
// "storage is empty" apart from "storage has not been read yet"
export function useHydrated() {
  return useSyncExternalStore(
    subscribe,
    () => true,
    () => false
  )
}
