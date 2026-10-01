import { HugeiconsIcon } from "@hugeicons/react"
import { ArrowRight01Icon } from "@hugeicons/core-free-icons"
import type { DemoPersona } from "@/config/demo"
import { IconTile } from "@/components/shared/icon-tile"
import { Spinner } from "@/components/ui/spinner"
import { cn } from "@/lib/utils"

type PersonaCardProps = {
  persona: DemoPersona
  onSelect: (persona: DemoPersona) => void
  loading?: boolean
  disabled?: boolean
}

export function PersonaCard({ persona, onSelect, loading, disabled }: PersonaCardProps) {
  return (
    <button
      type="button"
      onClick={() => onSelect(persona)}
      disabled={disabled}
      aria-busy={loading || undefined}
      className={cn(
        "cursor-pointer card-raised group flex w-full items-center gap-4 rounded-3xl p-4 text-left transition-all",
        "hover:border-hairline-strong active:translate-y-0.5 active:border-b-2",
        "focus-visible:ring-4 focus-visible:ring-ring/20 focus-visible:outline-none",
        "disabled:pointer-events-none disabled:opacity-60",
        loading && "border-primary opacity-100!"
      )}
    >
      <IconTile icon={persona.icon} tone={persona.area === "bank" ? "gold" : "indigo"} />
      <span className="min-w-0 flex-1">
        <span className="flex flex-wrap items-baseline gap-x-2">
          <span className="text-base font-black text-foreground">{persona.name}</span>
          <span className="text-xs font-extrabold text-gold-deep">{persona.tagline}</span>
        </span>
        <span className="mt-0.5 block text-sm leading-snug font-semibold text-muted-foreground">
          {persona.description}
        </span>
      </span>
      <span className="flex size-9 shrink-0 items-center justify-center rounded-full bg-cloud text-link transition-colors group-hover:bg-primary group-hover:text-primary-foreground">
        {loading ? <Spinner /> : <HugeiconsIcon icon={ArrowRight01Icon} size={18} strokeWidth={2.5} />}
      </span>
    </button>
  )
}
