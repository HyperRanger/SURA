// typed, ssr-safe wrapper over web storage that react can subscribe to through
// useSyncExternalStore. snapshots are the raw string, which is stable between
// reads, so components parse it themselves (see hooks/use-stored-value)

type StorageArea = "local" | "session"

export type StoredValue<T> = {
  key: string
  read: () => T | null
  readRaw: () => string | null
  write: (value: T) => void
  clear: () => void
  subscribe: (listener: () => void) => () => void
  parse: (raw: string | null) => T | null
}

const CHANGE_EVENT = "sura:storage"

function getArea(area: StorageArea): Storage | null {
  if (typeof window === "undefined") return null
  try {
    return area === "local" ? window.localStorage : window.sessionStorage
  } catch {
    // private mode or storage disabled by the browser
    return null
  }
}

export function createStoredValue<T>(area: StorageArea, key: string): StoredValue<T> {
  const parse = (raw: string | null): T | null => {
    if (raw === null) return null
    try {
      return JSON.parse(raw) as T
    } catch {
      return null
    }
  }

  const readRaw = () => getArea(area)?.getItem(key) ?? null

  const notify = () => window.dispatchEvent(new CustomEvent(CHANGE_EVENT, { detail: key }))

  return {
    key,
    parse,
    readRaw,
    read: () => parse(readRaw()),
    write(value) {
      getArea(area)?.setItem(key, JSON.stringify(value))
      notify()
    },
    clear() {
      getArea(area)?.removeItem(key)
      notify()
    },
    subscribe(listener) {
      // "storage" covers other tabs, the custom event covers this one
      const onStorage = (event: StorageEvent) => {
        if (event.key === key) listener()
      }
      const onLocalChange = (event: Event) => {
        if ((event as CustomEvent<string>).detail === key) listener()
      }
      window.addEventListener("storage", onStorage)
      window.addEventListener(CHANGE_EVENT, onLocalChange)
      return () => {
        window.removeEventListener("storage", onStorage)
        window.removeEventListener(CHANGE_EVENT, onLocalChange)
      }
    },
  }
}
