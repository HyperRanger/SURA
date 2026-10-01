"use client"

import { useEffect, useRef, useState, type FormEvent, type ReactNode } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { signup } from "@/actions/auth"
import { accountTypeOptions, incomeContextOptions, signupSteps } from "@/config/auth"
import { routes } from "@/config/routes"
import { useForm } from "@/hooks/use-form"
import { useMutation } from "@/hooks/use-mutation"
import { rememberChallenge } from "@/lib/session"
import { AuthCard } from "@/components/auth/auth-card"
import { Alert } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { ChoiceCards } from "@/components/ui/choice-cards"
import { FieldError, describedBy, fieldIds } from "@/components/ui/field"
import { StepProgress } from "@/components/ui/step-progress"
import { TextField } from "@/components/ui/text-field"
import {
  initialSignupValues,
  signupSchema,
  signupStepFields,
  toSignupPayload,
  type SignupValues,
} from "@/utils/auth-forms"
import { withNext } from "@/utils/redirect"

const TITLE_ID = "signup-step-title"

type SignupFormProps = {
  next?: string
  footer?: ReactNode
}

// P2, in three short steps: account type, then name and phone, then how they earn
// (savers) or their business (vendors). each step is validated before moving on,
// and the last one creates the account and hands over to /verify
export function SignupForm({ next, footer }: SignupFormProps) {
  const router = useRouter()
  const [stepIndex, setStepIndex] = useState(0)
  const { values, errors, setValue, validate } = useForm({
    initialValues: initialSignupValues,
    schema: signupSchema,
  })
  const { mutate, isPending, error, reset } = useMutation(signup)

  const steps = signupSteps[values.role]
  const step = steps[stepIndex]
  const isLastStep = stepIndex === steps.length - 1

  // on each new step, focus its first control (the chosen option for a radio group),
  // so keyboard and screen reader users land on the new question
  const formRef = useRef<HTMLFormElement>(null)
  const firstRender = useRef(true)
  useEffect(() => {
    if (firstRender.current) {
      firstRender.current = false
      return
    }
    const form = formRef.current
    const target =
      form?.querySelector<HTMLInputElement>("input[type=radio]:checked") ??
      form?.querySelector<HTMLInputElement>("input")
    target?.focus()
  }, [stepIndex])

  function goBack() {
    reset()
    setStepIndex((index) => Math.max(0, index - 1))
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const valid = validate(signupStepFields[step.id])
    if (!valid) return

    if (!isLastStep) {
      setStepIndex((index) => index + 1)
      return
    }

    const payload = toSignupPayload(valid)
    const result = await mutate(payload)
    if (!result.ok) return

    rememberChallenge(result.data, { phone: payload.phone, next, isNewAccount: true })
    router.push(routes.verify)
  }

  return (
    <AuthCard
      titleId={TITLE_ID}
      title={step.title}
      description={step.description}
      footer={footer}
      header={
        <StepProgress
          current={stepIndex}
          total={steps.length}
          onBack={goBack}
          label="signup progress"
        />
      }
    >
      <form ref={formRef} noValidate onSubmit={handleSubmit} className="flex flex-col gap-6">
        {step.id === "account" && (
          <ChoiceCards
            name="role"
            labelledBy={TITLE_ID}
            options={accountTypeOptions}
            value={values.role}
            onChange={(role) => setValue("role", role)}
          />
        )}

        {step.id === "details" && <DetailsStep values={values} errors={errors} setValue={setValue} />}

        {step.id === "earning" && (
          <>
            <ChoiceCards
              name="context"
              labelledBy={TITLE_ID}
              describedBy={describedBy("context", { error: errors.context })}
              options={incomeContextOptions}
              value={values.context}
              onChange={(context) => setValue("context", context)}
              invalid={Boolean(errors.context)}
            />
            <FieldError id={fieldIds("context").error} message={errors.context} />
            <TermsCheckbox values={values} errors={errors} setValue={setValue} />
          </>
        )}

        {step.id === "business" && (
          <>
            <TextField
              id="business-name"
              label="business name"
              placeholder="e.g. adeola provisions"
              autoComplete="organization"
              value={values.businessName}
              onChange={(event) => setValue("businessName", event.target.value)}
              error={errors.businessName}
            />
            <TextField
              id="business-category"
              label="what do you sell?"
              placeholder="e.g. electronics, groceries, school supplies"
              value={values.businessCategory}
              onChange={(event) => setValue("businessCategory", event.target.value)}
              error={errors.businessCategory}
            />
            <TermsCheckbox values={values} errors={errors} setValue={setValue} />
          </>
        )}

        {error && isLastStep && (
          <Alert variant="error" title={error.is(409) ? "you already have an account" : undefined}>
            {error.is(409) ? (
              <>
                that phone number is registered.{" "}
                <Link href={withNext(routes.login, next)} className="font-extrabold underline underline-offset-4">
                  log in instead
                </Link>
              </>
            ) : (
              error.message
            )}
          </Alert>
        )}

        <Button type="submit" size="lg" loading={isPending} className="w-full">
          {isLastStep ? (isPending ? "creating your account" : "create account") : "continue"}
        </Button>
      </form>
    </AuthCard>
  )
}

type StepProps = {
  values: SignupValues
  errors: Partial<Record<keyof SignupValues, string>>
  setValue: <K extends keyof SignupValues>(name: K, value: SignupValues[K]) => void
}

function DetailsStep({ values, errors, setValue }: StepProps) {
  const isVendor = values.role === "vendor"

  return (
    <>
      <TextField
        id="name"
        label={isVendor ? "your full name" : "full name"}
        placeholder="e.g. amaka obi"
        autoComplete="name"
        value={values.name}
        onChange={(event) => setValue("name", event.target.value)}
        error={errors.name}
      />
      <TextField
        id="phone"
        type="tel"
        inputMode="tel"
        autoComplete="tel"
        label={isVendor ? "business phone number" : "phone number"}
        placeholder="0803 000 0000"
        value={values.phone}
        onChange={(event) => setValue("phone", event.target.value)}
        error={errors.phone}
      />
    </>
  )
}

function TermsCheckbox({ values, errors, setValue }: StepProps) {
  const errorId = fieldIds("terms").error

  return (
    <div className="flex flex-col gap-2">
      <Checkbox
        id="terms"
        checked={values.termsAccepted}
        onChange={(event) => setValue("termsAccepted", event.target.checked)}
        invalid={Boolean(errors.termsAccepted)}
        aria-describedby={errors.termsAccepted ? errorId : undefined}
        label={
          <>
            i agree to the{" "}
            <Link href={routes.terms} className="font-extrabold text-link underline-offset-4 hover:underline">
              terms of use
            </Link>{" "}
            and{" "}
            <Link href={routes.privacy} className="font-extrabold text-link underline-offset-4 hover:underline">
              privacy notice
            </Link>
            , including how sura uses my contributions to build a score.
          </>
        }
      />
      <FieldError id={errorId} message={errors.termsAccepted} />
    </div>
  )
}
