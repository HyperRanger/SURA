"use client"

import { useState } from "react"
import Link from "next/link"
import { usePathname, useRouter } from "next/navigation"
import { HugeiconsIcon } from "@hugeicons/react"
import { LinkSquare02Icon } from "@hugeicons/core-free-icons"
import { getDeveloperHome, listWebhookEvents, listWebhooks } from "@/actions/bank"
import { developerTabs, isDeveloperTab, type DeveloperTab } from "@/config/bank"
import { routes } from "@/config/routes"
import { sampleRequest } from "@/config/for-banks"
import { siteConfig } from "@/config/site"
import { useQuery } from "@/hooks/use-query"
import { ApiKeysPanel } from "@/components/bank/api-keys-panel"
import { ApiPlaygroundPanel } from "@/components/bank/api-playground-panel"
import { DataTable, TableSkeleton, type Column } from "@/components/bank/data-table"
import { PageHeader, Section } from "@/components/bank/page-header"
import { QueryState } from "@/components/bank/query-state"
import { StatusBadge } from "@/components/bank/status-badge"
import { WebhookLogsPanel } from "@/components/bank/webhook-logs-panel"
import { WebhooksPanel } from "@/components/bank/webhooks-panel"
import { CodeBlock } from "@/components/shared/code-block"
import { CopyButton } from "@/components/shared/copy-button"
import { Alert } from "@/components/ui/alert"
import { Button, buttonVariants } from "@/components/ui/button"
import { Tabs, TabsList, TabsPanel, TabsTab } from "@/components/ui/tabs"
import type { WebhookEvent, WebhookEventInfo } from "@/types"

// matches backend/app/bank/integration_router.py and contracts.py
const machineEndpoints = [
  { method: "GET", path: "/v1/integrations/customers/{user_id}/score", scope: "score:read", description: "Current score, tier and the five-pillar breakdown" },
  { method: "GET", path: "/v1/integrations/customers/{user_id}/commitments", scope: "commitments:read", description: "The customer's locks, payout slot and voucher outcome" },
]

const noArgs: [] = []

const baseUrl = siteConfig.apiUrl || "https://<sura-api>"

const requestCode = `curl ${baseUrl}${sampleRequest.path} \\
  -H "${sampleRequest.apiKeyHeader}: <your sandbox key>"`

type DevelopersScreenProps = {
  initialTab?: DeveloperTab
  initialWebhookId?: string
}

// B11. create a sandbox key, then configure and test a signed webhook. the shell
// only shows this section to sessions holding bank:developer:write. the open tab
// lives in the url, so a refresh or a shared link lands on the same view
export function DevelopersScreen({ initialTab = "api-keys", initialWebhookId }: DevelopersScreenProps) {
  const router = useRouter()
  const pathname = usePathname()
  const home = useQuery(getDeveloperHome, noArgs)
  const [tab, setTab] = useState<DeveloperTab>(initialTab)
  const [logWebhookId, setLogWebhookId] = useState<string | null>(initialWebhookId ?? null)
  // a key typed into, or handed to, the playground. memory only, gone on refresh
  const [playgroundKey, setPlaygroundKey] = useState("")

  function go(next: DeveloperTab, webhookId: string | null = logWebhookId) {
    setTab(next)
    if (webhookId !== logWebhookId) setLogWebhookId(webhookId)
    const params = new URLSearchParams({ tab: next })
    if (next === "logs" && webhookId) params.set("webhook", webhookId)
    router.replace(`${pathname}?${params}`, { scroll: false })
  }

  return (
    <>
      <PageHeader
        title="Developers"
        description="Plug Sura into your own systems. Every machine request is scoped to your bank, with a key you create."
        meta={home.data && <StatusBadge status={home.data.environment} label={`${home.data.environment} environment`} />}
        actions={
          siteConfig.apiDocsUrl && (
            <a
              href={siteConfig.apiDocsUrl}
              target="_blank"
              rel="noreferrer"
              className={buttonVariants({ variant: "outline", size: "sm" })}
            >
              API reference
              <HugeiconsIcon icon={LinkSquare02Icon} size={18} strokeWidth={2.2} />
            </a>
          )
        }
      />

      <Tabs value={tab} onValueChange={(value) => isDeveloperTab(value) && go(value)}>
        <TabsList aria-label="Developer tools">
          {developerTabs.map((item) => (
            <TabsTab key={item.value} value={item.value} title={`Show ${item.label.toLowerCase()}`}>
              {item.label}
            </TabsTab>
          ))}
        </TabsList>

        <TabsPanel value="api-keys">
          <ApiKeysPanel
            onTryKey={(secret) => {
              setPlaygroundKey(secret)
              go("playground")
            }}
          />
        </TabsPanel>

        <TabsPanel value="playground">
          <ApiPlaygroundPanel apiKey={playgroundKey} onApiKeyChange={setPlaygroundKey} onCreateKey={() => go("api-keys")} />
        </TabsPanel>

        <TabsPanel value="webhooks">
          <WebhooksPanel onViewLogs={(webhookId) => go("logs", webhookId)} />
        </TabsPanel>

        <TabsPanel value="events">
          <EventsPanel />
        </TabsPanel>

        <TabsPanel value="logs">
          <WebhookLogsPanel
            webhookId={logWebhookId}
            onWebhookChange={(webhookId) => go("logs", webhookId)}
            onAddEndpoint={() => go("webhooks")}
          />
        </TabsPanel>

        <TabsPanel value="docs">
          <DocsPanel webhookDelivery={home.data?.webhook_delivery} onTry={() => go("playground")} />
        </TabsPanel>
      </Tabs>
    </>
  )
}

