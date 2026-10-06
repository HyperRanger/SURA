import type { ComponentProps } from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const badgeVariants = cva(
  "inline-flex w-fit shrink-0 items-center justify-center gap-1.5 rounded-full border-2 px-3 py-0.5 text-xs font-bold whitespace-nowrap [&>svg]:pointer-events-none",
  {
    variants: {
      variant: {
        default: "border-ring/15 bg-primary-soft text-link",
        gold: "border-gold/45 bg-gold-soft text-gold-deep",
        success: "border-success/25 bg-success-soft text-success",
        outline: "border-hairline bg-card text-muted-foreground",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

type BadgeProps = ComponentProps<"span"> & VariantProps<typeof badgeVariants>

function Badge({ className, variant, ...props }: BadgeProps) {
  return <span data-slot="badge" className={cn(badgeVariants({ variant }), className)} {...props} />
}

export { Badge, badgeVariants }
