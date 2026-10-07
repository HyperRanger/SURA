const COUNTRY_CODE = "234"

export function normalizePhone(input: string) {
  const digits = input.replace(/\D/g, "")
  if (digits.startsWith("0")) return COUNTRY_CODE + digits.slice(1)
  if (digits.length === 10 && /^[789]/.test(digits)) return COUNTRY_CODE + digits
  return digits
}

export function isValidNigerianMobile(input: string) {
  return /^234[789]\d{9}$/.test(normalizePhone(input))
}

export function formatPhone(input: string) {
  const match = normalizePhone(input).match(/^234(\d{3})(\d{3})(\d{4})$/)
  return match ? `+234 ${match[1]} ${match[2]} ${match[3]}` : input
}

export function maskPhone(input: string) {
  const match = normalizePhone(input).match(/^234(\d{3})\d{3}(\d{4})$/)
  return match ? `+234 ${match[1]} *** ${match[2]}` : input
}
