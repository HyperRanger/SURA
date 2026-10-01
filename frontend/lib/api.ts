import axios from "axios"
import { env, isProduction } from "@/config/env"
import { toApiError } from "@/lib/api-error"
import { getAccessToken } from "@/lib/session"

export const api = axios.create({
  baseURL: env.apiUrl,
  // generous because the hosted api can cold-start; pass a shorter timeout per call
  // where a fast failure matters more, like the footer health check
  timeout: 30_000,
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
    if (!isProduction && apiError.kind !== "cancelled") {
      console.error(
        `[api] ${apiError.method ?? "?"} ${apiError.url ?? "?"} → ${apiError.status ?? apiError.kind}: ${apiError.message}`,
        apiError.detail ?? ""
      )
    }
    return Promise.reject(apiError)
  }
)
