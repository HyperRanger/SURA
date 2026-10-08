export type SelfServiceRole = "individual" | "vendor"
export type UserRole = SelfServiceRole | "bank" | "admin" | (string & {})
export type IncomeContext = "trader" | "student" | "freelancer" | "other"
export type ChallengePurpose = "signup" | "login"

export type IndividualSignupPayload = {
  role: "individual"
  name: string
  phone: string
  email: string
  password: string
  context: IncomeContext
  terms_accepted: boolean
}

export type VendorSignupPayload = {
  role: "vendor"
  name: string
  phone: string
  email: string
  password: string
  business_name: string
  business_category: string
  terms_accepted: boolean
}

export type SignupPayload = IndividualSignupPayload | VendorSignupPayload
export type LoginPayload = { identifier: string; password: string; device_token?: string | null }
export type VerifyOtpPayload = { challenge_id: string; code: string }
export type ResendOtpPayload = { challenge_id: string }
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
  otp_required?: false
  trusted_device_token?: string
  trusted_device_expires_in_seconds?: number
}
export type LoginResponse = AuthChallengeResponse | AuthTokenResponse
export type Session = { accessToken: string; userId: string; role: UserRole; trustedDeviceToken?: string }
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
