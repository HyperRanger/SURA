import type { ComponentProps, ReactNode } from "react"
import { Field, describedBy } from "@/components/ui/field"
import { Input } from "@/components/ui/input"

type TextFieldProps = Omit<ComponentProps<typeof Input>, "id" | "invalid"> & {
  id: string
  label: ReactNode
  hint?: ReactNode
  error?: string
}

// label, input, hint and error wired together, for the common single-input case
export function TextField({ id, label, hint, error, className, ...inputProps }: TextFieldProps) {
  return (
    <Field id={id} label={label} hint={hint} error={error} className={className}>
      <Input
        id={id}
        invalid={Boolean(error)}
        aria-describedby={describedBy(id, { hint, error })}
        {...inputProps}
      />
    </Field>
  )
}
