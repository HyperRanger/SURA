"use client"

import { useState, type FormEvent } from "react"
import { WebhookIcon } from "@hugeicons/core-free-icons"
import {
  createWebhook,
  disableWebhook,
  listWebhookDeliveries,
  listWebhooks,
  rotateWebhookSecret,
  testWebhook,
  updateWebhook,
} from "@/actions/bank"
import { webhookEvents } from "@/config/bank"
import { useMutation } from "@/hooks/use-mutation"
import { useQuery } from "@/hooks/use-query"
import { ActionError, ConfirmButton, SecretReveal } from "@/components/bank/action-kit"
import { DataTable, TableSkeleton, type Column } from "@/components/bank/data-table"
import { Section } from "@/components/bank/page-header"
import { QueryState } from "@/components/bank/query-state"
import { StatusBadge } from "@/components/bank/status-badge"
import { CodeBlock } from "@/components/shared/code-block"
import { EmptyState } from "@/components/shared/empty-state"
import { Alert } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { Field, FieldError } from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import { Skeleton } from "@/components/ui/skeleton"
import type { Webhook, WebhookDelivery, WebhookEvent } from "@/types"
import { formatDateTime } from "@/utils/format"

const noArgs: [] = []

type Revealed = { label: string; secret: string }

// the api only accepts absolute https urls
function urlError(url: string) {
  if (!url.trim()) return "enter the https url that should receive events"
  try {
    const parsed = new URL(url.trim())
    return parsed.protocol === "https:" ? undefined : "the url must start with https://"
  } catch {
    return "enter a full url, e.g. https://bank.example/hooks/sura"
  }
}

// B11. subscriptions are configured and tested here. this release sends signed,
// simulated test deliveries only; live business events are not dispatched yet
export function WebhooksPanel() {
  const webhooks = useQuery(listWebhooks, noArgs)
  const [revealed, setRevealed] = useState<Revealed | null>(null)

  return (
    <Section
      title="webhooks"
      description="signed json payloads. each delivery carries an hmac-sha256 of its body, keyed with your signing secret."
    >
      <div className="flex flex-col gap-4">
        {revealed && (
          <SecretReveal title={revealed.label} secret={revealed.secret} onDismiss={() => setRevealed(null)} />
        )}

        <WebhookForm
          mode="create"
          onSaved={(secret, url) => {
            if (secret) setRevealed({ label: `signing secret for ${url}`, secret })
            webhooks.retry()
          }}
        />

        <QueryState
          query={webhooks}
          noun="webhooks"
          skeleton={<TableSkeleton rows={2} />}
          isEmpty={(rows) => rows.length === 0}
          empty={
            <EmptyState
              icon={WebhookIcon}
              title="no webhooks yet"
              description="add an https endpoint above, then send it a signed test delivery."
            />
          }
        >
          {(rows) => (
            <ul className="flex flex-col gap-4">
              {rows.map((webhook) => (
                <li key={webhook.webhook_id}>
                  <WebhookCard
                    webhook={webhook}
                    onChanged={webhooks.retry}
                    onSecret={(secret) => setRevealed({ label: `new signing secret for ${webhook.url}`, secret })}
                  />
                </li>
              ))}
            </ul>
          )}
        </QueryState>
      </div>
    </Section>
  )
}

type WebhookFormProps =
  | { mode: "create"; webhook?: undefined; onSaved: (secret: string | null, url: string) => void; onCancel?: undefined }
  | { mode: "edit"; webhook: Webhook; onSaved: (secret: string | null, url: string) => void; onCancel: () => void }

