import type { ReactNode } from "react"
import { cn } from "@/lib/utils"

type AuthCardProps = {
  title: ReactNode
  description?: ReactNode
  children: ReactNode
  footer?: ReactNode
  className?: string
}

export function AuthCard({ title, description, children, footer, className }: AuthCardProps) {
  return (
    <div className={cn("w-full", className)}>
      <div className="card-raised rounded-3xl p-6 sm:p-8">
        <h1 className="text-2xl font-black tracking-tight text-balance sm:text-3xl">{title}</h1>
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
