"use client"

import { useState, type FormEvent } from "react"
import { useRouter } from "next/navigation"
import { changeBankPassword } from "@/actions/bank"
import { routes } from "@/config/routes"
import { useBankAccess } from "@/hooks/use-bank-access"
import { useMutation } from "@/hooks/use-mutation"
import { endSession } from "@/lib/session"
import { ActionError } from "@/components/bank/action-kit"
import { DetailList, PageHeader, Section } from "@/components/bank/page-header"
import { Button } from "@/components/ui/button"
import { Field } from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import { humanize } from "@/utils/format"

const PASSWORD_MIN = 12
const PASSWORD_MAX = 72

type Errors = { current?: string; next?: string; confirm?: string }

// B14. every staff role can change its own password. doing so ends every session
// this person holds, including this one, so they sign in again straight after
export function AccountScreen() {
  const router = useRouter()
  const { session } = useBankAccess()
  const [current, setCurrent] = useState("")
  const [next, setNext] = useState("")
  const [confirm, setConfirm] = useState("")
  const [errors, setErrors] = useState<Errors>({})
  const change = useMutation(changeBankPassword)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const nextErrors: Errors = {
      current: current ? undefined : "enter your current password",
      next:
        next.length < PASSWORD_MIN
          ? `use at least ${PASSWORD_MIN} characters`
          : next.length > PASSWORD_MAX
          ? `use at most ${PASSWORD_MAX} characters`
          : next === current
          ? "choose a password you haven't been using"
          : undefined,
      confirm: confirm === next ? undefined : "the passwords don't match",
    }
    setErrors(nextErrors)
    if (nextErrors.current || nextErrors.next || nextErrors.confirm) return

    const result = await change.mutate({ current_password: current, new_password: next })
    if (result.ok) {
      endSession()
      router.replace(routes.bank.login)
    }
  }

  const fields: { id: string; key: keyof Errors; label: string; value: string; set: (value: string) => void; autoComplete: string }[] = [
    { id: "password-current", key: "current", label: "current password", value: current, set: setCurrent, autoComplete: "current-password" },
    { id: "password-new", key: "next", label: "new password", value: next, set: setNext, autoComplete: "new-password" },
    { id: "password-confirm", key: "confirm", label: "confirm new password", value: confirm, set: setConfirm, autoComplete: "new-password" },
  ]

  return (
    <>
      <PageHeader title="your account" description="how you're signed in to the bank console." />

      <div className="flex flex-col gap-10">
        {session && (
          <DetailList
            items={[
              { label: "role", value: humanize(session.role) },
              { label: "bank", value: <span className="font-mono text-xs normal-case">{session.institutionId ?? "—"}</span> },
              { label: "user id", value: <span className="font-mono text-xs normal-case">{session.userId}</span> },
              { label: "permissions", value: session.permissions?.length ?? "role defaults" },
            ]}
          />
        )}

        <Section title="change password" description="you'll be signed out everywhere, then sign in with the new one.">
          <form noValidate onSubmit={handleSubmit} className="card-raised flex flex-col gap-4 rounded-2xl p-4 sm:max-w-md sm:p-5">
            {fields.map((field) => (
              <Field key={field.id} id={field.id} label={field.label} error={errors[field.key]}>
                <Input
                  id={field.id}
                  type="password"
                  autoComplete={field.autoComplete}
                  value={field.value}
                  onChange={(event) => {
                    field.set(event.target.value)
                    if (errors[field.key]) setErrors((existing) => ({ ...existing, [field.key]: undefined }))
                  }}
                  invalid={Boolean(errors[field.key])}
                  aria-describedby={errors[field.key] ? `${field.id}-error` : undefined}
                  className="h-12 text-sm"
                />
              </Field>
            ))}

            <ActionError error={change.error} />

            <Button type="submit" loading={change.isPending} className="sm:self-start">
              change password
            </Button>
          </form>
        </Section>
      </div>
    </>
  )
}
