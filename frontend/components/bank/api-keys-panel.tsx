"use client"

import { useState, type FormEvent } from "react"
import { HugeiconsIcon } from "@hugeicons/react"
import { Add01Icon, Key01Icon, SentIcon } from "@hugeicons/core-free-icons"
import { createApiKey, listApiKeys, revokeApiKey, rotateApiKey } from "@/actions/bank"
import { apiKeyScopes } from "@/config/bank"
import { useMutation } from "@/hooks/use-mutation"
import { useQuery } from "@/hooks/use-query"
import { ActionError, ConfirmButton, SecretView } from "@/components/bank/action-kit"
import { DataTable, TableSkeleton, type Column } from "@/components/bank/data-table"
import { Section } from "@/components/bank/page-header"
import { QueryState } from "@/components/bank/query-state"
import { StatusBadge } from "@/components/bank/status-badge"
import { EmptyState } from "@/components/shared/empty-state"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { ChoiceCards } from "@/components/ui/choice-cards"
import { DatePicker } from "@/components/ui/date-picker"
import { Dialog } from "@/components/ui/dialog"
import { Field, FieldError } from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import type { ApiEnvironment, ApiKey, ApiKeyScope, ApiKeyWithSecret } from "@/types"
import { formatDateTime } from "@/utils/format"

const environmentOptions: { value: ApiEnvironment; label: string; description: string }[] = [
  { value: "sandbox", label: "Sandbox", description: "For building and testing against demo data." },
  { value: "live", label: "Live", description: "For production systems reading real customers." },
]

const noArgs: [] = []

function keyStatus(key: ApiKey, now: number) {
  if (key.revoked_at) return "revoked"
  if (key.expires_at && new Date(key.expires_at).getTime() <= now) return "expired"
  return "active"
}

// the api stores expiry in utc. a picked day lasts until the end of that day, locally
function expiryFromDate(date: string) {
  return date ? new Date(`${date}T23:59:59`).toISOString() : undefined
}

// what the dialog is showing: the create form, or a secret straight after create or rotate
type DialogState = { step: "create" } | { step: "secret"; key: ApiKeyWithSecret } | null

// B11. machine credentials for the bank's own systems. a secret is shown once,
// straight after create or rotate, and sura keeps only its hash
// onTryKey hands a fresh secret to the playground, so the first request is one click away
export function ApiKeysPanel({ onTryKey }: { onTryKey?: (secret: string) => void }) {
  const keys = useQuery(listApiKeys, noArgs)
  const rotate = useMutation(rotateApiKey)
  const revoke = useMutation(revokeApiKey)
  const [dialog, setDialog] = useState<DialogState>(null)
  const [busyKey, setBusyKey] = useState<string | null>(null)
  const [now] = useState(() => Date.now())

  async function handleRotate(key: ApiKey) {
    setBusyKey(key.key_id)
    const result = await rotate.mutate(key.key_id)
    setBusyKey(null)
    if (result.ok) {
      setDialog({ step: "secret", key: result.data })
      keys.retry()
    }
  }

  async function handleRevoke(key: ApiKey) {
    setBusyKey(key.key_id)
    const result = await revoke.mutate(key.key_id)
    setBusyKey(null)
    // 204: nothing comes back, so the list is the source of truth
    if (result.ok) keys.retry()
  }

  const createButton = (
    <Button type="button" size="sm" onClick={() => setDialog({ step: "create" })}>
      <HugeiconsIcon icon={Add01Icon} size={18} strokeWidth={2.4} />
      Create API key
    </Button>
  )

  const columns: Column<ApiKey>[] = [
    { header: "Name", cell: (row) => row.name },
    { header: "Key", cell: (row) => <span className="font-mono text-xs">{row.prefix}••••</span> },
    {
      header: "Scopes",
      cell: (row) => <span className="font-mono text-xs">{row.scopes.join(", ")}</span>,
    },
    { header: "Environment", cell: (row) => <StatusBadge status={row.environment} /> },
    { header: "Status", cell: (row) => <StatusBadge status={keyStatus(row, now)} /> },
    { header: "Created", cell: (row) => formatDateTime(row.created_at) },
    { header: "Last used", cell: (row) => (row.last_used_at ? formatDateTime(row.last_used_at) : "Never") },
    {
      header: "Manage",
      align: "right",
      wide: true,
      cell: (row) =>
        keyStatus(row, now) === "revoked" ? null : (
          <div className="relative z-10 flex flex-wrap gap-2 md:justify-end">
            <ConfirmButton
              confirmLabel="Yes, rotate"
              loading={rotate.isPending && busyKey === row.key_id}
              disabled={busyKey !== null && busyKey !== row.key_id}
              onConfirm={() => handleRotate(row)}
            >
              Rotate
            </ConfirmButton>
            <ConfirmButton
              confirmLabel="Yes, revoke"
              variant="ghost"
              loading={revoke.isPending && busyKey === row.key_id}
              disabled={busyKey !== null && busyKey !== row.key_id}
              onConfirm={() => handleRevoke(row)}
            >
              Revoke
            </ConfirmButton>
          </div>
        ),
    },
  ]

  return (
    <Section
      title="API keys"
      description="Authenticate your servers' requests with X-Sura-API-Key. Never share or expose a key publicly."
      action={keys.data && keys.data.length > 0 && createButton}
    >
      <div className="flex flex-col gap-4">
        <ActionError error={rotate.error ?? revoke.error} />

        <QueryState
          query={keys}
          noun="API keys"
          skeleton={<TableSkeleton rows={2} />}
          isEmpty={(rows) => rows.length === 0}
          empty={
            <EmptyState
              icon={Key01Icon}
              title="No API keys yet"
              description="Create a sandbox key to make your first machine request."
              action={createButton}
            />
          }
        >
          {(rows) => <DataTable caption="API keys" columns={columns} rows={rows} rowKey={(row) => row.key_id} />}
        </QueryState>
      </div>

      <Dialog
        open={dialog !== null}
        onOpenChange={(open) => !open && setDialog(null)}
        title={
          dialog?.step === "secret"
            ? dialog.key.rotated_key_id
              ? `New secret for ${dialog.key.name}`
              : `${dialog.key.name} is ready`
            : "Create API key"
        }
        description={dialog?.step === "create" ? "Scope each key to what that one system needs." : undefined}
      >
        {dialog?.step === "secret" ? (
          <SecretView secret={dialog.key.secret} onDone={() => setDialog(null)}>
            {dialog.key.rotated_key_id && (
              <p className="text-sm font-semibold text-muted-foreground">
                The old key stopped working the moment this one was issued.
              </p>
            )}
            {onTryKey && (
              <Button
                type="button"
                variant="outline"
                title="Make a live request with this key"
                onClick={() => {
                  onTryKey(dialog.key.secret)
                  setDialog(null)
                }}
                className="sm:self-start"
              >
                <HugeiconsIcon icon={SentIcon} size={18} strokeWidth={2.2} />
                Try it in the playground
              </Button>
            )}
          </SecretView>
        ) : (
          <CreateKeyForm
            onCancel={() => setDialog(null)}
            onCreated={(key) => {
              setDialog({ step: "secret", key })
              keys.retry()
            }}
          />
        )}
      </Dialog>
    </Section>
  )
}

