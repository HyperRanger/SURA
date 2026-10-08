"use client"

import { useState, type FormEvent } from "react"
import { HugeiconsIcon } from "@hugeicons/react"
import { Add01Icon, WebhookIcon } from "@hugeicons/core-free-icons"
import {
  createWebhook,
  disableWebhook,
  listWebhooks,
  rotateWebhookSecret,
  testWebhook,
  updateWebhook,
} from "@/actions/bank"
import { webhookEvents } from "@/config/bank"
import { useMutation } from "@/hooks/use-mutation"
import { useQuery } from "@/hooks/use-query"
import { ActionError, ConfirmButton, SecretView } from "@/components/bank/action-kit"
import { TableSkeleton } from "@/components/bank/data-table"
import { Section } from "@/components/bank/page-header"
import { QueryState } from "@/components/bank/query-state"
import { StatusBadge } from "@/components/bank/status-badge"
import { EmptyState } from "@/components/shared/empty-state"
import { Alert } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { Dialog } from "@/components/ui/dialog"
import { Field, FieldError } from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import type { Webhook, WebhookDelivery, WebhookEvent } from "@/types"
import { formatDateTime } from "@/utils/format"

const noArgs: [] = []

// the api only accepts absolute https urls
function urlError(url: string) {
  if (!url.trim()) return "Enter the HTTPS URL that should receive events"
  try {
    const parsed = new URL(url.trim())
    return parsed.protocol === "https:" ? undefined : "The URL must start with https://"
  } catch {
    return "Enter a full URL, e.g. https://bank.example/hooks/sura"
  }
}

type DialogState =
  | { step: "create" }
  | { step: "edit"; webhook: Webhook }
  | { step: "secret"; url: string; secret: string; rotated: boolean }
  | null

function dialogTitle(dialog: DialogState) {
  if (!dialog) return ""
  if (dialog.step === "create") return "Add an endpoint"
  if (dialog.step === "edit") return "Edit endpoint"
  return dialog.rotated ? "New signing secret" : "Endpoint added"
}

// B11. subscriptions are configured and tested here. this release sends signed,
// simulated test deliveries only; live business events are not dispatched yet
export function WebhooksPanel({ onViewLogs }: { onViewLogs: (webhookId: string) => void }) {
  const webhooks = useQuery(listWebhooks, noArgs)
  const [dialog, setDialog] = useState<DialogState>(null)

  const addButton = (
    <Button type="button" size="sm" onClick={() => setDialog({ step: "create" })}>
      <HugeiconsIcon icon={Add01Icon} size={18} strokeWidth={2.4} />
      Add endpoint
    </Button>
  )

  return (
    <Section
      title="Webhooks"
      description="Sura signs each payload with an HMAC-SHA256 of its body, keyed with the endpoint's signing secret."
      action={webhooks.data && webhooks.data.length > 0 && addButton}
    >
      <QueryState
        query={webhooks}
        noun="webhooks"
        skeleton={<TableSkeleton rows={2} />}
        isEmpty={(rows) => rows.length === 0}
        empty={
          <EmptyState
            icon={WebhookIcon}
            title="No endpoints yet"
            description="Add an HTTPS endpoint, then send it a signed test delivery."
            action={addButton}
          />
        }
      >
        {(rows) => (
          <ul className="flex flex-col gap-3">
            {rows.map((webhook) => (
              <li key={webhook.webhook_id}>
                <WebhookRow
                  webhook={webhook}
                  onChanged={webhooks.retry}
                  onEdit={() => setDialog({ step: "edit", webhook })}
                  onSecret={(secret) => setDialog({ step: "secret", url: webhook.url, secret, rotated: true })}
                  onViewLogs={() => onViewLogs(webhook.webhook_id)}
                />
              </li>
            ))}
          </ul>
        )}
      </QueryState>

      <Dialog
        open={dialog !== null}
        onOpenChange={(open) => !open && setDialog(null)}
        title={dialogTitle(dialog)}
        description={
          dialog?.step === "secret" ? (
            <span className="font-mono break-all">{dialog.url}</span>
          ) : dialog?.step === "create" ? (
            "choose where sura should send events, and which ones."
          ) : undefined
        }
      >
        {dialog?.step === "secret" ? (
          <SecretView secret={dialog.secret} onDone={() => setDialog(null)}>
            <p className="text-sm font-semibold text-muted-foreground">
              {dialog.rotated
                ? "Deliveries are signed with this secret from now on. Update your verifier before the next one."
                : "Use this to verify that each delivery really came from Sura."}
            </p>
          </SecretView>
        ) : dialog ? (
          <WebhookForm
            key={dialog.step === "edit" ? dialog.webhook.webhook_id : "new"}
            webhook={dialog.step === "edit" ? dialog.webhook : undefined}
            onCancel={() => setDialog(null)}
            onCreated={(created) => {
              // the list refreshes behind the dialog while the secret is on screen
              setDialog({ step: "secret", url: created.url, secret: created.secret, rotated: false })
              webhooks.retry()
            }}
            onSaved={() => {
              setDialog(null)
              webhooks.retry()
            }}
          />
        ) : null}
      </Dialog>
    </Section>
  )
}

type WebhookFormProps = {
  // set when editing; absent when creating
  webhook?: Webhook
  onCancel: () => void
  onCreated: (created: { url: string; secret: string }) => void
  onSaved: () => void
}