function WebhookForm({ mode, webhook, onSaved, onCancel }: WebhookFormProps) {
  const prefix = mode === "edit" ? `webhook-${webhook.webhook_id}` : "webhook-new"
  const [url, setUrl] = useState(webhook?.url ?? "")
  const [events, setEvents] = useState<WebhookEvent[]>(webhook?.events ?? ["score.updated"])
  const [errors, setErrors] = useState<{ url?: string; events?: string }>({})
  const create = useMutation(createWebhook)
  const update = useMutation(updateWebhook)
  const pending = create.isPending || update.isPending

  function toggleEvent(event: WebhookEvent, checked: boolean) {
    setEvents((current) => (checked ? [...current, event] : current.filter((value) => value !== event)))
    if (errors.events) setErrors((current) => ({ ...current, events: undefined }))
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const nextErrors = { url: urlError(url), events: events.length ? undefined : "choose at least one event" }
    setErrors(nextErrors)
    if (nextErrors.url || nextErrors.events) return

    const payload = { url: url.trim(), events }
    if (mode === "create") {
      const result = await create.mutate(payload)
      if (result.ok) {
        setUrl("")
        setEvents(["score.updated"])
        onSaved(result.data.signing_secret, result.data.url)
      }
    } else {
      const result = await update.mutate(webhook.webhook_id, payload)
      if (result.ok) onSaved(null, result.data.url)
    }
  }

  return (
    <form noValidate onSubmit={handleSubmit} className="card-raised flex flex-col gap-5 rounded-2xl p-4 sm:p-5">
      <Field id={`${prefix}-url`} label={mode === "create" ? "add an endpoint" : "endpoint url"} error={errors.url}>
        <Input
          id={`${prefix}-url`}
          type="url"
          inputMode="url"
          value={url}
          onChange={(event) => {
            setUrl(event.target.value)
            if (errors.url) setErrors((current) => ({ ...current, url: undefined }))
          }}
          invalid={Boolean(errors.url)}
          aria-describedby={errors.url ? `${prefix}-url-error` : undefined}
          placeholder="https://bank.example/hooks/sura"
          className="h-12 font-mono text-sm"
        />
      </Field>

      <fieldset>
        <legend className="mb-2 text-sm font-extrabold">events</legend>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {webhookEvents.map((name) => (
            <Checkbox
              key={name}
              id={`${prefix}-event-${name}`}
              checked={events.includes(name)}
              onChange={(event) => toggleEvent(name, event.target.checked)}
              invalid={Boolean(errors.events)}
              label={<span className="font-mono text-xs font-bold text-foreground normal-case">{name}</span>}
            />
          ))}
        </div>
        <FieldError message={errors.events} />
      </fieldset>

      <ActionError error={create.error ?? update.error} />

      <div className="flex flex-wrap gap-2">
        <Button type="submit" loading={pending}>
          {mode === "create" ? "add webhook" : "save changes"}
        </Button>
        {onCancel && (
          <Button type="button" variant="ghost" onClick={onCancel} disabled={pending}>
            cancel
          </Button>
        )}
      </div>
    </form>
  )
}

type WebhookCardProps = {
  webhook: Webhook
  onChanged: () => void
  onSecret: (secret: string) => void
}

