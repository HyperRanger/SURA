export type SelfServiceRole = "individual" | "vendor"
export type UserRole = SelfServiceRole | "bank" | "admin" | (string & {})
export type IncomeContext = "trader" | "student" | "freelancer" | "other"
export type ChallengePurpose = "signup" | "login"

export type IndividualSignupPayload = {
  role: "individual"
  name: string
  phone: string
  context: IncomeContext
  terms_accepted: boolean
}

export type VendorSignupPayload = {
  role: "vendor"
  name: string
  phone: string
  business_name: string
  business_category: string
  terms_accepted: boolean
}

export type SignupPayload = IndividualSignupPayload | VendorSignupPayload
export type LoginPayload = { phone: string }
export type VerifyOtpPayload = { challenge_id: string; code: string }
export type AuthChallengeResponse = {
  challenge_id: string
  purpose: ChallengePurpose
  expires_in_seconds: number
  resend_after_seconds: number
  demo_code?: string
}
export type AuthTokenResponse = {
  access_token: string
  token_type: "bearer"
  user_id: string
  role: UserRole
}
export type Session = { accessToken: string; userId: string; role: UserRole }
export type PendingChallenge = {
  challengeId: string
  purpose: ChallengePurpose
  isNewAccount: boolean
  phone: string
  demoCode?: string
  expiresAt: number
  resendAvailableAt: number
  next?: string
}
