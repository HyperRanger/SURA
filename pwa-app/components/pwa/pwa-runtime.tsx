"use client"

import { useEffect, useRef, useState } from "react"

type InstallPromptEvent = Event & {
  prompt: () => Promise<void>
  userChoice: Promise<{ outcome: "accepted" | "dismissed" }>
}

function isStandalone() {
  return window.matchMedia("(display-mode: standalone)").matches || ("standalone" in navigator && Boolean((navigator as Navigator & { standalone?: boolean }).standalone))
}

function isAppleMobile() {
  return /iPad|iPhone|iPod/.test(navigator.userAgent)
}

/** Registers the safe shell cache and gives the user clear install/offline state. */
export function PwaRuntime() {
  const [offline, setOffline] = useState(false)
  const [registration, setRegistration] = useState<ServiceWorkerRegistration | null>(null)
  const [installPrompt, setInstallPrompt] = useState<InstallPromptEvent | null>(null)
  const [appleInstallAvailable, setAppleInstallAvailable] = useState(false)
  const [showAppleInstallHint, setShowAppleInstallHint] = useState(false)
  const [updateReady, setUpdateReady] = useState(false)
  const reloadAfterActivation = useRef(false)

  useEffect(() => {
    setOffline(!navigator.onLine)
    setAppleInstallAvailable(isAppleMobile() && !isStandalone())

    const goOnline = () => setOffline(false)
    const goOffline = () => setOffline(true)
    const onInstallPrompt = (event: Event) => {
      event.preventDefault()
      setInstallPrompt(event as InstallPromptEvent)
    }

    window.addEventListener("online", goOnline)
    window.addEventListener("offline", goOffline)
    window.addEventListener("beforeinstallprompt", onInstallPrompt)

    if ("serviceWorker" in navigator) {
      navigator.serviceWorker
        .register("/sw.js", { scope: "/" })
        .then((nextRegistration) => {
          setRegistration(nextRegistration)
          setUpdateReady(Boolean(nextRegistration.waiting))
          nextRegistration.addEventListener("updatefound", () => {
            const installing = nextRegistration.installing
            if (!installing) return
            installing.addEventListener("statechange", () => {
              if (installing.state === "installed" && navigator.serviceWorker.controller) {
                setUpdateReady(true)
              }
            })
          })
        })
        .catch(() => {
          // PWA support is progressive. The site remains usable if registration
          // is unavailable, such as an unsupported or private browser context.
        })

      const onControllerChange = () => {
        if (reloadAfterActivation.current) window.location.reload()
      }
      navigator.serviceWorker.addEventListener("controllerchange", onControllerChange)

      return () => {
        window.removeEventListener("online", goOnline)
        window.removeEventListener("offline", goOffline)
        window.removeEventListener("beforeinstallprompt", onInstallPrompt)
        navigator.serviceWorker.removeEventListener("controllerchange", onControllerChange)
      }
    }

    return () => {
      window.removeEventListener("online", goOnline)
      window.removeEventListener("offline", goOffline)
      window.removeEventListener("beforeinstallprompt", onInstallPrompt)
    }
  }, [])

  async function install() {
    if (installPrompt) {
      await installPrompt.prompt()
      setInstallPrompt(null)
      return
    }
    if (isAppleMobile() && !isStandalone()) setShowAppleInstallHint(true)
  }

  function update() {
    if (!registration?.waiting) return
    reloadAfterActivation.current = true
    registration.waiting.postMessage({ type: "SKIP_WAITING" })
  }

  return (
    <>
      {offline && (
        <aside className="fixed inset-x-3 top-3 z-50 rounded-2xl bg-foreground px-4 py-3 text-center text-sm font-bold text-background shadow-lg" role="status">
          You are offline. Live balances, Locks, scores, vouchers, and payments need a connection.
        </aside>
      )}

      {updateReady && registration?.waiting && (
        <aside className="fixed inset-x-3 bottom-3 z-50 mx-auto flex max-w-md items-center justify-between gap-3 rounded-2xl bg-primary px-4 py-3 text-sm font-bold text-primary-foreground shadow-lg" role="status">
          <span>A newer Sura app is ready.</span>
          <button type="button" className="rounded-lg bg-background px-3 py-1.5 text-foreground" onClick={update}>
            Refresh
          </button>
        </aside>
      )}

      {(installPrompt || appleInstallAvailable) && !isStandalone() && (
        <button type="button" className="fixed bottom-3 right-3 z-40 rounded-full bg-primary px-4 py-2 text-sm font-bold text-primary-foreground shadow-lg" onClick={install}>
          Install Sura
        </button>
      )}

      {isAppleMobile() && !isStandalone() && showAppleInstallHint && (
        <aside className="fixed inset-x-3 bottom-3 z-50 mx-auto max-w-md rounded-2xl bg-foreground px-4 py-3 text-sm leading-relaxed text-background shadow-lg" role="status">
          In Safari, tap Share, then choose Add to Home Screen.
          <button type="button" className="ml-3 font-bold underline" onClick={() => setShowAppleInstallHint(false)}>
            Close
          </button>
        </aside>
      )}
    </>
  )
}
