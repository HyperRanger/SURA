// api paths, relative to NEXT_PUBLIC_API_URL. see /docs on the api for the contract
export const endpoints = {
  auth: {
    signup: "/v1/auth/signup",
    login: "/v1/auth/login",
    verifyOtp: "/v1/auth/verify-otp",
    demoToken: "/v1/auth/demo-token",
  },
  me: "/v1/me",
  logout: "/v1/logout",
  logoutAll: "/v1/logout-all",
  vendors: "/v1/vendors",
  commitments: "/v1/commitments",
  consent: "/v1/consent",
  notifications: "/v1/notifications",
  score: (userId: string) => `/v1/score/${encodeURIComponent(userId)}`,
  scoreHistory: (userId: string) => `/v1/score/${encodeURIComponent(userId)}/history`,
  app: {
    home: "/v1/app/home",
    vendorOverview: "/v1/app/vendor/overview",
    vendorRecommendations: "/v1/app/recommendations/vendors",
    resolveMember: "/v1/app/members/resolve",
    lockPreview: "/v1/app/commitments/lock-preview",
    groupHealth: (commitmentId: string) => `/v1/app/commitments/${encodeURIComponent(commitmentId)}/group-health`,
  },
  vendorRedemptions: "/v1/vendors/redemptions",
  demo: {
    loginAs: "/v1/demo/login-as",
  },
} as const
