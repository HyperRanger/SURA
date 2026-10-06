"use client"

import { useMemo } from "react"
import { useActiveSection } from "@/hooks/use-active-section"
import { cn } from "@/lib/utils"

type ContentsItem = { id: string; heading: string }

// the "on this page" list. sticky in the sidebar on large screens, highlights the section in view
export function LegalContents({ items }: { items: ContentsItem[] }) {
  const ids = useMemo(() => items.map((item) => item.id), [items])
  const active = useActiveSection(ids)

  return (
    <nav aria-label="Contents" className="lg:sticky lg:top-28">
      <h2 className="text-xs font-bold tracking-wider text-gold-deep">On this page</h2>
      <ol className="mt-4 flex flex-col border-l border-border">
        {items.map((item, index) => {
          const isActive = item.id === active
          return (
            <li key={item.id}>
              <a
                href={`#${item.id}`}
                aria-current={isActive ? "location" : undefined}
                className={cn(
                  "-ml-px block border-l-2 py-1.5 pl-4 text-sm font-bold transition-colors",
                  isActive
                    ? "border-gold text-link"
                    : "border-transparent text-muted-foreground hover:border-border hover:text-link"
                )}
              >
                <span className={cn("mr-1.5 tabular-nums", isActive ? "text-gold-deep" : "text-muted-foreground/70")}>
                  {index + 1}.
                </span>
                {item.heading}
              </a>
            </li>
          )
        })}
      </ol>
    </nav>
  )
}
