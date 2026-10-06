"use client"

import { useState, type FormEvent } from "react"
import { useRouter } from "next/navigation"
import { bankLogin, bankVerifyMfa, isMfaChallenge } from "@/actions/bank"
import { bankDemoLogin } from "@/actions/demo"
import { OTP_LENGTH } from "@/config/auth"
import { isDemoEnabled } from "@/config/env"
import { routes } from "@/config/routes"
import { useForm } from "@/hooks/use-form"
import { useMutation } from "@/hooks/use-mutation"
import { startSession } from "@/lib/session"
import { DemoCodeHint } from "@/components/auth/demo-code-hint"
import { Alert } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { OtpInput } from "@/components/ui/otp-input"
import { TextField } from "@/components/ui/text-field"
import type { BankMfaChallenge, BankSessionResponse } from "@/types"
import { compose, maxLength, required } from "@/utils/validators"

const looksLikeEmail = (value: string) => (/^[^\s@]+@[^\s@]+$/.test(value.trim()) ? undefined : "Enter your work email")

function loginSchema() {
  return {
    email: compose(required("Enter your work email"), looksLikeEmail, maxLength(320)),
    password: required("Enter your password"),
  }
}

// B1. email and password, then a second factor when the account has one.
// outside production a one-tap demo sign-in skips both
export function BankLoginForm({ next }: { next?: string }) {
  const router = useRouter()
  const [challenge, setChallenge] = useState<BankMfaChallenge | null>(null)
  const login = useMutation(bankLogin)
  const demo = useMutation(bankDemoLogin)
  const { values, errors, setValue, validate } = useForm({
    initialValues: { email: "", password: "" },
    schema: loginSchema,
  })

  function enter(session: BankSessionResponse) {
    startSession(session)
    router.replace(next ?? routes.bank.home)
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const valid = validate()
    if (!valid) return

    const result = await login.mutate({ email: valid.email.trim(), password: valid.password })
    if (!result.ok) return
    if (isMfaChallenge(result.data)) setChallenge(result.data)
    else enter(result.data)
  }

  async function handleDemo() {
    const result = await demo.mutate()
    if (result.ok) enter(result.data)
  }

  if (challenge) {
    return <MfaStep challenge={challenge} onVerified={enter} onRestart={() => setChallenge(null)} />
  }

  const busy = login.isPending || demo.isPending

  return (
    <div className="flex flex-col gap-6">
      <form noValidate onSubmit={handleSubmit} className="flex flex-col gap-5">
        <TextField
          id="email"
          type="email"
          inputMode="email"
          autoComplete="username"
          autoFocus
          label="Work email"
          placeholder="analyst@yourbank.com"
          value={values.email}
          onChange={(event) => setValue("email", event.target.value)}
          error={errors.email}
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

        {login.error && (
          <Alert variant="error" title={login.error.is(423) ? "Account locked" : undefined}>
            {login.error.message}
          </Alert>
        )}

        <Button type="submit" size="lg" loading={login.isPending} disabled={demo.isPending} className="w-full">
          {login.isPending ? "Signing in" : "Sign in"}
        </Button>
      </form>

      {isDemoEnabled && (
        <div className="flex flex-col gap-3 border-t-2 border-dashed border-hairline pt-6">
          <p className="text-center text-xs font-extrabold text-muted-foreground">For the live demo</p>
          <Button type="button" variant="outline" size="lg" loading={demo.isPending} disabled={busy} onClick={handleDemo}>
            {demo.isPending ? "Opening the demo bank" : "Continue as demo bank"}
          </Button>
          {demo.error && (
            <Alert variant="error">{demo.error.is(404) ? "The demo is switched off on this API." : demo.error.message}</Alert>
          )}
        </div>
      )}
    </div>
  )
}

type MfaStepProps = {
  challenge: BankMfaChallenge
  onVerified: (session: BankSessionResponse) => void
  onRestart: () => void
}

function MfaStep({ challenge, onVerified, onRestart }: MfaStepProps) {
  const [code, setCode] = useState("")
  const verify = useMutation(bankVerifyMfa)
  // an expired or overused challenge can't be retried; the person signs in again
  const mustRestart = verify.error?.is(400) || verify.error?.is(429)

  async function submit(value: string) {
    if (value.length !== OTP_LENGTH) return
    const result = await verify.mutate({ challenge_id: challenge.challenge_id, code: value })
    if (result.ok) onVerified(result.data)
    else if (result.error.is(401)) setCode("")
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    void submit(code)
  }

  return (
    <form noValidate onSubmit={handleSubmit} className="flex flex-col gap-6">
      <p className="text-sm leading-relaxed font-semibold text-muted-foreground">
        We sent a {OTP_LENGTH}-digit code to the phone on your staff account.
      </p>

      <DemoCodeHint
        code={challenge.demo_code}
        disabled={verify.isPending}
        onUse={(demoCode) => {
          setCode(demoCode)
          void submit(demoCode)
        }}
      />

      <OtpInput
        value={code}
        onChange={(value) => {
          setCode(value)
          if (verify.error) verify.reset()
        }}
        onComplete={(value) => void submit(value)}
        length={OTP_LENGTH}
        disabled={verify.isPending || mustRestart}
        invalid={Boolean(verify.error)}
        label="Security code"
        autoFocus
      />

      {verify.error && <Alert variant="error">{verify.error.message}</Alert>}

      {mustRestart ? (
        <Button type="button" size="lg" onClick={onRestart} className="w-full">
          Sign in again
        </Button>
      ) : (
        <Button type="submit" size="lg" loading={verify.isPending} disabled={code.length !== OTP_LENGTH} className="w-full">
          {verify.isPending ? "Checking" : "Verify"}
        </Button>
      )}

      <Button type="button" variant="link" size="sm" onClick={onRestart} disabled={verify.isPending}>
        Use a different account
      </Button>
    </form>
  )
}
