"use client"

import type { FormEvent } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { signup } from "@/actions/auth"
import { accountTypeOptions, incomeContextOptions } from "@/config/auth"
import { routes } from "@/config/routes"
import { useForm } from "@/hooks/use-form"
import { useMutation } from "@/hooks/use-mutation"
import { rememberChallenge } from "@/lib/session"
import { Alert } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { ChoiceCards } from "@/components/ui/choice-cards"
import { Field, FieldError, describedBy, fieldIds } from "@/components/ui/field"
import { TextField } from "@/components/ui/text-field"
import { initialSignupValues, signupSchema, toSignupPayload } from "@/utils/auth-forms"
import { withNext } from "@/utils/redirect"

// P2. creates the account, then hands over to /verify with the issued challenge
export function SignupForm({ next }: { next?: string }) {
  const router = useRouter()
  const { values, errors, setValue, validate } = useForm({
    initialValues: initialSignupValues,
    schema: signupSchema,
  })
  const { mutate, isPending, error } = useMutation(signup)
  const isVendor = values.role === "vendor"
  const alreadyRegistered = error?.is(409)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const valid = validate()
    if (!valid) return

    const payload = toSignupPayload(valid)
    const result = await mutate(payload)
    if (!result.ok) return

    rememberChallenge(result.data, { phone: payload.phone, next, isNewAccount: true })
    router.push(routes.verify)
  }

  return (
    <form noValidate onSubmit={handleSubmit} className="flex flex-col gap-6">
      <Field id="role" label="what brings you to sura?" asLabel={false}>
        <ChoiceCards
          name="role"
          labelledBy="role-label"
          options={accountTypeOptions}
          value={values.role}
          onChange={(role) => setValue("role", role)}
        />
      </Field>

      <TextField
        id="name"
        label={isVendor ? "your full name" : "full name"}
        placeholder="e.g. amaka obi"
        autoComplete="name"
        value={values.name}
        onChange={(event) => setValue("name", event.target.value)}
        error={errors.name}
      />

      {isVendor && (
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
            hint="we verify every vendor before they can accept vouchers."
          />
        </>
      )}

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
        hint="we'll text a 6-digit code to this number."
      />

      {!isVendor && (
        <Field id="context" label="how do you earn?" asLabel={false} error={errors.context}>
          <ChoiceCards
            name="context"
            labelledBy="context-label"
            describedBy={describedBy("context", { error: errors.context })}
            options={incomeContextOptions}
            value={values.context}
            onChange={(context) => setValue("context", context)}
            invalid={Boolean(errors.context)}
          />
        </Field>
      )}

      <div className="flex flex-col gap-2">
        <Checkbox
          id="terms"
          checked={values.termsAccepted}
          onChange={(event) => setValue("termsAccepted", event.target.checked)}
          invalid={Boolean(errors.termsAccepted)}
          aria-describedby={errors.termsAccepted ? fieldIds("terms").error : undefined}
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
        <FieldError id={fieldIds("terms").error} message={errors.termsAccepted} />
      </div>

      {error && (
        <Alert variant="error" title={alreadyRegistered ? "you already have an account" : undefined}>
          {alreadyRegistered ? (
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
        {isPending ? "creating your account" : "create account"}
      </Button>
    </form>
  )
}
