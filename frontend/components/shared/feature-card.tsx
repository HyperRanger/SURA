import type { Feature } from "@/types"
import { IconTile } from "@/components/shared/icon-tile"

export function FeatureCard({ feature }: { feature: Feature }) {
  return (
    <article className="card-raised rounded-[2rem] p-7 transition-transform duration-200 hover:-translate-y-1">
      <IconTile icon={feature.icon} tone={feature.tone} size="lg" />
      <h3 className="mt-5 text-xl font-black">{feature.title}</h3>
      <p className="mt-2 text-[15px] leading-relaxed text-muted-foreground">{feature.description}</p>
    </article>
  )
}
