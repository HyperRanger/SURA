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
    login: "/bank/login",
    home: "/bank",
    commitments: "/bank/commitments",
    commitment: (id: string) => `/bank/commitments/${encodeURIComponent(id)}`,
    users: "/bank/users",
    user: (id: string) => `/bank/users/${encodeURIComponent(id)}`,
    auditLog: "/bank/audit-log",
    flags: "/bank/flags",
    flag: (id: string) => `/bank/flags/${encodeURIComponent(id)}`,
    settlements: "/bank/settlements",
    developers: "/bank/developers",
    team: "/bank/team",
    settings: "/bank/settings",
    account: "/bank/account",
  },
} as const
