// every NEXT_PUBLIC_ variable is read here once, so the rest of the app never
// touches process.env directly and a missing value is easy to trace

const appEnv = (
  process.env.NEXT_PUBLIC_APP_ENV ?? process.env.VERCEL_ENV ?? "development"
).trim().toLowerCase()

const isProductionEnvironment = appEnv === "production" || appEnv === "prod"
// A dedicated, seeded hackathon deployment may opt into the visible demo OTP
// journey even when it is hosted on a production Vercel URL. It must never be
// enabled for a deployment containing real customer data.
const isDemoDeployment = process.env.NEXT_PUBLIC_DEMO_MODE === "true"
const productionSiteUrl = "https://sura-seven.vercel.app"

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
  // The public Sura website owns the bank-information and Bank Portal routes.
  // Production is deliberately pinned to the canonical domain: a stale Vercel
  // environment variable must never send an institution to a localhost URL.
  siteUrl: isProductionEnvironment
    ? productionSiteUrl
    : readUrl("NEXT_PUBLIC_SITE_URL", process.env.NEXT_PUBLIC_SITE_URL),
  appEnv,
  // the backend's DEMO_OTP_CODE. only needed to sign in as the named seeded people
  // on /demo, never set it in production
  demoOtpCode: process.env.NEXT_PUBLIC_DEMO_OTP_CODE ?? "",
} as const

export const isProduction = isProductionEnvironment

// A dedicated demo deployment may enable this explicitly. Normal production
// deployments remain closed, matching the backend's ENVIRONMENT setting.
export const isDemoEnabled = isDemoDeployment || !isProduction
