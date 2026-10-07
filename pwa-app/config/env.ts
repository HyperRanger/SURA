// every NEXT_PUBLIC_ variable is read here once, so the rest of the app never
// touches process.env directly and a missing value is easy to trace

const appEnv = (process.env.NEXT_PUBLIC_APP_ENV ?? "development").trim().toLowerCase()

// axios treats anything that isn't an absolute url as a path on the current page,
// so a typo like API_URL==https://... would quietly call /=https:/... instead.
// stray "=", quotes and spaces are stripped, and anything still not http(s) is dropped loudly
function readUrl(name: string, raw: string | undefined) {
  const value = (raw ?? "").trim().replace(/^[=\s"']+|["'\s]+$/g, "").replace(/\/+$/, "")
  if (!value) return ""
  if (!/^https?:\/\//i.test(value)) {
    console.error(`[env] ${name} must start with http:// or https://, got "${raw}"`)
    return ""
  }
  return value
}

export const env = {
  apiUrl: readUrl("NEXT_PUBLIC_API_URL", process.env.NEXT_PUBLIC_API_URL),
  // the marketing website, home of the bank information page and the bank console
  siteUrl: readUrl("NEXT_PUBLIC_SITE_URL", process.env.NEXT_PUBLIC_SITE_URL),
  appEnv,
  // the backend's DEMO_OTP_CODE. only needed to sign in as the named seeded people
  // on /demo, never set it in production
  demoOtpCode: process.env.NEXT_PUBLIC_DEMO_OTP_CODE ?? "",
} as const

export const isProduction = appEnv === "production" || appEnv === "prod"

// the demo switcher and demo code hints are off in production, matching the backend
export const isDemoEnabled = !isProduction
