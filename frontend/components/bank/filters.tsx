"use client"

import type { ReactNode } from "react"
import { HugeiconsIcon } from "@hugeicons/react"
import { Search01Icon } from "@hugeicons/core-free-icons"
import { DatePicker } from "@/components/ui/date-picker"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { cn } from "@/lib/utils"

export function FilterBar({ children, className }: { children: ReactNode; className?: string }) {
  return <div className={cn("mb-5 flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-end", className)}>{children}</div>
}

// a row of selects that share the width evenly, two to a row on phones. pass
// className="sm:w-auto" to each filter so it fills its cell
export function FilterGrid({ id, children, className }: { id?: string; children: ReactNode; className?: string }) {
  return (
    <div id={id} className={cn("mb-5 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5", className)}>
      {children}
    </div>
  )
}

type SearchFilterProps = {
  id: string
  label: string
  value: string
  onChange: (value: string) => void
  placeholder?: string
  className?: string
}

export function SearchFilter({ id, label, value, onChange, placeholder, className }: SearchFilterProps) {
  return (
    <div className={cn("relative min-w-0 sm:flex-1", className)}>
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
  allLabel = "All",
  className,
}: SelectFilterProps<T>) {
  return (
    <div className={cn("flex flex-col gap-1.5 sm:w-44", className)}>
      <label htmlFor={id} className="text-xs font-bold text-muted-foreground">
        {label}
      </label>
      <Select
        items={[{ value: null, label: allLabel }, ...options]}
        value={value || null}
        onValueChange={(next) => onChange((next ?? "") as T | "")}
      >
        <SelectTrigger id={id} title={`${label}: ${options.find((option) => option.value === value)?.label ?? allLabel}`}>
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value={null}>{allLabel}</SelectItem>
          {options.map((option) => (
            <SelectItem key={option.value} value={option.value}>
              {option.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
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
      <label htmlFor={id} className="text-xs font-bold text-muted-foreground">
        {label}
      </label>
      <Input
        id={id}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        autoComplete="off"
        spellCheck={false}
        className="h-12 font-mono text-sm"
      />
    </div>
  )
}

type DateFilterProps = {
  id: string
  label: string
  value: string
  onChange: (value: string) => void
  className?: string
}

export function DateFilter({ id, label, value, onChange, className }: DateFilterProps) {
  return (
    <div className={cn("flex flex-col gap-1.5 sm:w-48", className)}>
      <label htmlFor={id} className="text-xs font-bold text-muted-foreground">
        {label}
      </label>
      <DatePicker id={id} value={value} onChange={onChange} placeholder="Any day" />
    </div>
  )
}

// the date pickers give a calendar day; the api compares full timestamps
export const startOfDay = (date: string) => (date ? `${date}T00:00:00` : undefined)
export const endOfDay = (date: string) => (date ? `${date}T23:59:59` : undefined)

// turns a plain list of api values into select options with readable labels
export function toOptions<T extends string>(values: readonly T[]) {
  return values.map((value) => ({ value, label: value.replace(/_/g, " ") }))
}
