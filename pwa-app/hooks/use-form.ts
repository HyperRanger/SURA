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

function pick<V>(errors: FieldErrors<V>, fields: ReadonlySet<keyof V>) {
  const picked: FieldErrors<V> = {}
  for (const field of fields) if (errors[field]) picked[field] = errors[field]
  return picked
}

// small form state helper. a field only shows errors once it has been validated,
// then they clear as the person fixes it. validate() takes an optional list of
// fields, so a multi-step form can check one step without flagging the next
export function useForm<V extends Record<string, unknown>>({
  initialValues,
  schema,
}: UseFormOptions<V>) {
  const [values, setValues] = useState(initialValues)
  const [errors, setErrors] = useState<FieldErrors<V>>({})
  const [validated, setValidated] = useState<ReadonlySet<keyof V>>(() => new Set())

  const setValue = useCallback(
    <K extends keyof V>(name: K, value: V[K]) => {
      const next = { ...values, [name]: value }
      setValues(next)
      if (validated.size > 0) setErrors(pick(runSchema(next, schema(next)), validated))
    },
    [schema, validated, values]
  )

  // returns the values when every field in scope passes, otherwise null
  const validate = useCallback(
    (fields?: readonly (keyof V)[]) => {
      const currentSchema = schema(values)
      const scope = fields ?? (Object.keys(currentSchema) as (keyof V)[])
      const nextValidated = new Set([...validated, ...scope])
      const allErrors = runSchema(values, currentSchema)

      setValidated(nextValidated)
      setErrors(pick(allErrors, nextValidated))
      return scope.some((field) => allErrors[field]) ? null : values
    },
    [schema, validated, values]
  )

  return { values, errors, setValue, validate }
}
