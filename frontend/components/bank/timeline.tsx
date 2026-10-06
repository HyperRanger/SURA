import type { ReactNode } from "react"
import { formatDateTime } from "@/utils/format"

export type TimelineItem = {
  id: string
  title: ReactNode
  detail?: ReactNode
  at: string | null
}

// newest first, as the api returns it
export function Timeline({ items, empty }: { items: TimelineItem[]; empty: string }) {
  if (items.length === 0) {
    return (
      <p className="rounded-2xl border-2 border-dashed border-hairline px-4 py-6 text-center text-sm font-semibold text-muted-foreground">
        {empty}
      </p>
    )
  }

  return (
    <ol className="card-raised rounded-2xl p-4 sm:p-5">
      {items.map((item, index) => (
        <li key={item.id} className="relative flex gap-3.5 pb-5 last:pb-0">
          {index < items.length - 1 && (
            <span aria-hidden="true" className="absolute top-4 bottom-0 left-[5px] w-0.5 bg-hairline" />
          )}
          <span aria-hidden="true" className="mt-1.5 size-3 shrink-0 rounded-full border-2 border-ring bg-card" />
          <div className="min-w-0 flex-1">
            <div className="flex flex-col gap-0.5 sm:flex-row sm:items-baseline sm:justify-between sm:gap-3">
              <p className="text-sm font-bold">{item.title}</p>
              <time className="shrink-0 text-xs font-bold text-muted-foreground">{formatDateTime(item.at)}</time>
            </div>
            {item.detail && <div className="mt-0.5 text-sm font-semibold text-muted-foreground">{item.detail}</div>}
          </div>
        </li>
      ))}
    </ol>
  )
}