// the catalogue from the api, with how many active endpoints listen for each event
function EventsPanel() {
  const events = useQuery(listWebhookEvents, noArgs)
  const webhooks = useQuery(listWebhooks, noArgs)

  const listeners = (event: WebhookEvent) =>
    webhooks.data?.filter((webhook) => webhook.status === "active" && webhook.events.includes(event)).length

  const columns: Column<WebhookEventInfo>[] = [
    { header: "Event", cell: (row) => <span className="font-mono">{row.event_type}</span> },
    { header: "Delivery", cell: (row) => row.delivery },
    { header: "Retries", cell: (row) => row.retry },
    {
      header: "Active endpoints",
      align: "right",
      cell: (row) => {
        const count = listeners(row.event_type)
        return count === undefined ? "—" : count
      },
    },
  ]

  return (
    <Section title="Events" description="What a webhook endpoint can subscribe to. Choose them when you add or edit an endpoint.">
      <div className="flex flex-col gap-4">
        <Alert variant="info" title="Test deliveries only in this release">
          Endpoints receive signed test deliveries today. Live business events, and retries, come in a later release.
        </Alert>
        <QueryState query={events} noun="events" skeleton={<TableSkeleton rows={6} />}>
          {(rows) => <DataTable caption="Webhook events" columns={columns} rows={rows} rowKey={(row) => row.event_type} />}
        </QueryState>
      </div>
    </Section>
  )
}

function DocsPanel({ webhookDelivery, onTry }: { webhookDelivery?: string; onTry: () => void }) {
  return (
    <div className="flex flex-col gap-10">
      <Section title="Connect" description="Every machine request needs a key from the API keys tab.">
        <dl className="card-raised divide-y-2 divide-hairline rounded-2xl">
          <div className="flex flex-col gap-2 px-4 py-3 sm:flex-row sm:items-center sm:gap-6">
            <dt className="text-sm font-bold sm:w-40 sm:shrink-0">Base URL</dt>
            <dd className="flex min-w-0 flex-1 items-center justify-between gap-3">
              <span className="font-mono text-sm break-all text-muted-foreground">{baseUrl}</span>
              <CopyButton value={baseUrl} />
            </dd>
          </div>
          <div className="flex flex-col gap-1 px-4 py-3 sm:flex-row sm:items-center sm:gap-6">
            <dt className="text-sm font-bold sm:w-40 sm:shrink-0">Auth header</dt>
            <dd className="font-mono text-sm text-muted-foreground">{sampleRequest.apiKeyHeader}</dd>
          </div>
          {webhookDelivery && (
            <div className="flex flex-col gap-1 px-4 py-3 sm:flex-row sm:items-center sm:gap-6">
              <dt className="text-sm font-bold sm:w-40 sm:shrink-0">Webhooks</dt>
              <dd className="text-sm font-semibold text-muted-foreground">{webhookDelivery}</dd>
            </div>
          )}
        </dl>
      </Section>

      <Section
        title="Endpoints"
        description="Read only. A key can never reach another bank's customers."
        action={
          <Button type="button" variant="outline" size="sm" title="Call these endpoints live" onClick={onTry}>
            Try it live
          </Button>
        }
      >
        <ul className="flex flex-col gap-3">
          {machineEndpoints.map((endpoint) => (
            <li key={endpoint.path} className="card-raised rounded-2xl p-4">
              <div className="flex flex-wrap items-center gap-2">
                <span className="rounded-full bg-primary px-2.5 py-0.5 text-xs font-bold text-primary-foreground">
                  {endpoint.method}
                </span>
                <code className="font-mono text-sm font-bold break-all">{endpoint.path}</code>
              </div>
              <p className="mt-2 text-sm font-semibold text-muted-foreground">{endpoint.description}</p>
              <p className="mt-1 text-xs font-bold text-muted-foreground">
                Scope <code className="font-mono text-link">{endpoint.scope}</code>
              </p>
            </li>
          ))}
        </ul>
      </Section>

      <Section title="Sample request">
        <div className="grid gap-3 lg:grid-cols-2">
          <CodeBlock label={`Request: ${sampleRequest.label.toLowerCase()}`} code={requestCode} />
          <CodeBlock label="Response (trimmed)" code={sampleRequest.response} />
        </div>
      </Section>

      <p className="text-sm font-semibold text-muted-foreground">
        Pitching Sura to your team?{" "}
        <Link href={routes.forBanks} className="font-bold text-link underline-offset-4 hover:underline">
          See the overview for banks
        </Link>
      </p>
    </div>
  )
}
