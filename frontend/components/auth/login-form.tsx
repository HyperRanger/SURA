"use client"

import type { FormEvent } from "react"
import { useRouter } from "next/navigation"
import { requestLoginCode } from "@/actions/auth"
import { routes } from "@/config/routes"
import { useForm } from "@/hooks/use-form"
import { useMutation } from "@/hooks/use-mutation"
import { rememberChallenge } from "@/lib/session"
import { Alert } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { TextField } from "@/components/ui/text-field"
import { initialLoginValues, loginSchema } from "@/utils/auth-forms"
import { normalizePhone } from "@/utils/phone"

// P3. asks for a code; the api answers the same way for unknown numbers
export function LoginForm({ next }: { next?: string }) {
  const router = useRouter()
  const { values, errors, setValue, validate } = useForm({
    initialValues: initialLoginValues,
    schema: loginSchema,
  })
  const { mutate, isPending, error } = useMutation(requestLoginCode)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const valid = validate()
    if (!valid) return

    const phone = normalizePhone(valid.phone)
    const result = await mutate({ phone })
    if (!result.ok) return

    rememberChallenge(result.data, { phone, next, isNewAccount: false })
    router.push(routes.verify)
  }

  return (
    <form noValidate onSubmit={handleSubmit} className="flex flex-col gap-6">
      <TextField
        id="phone"
        type="number"
        inputMode="numeric"
        autoComplete="tel"
        autoFocus
        label="phone number"
        placeholder="0803 000 0000"
        value={values.phone}
        onChange={(event) => setValue("phone", event.target.value)}
        error={errors.phone}
        hint="use the number you signed up with."
      />

      {error && <Alert variant="error">{error.message}</Alert>}

      <Button type="submit" size="lg" loading={isPending} className="w-full">
        {isPending ? "sending your code" : "continue"}
      </Button>
    </form>
  )
}
