import type { ReactNode } from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { HugeiconsIcon, type IconSvgElement } from "@hugeicons/react"
import { Alert02Icon, InformationCircleIcon, Key01Icon } from "@hugeicons/core-free-icons"
import { cn } from "@/lib/utils"

const alertVariants = cva("flex items-start gap-3 rounded-2xl border-2 px-4 py-3 text-sm font-semibold", {
  variants: {
    variant: {
      info: "border-ring/15 bg-indigo-soft text-link",
      error: "border-destructive/25 bg-destructive/8 text-destructive",
      gold: "border-gold/45 bg-gold-soft text-gold-deep",
    },
  },
  defaultVariants: { variant: "info" },
})

const icons: Record<NonNullable<VariantProps<typeof alertVariants>["variant"]>, IconSvgElement> = {
  info: InformationCircleIcon,
  error: Alert02Icon,
  gold: Key01Icon,
}

type AlertProps = VariantProps<typeof alertVariants> & {
  title?: ReactNode
  children?: ReactNode
  icon?: IconSvgElement
  action?: ReactNode
  className?: string
}

export function Alert({ variant = "info", title, children, icon, action, className }: AlertProps) {
  return (
    <div
      role={variant === "error" ? "alert" : "status"}
      className={cn(alertVariants({ variant }), className)}
    >
      <HugeiconsIcon
        icon={icon ?? icons[variant ?? "info"]}
        size={20}
        strokeWidth={2}
        className="mt-px shrink-0"
      />
      <div className="flex-1">
        {title && <p className="font-bold">{title}</p>}
        {children && <div className={cn(title && "mt-0.5 font-semibold opacity-90")}>{children}</div>}
      </div>
      {action}
    </div>
  )
}
