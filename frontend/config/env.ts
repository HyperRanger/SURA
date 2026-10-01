// every NEXT_PUBLIC_ variable is read here once, so the rest of the app never
// touches process.env directly and a missing value is easy to trace

const appEnv = (process.env.NEXT_PUBLIC_APP_ENV ?? "development").trim().toLowerCase()

export const env = {
  apiUrl: (process.env.NEXT_PUBLIC_API_URL ?? "").replace(/\/+$/, ""),
  appEnv,
  // the backend's DEMO_OTP_CODE. only needed to sign in as the named seeded people
  // on /demo, never set it in production
  demoOtpCode: process.env.NEXT_PUBLIC_DEMO_OTP_CODE ?? "",
} as const

export const isProduction = appEnv === "production" || appEnv === "prod"

// the demo switcher and demo code hints are off in production, matching the backend
export const isDemoEnabled = !isProduction
