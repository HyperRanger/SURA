import type { ReactNode } from "react"
import { HugeiconsIcon } from "@hugeicons/react"
import { ArrowRight01Icon, ArrowUpRight01Icon } from "@hugeicons/core-free-icons"
import type { DemoArea, DemoPersona } from "@/config/demo"
import { IconTile } from "@/components/shared/icon-tile"
import { Spinner } from "@/components/ui/spinner"
import { cn } from "@/lib/utils"
import type { Tone } from "@/types"

const areaTones: Record<DemoArea, Tone> = {
  member: "iris",
  vendor: "mint",
  bank: "gold",
}

const cardClass = cn(
  "card-raised group flex w-full items-center gap-4 rounded-3xl p-4 text-left transition-all",
  "hover:border-hairline-strong active:translate-y-0.5 active:border-b-2",
  "focus-visible:ring-4 focus-visible:ring-ring/20 focus-visible:outline-none"
)

type PersonaCardProps = {
  persona: DemoPersona
  onSelect: (persona: DemoPersona) => void
  loading?: boolean
  disabled?: boolean
}

// a seeded person to sign in as, or a link out for the bank, which signs in on the website
export function PersonaCard({ persona, onSelect, loading, disabled }: PersonaCardProps) {
  if (persona.signIn.type === "external") {
    return (
      <a href={persona.signIn.href} className={cardClass}>
        <PersonaBody persona={persona}>
          <HugeiconsIcon icon={ArrowUpRight01Icon} size={18} strokeWidth={2.5} />
        </PersonaBody>
      </a>
    )
  }

  return (
    <button
      type="button"
      onClick={() => onSelect(persona)}
      disabled={disabled}
      aria-busy={loading || undefined}
      className={cn(cardClass, "disabled:pointer-events-none disabled:opacity-60", loading && "border-ring opacity-100!")}
    >
      <PersonaBody persona={persona}>
        {loading ? <Spinner /> : <HugeiconsIcon icon={ArrowRight01Icon} size={18} strokeWidth={2.5} />}
      </PersonaBody>
    </button>
  )
}

function PersonaBody({ persona, children }: { persona: DemoPersona; children: ReactNode }) {
  return (
    <>
      <IconTile icon={persona.icon} tone={areaTones[persona.area]} />
      <span className="min-w-0 flex-1">
        <span className="flex flex-wrap items-baseline gap-x-2">
          <span className="text-base font-bold text-foreground">{persona.name}</span>
          <span className="text-xs font-bold text-link">{persona.tagline}</span>
        </span>
        <span className="mt-0.5 block text-sm leading-snug font-semibold text-muted-foreground">
          {persona.description}
        </span>
      </span>
      <span className="flex size-9 shrink-0 items-center justify-center rounded-full bg-cloud text-link transition-colors group-hover:bg-primary group-hover:text-primary-foreground">
        {children}
      </span>
    </>
  )
}
