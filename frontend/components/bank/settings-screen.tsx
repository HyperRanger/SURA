"use client"

import { useState, type FormEvent } from "react"
import { HugeiconsIcon } from "@hugeicons/react"
import { PencilEdit02Icon } from "@hugeicons/core-free-icons"
import { getBankSettings, updateBankSettings } from "@/actions/bank"
import { useQuery } from "@/hooks/use-query"
import { useMutation } from "@/hooks/use-mutation"
import { ActionError } from "@/components/bank/action-kit"
import { SelectFilter } from "@/components/bank/filters"
import { DetailList, PageHeader, Section } from "@/components/bank/page-header"
import { QueryState } from "@/components/bank/query-state"
import { StatusBadge } from "@/components/bank/status-badge"
import { CodeBlock } from "@/components/shared/code-block"
import { Alert } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Dialog } from "@/components/ui/dialog"
import { Field } from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import { Skeleton } from "@/components/ui/skeleton"
import type { ApiEnvironment, BankSettings } from "@/types"
import { formatDateTime } from "@/utils/format"

const noArgs: [] = []
const RETENTION_MIN = 30
const RETENTION_MAX = 3650

const environmentOptions: { value: ApiEnvironment; label: string }[] = [
  { value: "sandbox", label: "sandbox" },
  { value: "live", label: "live" },
]

// B13
export function SettingsScreen() {
  const query = useQuery(getBankSettings, noArgs)

  return (
    <QueryState
      query={query}
      noun="settings"
      skeleton={
        <>
          <PageHeader title="settings" description="your bank's name, environment and data retention on sura." />
          <Skeleton className="h-40 rounded-2xl" />
        </>
      }
    >
      {(settings) => <SettingsView settings={settings} onSaved={query.setData} />}
    </QueryState>
  )
}

// what's set now, read only. editing happens in a dialog so the page stays a summary
function SettingsView({ settings, onSaved }: { settings: BankSettings; onSaved: (settings: BankSettings) => void }) {
  const [editing, setEditing] = useState(false)
  const [saved, setSaved] = useState(false)

  return (
    <>
      <PageHeader
        title="settings"
        description="your bank's name, environment and data retention on sura."
        actions={
          <Button type="button" title="change your bank's settings" onClick={() => setEditing(true)}>
            <HugeiconsIcon icon={PencilEdit02Icon} size={18} strokeWidth={2.2} />
            edit settings
          </Button>
        }
      />

      <div className="flex flex-col gap-10">
        {saved && (
          <Alert variant="info" title="settings saved">
            the change is recorded in your audit log.
          </Alert>
        )}

        <DetailList
          items={[
            { label: "bank name", value: settings.name },
            {
              label: "environment",
              value: <StatusBadge status={settings.environment} tone={settings.environment === "live" ? "gold" : "indigo"} />,
            },
            { label: "data retention", value: `${settings.retention_days} days` },
            { label: "last changed", value: formatDateTime(settings.updated_at) },
          ]}
        />

        <Section title="supported vendor categories" description="where your customers' locked savings can be spent.">
          {settings.supported_vendor_categories.length === 0 ? (
            <p className="rounded-2xl border-2 border-dashed border-hairline px-4 py-6 text-center text-sm font-semibold text-muted-foreground">
              no categories yet. add them from edit settings.
            </p>
          ) : (
            <ul className="flex flex-wrap gap-2">
              {settings.supported_vendor_categories.map((category) => (
                <li key={category}>
                  <Badge variant="outline" className="px-3.5 py-1.5 text-sm">
                    {category}
                  </Badge>
                </li>
              ))}
            </ul>
          )}
        </Section>

        <Section title="security settings" description="managed with sura during onboarding. read only here.">
          <CodeBlock code={JSON.stringify(settings.security_settings, null, 2)} />
        </Section>
      </div>

      <Dialog
        open={editing}
        onOpenChange={setEditing}
        title="edit settings"
        description="every change is written to your audit log."
        className="max-w-xl"
      >
        {/* keyed so reopening after a save starts from what the api now holds */}
        <SettingsForm
          key={settings.updated_at ?? "initial"}
          settings={settings}
          onCancel={() => setEditing(false)}
          onSaved={(next) => {
            onSaved(next)
            setSaved(true)
            setEditing(false)
          }}
        />
      </Dialog>
    </>
  )
}

type Errors = { name?: string; retention?: string }

type SettingsFormProps = {
  settings: BankSettings
  onSaved: (settings: BankSettings) => void
  onCancel: () => void
}

function SettingsForm({ settings, onSaved, onCancel }: SettingsFormProps) {
  const [name, setName] = useState(settings.name)
  const [environment, setEnvironment] = useState<ApiEnvironment | "">(settings.environment)
  const [retention, setRetention] = useState(String(settings.retention_days))
  const [categories, setCategories] = useState(settings.supported_vendor_categories.join(", "))
  const [errors, setErrors] = useState<Errors>({})
  const save = useMutation(updateBankSettings)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const days = Number(retention)
    const nextErrors: Errors = {
      name: name.trim() ? undefined : "enter your bank's name",
      retention:
        Number.isInteger(days) && days >= RETENTION_MIN && days <= RETENTION_MAX
          ? undefined
          : `choose between ${RETENTION_MIN} and ${RETENTION_MAX} days`,
    }
    setErrors(nextErrors)
    if (nextErrors.name || nextErrors.retention) return

    const result = await save.mutate({
      name: name.trim(),
      environment: environment || settings.environment,
      retention_days: days,
      supported_vendor_categories: categories
        .split(",")
        .map((value) => value.trim())
        .filter(Boolean),
    })
    if (result.ok) onSaved(result.data)
  }

  return (
    <form noValidate onSubmit={handleSubmit} className="flex flex-col gap-5">
      <div className="grid gap-4 sm:grid-cols-2">
        <Field id="settings-name" label="bank name" error={errors.name}>
          <Input
            id="settings-name"
            value={name}
            maxLength={160}
            onChange={(event) => setName(event.target.value)}
            invalid={Boolean(errors.name)}
            aria-describedby={errors.name ? "settings-name-error" : undefined}
            className="h-12 text-sm"
          />
        </Field>
        <Field
          id="settings-retention"
          label="data retention (days)"
          error={errors.retention}
          hint={`${RETENTION_MIN} to ${RETENTION_MAX} days`}
        >
          <Input
            id="settings-retention"
            type="number"
            inputMode="numeric"
            min={RETENTION_MIN}
            max={RETENTION_MAX}
            value={retention}
            onChange={(event) => setRetention(event.target.value)}
            invalid={Boolean(errors.retention)}
            aria-describedby={errors.retention ? "settings-retention-error" : "settings-retention-hint"}
            className="h-12 text-sm"
          />
        </Field>
      </div>

      <SelectFilter
        id="settings-environment"
        label="environment"
        value={environment}
        onChange={setEnvironment}
        options={environmentOptions}
        allLabel="choose"
        className="sm:w-full"
      />

      <Field id="settings-categories" label="supported vendor categories" hint="separate with commas">
        <Input
          id="settings-categories"
          value={categories}
          onChange={(event) => setCategories(event.target.value)}
          placeholder="e.g. electronics, school fees, groceries"
          aria-describedby="settings-categories-hint"
          className="h-12 text-sm"
        />
      </Field>

      <ActionError error={save.error} />

      <div className="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
        <Button type="button" variant="ghost" onClick={onCancel} disabled={save.isPending}>
          cancel
        </Button>
        <Button type="submit" loading={save.isPending}>
          save settings
        </Button>
      </div>
    </form>
  )
}
