const COUNTRY_CODE = "234"

// mirrors the backend's normalize_phone so the number we show is the number it stores:
// 0803 000 0012, +234 803 000 0012 and 803 000 0012 all become 2348030000012
export function normalizePhone(input: string) {
  const digits = input.replace(/\D/g, "")
  if (digits.startsWith("0")) return COUNTRY_CODE + digits.slice(1)
  if (digits.length === 10 && /^[789]/.test(digits)) return COUNTRY_CODE + digits
  return digits
}

export function isValidNigerianMobile(input: string) {
  return /^234[789]\d{9}$/.test(normalizePhone(input))
}

// 2348030000012 → +234 803 000 0012
export function formatPhone(input: string) {
  const phone = normalizePhone(input)
  const match = phone.match(/^234(\d{3})(\d{3})(\d{4})$/)
  return match ? `+234 ${match[1]} ${match[2]} ${match[3]}` : input
}

// 2348030000012 → +234 803 *** 0012, for screens a passer-by might see
export function maskPhone(input: string) {
  const phone = normalizePhone(input)
  const match = phone.match(/^234(\d{3})\d{3}(\d{4})$/)
  return match ? `+234 ${match[1]} *** ${match[2]}` : input
}
