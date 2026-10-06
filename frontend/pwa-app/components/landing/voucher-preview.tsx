import { HugeiconsIcon } from "@hugeicons/react"
import { CancelCircleIcon, CheckmarkCircle02Icon, QrCodeIcon, StoreVerified01Icon } from "@hugeicons/core-free-icons"
import { voucherPreview } from "@/config/landing"
import { formatNaira } from "@/utils/format"

// an illustrative voucher, and what happens when it's shown at the right and the
// wrong counter. drawn for the iris panel it sits on
export function VoucherPreview() {
  const { code, amount, vendor, beneficiary, cycle, expires, wrongVendor } = voucherPreview

  return (
    <div aria-hidden="true" className="mx-auto w-full max-w-sm select-none">
      <div className="relative rounded-3xl bg-card text-card-foreground">
        <div className="p-5">
          <div className="flex items-center justify-between">
            <p className="text-xs font-bold text-muted-foreground">
              Voucher · Cycle {cycle} · {beneficiary}
            </p>
            <span className="rounded-full bg-success-soft px-2.5 py-0.5 text-[11px] font-bold text-success">Ready</span>
          </div>
          <p className="mt-2 text-4xl font-bold tracking-tight tabular-nums">{formatNaira(amount)}</p>
          <p className="mt-2 flex items-center gap-1.5 text-sm font-bold">
            <HugeiconsIcon icon={StoreVerified01Icon} size={18} strokeWidth={2} className="text-link" />
            Redeem only at {vendor}
          </p>
        </div>

        {/* the perforation: two notches cut in the panel colour and a dashed tear line */}
        <div className="relative h-0 border-t-2 border-dashed border-hairline">
          <span className="absolute -top-3 -left-3 size-6 rounded-full bg-primary" />
          <span className="absolute -top-3 -right-3 size-6 rounded-full bg-primary" />
        </div>

        <div className="flex items-center justify-between gap-4 p-5">
          <div>
            <p className="font-mono text-sm font-bold tracking-wider">{code}</p>
            <p className="mt-0.5 text-xs font-semibold text-muted-foreground">Expires {expires}</p>
          </div>
          <span className="flex size-12 items-center justify-center rounded-2xl bg-cloud text-foreground">
            <HugeiconsIcon icon={QrCodeIcon} size={28} strokeWidth={1.8} />
          </span>
        </div>
      </div>

      <ul className="mt-4 flex flex-col gap-2 text-sm font-bold">
        <li className="flex items-center gap-2.5 rounded-full bg-white/10 py-2 pr-4 pl-2">
          <span className="flex size-7 items-center justify-center rounded-full bg-success text-white">
            <HugeiconsIcon icon={CheckmarkCircle02Icon} size={16} strokeWidth={2.2} />
          </span>
          <span className="flex-1">{vendor}</span>
          <span className="text-xs text-white/80">Redeemed</span>
        </li>
        <li className="flex items-center gap-2.5 rounded-full bg-white/10 py-2 pr-4 pl-2">
          <span className="flex size-7 items-center justify-center rounded-full bg-destructive text-white">
            <HugeiconsIcon icon={CancelCircleIcon} size={16} strokeWidth={2.2} />
          </span>
          <span className="flex-1">{wrongVendor}</span>
          <span className="text-xs text-white/80">Rejected: wrong vendor</span>
        </li>
      </ul>
    </div>
  )
}
