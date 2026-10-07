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

// P8. one tap signs in as a seeded person and replaces whoever was signed in,
// so a presenter can hop between members and the vendor on stage
export function DemoSwitcher() {
  const router = useRouter()
  const session = useStoredValue(sessionStore)
  const { mutate, isPending, error } = useMutation(demoSignIn)
  const [active, setActive] = useState<DemoPersona | null>(null)

  async function handleSelect(persona: DemoPersona) {
    if (persona.signIn.type === "external") return
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
          title="You're signed in"
          action={
            <div className="flex shrink-0 flex-col gap-2">
              <Link href={homeForRole(session.role)} className={buttonVariants({ size: "sm" })}>
                Continue
              </Link>
              <Button type="button" variant="outline" size="sm" onClick={endSession}>
                Sign out
              </Button>
            </div>
          }
        >
          As {session.role === "vendor" ? "a vendor" : "a member"}. Pick someone below to switch.
        </Alert>
      )}

      {error && active && (
        <Alert variant="error" title={`Couldn't sign in as ${active.name}`}>
          {error.is(404) ? "The demo is switched off on this API." : error.message}
        </Alert>
      )}

      {demoAreas.map(({ area, title }) => {
        const personas = availablePersonas.filter((persona) => persona.area === area)
        if (personas.length === 0) return null

        return (
          <section key={area} aria-labelledby={`demo-${area}`}>
            <h2 id={`demo-${area}`} className="mb-3 text-lg font-bold">
              {title}
            </h2>
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
    </div>
  )
}
