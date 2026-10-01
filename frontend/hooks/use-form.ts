"use client"

import { useCallback, useState } from "react"
import type { Validator } from "@/utils/validators"

type FieldErrors<V> = Partial<Record<keyof V, string>>

// the schema can depend on the current values, e.g. vendor-only fields
type Schema<V> = { [K in keyof V]?: Validator<V[K]> }

type UseFormOptions<V> = {
  initialValues: V
  schema: (values: V) => Schema<V>
}

function runSchema<V>(values: V, schema: Schema<V>) {
  const errors: FieldErrors<V> = {}
  for (const name of Object.keys(schema) as (keyof V)[]) {
    const error = schema[name]?.(values[name])
    if (error) errors[name] = error
  }
  return errors
}

// small form state helper: errors appear after the first submit attempt, then
// clear field by field as the person fixes them
export function useForm<V extends Record<string, unknown>>({
  initialValues,
  schema,
}: UseFormOptions<V>) {
  const [values, setValues] = useState(initialValues)
  const [errors, setErrors] = useState<FieldErrors<V>>({})
  const [submitted, setSubmitted] = useState(false)

  const setValue = useCallback(
    <K extends keyof V>(name: K, value: V[K]) => {
      const next = { ...values, [name]: value }
      setValues(next)
      if (submitted) setErrors(runSchema(next, schema(next)))
    },
    [schema, submitted, values]
  )

  // returns the validated values, or null when something needs fixing
  const validate = useCallback(() => {
    setSubmitted(true)
    const nextErrors = runSchema(values, schema(values))
    setErrors(nextErrors)
    return Object.keys(nextErrors).length === 0 ? values : null
  }, [schema, values])

  return { values, errors, setValue, validate }
}
