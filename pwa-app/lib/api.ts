import axios from "axios"
import { env, isProduction } from "@/config/env"
import { toApiError } from "@/lib/api-error"
import { getAccessToken, redirectAfterSessionExpiry } from "@/lib/session"

export const api = axios.create({
  baseURL: env.apiUrl,
  // Hosted demo instances may need longer than a minute to wake from idle.
  timeout: 90_000,
  headers: { "Content-Type": "application/json" },
})

api.interceptors.request.use((config) => {
  const token = getAccessToken()
  if (token && !config.headers.Authorization) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const apiError = toApiError(error)
    // A protected request receiving 401 means the backend has ended this
    // session (idle timeout, JWT expiry, logout, suspension, or revocation).
    // Clear the locally stored bearer token before any UI can reuse it.
    if (apiError.status === 401 && getAccessToken()) {
      redirectAfterSessionExpiry()
    }
    if (!isProduction && apiError.kind !== "cancelled") {
      const request = axios.isAxiosError(error) ? error.config : undefined
      console.error(
        `[api] ${apiError.method ?? request?.method?.toUpperCase() ?? "?"} ${apiError.url ?? request?.url ?? env.apiUrl ?? "?"} → ${apiError.status ?? apiError.kind}: ${apiError.message}`,
        apiError.detail ?? ""
      )
    }
    return Promise.reject(apiError)
  }
)
