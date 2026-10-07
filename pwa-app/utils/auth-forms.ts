import { incomeContexts, type SignupStepId } from "@/config/auth"
import type { IncomeContext, SelfServiceRole, SignupPayload } from "@/types"
import { normalizePhone } from "@/utils/phone"
import { checked, compose, maxLength, nigerianMobile, oneOf, required } from "@/utils/validators"

export type SignupValues = {
  role: SelfServiceRole
  name: string
  phone: string
  context: IncomeContext | ""
  businessName: string
  businessCategory: string
  termsAccepted: boolean
}

export function initialSignupValues(role: SelfServiceRole = "individual"): SignupValues {
  return {
    role,
    name: "",
    phone: "",
    context: "",
    businessName: "",
    businessCategory: "",
    termsAccepted: false,
  }
}

export const signupStepFields: Record<SignupStepId, readonly (keyof SignupValues)[]> = {
  account: ["role"],
  details: ["name", "phone"],
  earning: ["context", "termsAccepted"],
  business: ["businessName", "businessCategory", "termsAccepted"],
}

const phoneRule = compose(required("Enter your phone number"), nigerianMobile())

export function signupSchema(values: SignupValues) {
  const shared = {
    name: compose(required("Enter your full name"), maxLength(200)),
    phone: phoneRule,
    termsAccepted: checked("Accept the terms to continue"),
  }

  if (values.role === "vendor") {
    return {
      ...shared,
      businessName: compose(required("Enter your business name"), maxLength(200)),
      businessCategory: compose(required("Say what your business sells"), maxLength(120)),
    }
  }

  return { ...shared, context: oneOf(incomeContexts, "Pick the one closest to how you earn") }
}

export function toSignupPayload(values: SignupValues): SignupPayload {
  const base = {
    name: values.name.trim(),
    phone: normalizePhone(values.phone),
    terms_accepted: values.termsAccepted,
  }

  if (values.role === "vendor") {
    return {
      ...base,
      role: "vendor",
      business_name: values.businessName.trim(),
      business_category: values.businessCategory.trim(),
    }
  }

  return { ...base, role: "individual", context: values.context as IncomeContext }
}

export type LoginValues = { phone: string }

export const initialLoginValues: LoginValues = { phone: "" }

export function loginSchema() {
  return { phone: phoneRule }
}
