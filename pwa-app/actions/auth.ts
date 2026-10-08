import { api } from "@/lib/api"
import { endpoints } from "@/config/endpoints"
import type {
  AuthChallengeResponse,
  AuthTokenResponse,
  LoginResponse,
  LoginPayload,
  ResendOtpPayload,
  SignupPayload,
  VerifyOtpPayload,
} from "@/types"

// P2. creates the account unverified and sends a code to the phone
export async function signup(payload: SignupPayload) {
  const { data } = await api.post<AuthChallengeResponse>(endpoints.auth.signup, payload)
  return data
}

// P3. answers the same way for unknown numbers, so a wrong number only fails at /verify
export async function requestLoginCode(payload: LoginPayload) {
  const { data } = await api.post<LoginResponse>(endpoints.auth.login, payload)
  return data
}

export async function resendOtp(payload: ResendOtpPayload) {
  const { data } = await api.post<AuthChallengeResponse>(endpoints.auth.resendOtp, payload)
  return data
}

// P4. consumes the code and returns the session token with the assigned role
export async function verifyOtp(payload: VerifyOtpPayload) {
  const { data } = await api.post<AuthTokenResponse>(endpoints.auth.verifyOtp, payload)
  return data
}
