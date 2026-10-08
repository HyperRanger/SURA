import { HugeiconsIcon } from "@hugeicons/react"
import { CheckmarkCircle02Icon } from "@hugeicons/core-free-icons"
import { vendorLockPoints } from "@/config/landing"
import { VoucherPreview } from "@/components/landing/voucher-preview"

export function VendorLock() {
  return (
    <section id="vendor-lock" className="py-16 md:py-24">
      <div className="container-app">
        <div className="grid items-center gap-10 rounded-[2rem] border-b-8 border-primary-deep bg-primary px-5 py-8 text-primary-foreground sm:px-8 md:grid-cols-[1.1fr_0.9fr] md:p-12">
          <div>
            <p className="text-sm font-bold text-gold">Vendor lock</p>
            <h2 className="mt-2 text-3xl font-bold tracking-tight text-balance sm:text-4xl">
              Payouts go to a shop, not a pocket
            </h2>
            <p className="mt-3 text-base leading-relaxed text-pretty text-primary-foreground/85 sm:text-lg">
              Your circle picks a verified vendor on day one. When it&apos;s your turn, you get a voucher for that
              vendor, so the money buys the thing you saved for and nobody can collect and disappear.
            </p>
            <ul className="mt-6 flex flex-col gap-3">
              {vendorLockPoints.map((point) => (
                <li key={point} className="flex items-start gap-2.5 text-[15px] leading-snug font-semibold">
                  <HugeiconsIcon icon={CheckmarkCircle02Icon} size={20} strokeWidth={2.2} className="mt-px shrink-0 text-gold" />
                  {point}
                </li>
              ))}
            </ul>
          </div>

          <VoucherPreview />
        </div>
      </div>
    </section>
  )
}
