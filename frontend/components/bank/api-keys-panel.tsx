"use client"

import { useState, type FormEvent } from "react"
import { Key01Icon } from "@hugeicons/core-free-icons"
import { createApiKey, listApiKeys, revokeApiKey, rotateApiKey } from "@/actions/bank"
import { apiKeyScopes } from "@/config/bank"
import { useMutation } from "@/hooks/use-mutation"
import { useQuery } from "@/hooks/use-query"
import { ActionError, ConfirmButton, SecretReveal } from "@/components/bank/action-kit"
import { DataTable, TableSkeleton, type Column } from "@/components/bank/data-table"
import { SelectFilter } from "@/components/bank/filters"
import { Section } from "@/components/bank/page-header"
import { QueryState } from "@/components/bank/query-state"
import { StatusBadge } from "@/components/bank/status-badge"
import { EmptyState } from "@/components/shared/empty-state"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { Field, FieldError } from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import type { ApiEnvironment, ApiKey, ApiKeyScope, ApiKeyWithSecret } from "@/types"
import { formatDateTime } from "@/utils/format"

const environmentOptions: { value: ApiEnvironment; label: string }[] = [
  { value: "sandbox", label: "sandbox" },
  { value: "live", label: "live" },
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

// B11. machine credentials for the bank's own systems. a secret is shown once,
// straight after create or rotate, and sura keeps only its hash
export function ApiKeysPanel() {
  const keys = useQuery(listApiKeys, noArgs)
  const rotate = useMutation(rotateApiKey)
  const revoke = useMutation(revokeApiKey)
  const [revealed, setRevealed] = useState<ApiKeyWithSecret | null>(null)
  const [busyKey, setBusyKey] = useState<string | null>(null)
  const [now] = useState(() => Date.now())

  async function handleRotate(key: ApiKey) {
    setBusyKey(key.key_id)
    const result = await rotate.mutate(key.key_id)
    setBusyKey(null)
    if (result.ok) {
      setRevealed(result.data)
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

  const columns: Column<ApiKey>[] = [
    { header: "name", cell: (row) => <span className="normal-case">{row.name}</span> },
    { header: "key", cell: (row) => <span className="font-mono text-xs normal-case">{row.prefix}…</span> },
    { header: "status", cell: (row) => <StatusBadge status={keyStatus(row, now)} /> },
    { header: "environment", cell: (row) => <StatusBadge status={row.environment} /> },
    {
      header: "scopes",
      cell: (row) => <span className="font-mono text-xs normal-case">{row.scopes.join(", ")}</span>,
    },
    { header: "last used", cell: (row) => formatDateTime(row.last_used_at) },
    { header: "expires", cell: (row) => (row.expires_at ? formatDateTime(row.expires_at) : "never") },
    {
      header: "actions",
      cell: (row) =>
        keyStatus(row, now) === "revoked" ? (
          <span className="text-xs font-bold text-muted-foreground">revoked {formatDateTime(row.revoked_at)}</span>
        ) : (
          <div className="relative z-10 flex flex-wrap gap-2">
            <ConfirmButton
              confirmLabel="yes, rotate"
              loading={rotate.isPending && busyKey === row.key_id}
              disabled={busyKey !== null && busyKey !== row.key_id}
              onConfirm={() => handleRotate(row)}
            >
              rotate
            </ConfirmButton>
            <ConfirmButton
              confirmLabel="yes, revoke"
              variant="ghost"
              loading={revoke.isPending && busyKey === row.key_id}
              disabled={busyKey !== null && busyKey !== row.key_id}
              onConfirm={() => handleRevoke(row)}
            >
              revoke
            </ConfirmButton>
          </div>
        ),
    },
  ]

  return (
    <Section
      title="api keys"
      description="for your servers, sent as X-Sura-API-Key. scope each key to what that system needs."
    >
      <div className="flex flex-col gap-4">
        {revealed && (
          <SecretReveal
            title={revealed.rotated_key_id ? `new secret for ${revealed.name}` : `secret for ${revealed.name}`}
            secret={revealed.secret}
            onDismiss={() => setRevealed(null)}
          >
            {revealed.rotated_key_id && (
              <p className="mt-2">the old key stopped working the moment this one was issued.</p>
            )}
          </SecretReveal>
        )}

        <CreateKeyForm
          onCreated={(key) => {
            setRevealed(key)
            keys.retry()
          }}
        />

        <ActionError error={rotate.error ?? revoke.error} />

        <QueryState
          query={keys}
          noun="api keys"
          skeleton={<TableSkeleton rows={2} />}
          isEmpty={(rows) => rows.length === 0}
          empty={
            <EmptyState
              icon={Key01Icon}
              title="no api keys yet"
              description="create a sandbox key above to make your first machine request."
            />
          }
        >
          {(rows) => <DataTable caption="api keys" columns={columns} rows={rows} rowKey={(row) => row.key_id} />}
        </QueryState>
      </div>
    </Section>
  )
}

function CreateKeyForm({ onCreated }: { onCreated: (key: ApiKeyWithSecret) => void }) {
  const [name, setName] = useState("")
  const [scopes, setScopes] = useState<ApiKeyScope[]>(["score:read"])
  const [environment, setEnvironment] = useState<ApiEnvironment | "">("sandbox")
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
      name: name.trim() ? undefined : "name the system that will use this key",
      scopes: scopes.length ? undefined : "choose at least one scope",
    }
    setErrors(nextErrors)
    if (nextErrors.name || nextErrors.scopes) return

    const result = await create.mutate({
      name: name.trim(),
      scopes,
      environment: environment || "sandbox",
      expires_at: expiryFromDate(expiry),
    })
    if (result.ok) {
      setName("")
      setExpiry("")
      onCreated(result.data)
    }
  }

  return (
    <form noValidate onSubmit={handleSubmit} className="card-raised flex flex-col gap-5 rounded-2xl p-4 sm:p-5">
      <div className="grid gap-4 sm:grid-cols-[minmax(0,2fr)_minmax(0,1fr)_minmax(0,1fr)] sm:items-end">
        <Field id="key-name" label="key name" error={errors.name}>
          <Input
            id="key-name"
            value={name}
            maxLength={120}
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
        <SelectFilter
          id="key-environment"
          label="environment"
          value={environment}
          onChange={setEnvironment}
          options={environmentOptions}
          allLabel="choose"
          className="sm:w-auto"
        />
        <Field id="key-expiry" label="expires (optional)">
          <Input id="key-expiry" type="date" value={expiry} onChange={(event) => setExpiry(event.target.value)} className="h-12 text-sm" />
        </Field>
      </div>

      <fieldset>
        <legend className="mb-2 text-sm font-extrabold">scopes</legend>
        <div className="grid gap-3 sm:grid-cols-2">
          {apiKeyScopes.map((scope) => (
            <Checkbox
              key={scope.value}
              id={`key-scope-${scope.value}`}
              checked={scopes.includes(scope.value)}
              onChange={(event) => toggleScope(scope.value, event.target.checked)}
              invalid={Boolean(errors.scopes)}
              label={
                <>
                  <span className="font-mono font-extrabold text-foreground normal-case">{scope.label}</span>
                  <span className="block text-xs">{scope.description}</span>
                </>
              }
            />
          ))}
        </div>
        <FieldError message={errors.scopes} />
      </fieldset>

      <ActionError error={create.error} />

      <Button type="submit" loading={create.isPending} className="sm:self-start">
        create key
      </Button>
    </form>
  )
}
