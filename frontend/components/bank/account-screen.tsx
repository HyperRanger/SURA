"use client"

import { useState, type FormEvent } from "react"
import { useRouter } from "next/navigation"
import { LockPasswordIcon } from "@hugeicons/core-free-icons"
import { changeBankPassword } from "@/actions/bank"
import { routes } from "@/config/routes"
import { useBankAccess } from "@/hooks/use-bank-access"
import { useMutation } from "@/hooks/use-mutation"
import { endSession } from "@/lib/session"
import { ActionError } from "@/components/bank/action-kit"
import { DetailList, PageHeader, Section } from "@/components/bank/page-header"
import { IconTile } from "@/components/shared/icon-tile"
import { Button } from "@/components/ui/button"
import { Dialog } from "@/components/ui/dialog"
import { Field } from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import { humanize } from "@/utils/format"

const PASSWORD_MIN = 12
const PASSWORD_MAX = 72

type Errors = { current?: string; next?: string; confirm?: string }

// B14. every staff role can change its own password. doing so ends every session
// this person holds, including this one, so they sign in again straight after
export function AccountScreen() {
  const { session } = useBankAccess()
  const [changingPassword, setChangingPassword] = useState(false)

  return (
    <>
      <PageHeader title="Your account" description="How you're signed in to the bank console." />

      <div className="flex flex-col gap-10">
        {session && (
          <DetailList
            items={[
              { label: "Role", value: humanize(session.role) },
              { label: "Bank", value: <span className="font-mono text-xs">{session.institutionId ?? "—"}</span> },
              { label: "User ID", value: <span className="font-mono text-xs">{session.userId}</span> },
              { label: "Permissions", value: session.permissions?.length ?? "Role defaults" },
            ]}
          />
        )}

        <Section title="Security">
          <div className="card-raised flex flex-col gap-4 rounded-2xl p-4 sm:flex-row sm:items-center sm:p-5">
            <IconTile icon={LockPasswordIcon} tone="indigo" />
            <div className="min-w-0 flex-1">
              <p className="text-base font-black">Password</p>
              <p className="mt-0.5 text-sm leading-snug font-semibold text-muted-foreground">
                Changing it signs you out everywhere, including here. You then sign in with the new one.
              </p>
            </div>
            <Button
              type="button"
              variant="outline"
              title="Choose a new password for your account"
              onClick={() => setChangingPassword(true)}
              className="sm:self-center"
            >
              Change password
            </Button>
          </div>
        </Section>
      </div>

      <Dialog
        open={changingPassword}
        onOpenChange={setChangingPassword}
        title="Change password"
        description="You'll be signed out everywhere, then sign in with the new one."
      >
        <ChangePasswordForm onCancel={() => setChangingPassword(false)} />
      </Dialog>
    </>
  )
}

function ChangePasswordForm({ onCancel }: { onCancel: () => void }) {
  const router = useRouter()
  const [current, setCurrent] = useState("")
  const [next, setNext] = useState("")
  const [confirm, setConfirm] = useState("")
  const [errors, setErrors] = useState<Errors>({})
  const change = useMutation(changeBankPassword)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const nextErrors: Errors = {
      current: current ? undefined : "Enter your current password",
      next:
        next.length < PASSWORD_MIN
          ? `Use at least ${PASSWORD_MIN} characters`
          : next.length > PASSWORD_MAX
          ? `Use at most ${PASSWORD_MAX} characters`
          : next === current
          ? "Choose a password you haven't been using"
          : undefined,
      confirm: confirm === next ? undefined : "The passwords don't match",
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
    { id: "password-current", key: "current", label: "Current password", value: current, set: setCurrent, autoComplete: "current-password" },
    { id: "password-new", key: "next", label: "New password", value: next, set: setNext, autoComplete: "new-password" },
    { id: "password-confirm", key: "confirm", label: "Confirm new password", value: confirm, set: setConfirm, autoComplete: "new-password" },
  ]

  return (
    <form noValidate onSubmit={handleSubmit} className="flex flex-col gap-4">
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

      <div className="mt-1 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
        <Button type="button" variant="ghost" onClick={onCancel} disabled={change.isPending}>
          Cancel
        </Button>
        <Button type="submit" loading={change.isPending}>
          Change password
        </Button>
      </div>
    </form>
  )
}
