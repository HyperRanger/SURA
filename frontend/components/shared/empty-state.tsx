import type { ReactNode } from "react"
import type { IconSvgElement } from "@hugeicons/react"
import { IconTile } from "@/components/shared/icon-tile"
import { cn } from "@/lib/utils"

type EmptyStateProps = {
  icon: IconSvgElement
  title: string
  description?: ReactNode
  action?: ReactNode
  className?: string
}

// U7. shown when a list loaded fine but has nothing in it
export function EmptyState({ icon, title, description, action, className }: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center rounded-3xl border-2 border-dashed border-hairline px-6 py-12 text-center",
        className
      )}
    >
      <IconTile icon={icon} />
      <p className="mt-4 text-base font-bold">{title}</p>
      {description && (
        <p className="mt-1 max-w-sm text-sm leading-relaxed font-semibold text-muted-foreground">{description}</p>
      )}
      {action && <div className="mt-5">{action}</div>}
    </div>
  )
}
