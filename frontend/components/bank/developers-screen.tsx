import Link from "next/link"
import { HugeiconsIcon } from "@hugeicons/react"
import { LinkSquare02Icon } from "@hugeicons/core-free-icons"
import { routes } from "@/config/routes"
import { sampleRequest } from "@/config/for-banks"
import { siteConfig } from "@/config/site"
import { PageHeader, Section } from "@/components/bank/page-header"
import { CodeBlock } from "@/components/shared/code-block"
import { CopyButton } from "@/components/shared/copy-button"
import { Alert } from "@/components/ui/alert"
import { buttonVariants } from "@/components/ui/button"

// matches backend/app/bank/integration_router.py and contracts.py
const machineEndpoints = [
  { method: "GET", path: "/v1/integrations/customers/{user_id}/score", scope: "score:read", description: "current score, tier and the five-pillar breakdown" },
  { method: "GET", path: "/v1/integrations/customers/{user_id}/commitments", scope: "commitments:read", description: "the customer's locks, payout slot and voucher outcome" },
]

const webhookEvents = [
  "contribution.recorded",
  "cycle.paid",
  "voucher.issued",
  "voucher.redeemed",
  "score.updated",
  "flag.created",
]

const baseUrl = siteConfig.apiUrl || "https://<sura-api>"

const requestCode = `curl ${baseUrl}${sampleRequest.path} \\
  -H "${sampleRequest.apiKeyHeader}: ${sampleRequest.placeholderKey}"`

// B11. static on purpose: it documents the contract, so it works for every bank
// role, including the demo analyst who has no developer permission
export function DevelopersScreen() {
  return (
    <>
      <PageHeader
        title="developers"
        description="plug sura into your own systems. every machine request is scoped to your bank, with a key you create."
        actions={
          siteConfig.apiDocsUrl && (
            <a
              href={siteConfig.apiDocsUrl}
              target="_blank"
              rel="noreferrer"
              className={buttonVariants({ size: "sm" })}
            >
              live api docs
              <HugeiconsIcon icon={LinkSquare02Icon} size={18} strokeWidth={2.2} />
            </a>
          )
        }
      />

      <div className="flex flex-col gap-10">
        <Section title="connect">
          <dl className="card-raised divide-y divide-hairline rounded-2xl">
            <div className="flex flex-col gap-1 px-4 py-3 sm:flex-row sm:items-center sm:gap-6">
              <dt className="text-sm font-extrabold sm:w-40 sm:shrink-0">base url</dt>
              <dd className="font-mono text-sm break-all text-muted-foreground normal-case">{baseUrl}</dd>
            </div>
            <div className="flex flex-col gap-1 px-4 py-3 sm:flex-row sm:items-center sm:gap-6">
              <dt className="text-sm font-extrabold sm:w-40 sm:shrink-0">auth header</dt>
              <dd className="font-mono text-sm text-muted-foreground normal-case">{sampleRequest.apiKeyHeader}</dd>
            </div>
            <div className="flex flex-col gap-2 px-4 py-3 sm:flex-row sm:items-center sm:gap-6">
              <dt className="text-sm font-extrabold sm:w-40 sm:shrink-0">sandbox key</dt>
              <dd className="flex min-w-0 flex-1 flex-wrap items-center justify-between gap-3">
                <span className="font-mono text-sm break-all text-muted-foreground normal-case">
                  {sampleRequest.placeholderKey}
                </span>
                <CopyButton value={sampleRequest.placeholderKey} />
              </dd>
            </div>
          </dl>
          <Alert variant="gold" className="mt-3" title="this key is a placeholder">
            real keys are created by your bank administrator, scoped to least privilege, and shown exactly once.
          </Alert>
        </Section>

        <Section title="endpoints" description="read only. a key can never reach another bank's customers.">
          <ul className="flex flex-col gap-3">
            {machineEndpoints.map((endpoint) => (
              <li key={endpoint.path} className="card-raised rounded-2xl p-4">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="rounded-full bg-primary px-2.5 py-0.5 text-xs font-black text-primary-foreground normal-case">
                    {endpoint.method}
                  </span>
                  <code className="font-mono text-sm font-bold break-all normal-case">{endpoint.path}</code>
                </div>
                <p className="mt-2 text-sm font-semibold text-muted-foreground">{endpoint.description}</p>
                <p className="mt-1 text-xs font-bold text-muted-foreground">
                  scope <code className="font-mono text-link normal-case">{endpoint.scope}</code>
                </p>
              </li>
            ))}
          </ul>
        </Section>

        <Section title="sample request">
          <div className="grid gap-3 lg:grid-cols-2">
            <CodeBlock label={`request: ${sampleRequest.label}`} code={requestCode} />
            <CodeBlock label="response (trimmed)" code={sampleRequest.response} />
          </div>
        </Section>

        <Section title="webhook events" description="signed json payloads. test deliveries only in this release.">
          <ul className="flex flex-wrap gap-2">
            {webhookEvents.map((event) => (
              <li key={event} className="rounded-full border-2 border-hairline bg-card px-3 py-1 font-mono text-xs font-bold normal-case">
                {event}
              </li>
            ))}
          </ul>
        </Section>

        <p className="text-sm font-semibold text-muted-foreground">
          pitching sura to your team?{" "}
          <Link href={routes.forBanks} className="font-extrabold text-link underline-offset-4 hover:underline">
            see the overview for banks
          </Link>
        </p>
      </div>
    </>
  )
}
