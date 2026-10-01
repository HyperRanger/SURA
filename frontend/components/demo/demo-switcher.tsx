"use client"

import { useState } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { demoSignIn } from "@/actions/demo"
import { demoAreas, demoPersonas, isPersonaAvailable, type DemoPersona } from "@/config/demo"
import { useMutation } from "@/hooks/use-mutation"
import { useStoredValue } from "@/hooks/use-stored-value"
import { endSession, sessionStore, startSession } from "@/lib/session"
import { PersonaCard } from "@/components/demo/persona-card"
import { Alert } from "@/components/ui/alert"
import { Button, buttonVariants } from "@/components/ui/button"
import { homeForRole } from "@/utils/redirect"

const availablePersonas = demoPersonas.filter(isPersonaAvailable)
const hiddenCount = demoPersonas.length - availablePersonas.length

// P8. one tap signs in as a seeded person and replaces whoever was signed in,
// so a presenter can hop between members, the vendor and the bank on stage
export function DemoSwitcher() {
  const router = useRouter()
  const session = useStoredValue(sessionStore)
  const { mutate, isPending, error } = useMutation(demoSignIn)
  const [active, setActive] = useState<DemoPersona | null>(null)

  async function handleSelect(persona: DemoPersona) {
    setActive(persona)
    const result = await mutate(persona.signIn)
    if (!result.ok) return

    startSession(result.data)
    router.push(homeForRole(result.data.role))
  }

  return (
    <div className="flex flex-col gap-8">
      {session && (
        <Alert
          variant="info"
          title="you're signed in"
          action={
            <div className="flex shrink-0 flex-wrap gap-2">
              <Link href={homeForRole(session.role)} className={buttonVariants({ size: "sm" })}>
                continue
              </Link>
              <Button type="button" variant="outline" size="sm" onClick={endSession}>
                sign out
              </Button>
            </div>
          }
        >
          as {session.role.replaceAll("_", " ")}. pick someone below to switch.
        </Alert>
      )}

      {error && active && (
        <Alert variant="error" title={`couldn't sign in as ${active.name}`}>
          {error.is(404) ? "the demo is switched off on this api." : error.message}
        </Alert>
      )}

      {demoAreas.map(({ area, title }) => {
        const personas = availablePersonas.filter((persona) => persona.area === area)
        if (personas.length === 0) return null

        return (
          <section key={area} aria-labelledby={`demo-${area}`}>
            <div className="mb-3 flex flex-col gap-0.5 sm:flex-row sm:items-baseline sm:justify-between sm:gap-3">
              <h2 id={`demo-${area}`} className="text-lg font-black">
                {title}
              </h2>
            </div>
            <div className="flex flex-col gap-3">
              {personas.map((persona) => (
                <PersonaCard
                  key={persona.id}
                  persona={persona}
                  onSelect={handleSelect}
                  loading={isPending && active?.id === persona.id}
                  disabled={isPending}
                />
              ))}
            </div>
          </section>
        )
      })}

      {/*{hiddenCount > 0 && (
        <p className="text-xs font-semibold text-muted-foreground">
          {hiddenCount} named {hiddenCount === 1 ? "person is" : "people are"} hidden. set{" "}
          <code className="font-mono normal-case">NEXT_PUBLIC_DEMO_OTP_CODE</code> to the api&apos;s demo
          code to show them.
        </p>
      )}*/}
    </div>
  )
}
