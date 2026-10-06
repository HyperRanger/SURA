import { isValidNigerianMobile } from "@/utils/phone"

// a validator returns an error message, or undefined when the value is fine
export type Validator<T = string> = (value: T) => string | undefined

export const required =
  (message = "This field is required"): Validator<string> =>
  (value) =>
    value.trim() ? undefined : message

export const minLength =
  (min: number, message?: string): Validator<string> =>
  (value) =>
    value.trim().length >= min ? undefined : (message ?? `Use at least ${min} characters`)

export const maxLength =
  (max: number, message?: string): Validator<string> =>
  (value) =>
    value.trim().length <= max ? undefined : (message ?? `Use at most ${max} characters`)

export const nigerianMobile =
  (message = "Enter a Nigerian mobile number, like 0803 000 0000"): Validator<string> =>
  (value) =>
    isValidNigerianMobile(value) ? undefined : message

export const checked =
  (message: string): Validator<boolean> =>
  (value) =>
    value ? undefined : message

export const oneOf =
  <T extends string>(options: readonly T[], message: string): Validator<T | ""> =>
  (value) =>
    options.includes(value as T) ? undefined : message

// runs validators in order and stops at the first failure
export function compose<T>(...validators: Validator<T>[]): Validator<T> {
  return (value) => {
    for (const validate of validators) {
      const error = validate(value)
      if (error) return error
    }
    return undefined
  }
}
