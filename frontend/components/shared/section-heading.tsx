import type { ReactNode } from "react"
import { cn } from "@/lib/utils"

type SectionHeadingProps = {
  eyebrow?: string
  title: ReactNode
  description?: ReactNode
  className?: string
}

export function SectionHeading({ eyebrow, title, description, className }: SectionHeadingProps) {
  return (
    <div className={cn("mx-auto max-w-2xl text-center", className)}>
      {eyebrow && (
        <p className="text-sm font-extrabold uppercase tracking-[0.2em] text-muted-foreground">
          {eyebrow}
        </p>
      )}
      <h2 className="mt-5 text-3xl font-black tracking-tight text-balance sm:text-4xl md:text-5xl">
        {title}
      </h2>
      {description && (
        <p className="mt-4 text-base leading-relaxed text-pretty text-muted-foreground sm:text-lg">
          {description}
        </p>
      )}
    </div>
  )
}
