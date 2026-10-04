"use client"

import type { ReactNode } from "react"
import { HugeiconsIcon } from "@hugeicons/react"
import { ArrowDown01Icon, Search01Icon } from "@hugeicons/core-free-icons"
import { Input } from "@/components/ui/input"
import { cn } from "@/lib/utils"

export function FilterBar({ children }: { children: ReactNode }) {
  return <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-end">{children}</div>
}

type SearchFilterProps = {
  id: string
  label: string
  value: string
  onChange: (value: string) => void
  placeholder?: string
}

export function SearchFilter({ id, label, value, onChange, placeholder }: SearchFilterProps) {
  return (
    <div className="relative min-w-0 sm:flex-1">
      <label htmlFor={id} className="sr-only">
        {label}
      </label>
      <HugeiconsIcon
        icon={Search01Icon}
        size={18}
        strokeWidth={2.2}
        className="pointer-events-none absolute top-1/2 left-4 -translate-y-1/2 text-muted-foreground"
      />
      <Input
        id={id}
        type="search"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        autoComplete="off"
        className="h-12 pl-11 text-sm"
      />
    </div>
  )
}

type SelectFilterProps<T extends string> = {
  id: string
  label: string
  value: T | ""
  onChange: (value: T | "") => void
  options: readonly { value: T; label: string }[]
  // the label for "no filter"
  allLabel?: string
  className?: string
}

export function SelectFilter<T extends string>({
  id,
  label,
  value,
  onChange,
  options,
  allLabel = "all",
  className,
}: SelectFilterProps<T>) {
  return (
    <div className={cn("flex flex-col gap-1.5 sm:w-44", className)}>
      <label htmlFor={id} className="text-xs font-extrabold text-muted-foreground">
        {label}
      </label>
      <div className="relative">
        <select
          id={id}
          value={value}
          onChange={(event) => onChange(event.target.value as T | "")}
          className="h-12 w-full cursor-pointer appearance-none rounded-2xl border-2 border-b-4 border-hairline bg-card pr-10 pl-4 text-sm font-bold outline-none hover:border-hairline-strong focus-visible:border-ring focus-visible:ring-4 focus-visible:ring-ring/15"
        >
          <option value="">{allLabel}</option>
          {options.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
        <HugeiconsIcon
          icon={ArrowDown01Icon}
          size={16}
          strokeWidth={2.5}
          className="pointer-events-none absolute top-1/2 right-4 -translate-y-1/2 text-muted-foreground"
        />
      </div>
    </div>
  )
}

type TextFilterProps = {
  id: string
  label: string
  value: string
  onChange: (value: string) => void
  placeholder?: string
  className?: string
}

// a labelled exact-match field, e.g. one identifier, next to the selects
export function TextFilter({ id, label, value, onChange, placeholder, className }: TextFilterProps) {
  return (
    <div className={cn("flex flex-col gap-1.5 sm:w-56", className)}>
      <label htmlFor={id} className="text-xs font-extrabold text-muted-foreground">
        {label}
      </label>
      <Input
        id={id}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        autoComplete="off"
        spellCheck={false}
        className="h-12 font-mono text-sm normal-case"
      />
    </div>
  )
}

type DateFilterProps = {
  id: string
  label: string
  value: string
  onChange: (value: string) => void
}

export function DateFilter({ id, label, value, onChange }: DateFilterProps) {
  return (
    <div className="flex flex-col gap-1.5 sm:w-44">
      <label htmlFor={id} className="text-xs font-extrabold text-muted-foreground">
        {label}
      </label>
      <Input
        id={id}
        type="date"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="h-12 text-sm"
      />
    </div>
  )
}

// the date inputs give a calendar day; the api compares full timestamps
export const startOfDay = (date: string) => (date ? `${date}T00:00:00` : undefined)
export const endOfDay = (date: string) => (date ? `${date}T23:59:59` : undefined)

// turns a plain list of api values into select options with readable labels
export function toOptions<T extends string>(values: readonly T[]) {
  return values.map((value) => ({ value, label: value.replace(/_/g, " ") }))
}
