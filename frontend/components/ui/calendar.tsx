"use client"

import { useState } from "react"
import { HugeiconsIcon } from "@hugeicons/react"
import { ArrowLeft01Icon, ArrowRight01Icon } from "@hugeicons/core-free-icons"
import { cn } from "@/lib/utils"

const WEEKDAYS = ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"]

const monthFormatter = new Intl.DateTimeFormat("en-NG", { month: "long", year: "numeric" })
const dayFormatter = new Intl.DateTimeFormat("en-NG", { weekday: "long", day: "numeric", month: "long", year: "numeric" })

const sameDay = (a: Date, b: Date) =>
  a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate()

// six rows of seven, starting on the sunday on or before the 1st, so the grid never jumps in height
function monthGrid(month: Date) {
  const first = new Date(month.getFullYear(), month.getMonth(), 1)
  const start = new Date(first)
  start.setDate(first.getDate() - first.getDay())
  return Array.from({ length: 42 }, (_, index) => {
    const day = new Date(start)
    day.setDate(start.getDate() + index)
    return day
  })
}

type CalendarProps = {
  selected?: Date
  onSelect: (date: Date) => void
  // days that can't be picked, e.g. anything in the past for an expiry
  disabled?: (date: Date) => boolean
  className?: string
}

export function Calendar({ selected, onSelect, disabled, className }: CalendarProps) {
  const [month, setMonth] = useState(() => {
    const base = selected ?? new Date()
    return new Date(base.getFullYear(), base.getMonth(), 1)
  })
  const today = new Date()

  function shift(months: number) {
    setMonth((current) => new Date(current.getFullYear(), current.getMonth() + months, 1))
  }

  return (
    <div data-slot="calendar" className={cn("w-72 select-none", className)}>
      <div className="mb-2 flex items-center justify-between gap-2">
        <NavButton label="Previous month" icon={ArrowLeft01Icon} onClick={() => shift(-1)} />
        <p aria-live="polite" className="text-sm font-black">
          {monthFormatter.format(month)}
        </p>
        <NavButton label="Next month" icon={ArrowRight01Icon} onClick={() => shift(1)} />
      </div>

      <div className="grid grid-cols-7 gap-1">
        {WEEKDAYS.map((day) => (
          <span key={day} aria-hidden className="flex h-8 items-center justify-center text-xs font-extrabold text-muted-foreground">
            {day}
          </span>
        ))}
        {monthGrid(month).map((day) => {
          const outside = day.getMonth() !== month.getMonth()
          const isSelected = selected ? sameDay(day, selected) : false
          const isToday = sameDay(day, today)
          const isDisabled = disabled?.(day) ?? false
          return (
            <button
              key={day.toISOString()}
              type="button"
              aria-pressed={isSelected}
              aria-current={isToday ? "date" : undefined}
              aria-label={dayFormatter.format(day)}
              title={dayFormatter.format(day)}
              disabled={isDisabled}
              onClick={() => onSelect(day)}
              className={cn(
                "flex size-9 cursor-pointer items-center justify-center rounded-full text-sm font-bold tabular-nums transition-colors outline-none",
                "hover:bg-cloud hover:text-link focus-visible:ring-4 focus-visible:ring-ring/30",
                "disabled:cursor-not-allowed disabled:opacity-35 disabled:hover:bg-transparent",
                outside && "text-muted-foreground/60",
                isToday && !isSelected && "border-2 border-gold text-gold-deep",
                isSelected && "bg-primary text-primary-foreground hover:bg-primary-bright hover:text-primary-foreground"
              )}
            >
              {day.getDate()}
            </button>
          )
        })}
      </div>
    </div>
  )
}

type NavButtonProps = {
  label: string
  icon: typeof ArrowLeft01Icon
  onClick: () => void
}

function NavButton({ label, icon, onClick }: NavButtonProps) {
  return (
    <button
      type="button"
      aria-label={label}
      title={label}
      onClick={onClick}
      className="flex size-9 cursor-pointer items-center justify-center rounded-full text-muted-foreground transition-colors outline-none hover:bg-cloud hover:text-link focus-visible:ring-4 focus-visible:ring-ring/30"
    >
      <HugeiconsIcon icon={icon} size={18} strokeWidth={2.5} />
    </button>
  )
}
