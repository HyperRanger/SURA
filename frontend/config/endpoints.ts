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
    login: "/v1/bank/login",
    verifyMfa: "/v1/bank/login/verify",
    demoLogin: "/v1/bank/demo-login",
    overview: "/v1/bank/overview",
    commitments: "/v1/bank/commitments",
    commitment: (id: string) => `/v1/bank/commitments/${encodeURIComponent(id)}`,
    users: "/v1/bank/users",
    user: (id: string) => `/v1/bank/users/${encodeURIComponent(id)}`,
    userScore: (id: string) => `/v1/bank/users/${encodeURIComponent(id)}/score`,
    userCommitments: (id: string) => `/v1/bank/users/${encodeURIComponent(id)}/commitments`,
    userFlags: (id: string) => `/v1/bank/users/${encodeURIComponent(id)}/flags`,
    auditLog: "/v1/bank/audit-log",
    auditLogExport: "/v1/bank/audit-log/export",
    flags: "/v1/bank/flags",
    flag: (id: string) => `/v1/bank/flags/${encodeURIComponent(id)}`,
    resolveFlag: (id: string) => `/v1/bank/flags/${encodeURIComponent(id)}/resolve`,
    settlements: "/v1/bank/settlements",
  },
} as const
