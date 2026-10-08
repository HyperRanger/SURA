"use client"

import type { FormEvent } from "react"
import { useRouter } from "next/navigation"
import { requestLoginCode } from "@/actions/auth"
import { routes } from "@/config/routes"
import { useForm } from "@/hooks/use-form"
import { useMutation } from "@/hooks/use-mutation"
import { rememberChallenge, sessionStore, startSession } from "@/lib/session"
import { Alert } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { TextField } from "@/components/ui/text-field"
import { initialLoginValues, loginSchema } from "@/utils/auth-forms"
import { homeForRole } from "@/utils/redirect"

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

    const result = await mutate({
      identifier: valid.identifier.trim(),
      password: valid.password,
      device_token: sessionStore.read()?.trustedDeviceToken,
    })
    if (!result.ok) return

    if ("access_token" in result.data) {
      startSession(result.data)
      router.replace(next ?? homeForRole(result.data.role, { isNewAccount: false }))
      return
    }

    rememberChallenge(result.data, { phone: valid.identifier, next, isNewAccount: false })
    router.push(routes.verify)
  }

  return (
    <form noValidate onSubmit={handleSubmit} className="flex flex-col gap-6">
      <TextField
        id="identifier"
        autoComplete="username"
        autoFocus
        label="Email address or phone number"
        placeholder="you@example.com or 0803 000 0000"
        value={values.identifier}
        onChange={(event) => setValue("identifier", event.target.value)}
        error={errors.identifier}
      />
      <TextField
        id="password"
        type="password"
        autoComplete="current-password"
        label="Password"
        value={values.password}
        onChange={(event) => setValue("password", event.target.value)}
        error={errors.password}
      />

      {error && <Alert variant="error">{error.message}</Alert>}

      <Button type="submit" size="lg" loading={isPending} className="w-full">
        {isPending ? "Signing in" : "Log in"}
      </Button>
    </form>
  )
}