function WebhookForm({ webhook, onCancel, onCreated, onSaved }: WebhookFormProps) {
  const prefix = webhook ? `webhook-${webhook.webhook_id}` : "webhook-new"
  const [url, setUrl] = useState(webhook?.url ?? "")
  const [events, setEvents] = useState<WebhookEvent[]>(webhook?.events ?? ["score.updated"])
  const [errors, setErrors] = useState<{ url?: string; events?: string }>({})
  const create = useMutation(createWebhook)
  const update = useMutation(updateWebhook)
  const pending = create.isPending || update.isPending
  const allChosen = events.length === webhookEvents.length

  function toggleEvent(event: WebhookEvent, checked: boolean) {
    setEvents((current) => (checked ? [...current, event] : current.filter((value) => value !== event)))
    if (errors.events) setErrors((current) => ({ ...current, events: undefined }))
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const nextErrors = { url: urlError(url), events: events.length ? undefined : "Choose at least one event" }
    setErrors(nextErrors)
    if (nextErrors.url || nextErrors.events) return

    const payload = { url: url.trim(), events }
    if (webhook) {
      const result = await update.mutate(webhook.webhook_id, payload)
      if (result.ok) onSaved()
    } else {
      const result = await create.mutate(payload)
      if (result.ok) onCreated({ url: result.data.url, secret: result.data.signing_secret })
    }
  }

  return (
    <form noValidate onSubmit={handleSubmit} className="flex flex-col gap-5">
      <Field id={`${prefix}-url`} label="Endpoint URL" error={errors.url}>
        <Input
          id={`${prefix}-url`}
          type="url"
          inputMode="url"
          autoFocus
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
        <div className="mb-2 flex items-center justify-between gap-3">
          <legend className="text-sm font-bold">Events</legend>
          <Button
            type="button"
            variant="link"
            size="sm"
            className="h-auto px-0"
            onClick={() => setEvents(allChosen ? [] : [...webhookEvents])}
          >
            {allChosen ? "Clear all" : "Select all"}
          </Button>
        </div>
        <div className="grid gap-3 sm:grid-cols-2">
          {webhookEvents.map((name) => (
            <Checkbox
              key={name}
              id={`${prefix}-event-${name}`}
              checked={events.includes(name)}
              onChange={(event) => toggleEvent(name, event.target.checked)}
              invalid={Boolean(errors.events)}
              label={<span className="font-mono text-xs font-bold text-foreground">{name}</span>}
            />
          ))}
        </div>
        <FieldError message={errors.events} />
      </fieldset>

      <ActionError error={create.error ?? update.error} />

      <div className="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
        <Button type="button" variant="ghost" onClick={onCancel} disabled={pending}>
          Cancel
        </Button>
        <Button type="submit" loading={pending}>
          {webhook ? "Save changes" : "Add endpoint"}
        </Button>
      </div>
    </form>
  )
}

type WebhookRowProps = {
  webhook: Webhook
  onChanged: () => void
  onEdit: () => void
  onSecret: (secret: string) => void
  onViewLogs: () => void
}

function WebhookRow({ webhook, onChanged, onEdit, onSecret, onViewLogs }: WebhookRowProps) {
  const [lastTest, setLastTest] = useState<WebhookDelivery | null>(null)
  const test = useMutation(testWebhook)
  const rotate = useMutation(rotateWebhookSecret)
  const enable = useMutation(updateWebhook)
  const disable = useMutation(disableWebhook)
  const active = webhook.status === "active"

  async function handleTest() {
    const result = await test.mutate(webhook.webhook_id)
    if (result.ok) setLastTest(result.data)
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

  return (
    <div className="card-raised flex flex-col gap-4 rounded-2xl p-4 sm:p-5">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <StatusBadge status={webhook.status} tone={active ? "indigo" : "neutral"} />
            <p className="min-w-0 font-mono text-sm font-bold break-all">{webhook.url}</p>
          </div>
          <ul className="mt-3 flex flex-wrap gap-1.5">
            {webhook.events.map((event) => (
              <li
                key={event}
                className="rounded-full border-2 border-hairline bg-card px-2.5 py-0.5 font-mono text-xs font-bold"
              >
                {event}
              </li>
            ))}
          </ul>
          <p className="mt-3 text-xs font-bold text-muted-foreground">
            Added {formatDateTime(webhook.created_at)}
            {webhook.updated_at && ` · updated ${formatDateTime(webhook.updated_at)}`}
          </p>
        </div>
        <div className="flex shrink-0 flex-wrap gap-2">
          <Button type="button" size="sm" onClick={handleTest} loading={test.isPending} disabled={!active}>
            Send test
          </Button>
          <Button type="button" size="sm" variant="outline" onClick={onViewLogs}>
            Logs
          </Button>
          <Button type="button" size="sm" variant="outline" onClick={onEdit}>
            Edit
          </Button>
          <ConfirmButton confirmLabel="Yes, rotate" loading={rotate.isPending} onConfirm={handleRotate}>
            Rotate secret
          </ConfirmButton>
          {active ? (
            <ConfirmButton confirmLabel="Yes, disable" variant="ghost" loading={disable.isPending} onConfirm={handleDisable}>
              Disable
            </ConfirmButton>
          ) : (
            <Button type="button" size="sm" variant="ghost" onClick={handleEnable} loading={enable.isPending}>
              Enable
            </Button>
          )}
        </div>
      </div>

      <ActionError error={test.error ?? rotate.error ?? enable.error ?? disable.error} />

      {lastTest && (
        <Alert
          variant="info"
          title={`Test delivered · ${lastTest.response_status ?? "no"} response`}
          action={
            <Button type="button" variant="outline" size="sm" onClick={onViewLogs}>
              View in logs
            </Button>
          }
        >
          {lastTest.response_summary}
        </Alert>
      )}
    </div>
  )
}
