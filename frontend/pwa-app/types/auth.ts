// shapes mirror the backend contract at /docs (auth and demo tags)

export type SelfServiceRole = "individual" | "vendor"

// bank staff roles are provisioned, e.g. bank_admin, and use the website's console
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
  // the contact person; the backend names the account after the business
  name: string
  phone: string
  business_name: string
  business_category: string
  terms_accepted: boolean
}

export type SignupPayload = IndividualSignupPayload | VendorSignupPayload

export type LoginPayload = {
  phone: string
}

export type VerifyOtpPayload = {
  challenge_id: string
  code: string
}

export type AuthChallengeResponse = {
  challenge_id: string
  purpose: ChallengePurpose
  expires_in_seconds: number
  resend_after_seconds: number
  // only returned outside production
  demo_code?: string
}

export type AuthTokenResponse = {
  access_token: string
  token_type: "bearer"
  user_id: string
  role: UserRole
}

export type Session = {
  accessToken: string
  userId: string
  role: UserRole
}

// held between /login or /signup and /verify, so a refresh on /verify keeps working
export type PendingChallenge = {
  challengeId: string
  purpose: ChallengePurpose
  // stays true across a resend, which the api always issues as a login code
  isNewAccount: boolean
  phone: string
  demoCode?: string
  expiresAt: number
  resendAvailableAt: number
  // where to land after verifying, e.g. the page a session expired on
  next?: string
}
