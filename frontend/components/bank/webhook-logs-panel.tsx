"use client"

import { useState } from "react"
import { HugeiconsIcon } from "@hugeicons/react"
import { RefreshIcon, SentIcon, WebhookIcon } from "@hugeicons/core-free-icons"
import { listWebhookDeliveries, listWebhooks } from "@/actions/bank"
import { useQuery } from "@/hooks/use-query"
import { SelectFilter } from "@/components/bank/filters"
import { Section } from "@/components/bank/page-header"
import { QueryState } from "@/components/bank/query-state"
import { StatusBadge } from "@/components/bank/status-badge"
import { CodeBlock } from "@/components/shared/code-block"
import { EmptyState } from "@/components/shared/empty-state"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { cn } from "@/lib/utils"
import type { Webhook, WebhookDelivery } from "@/types"
import { formatDateTime } from "@/utils/format"

const noArgs: [] = []

type WebhookLogsPanelProps = {
  // the endpoint to open on, e.g. after "logs" on the webhooks tab
  webhookId: string | null
  onWebhookChange: (webhookId: string) => void
  onAddEndpoint: () => void
}

// every delivery sura recorded for one endpoint, newest first, with the exact
// payload and signature so a bank can check its verifier against them
export function WebhookLogsPanel({ webhookId, onWebhookChange, onAddEndpoint }: WebhookLogsPanelProps) {
  const webhooks = useQuery(listWebhooks, noArgs)

  return (
    <Section title="Logs" description="Signed deliveries Sura recorded for each endpoint, newest first.">
      <QueryState
        query={webhooks}
        noun="webhooks"
        skeleton={<Skeleton className="h-64 rounded-2xl" />}
        isEmpty={(rows) => rows.length === 0}
        empty={
          <EmptyState
            icon={WebhookIcon}
            title="Nothing to log yet"
            description="Add a webhook endpoint and send it a test. Its deliveries show up here."
            action={
              <Button type="button" size="sm" onClick={onAddEndpoint}>
                Go to webhooks
              </Button>
            }
          />
        }
      >
        {(rows) => {
          // a stale id, e.g. from an old link, falls back to the newest endpoint
          const selected = rows.find((row) => row.webhook_id === webhookId) ?? rows[0]
          return (
            <EndpointLog
              key={selected.webhook_id}
              webhooks={rows}
              selected={selected}
              onWebhookChange={onWebhookChange}
            />
          )
        }}
      </QueryState>
    </Section>
  )
}

type EndpointLogProps = {
  webhooks: Webhook[]
  selected: Webhook
  onWebhookChange: (webhookId: string) => void
}

function EndpointLog({ webhooks, selected, onWebhookChange }: EndpointLogProps) {
  const deliveries = useQuery(listWebhookDeliveries, [selected.webhook_id])
  const [openId, setOpenId] = useState<string | null>(null)
  const options = webhooks.map((webhook) => ({
    value: webhook.webhook_id,
    label: `${webhook.url}${webhook.status === "disabled" ? " (disabled)" : ""}`,
  }))

  return (
    <div className="flex flex-col gap-5">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
        <SelectFilter
          id="logs-endpoint"
          label="Endpoint"
          value={selected.webhook_id}
          onChange={(value) => value && onWebhookChange(value)}
          options={options}
          allLabel="Choose an endpoint"
          className="min-w-0 sm:w-auto sm:flex-1 [&_select]:font-mono"
        />
        <Button type="button" variant="outline" onClick={deliveries.retry} disabled={deliveries.isLoading}>
          <HugeiconsIcon icon={RefreshIcon} size={18} strokeWidth={2.2} />
          Refresh
        </Button>
      </div>

      <QueryState
        query={deliveries}
        noun="deliveries"
        skeleton={<Skeleton className="h-64 rounded-2xl" />}
        isEmpty={(rows) => rows.length === 0}
        empty={
          <EmptyState
            icon={SentIcon}
            title="No deliveries yet"
            description="Use Send test on the Webhooks tab to record a signed delivery to this endpoint."
          />
        }
      >
        {(rows) => {
          const open = rows.find((row) => row.delivery_id === openId) ?? rows[0]
          return (
            <div className="grid gap-4 lg:grid-cols-[minmax(0,2fr)_minmax(0,3fr)] lg:items-start">
              <ul aria-label="Deliveries" className="card-raised divide-y-2 divide-hairline overflow-hidden rounded-2xl">
                {rows.map((row) => (
                  <li key={row.delivery_id}>
                    <button
                      type="button"
                      onClick={() => setOpenId(row.delivery_id)}
                      aria-current={row.delivery_id === open.delivery_id ? "true" : undefined}
                      className={cn(
                        "flex w-full items-center justify-between gap-3 px-4 py-3 text-left transition-colors outline-none hover:bg-cloud focus-visible:bg-cloud",
                        row.delivery_id === open.delivery_id && "bg-indigo-soft hover:bg-indigo-soft"
                      )}
                    >
                      <span className="min-w-0">
                        <span className="block truncate font-mono text-sm font-bold">{row.event_type}</span>
                        <span className="block text-xs font-bold text-muted-foreground">
                          {formatDateTime(row.delivered_at ?? row.created_at)}
                        </span>
                      </span>
                      <StatusBadge status={row.status} label={row.response_status ? String(row.response_status) : undefined} />
                    </button>
                  </li>
                ))}
              </ul>
              <DeliveryDetail delivery={open} />
            </div>
          )
        }}
      </QueryState>
    </div>
  )
}

function DeliveryDetail({ delivery }: { delivery: WebhookDelivery }) {
  const facts = [
    { label: "Status", value: <StatusBadge status={delivery.status} /> },
    { label: "Response", value: delivery.response_status ?? "—" },
    { label: "Attempt", value: delivery.attempt_number },
    { label: "Sent", value: formatDateTime(delivery.delivered_at ?? delivery.created_at) },
  ]

  return (
    <div className="flex flex-col gap-3">
      <dl className="card-raised grid grid-cols-2 gap-x-4 gap-y-3 rounded-2xl p-4 sm:grid-cols-4">
        {facts.map((fact) => (
          <div key={fact.label} className="min-w-0">
            <dt className="text-xs font-bold tracking-wide text-muted-foreground">{fact.label}</dt>
            <dd className="mt-1 text-sm font-bold">{fact.value}</dd>
          </div>
        ))}
        <div className="col-span-full min-w-0">
          <dt className="text-xs font-bold tracking-wide text-muted-foreground">Event ID</dt>
          <dd className="mt-1 font-mono text-xs font-semibold break-all">{delivery.event_id}</dd>
        </div>
        {delivery.response_summary && (
          <div className="col-span-full min-w-0">
            <dt className="text-xs font-bold tracking-wide text-muted-foreground">Note</dt>
            <dd className="mt-1 text-sm font-semibold text-muted-foreground">{delivery.response_summary}</dd>
          </div>
        )}
      </dl>
      <CodeBlock label="Payload" code={JSON.stringify(delivery.payload, null, 2)} />
      <CodeBlock label="Signature (HMAC-SHA256 of the payload)" code={delivery.signature} />
    </div>
  )
}
