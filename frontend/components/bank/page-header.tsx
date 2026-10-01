import type { ReactNode } from "react"
import { BackButton } from "@/components/shared/back-button"

type PageHeaderProps = {
  title: ReactNode
  description?: ReactNode
  // detail screens pass the list they belong to, used when there is no history
  backHref?: string
  backLabel?: string
  meta?: ReactNode
  actions?: ReactNode
}

export function PageHeader({ title, description, backHref, backLabel, meta, actions }: PageHeaderProps) {
  return (
    <header className="mb-6 sm:mb-8">
      {backHref && <BackButton fallbackHref={backHref} label={backLabel} className="-ml-2 mb-2" />}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div className="min-w-0">
          <h1 className="text-2xl font-black tracking-tight text-balance sm:text-3xl">{title}</h1>
          {description && (
            <p className="mt-1.5 max-w-2xl text-sm leading-relaxed font-semibold text-muted-foreground">
              {description}
            </p>
          )}
          {meta && <div className="mt-3 flex flex-wrap items-center gap-2">{meta}</div>}
        </div>
        {actions && <div className="flex shrink-0 flex-wrap gap-2">{actions}</div>}
      </div>
    </header>
  )
}

type SectionProps = {
  title: string
  description?: ReactNode
  action?: ReactNode
  children: ReactNode
  className?: string
}

export function Section({ title, description, action, children, className }: SectionProps) {
  return (
    <section className={className}>
      <div className="mb-3 flex items-end justify-between gap-3">
        <div>
          <h2 className="text-lg font-black">{title}</h2>
          {description && <p className="mt-0.5 text-sm font-semibold text-muted-foreground">{description}</p>}
        </div>
        {action}
      </div>
      {children}
    </section>
  )
}

// label and value pairs for summary panels
export function DetailList({ items }: { items: { label: string; value: ReactNode }[] }) {
  return (
    <dl className="card-raised grid grid-cols-2 gap-x-4 gap-y-4 rounded-2xl p-4 sm:grid-cols-3 sm:p-5 lg:grid-cols-4">
      {items.map((item) => (
        <div key={item.label} className="min-w-0">
          <dt className="text-xs font-extrabold tracking-wide text-muted-foreground">{item.label}</dt>
          <dd className="mt-1 text-sm font-bold break-words">{item.value}</dd>
        </div>
      ))}
    </dl>
  )
}