function WebhookCard({ webhook, onChanged, onSecret }: WebhookCardProps) {
  const [editing, setEditing] = useState(false)
  const [showDeliveries, setShowDeliveries] = useState(false)
  // bumps after a test so the delivery log remounts and refetches
  const [deliveryVersion, setDeliveryVersion] = useState(0)
  const [lastTest, setLastTest] = useState<WebhookDelivery | null>(null)
  const test = useMutation(testWebhook)
  const rotate = useMutation(rotateWebhookSecret)
  const enable = useMutation(updateWebhook)
  const disable = useMutation(disableWebhook)
  const active = webhook.status === "active"

  async function handleTest() {
    const result = await test.mutate(webhook.webhook_id)
    if (result.ok) {
      setLastTest(result.data)
      setShowDeliveries(true)
      setDeliveryVersion((n) => n + 1)
    }
  }

  async function handleRotate() {
    const result = await rotate.mutate(webhook.webhook_id)
    if (result.ok) onSecret(result.data.signing_secret)
  }

  async function handleEnable() {
    const result = await enable.mutate(webhook.webhook_id, { status: "active" })
    if (result.ok) onChanged()
  }

  async function handleDisable() {
    // 204 with no body, so the list is refetched for the new status
    const result = await disable.mutate(webhook.webhook_id)
    if (result.ok) onChanged()
  }

  if (editing) {
    return (
      <WebhookForm
        mode="edit"
        webhook={webhook}
        onCancel={() => setEditing(false)}
        onSaved={() => {
          setEditing(false)
          onChanged()
        }}
      />
    )
  }

  return (
    <div className="card-raised flex flex-col gap-4 rounded-2xl p-4 sm:p-5">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <p className="font-mono text-sm font-bold break-all normal-case">{webhook.url}</p>
          <div className="mt-2 flex flex-wrap items-center gap-2">
            <StatusBadge status={webhook.status} tone={active ? "indigo" : "neutral"} />
            {webhook.events.map((event) => (
              <span
                key={event}
                className="rounded-full border-2 border-hairline bg-card px-2.5 py-0.5 font-mono text-xs font-bold normal-case"
              >
                {event}
              </span>
            ))}
          </div>
          <p className="mt-2 text-xs font-bold text-muted-foreground">
            created {formatDateTime(webhook.created_at)}
            {webhook.updated_at && ` · updated ${formatDateTime(webhook.updated_at)}`}
          </p>
        </div>
        <div className="flex shrink-0 flex-wrap gap-2">
          <Button type="button" size="sm" onClick={handleTest} loading={test.isPending} disabled={!active}>
            send test
          </Button>
          <Button type="button" size="sm" variant="outline" onClick={() => setEditing(true)}>
            edit
          </Button>
          <ConfirmButton confirmLabel="yes, rotate" loading={rotate.isPending} onConfirm={handleRotate}>
            rotate secret
          </ConfirmButton>
          {active ? (
            <ConfirmButton confirmLabel="yes, disable" variant="ghost" loading={disable.isPending} onConfirm={handleDisable}>
              disable
            </ConfirmButton>
          ) : (
            <Button type="button" size="sm" variant="ghost" onClick={handleEnable} loading={enable.isPending}>
              enable
            </Button>
          )}
        </div>
      </div>

      <ActionError error={test.error ?? rotate.error ?? enable.error ?? disable.error} />

      {lastTest && (
        <Alert variant="info" title={`test delivered · ${lastTest.response_status ?? "no"} response`}>
          {lastTest.response_summary}
        </Alert>
      )}

      <div>
        <Button type="button" variant="link" size="sm" className="h-auto px-0" onClick={() => setShowDeliveries((open) => !open)}>
          {showDeliveries ? "hide delivery log" : "show delivery log"}
        </Button>
        {showDeliveries && <DeliveryLog key={deliveryVersion} webhookId={webhook.webhook_id} />}
      </div>
    </div>
  )
}

const deliveryColumns: Column<WebhookDelivery>[] = [
  { header: "event", cell: (row) => <span className="font-mono text-xs normal-case">{row.event_type}</span> },
  { header: "status", cell: (row) => <StatusBadge status={row.status} /> },
  { header: "response", cell: (row) => row.response_status ?? "—", align: "right" },
  { header: "attempt", cell: (row) => row.attempt_number, align: "right" },
  { header: "sent", cell: (row) => formatDateTime(row.delivered_at ?? row.created_at) },
]

function DeliveryLog({ webhookId }: { webhookId: string }) {
  const deliveries = useQuery(listWebhookDeliveries, [webhookId])
  const latest = deliveries.data?.[0]

  return (
    <div className="mt-3 flex flex-col gap-3">
      <QueryState
        query={deliveries}
        noun="deliveries"
        skeleton={<Skeleton className="h-24 rounded-2xl" />}
        isEmpty={(rows) => rows.length === 0}
        empty={
          <p className="rounded-2xl border-2 border-dashed border-hairline px-4 py-6 text-center text-sm font-semibold text-muted-foreground">
            no deliveries yet. send a test to see one here.
          </p>
        }
      >
        {(rows) => (
          <DataTable caption="webhook deliveries" columns={deliveryColumns} rows={rows} rowKey={(row) => row.delivery_id} />
        )}
      </QueryState>
      {latest && (
        <div className="grid gap-3 lg:grid-cols-2">
          <CodeBlock label="latest payload" code={JSON.stringify(latest.payload, null, 2)} />
          <CodeBlock label="signature (hmac-sha256 of the payload)" code={latest.signature} />
        </div>
      )}
    </div>
  )
}
