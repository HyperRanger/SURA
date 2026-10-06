import type { ReactNode } from "react"
import Link from "next/link"
import { HugeiconsIcon } from "@hugeicons/react"
import { ArrowRight01Icon } from "@hugeicons/core-free-icons"
import { Skeleton } from "@/components/ui/skeleton"
import { cn } from "@/lib/utils"

export type Column<T> = {
  header: string
  cell: (row: T) => ReactNode
  align?: "left" | "right"
  // on phones, spans the whole card and never truncates, e.g. a row of buttons
  wide?: boolean
}

type DataTableProps<T> = {
  // the first column names the row; it heads each card on small screens
  columns: Column<T>[]
  rows: T[]
  rowKey: (row: T) => string
  rowHref?: (row: T) => string
  caption: string
}

// a table on wide screens and a stack of cards on phones, from one column list.
// with rowHref the whole row is one link, named by its first column
export function DataTable<T>({ columns, rows, rowKey, rowHref, caption }: DataTableProps<T>) {
  const [primary, ...rest] = columns

  return (
    <>
      <ul aria-label={caption} className="flex flex-col gap-3 md:hidden">
        {rows.map((row) => {
          const href = rowHref?.(row)
          return (
            <li key={rowKey(row)} className="card-raised relative rounded-2xl p-4">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0 text-sm font-bold">
                  {href ? (
                    <Link href={href} title="Open details" className="after:absolute after:inset-0 after:rounded-2xl focus-visible:outline-none">
                      {primary.cell(row)}
                    </Link>
                  ) : (
                    primary.cell(row)
                  )}
                </div>
                {href && (
                  <HugeiconsIcon icon={ArrowRight01Icon} size={18} strokeWidth={2.5} className="mt-0.5 shrink-0 text-muted-foreground" />
                )}
              </div>
              <dl className="mt-3 grid grid-cols-2 gap-x-4 gap-y-2.5">
                {rest.map((column) => (
                  <div key={column.header} className={cn("min-w-0", column.wide && "col-span-2")}>
                    <dt className="text-[11px] font-bold tracking-wide text-muted-foreground">{column.header}</dt>
                    <dd className={cn("mt-0.5 text-sm font-semibold", !column.wide && "truncate")}>{column.cell(row)}</dd>
                  </div>
                ))}
              </dl>
            </li>
          )
        })}
      </ul>

      <div className="card-raised hidden overflow-x-auto rounded-2xl md:block">
        <table className="w-full text-sm">
          <caption className="sr-only">{caption}</caption>
          <thead>
            <tr className="border-b-2 border-hairline text-left">
              {columns.map((column) => (
                <th
                  key={column.header}
                  scope="col"
                  className={cn(
                    "px-4 py-3 text-xs font-bold tracking-wide whitespace-nowrap text-muted-foreground",
                    column.align === "right" && "text-right"
                  )}
                >
                  {column.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => {
              const href = rowHref?.(row)
              return (
                <tr
                  key={rowKey(row)}
                  className={cn(
                    "relative border-b border-hairline last:border-b-0",
                    href && "transition-colors focus-within:bg-cloud hover:bg-cloud"
                  )}
                >
                  {columns.map((column, index) => (
                    <td
                      key={column.header}
                      className={cn(
                        "px-4 py-3 align-middle font-semibold",
                        index === 0 && "font-bold",
                        column.align === "right" && "text-right tabular-nums"
                      )}
                    >
                      {index === 0 && href ? (
                        <Link href={href} title="Open details" className="after:absolute after:inset-0 focus-visible:outline-none">
                          {column.cell(row)}
                        </Link>
                      ) : (
                        column.cell(row)
                      )}
                    </td>
                  ))}
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </>
  )
}

export function TableSkeleton({ rows = 5 }: { rows?: number }) {
  return (
    <div className="flex flex-col gap-3">
      {Array.from({ length: rows }, (_, i) => (
        <Skeleton key={i} className="h-16 rounded-2xl md:h-12" />
      ))}
    </div>
  )
}
