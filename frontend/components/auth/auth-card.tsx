import type { ReactNode } from "react"
import { cn } from "@/lib/utils"

type AuthCardProps = {
  title: ReactNode
  description?: ReactNode
  // sits above the title, e.g. a step progress bar
  header?: ReactNode
  // lets a form point aria-labelledby at the title, e.g. a radio group that is the question
  titleId?: string
  children: ReactNode
  footer?: ReactNode
  className?: string
}

export function AuthCard({
  title,
  description,
  header,
  titleId,
  children,
  footer,
  className,
}: AuthCardProps) {
  return (
    <div className={cn("w-full", className)}>
      <div className="card-raised rounded-3xl p-6 sm:p-8">
        {header && <div className="mb-6">{header}</div>}
        <h1 id={titleId} className="text-2xl font-black tracking-tight text-balance sm:text-3xl">
          {title}
        </h1>
        {description && (
          <p className="mt-2 text-sm leading-relaxed font-semibold text-muted-foreground">
            {description}
          </p>
        )}
        <div className="mt-7">{children}</div>
      </div>
      {footer && (
        <div className="mt-5 text-center text-sm font-semibold text-muted-foreground">{footer}</div>
      )}
    </div>
  )
}
