import { HugeiconsIcon, type IconSvgElement } from "@hugeicons/react"
import type { Tone } from "@/types"
import { cn } from "@/lib/utils"

const tones: Record<Tone, string> = {
  indigo: "bg-indigo-soft text-link",
  gold: "bg-gold-soft text-gold-deep",
}

type IconTileProps = {
  icon: IconSvgElement
  tone?: Tone
  size?: "md" | "lg"
  className?: string
}

export function IconTile({ icon, tone = "indigo", size = "md", className }: IconTileProps) {
  return (
    <span
      className={cn(
        "flex shrink-0 items-center justify-center rounded-full",
        size === "md" ? "size-12" : "size-14",
        tones[tone],
        className
      )}
    >
      <HugeiconsIcon icon={icon} size={size === "md" ? 24 : 28} strokeWidth={2} />
    </span>
  )
}
