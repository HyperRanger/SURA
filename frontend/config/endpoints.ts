// api paths, relative to NEXT_PUBLIC_API_URL. see /docs on the api for the contract
export const endpoints = {
  health: "/health",
  auth: {
    signup: "/v1/auth/signup",
    login: "/v1/auth/login",
    verifyOtp: "/v1/auth/verify-otp",
    demoToken: "/v1/auth/demo-token",
  },
  me: "/v1/me",
  demo: {
    loginAs: "/v1/demo/login-as",
  },
  bank: {
    demoLogin: "/v1/bank/demo-login",
  },
} as const
