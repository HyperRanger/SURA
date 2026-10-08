"use client"

import { useMemo, useSyncExternalStore } from "react"
import type { StoredValue } from "@/lib/storage"

const getServerSnapshot = () => null

// reads a web storage value and re-renders when it changes, in this tab or another
export function useStoredValue<T>(store: StoredValue<T>) {
  const raw = useSyncExternalStore(store.subscribe, store.readRaw, getServerSnapshot)
  return useMemo(() => store.parse(raw), [store, raw])
}
