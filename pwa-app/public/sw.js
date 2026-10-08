/*
 * Sura PWA service worker.
 *
 * This worker only caches the public app shell and static assets from this
 * origin. It never caches API responses, authenticated routes, vouchers,
 * tokens, or mutation requests. Financial state must always come from the
 * network and the API remains the source of truth.
 */

const CACHE_NAME = "sura-public-shell-v1"
const PUBLIC_SHELL = ["/", "/offline.html", "/icon-192.png", "/icon-512.png", "/sura-mark.svg"]
const STATIC_DESTINATIONS = new Set(["script", "style", "image", "font"])

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(PUBLIC_SHELL)).then(() => self.skipWaiting()),
  )
})

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) => Promise.all(keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))))
      .then(() => self.clients.claim()),
  )
})

self.addEventListener("message", (event) => {
  if (event.data?.type === "SKIP_WAITING") {
    self.skipWaiting()
  }
})

async function cacheStaticAsset(request) {
  const cache = await caches.open(CACHE_NAME)
  const cached = await cache.match(request)
  if (cached) return cached

  const response = await fetch(request)
  if (response.ok) {
    cache.put(request, response.clone())
  }
  return response
}

async function publicNavigation(request, url) {
  try {
    const response = await fetch(request)

    // The landing page has no account or financial data and forms the safe
    // offline entry shell. Authenticated and vendor pages are never cached.
    if (response.ok && url.pathname === "/") {
      const cache = await caches.open(CACHE_NAME)
      cache.put(request, response.clone())
    }
    return response
  } catch {
    const cache = await caches.open(CACHE_NAME)
    if (url.pathname === "/") {
      const shell = await cache.match("/")
      if (shell) return shell
    }
    return cache.match("/offline.html")
  }
}

self.addEventListener("fetch", (event) => {
  const { request } = event
  const url = new URL(request.url)

  // Requests to the deployed Sura API are cross-origin. Never intercept or
  // cache them. The same is true for non-GET requests on this origin.
  if (url.origin !== self.location.origin || request.method !== "GET") {
    return
  }

  if (request.mode === "navigate") {
    event.respondWith(publicNavigation(request, url))
    return
  }

  // Runtime assets make the already-visited public shell reopen quickly. RSC
  // payloads and any fetch with an empty destination remain network-only.
  if (STATIC_DESTINATIONS.has(request.destination)) {
    event.respondWith(cacheStaticAsset(request))
  }
})
