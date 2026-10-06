import { HugeiconsIcon, type IconSvgElement } from "@hugeicons/react"
import type { Tone } from "@/types"
import { cn } from "@/lib/utils"

const tones: Record<Tone, string> = {
  iris: "bg-primary-soft text-link",
  gold: "bg-gold-soft text-gold-deep",
  mint: "bg-success-soft text-success",
}

type IconTileProps = {
  icon: IconSvgElement
  tone?: Tone
  size?: "sm" | "md" | "lg"
  className?: string
}

const sizes = {
  sm: { box: "size-10", icon: 20 },
  md: { box: "size-12", icon: 24 },
  lg: { box: "size-14", icon: 28 },
}

export function IconTile({ icon, tone = "iris", size = "md", className }: IconTileProps) {
  return (
    <span className={cn("flex shrink-0 items-center justify-center rounded-full", sizes[size].box, tones[tone], className)}>
      <HugeiconsIcon icon={icon} size={sizes[size].icon} strokeWidth={2} />
    </span>
  )
}
