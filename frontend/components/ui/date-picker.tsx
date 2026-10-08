"use client"

import { useState } from "react"
import { HugeiconsIcon } from "@hugeicons/react"
import { Calendar03Icon, Cancel01Icon } from "@hugeicons/core-free-icons"
import { Calendar } from "@/components/ui/calendar"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { cn } from "@/lib/utils"

const displayFormatter = new Intl.DateTimeFormat("en-NG", { day: "numeric", month: "short", year: "numeric" })

// the value is a calendar day as "yyyy-mm-dd", the same shape a native date input gives,
// read in local time so the day shown is the day picked
export function parseDay(value: string) {
  if (!value) return undefined
  const [year, month, day] = value.split("-").map(Number)
  return year && month && day ? new Date(year, month - 1, day) : undefined
}

export function formatDay(date: Date) {
  const pad = (part: number) => String(part).padStart(2, "0")
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
}

type DatePickerProps = {
  id?: string
  value: string
  onChange: (value: string) => void
  placeholder?: string
  disabled?: (date: Date) => boolean
  className?: string
  "aria-describedby"?: string
}

export function DatePicker({
  id,
  value,
  onChange,
  placeholder = "pick a date",
  disabled,
  className,
  "aria-describedby": describedBy,
}: DatePickerProps) {
  const [open, setOpen] = useState(false)
  const selected = parseDay(value)
  const label = selected ? displayFormatter.format(selected) : undefined

  return (
    <div className={cn("relative", className)}>
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger
          id={id}
          aria-describedby={describedBy}
          title={label ?? placeholder}
          className={cn(
            "flex h-12 w-full cursor-pointer items-center gap-2.5 rounded-2xl border-2 border-b-4 border-hairline bg-card pl-4 text-left text-sm font-bold transition-colors outline-none",
            "hover:border-hairline-strong focus-visible:border-ring focus-visible:ring-4 focus-visible:ring-ring/15 data-popup-open:border-ring",
            selected ? "pr-11" : "pr-4"
          )}
        >
          <HugeiconsIcon icon={Calendar03Icon} size={17} strokeWidth={2.2} className="shrink-0 text-muted-foreground" />
          <span className={cn("min-w-0 flex-1 truncate", !selected && "font-semibold text-muted-foreground")}>
            {label ?? placeholder}
          </span>
        </PopoverTrigger>
        <PopoverContent>
          <Calendar
            selected={selected}
            disabled={disabled}
            onSelect={(date) => {
              onChange(formatDay(date))
              setOpen(false)
            }}
          />
        </PopoverContent>
      </Popover>

      {/* a sibling of the trigger, since a button can't hold another button */}
      {selected && (
        <button
          type="button"
          aria-label="Clear date"
          title="Clear date"
          onClick={() => onChange("")}
          className="absolute top-1/2 right-2.5 flex size-7 -translate-y-[calc(50%+1px)] cursor-pointer items-center justify-center rounded-full text-muted-foreground transition-colors hover:bg-cloud hover:text-link"
        >
          <HugeiconsIcon icon={Cancel01Icon} size={14} strokeWidth={2.5} />
        </button>
      )}
    </div>
  )
}
