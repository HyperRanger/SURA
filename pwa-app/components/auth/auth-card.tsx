import type { ReactNode } from "react"
import { cn } from "@/lib/utils"

type AuthCardProps = {
  title: ReactNode
  description?: ReactNode
  header?: ReactNode
  titleId?: string
  children: ReactNode
  footer?: ReactNode
  className?: string
}

// on a phone the screen itself is the surface, like a native app. from sm up the
// form sits in a raised card in the middle of the page
export function AuthCard({ title, description, header, titleId, children, footer, className }: AuthCardProps) {
  return (
    <div className={cn("w-full max-w-md", className)}>
      <div className="sm:card-raised sm:rounded-3xl sm:p-8">
        {header && <div className="mb-6">{header}</div>}
        <h1 id={titleId} className="text-[1.75rem] leading-tight font-bold tracking-tight text-balance sm:text-3xl">
          {title}
        </h1>
        {description && (
          <p className="mt-2 text-sm leading-relaxed font-semibold text-muted-foreground">{description}</p>
        )}
        <div className="mt-7">{children}</div>
      </div>
      {footer && <div className="mt-6 text-center text-sm font-semibold text-muted-foreground">{footer}</div>}
    </div>
  )
}
