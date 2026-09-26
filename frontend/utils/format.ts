const nairaFormatter = new Intl.NumberFormat("en-NG", {
  style: "currency",
  currency: "NGN",
  maximumFractionDigits: 0,
})

export function formatNaira(amount: number) {
  return nairaFormatter.format(amount)
}

export function initials(name: string) {
  return name.slice(0, 1)
}