type CreateKeyFormProps = {
  onCreated: (key: ApiKeyWithSecret) => void
  onCancel: () => void
}

function CreateKeyForm({ onCreated, onCancel }: CreateKeyFormProps) {
  const [name, setName] = useState("")
  const [scopes, setScopes] = useState<ApiKeyScope[]>(["score:read"])
  const [environment, setEnvironment] = useState<ApiEnvironment>("sandbox")
  const [expiry, setExpiry] = useState("")
  const [errors, setErrors] = useState<{ name?: string; scopes?: string }>({})
  const create = useMutation(createApiKey)

  function toggleScope(scope: ApiKeyScope, checked: boolean) {
    setScopes((current) => (checked ? [...current, scope] : current.filter((value) => value !== scope)))
    if (errors.scopes) setErrors((current) => ({ ...current, scopes: undefined }))
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const nextErrors = {
      name: name.trim() ? undefined : "Name the system that will use this key",
      scopes: scopes.length ? undefined : "Choose at least one scope",
    }
    setErrors(nextErrors)
    if (nextErrors.name || nextErrors.scopes) return

    const result = await create.mutate({
      name: name.trim(),
      scopes,
      environment,
      expires_at: expiryFromDate(expiry),
    })
    if (result.ok) onCreated(result.data)
  }

  return (
    <form noValidate onSubmit={handleSubmit} className="flex flex-col gap-5">
      <Field id="key-name" label="Name" error={errors.name}>
        <Input
          id="key-name"
          value={name}
          maxLength={120}
          autoFocus
          onChange={(event) => {
            setName(event.target.value)
            if (errors.name) setErrors((current) => ({ ...current, name: undefined }))
          }}
          invalid={Boolean(errors.name)}
          aria-describedby={errors.name ? "key-name-error" : undefined}
          placeholder="e.g. loan origination sandbox"
          className="h-12 text-sm"
        />
      </Field>

      <div className="flex flex-col gap-2">
        <span id="key-environment-label" className="text-sm font-extrabold">
          Environment
        </span>
        <ChoiceCards
          name="key-environment"
          labelledBy="key-environment-label"
          options={environmentOptions}
          value={environment}
          onChange={setEnvironment}
          className="grid sm:grid-cols-2"
        />
      </div>

      <fieldset>
        <legend className="mb-2 text-sm font-extrabold">Scopes</legend>
        <div className="flex flex-col gap-3">
          {apiKeyScopes.map((scope) => (
            <Checkbox
              key={scope.value}
              id={`key-scope-${scope.value}`}
              checked={scopes.includes(scope.value)}
              onChange={(event) => toggleScope(scope.value, event.target.checked)}
              invalid={Boolean(errors.scopes)}
              label={
                <>
                  <span className="font-mono font-extrabold text-foreground">{scope.label}</span>
                  <span className="block text-xs">{scope.description}</span>
                </>
              }
            />
          ))}
        </div>
        <FieldError message={errors.scopes} />
      </fieldset>

      <Field id="key-expiry" label="Expires (optional)" hint="Leave empty for a key that never expires.">
        <DatePicker
          id="key-expiry"
          value={expiry}
          onChange={setExpiry}
          placeholder="Never expires"
          aria-describedby="key-expiry-hint"
          // a key can't expire before today
          disabled={(date) => date < new Date(new Date().setHours(0, 0, 0, 0))}
        />
      </Field>

      <ActionError error={create.error} />

      <div className="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
        <Button type="button" variant="ghost" onClick={onCancel} disabled={create.isPending}>
          Cancel
        </Button>
        <Button type="submit" loading={create.isPending}>
          Create key
        </Button>
      </div>
    </form>
  )
}
