import { api } from "@/lib/api"
import { endpoints } from "@/config/endpoints"
import { env } from "@/config/env"
import type { DemoSignIn } from "@/config/demo"
import type { AuthTokenResponse } from "@/types"

// every call here is refused by the api in production

export async function demoLoginAs(role: "individual" | "vendor") {
  const { data } = await api.post<AuthTokenResponse>(endpoints.demo.loginAs, { role })
  return data
}

// signs in as a named seeded person. the demo-token endpoint returns no role,
// and every seeded person it serves is a member
export async function demoLoginAsUser(userId: string, otpCode: string): Promise<AuthTokenResponse> {
  const { data } = await api.post<Pick<AuthTokenResponse, "access_token" | "token_type">>(
    endpoints.auth.demoToken,
    { user_id: userId, otp_code: otpCode }
  )
  return { ...data, user_id: userId, role: "individual" }
}

// external sign-ins are plain links and never reach here
export function demoSignIn(signIn: Exclude<DemoSignIn, { type: "external" }>): Promise<AuthTokenResponse> {
  switch (signIn.type) {
    case "seeded-user":
      return demoLoginAsUser(signIn.userId, env.demoOtpCode)
    case "role":
      return demoLoginAs(signIn.role)
  }
}
