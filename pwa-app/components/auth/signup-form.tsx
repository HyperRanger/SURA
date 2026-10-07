"use client"

import { useEffect, useRef, useState, type FormEvent, type ReactNode } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { StoreVerified01Icon } from "@hugeicons/core-free-icons"
import { signup } from "@/actions/auth"
import { accountTypeOptions, businessCategorySuggestions, incomeContextOptions, signupSteps } from "@/config/auth"
import { routes } from "@/config/routes"
import { useForm } from "@/hooks/use-form"
import { useMutation } from "@/hooks/use-mutation"
import { rememberChallenge } from "@/lib/session"
import { cn } from "@/lib/utils"
import { AuthCard } from "@/components/auth/auth-card"
import { Alert } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { ChoiceCards } from "@/components/ui/choice-cards"
import { FieldError, describedBy, fieldIds } from "@/components/ui/field"
import { StepProgress } from "@/components/ui/step-progress"
import { TextField } from "@/components/ui/text-field"
import type { SelfServiceRole } from "@/types"
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
  // from ?role=, e.g. the landing's vendor link. skips straight past the account question
  initialRole?: SelfServiceRole
  footer?: ReactNode
}

// P2, in three short steps: individual or vendor, then name and phone, then how they
// earn (individuals) or their business (vendors). each step is validated before
// moving on, and the last one creates the account and hands over to /verify
export function SignupForm({ next, initialRole, footer }: SignupFormProps) {
  const router = useRouter()
  const [stepIndex, setStepIndex] = useState(initialRole ? 1 : 0)
  const { values, errors, setValue, validate } = useForm({
    initialValues: initialSignupValues(initialRole),
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
      header={<StepProgress current={stepIndex} total={steps.length} onBack={goBack} label="Signup progress" />}
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

        {step.id === "business" && <BusinessStep values={values} errors={errors} setValue={setValue} />}

        {error && isLastStep && (
          <Alert variant="error" title={error.is(409) ? "You already have an account" : undefined}>
            {error.is(409) ? (
              <>
                That phone number is registered.{" "}
                <Link href={withNext(routes.login, next)} className="font-bold underline underline-offset-4">
                  Log in instead
                </Link>
              </>
            ) : (
              error.message
            )}
          </Alert>
        )}

        <Button type="submit" size="lg" loading={isPending} className="w-full">
          {isLastStep ? (isPending ? "Creating your account" : "Create account") : "Continue"}
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
        label={isVendor ? "Your full name" : "Full name"}
        placeholder="e.g. Amaka Obi"
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
        label={isVendor ? "Business phone number" : "Phone number"}
        placeholder="0803 000 0000"
        value={values.phone}
        onChange={(event) => setValue("phone", event.target.value)}
        error={errors.phone}
      />
    </>
  )
}

function BusinessStep({ values, errors, setValue }: StepProps) {
  return (
    <>
      <TextField
        id="business-name"
        label="Business name"
        placeholder="e.g. Ade Electronics"
        autoComplete="organization"
        value={values.businessName}
        onChange={(event) => setValue("businessName", event.target.value)}
        error={errors.businessName}
      />
      <div className="flex flex-col gap-3">
        <TextField
          id="business-category"
          label="What do you sell?"
          placeholder="e.g. Phones and laptops"
          value={values.businessCategory}
          onChange={(event) => setValue("businessCategory", event.target.value)}
          error={errors.businessCategory}
        />
        <div role="group" aria-label="Common categories" className="flex flex-wrap gap-2">
          {businessCategorySuggestions.map((category) => {
            const selected = values.businessCategory === category
            return (
              <button
                key={category}
                type="button"
                aria-pressed={selected}
                onClick={() => setValue("businessCategory", category)}
                className={cn(
                  "rounded-full border-2 px-3 py-1.5 text-xs font-bold transition-colors outline-none focus-visible:ring-4 focus-visible:ring-ring/20",
                  selected
                    ? "border-ring bg-primary-soft text-link"
                    : "border-hairline bg-card text-muted-foreground hover:border-hairline-strong hover:text-link"
                )}
              >
                {category}
              </button>
            )
          })}
        </div>
      </div>

      <Alert variant="info" icon={StoreVerified01Icon} title="Verification comes next">
        After you confirm your number, Sura checks your business. You can sign in straight away, and members can
        pick you for their Lock once you&apos;re verified.
      </Alert>

      <TermsCheckbox values={values} errors={errors} setValue={setValue} />
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
            I agree to the{" "}
            <Link href={routes.terms} className="font-bold text-link underline-offset-4 hover:underline">
              terms of use
            </Link>{" "}
            and{" "}
            <Link href={routes.privacy} className="font-bold text-link underline-offset-4 hover:underline">
              privacy notice
            </Link>
            , including how Sura uses my contributions to build a score.
          </>
        }
      />
      <FieldError id={errorId} message={errors.termsAccepted} />
    </div>
  )
}
