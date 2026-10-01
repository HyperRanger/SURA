// one place for every path, so a renamed route is a one-line change
export const routes = {
  home: "/",
  signup: "/signup",
  login: "/login",
  verify: "/verify",
  terms: "/terms",
  privacy: "/privacy",
  forBanks: "/for-banks",
  demo: "/demo",
  member: {
    home: "/app",
    welcome: "/app/welcome",
  },
  vendor: {
    home: "/vendor",
  },
  bank: {
    home: "/bank",
  },
} as const
