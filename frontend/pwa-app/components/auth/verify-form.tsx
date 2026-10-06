"use client"

import { useEffect, useRef, useState, type FormEvent } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { requestLoginCode, verifyOtp } from "@/actions/auth"
import { OTP_LENGTH } from "@/config/auth"
import { routes } from "@/config/routes"
import { useCountdown } from "@/hooks/use-countdown"
import { useHydrated } from "@/hooks/use-hydrated"
import { useMutation } from "@/hooks/use-mutation"
import { useStoredValue } from "@/hooks/use-stored-value"
import { challengeStore, rememberChallenge, startSession } from "@/lib/session"
import { AuthCard } from "@/components/auth/auth-card"
import { DemoCodeHint } from "@/components/auth/demo-code-hint"
import { ResendCode } from "@/components/auth/resend-code"
import { Alert } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { OtpInput } from "@/components/ui/otp-input"
import { Spinner } from "@/components/ui/spinner"
import type { PendingChallenge } from "@/types"
import { formatCountdown } from "@/utils/format"
import { maskPhone } from "@/utils/phone"
import { homeForRole, withNext } from "@/utils/redirect"

// P4. reads the challenge saved by /login or /signup. with none saved (a direct
// visit, or a new tab) there is nothing to verify, so it sends people to /login
export function VerifyForm() {
  const router = useRouter()
  const hydrated = useHydrated()
  const challenge = useStoredValue(challengeStore)
  const completed = useRef(false)

  useEffect(() => {
    if (hydrated && !challenge && !completed.current) router.replace(routes.login)
  }, [hydrated, challenge, router])

  if (!challenge) {
    return (
      <div className="flex justify-center py-20 text-muted-foreground">
        <Spinner className="size-6" />
        <span className="sr-only">Loading</span>
      </div>
    )
  }

  return (
    <VerifyChallenge
      challenge={challenge}
      onVerified={(destination) => {
        completed.current = true
        challengeStore.clear()
        router.replace(destination)
      }}
    />
  )
}

type VerifyChallengeProps = {
  challenge: PendingChallenge
  onVerified: (destination: string) => void
}

function VerifyChallenge({ challenge, onVerified }: VerifyChallengeProps) {
  const [code, setCode] = useState("")
  const verify = useMutation(verifyOtp)
  const resend = useMutation(requestLoginCode)
  const busy = verify.isPending || resend.isPending
  const error = verify.error ?? resend.error
  const changeNumberHref = withNext(challenge.isNewAccount ? routes.signup : routes.login, challenge.next)

  async function submit(value: string) {
    if (value.length !== OTP_LENGTH) return
    const result = await verify.mutate({ challenge_id: challenge.challengeId, code: value })

    if (!result.ok) {
      // a wrong code is cleared so the next attempt starts from the first box
      if (result.error.is(401)) setCode("")
      return
    }

    // individuals land on the member home, vendors on the terminal. the role is the
    // one the api put in the token, never one the page assumed
    startSession(result.data)
    onVerified(challenge.next ?? homeForRole(result.data.role, { isNewAccount: challenge.isNewAccount }))
  }

  async function handleResend() {
    verify.reset()
    const result = await resend.mutate({ phone: challenge.phone })
    if (!result.ok) return

    setCode("")
    rememberChallenge(result.data, {
      phone: challenge.phone,
      next: challenge.next,
      isNewAccount: challenge.isNewAccount,
    })
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    void submit(code)
  }

  return (
    <AuthCard
      title="Enter your code"
      description={
        <>
          We sent a {OTP_LENGTH}-digit code to{" "}
          <span className="font-bold whitespace-nowrap text-foreground">{maskPhone(challenge.phone)}</span>.{" "}
          <Link href={changeNumberHref} className="font-bold text-link underline-offset-4 hover:underline">
            Change number
          </Link>
        </>
      }
    >
      <form noValidate onSubmit={handleSubmit} className="flex flex-col gap-6">
        <DemoCodeHint
          code={challenge.demoCode}
          disabled={busy}
          onUse={(demoCode) => {
            setCode(demoCode)
            void submit(demoCode)
          }}
        />

        <div className="flex flex-col gap-3">
          <OtpInput
            value={code}
            onChange={(value) => {
              setCode(value)
              if (verify.error) verify.reset()
            }}
            onComplete={(value) => void submit(value)}
            length={OTP_LENGTH}
            disabled={busy}
            invalid={Boolean(verify.error)}
            describedBy="code-expiry"
            autoFocus
          />
          <CodeExpiry key={challenge.expiresAt} expiresAt={challenge.expiresAt} />
        </div>

        {error && <Alert variant="error">{error.message}</Alert>}

        <Button
          type="submit"
          size="lg"
          loading={verify.isPending}
          disabled={code.length !== OTP_LENGTH || resend.isPending}
          className="w-full"
        >
          {verify.isPending ? "Checking" : "Verify"}
        </Button>

        <div className="text-center">
          <ResendCode
            key={challenge.resendAvailableAt}
            availableAt={challenge.resendAvailableAt}
            onResend={handleResend}
            loading={resend.isPending}
          />
        </div>
      </form>
    </AuthCard>
  )
}

function CodeExpiry({ expiresAt }: { expiresAt: number }) {
  const secondsLeft = useCountdown(expiresAt)

  return (
    <p id="code-expiry" className="text-xs font-semibold text-muted-foreground">
      {secondsLeft > 0 ? (
        <>
          Code expires in <span className="font-bold tabular-nums">{formatCountdown(secondsLeft)}</span>
        </>
      ) : (
        <span className="font-bold text-destructive">This code has expired. Request a new one below.</span>
      )}
    </p>
  )
}
