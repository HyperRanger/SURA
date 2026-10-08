import { incomeContexts, type SignupStepId } from "@/config/auth"
import type { IncomeContext, SelfServiceRole, SignupPayload } from "@/types"
import { normalizePhone } from "@/utils/phone"
import { checked, compose, maxLength, minLength, nigerianMobile, oneOf, required } from "@/utils/validators"

export type SignupValues = {
  role: SelfServiceRole
  name: string
  phone: string
  email: string
  password: string
  passwordConfirmation: string
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
    email: "",
    password: "",
    passwordConfirmation: "",
    context: "",
    businessName: "",
    businessCategory: "",
    termsAccepted: false,
  }
}

export const signupStepFields: Record<SignupStepId, readonly (keyof SignupValues)[]> = {
  account: ["role"],
  details: ["name", "phone", "email", "password", "passwordConfirmation"],
  earning: ["context", "termsAccepted"],
  business: ["businessName", "businessCategory", "termsAccepted"],
}

const phoneRule = compose(required("Enter your phone number"), nigerianMobile())

export function signupSchema(values: SignupValues) {
  const shared = {
    name: compose(required("Enter your full name"), maxLength(200)),
    phone: phoneRule,
    email: compose(required("Enter your email address"), maxLength(320)),
    password: compose(required("Create a password"), minLength(12, "Use at least 12 characters")),
    passwordConfirmation: (value: string) => value === values.password ? undefined : "Passwords do not match",
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
    email: values.email.trim().toLowerCase(),
    password: values.password,
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

export type LoginValues = { identifier: string; password: string }

export const initialLoginValues: LoginValues = { identifier: "", password: "" }

export function loginSchema() {
  return {
    identifier: required("Enter your email address or phone number"),
    password: compose(required("Enter your password"), minLength(1)),
  }
}
