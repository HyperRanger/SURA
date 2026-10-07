import type { ReactNode } from "react"
import { cn } from "@/lib/utils"

type SectionHeadingProps = {
  eyebrow?: string
  title: ReactNode
  description?: ReactNode
  // left on phones reads like an app screen; centred suits the wide desktop sections
  align?: "start" | "center"
  className?: string
}

export function SectionHeading({ title, description, align = "start", className }: SectionHeadingProps) {
  return (
    <div className={cn("max-w-2xl", align === "center" && "mx-auto md:text-center", className)}>
      <h2 className="mt-2 text-3xl font-bold tracking-tight text-balance sm:text-4xl">{title}</h2>
      {description && (
        <p className="mt-3 text-base leading-relaxed text-pretty text-muted-foreground sm:text-lg">{description}</p>
      )}
    </div>
  )
}
