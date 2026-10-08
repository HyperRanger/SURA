import { isAxiosError } from "axios"

export type ApiErrorKind = "network" | "timeout" | "http" | "cancelled" | "unknown"

type ApiErrorInit = {
  kind: ApiErrorKind
  message: string
  status?: number
  method?: string
  url?: string
  detail?: unknown
  cause?: unknown
}

// every failed request becomes one of these, so ui code only ever reads
// error.message and error.status, and logs carry the method and url
export class ApiError extends Error {
  readonly kind: ApiErrorKind
  readonly status?: number
  readonly method?: string
  readonly url?: string
  readonly detail?: unknown

  constructor({ kind, message, status, method, url, detail, cause }: ApiErrorInit) {
    super(message, { cause })
    this.name = "ApiError"
    this.kind = kind
    this.status = status
    this.method = method
    this.url = url
    this.detail = detail
  }

  is(status: number) {
    return this.status === status
  }
}

const fallbackMessages: Record<ApiErrorKind, string> = {
  network: "We couldn't reach Sura. Check your connection and try again.",
  timeout: "Sura is taking too long to respond. Please try again.",
  cancelled: "The request was cancelled.",
  http: "Something went wrong on our side. Please try again.",
  unknown: "Something went wrong. Please try again.",
}

type ValidationIssue = { msg?: string; loc?: (string | number)[] }

// fastapi sends { detail: "text" } for handled errors and
// { detail: [{ loc, msg }] } for request validation errors
function messageFromDetail(detail: unknown): string | undefined {
  if (typeof detail === "string" && detail.trim()) return detail
  if (Array.isArray(detail) && detail.length > 0) {
    const first = detail[0] as ValidationIssue
    if (!first?.msg) return undefined
    const field = first.loc?.filter((part) => part !== "body").join(".")
    return field ? `${field}: ${first.msg}` : first.msg
  }
  return undefined
}

export function toApiError(error: unknown): ApiError {
  if (error instanceof ApiError) return error

  if (isAxiosError(error)) {
    const method = error.config?.method?.toUpperCase()
    const url = error.config?.url
    const base = { method, url, cause: error }

    if (error.code === "ERR_CANCELED") {
      return new ApiError({ ...base, kind: "cancelled", message: fallbackMessages.cancelled })
    }
    if (error.code === "ECONNABORTED" || error.code === "ETIMEDOUT") {
      return new ApiError({ ...base, kind: "timeout", message: fallbackMessages.timeout })
    }
    if (!error.response) {
      return new ApiError({ ...base, kind: "network", message: fallbackMessages.network })
    }

    const { status, data } = error.response
    const detail = (data as { detail?: unknown } | undefined)?.detail
    return new ApiError({
      ...base,
      kind: "http",
      status,
      detail,
      message: messageFromDetail(detail) ?? fallbackMessages.http,
    })
  }

  return new ApiError({
    kind: "unknown",
    message: fallbackMessages.unknown,
    cause: error,
  })
}

export function getErrorMessage(error: unknown) {
  return toApiError(error).message
}
