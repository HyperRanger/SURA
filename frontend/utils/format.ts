const nairaFormatter = new Intl.NumberFormat("en-NG", {
  style: "currency",
  currency: "NGN",
  maximumFractionDigits: 0,
})

export function formatNaira(amount: number) {
  return nairaFormatter.format(amount)
}

const dateFormatter = new Intl.DateTimeFormat("en-NG", {
  day: "numeric",
  month: "long",
  year: "numeric",
  timeZone: "Africa/Lagos",
})

// "2026-10-01" → "1 october 2026" (shown lowercase by the site styles)
export function formatDate(value: string | Date) {
  return dateFormatter.format(typeof value === "string" ? new Date(value) : value)
}

// 272 → "4:32"
export function formatCountdown(totalSeconds: number) {
  const seconds = Math.max(0, Math.floor(totalSeconds))
  const minutes = Math.floor(seconds / 60)
  return `${minutes}:${String(seconds % 60).padStart(2, "0")}`
}

export function initials(name: string) {
  return name.slice(0, 1)
}

const dateTimeFormatter = new Intl.DateTimeFormat("en-NG", {
  day: "numeric",
  month: "short",
  year: "numeric",
  hour: "numeric",
  minute: "2-digit",
  timeZone: "Africa/Lagos",
})

// the api sends naive utc timestamps without a zone, so one is added before parsing
function parseApiDate(value: string) {
  return new Date(/[zZ]|[+-]\d{2}:?\d{2}$/.test(value) ? value : `${value}Z`)
}

// "2026-10-01T14:05:00" → "1 oct 2026, 3:05 pm" in lagos time. "—" when missing
export function formatDateTime(value: string | null | undefined) {
  if (!value) return "—"
  const date = parseApiDate(value)
  return Number.isNaN(date.getTime()) ? "—" : dateTimeFormatter.format(date)
}

// 0.875 → "88%". "—" when there is nothing to measure yet
export function formatPercent(ratio: number | null | undefined) {
  if (ratio === null || ratio === undefined) return "—"
  return `${Math.round(ratio * 100)}%`
}

// "risk_flag_resolved" or "voucher.redeemed" → "risk flag resolved"
export function humanize(value: string | null | undefined) {
  if (!value) return "—"
  return value.replace(/[_.]+/g, " ").trim()
}
