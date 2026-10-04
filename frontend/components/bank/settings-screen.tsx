"use client"

import { useState, type FormEvent } from "react"
import { getBankSettings, updateBankSettings } from "@/actions/bank"
import { useQuery } from "@/hooks/use-query"
import { useMutation } from "@/hooks/use-mutation"
import { ActionError } from "@/components/bank/action-kit"
import { SelectFilter } from "@/components/bank/filters"
import { PageHeader, Section } from "@/components/bank/page-header"
import { QueryState } from "@/components/bank/query-state"
import { StatusBadge } from "@/components/bank/status-badge"
import { CodeBlock } from "@/components/shared/code-block"
import { Alert } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
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
    <>
      <PageHeader title="settings" description="your bank's name, environment and data retention on sura." />
      <QueryState query={query} noun="settings" skeleton={<Skeleton className="h-72 rounded-2xl" />}>
        {(settings) => <SettingsForm key={settings.updated_at ?? "initial"} settings={settings} onSaved={query.setData} />}
      </QueryState>
    </>
  )
}

type Errors = { name?: string; retention?: string }

function SettingsForm({ settings, onSaved }: { settings: BankSettings; onSaved: (settings: BankSettings) => void }) {
  const [name, setName] = useState(settings.name)
  const [environment, setEnvironment] = useState<ApiEnvironment | "">(settings.environment)
  const [retention, setRetention] = useState(String(settings.retention_days))
  const [categories, setCategories] = useState(settings.supported_vendor_categories.join(", "))
  const [errors, setErrors] = useState<Errors>({})
  const [saved, setSaved] = useState(false)
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
    setSaved(false)
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
    if (result.ok) {
      setSaved(true)
      onSaved(result.data)
    }
  }

  return (
    <div className="flex flex-col gap-10">
      <form noValidate onSubmit={handleSubmit} className="card-raised flex flex-col gap-5 rounded-2xl p-4 sm:p-5">
        <div className="flex flex-wrap items-center gap-2">
          <StatusBadge status={settings.environment} label={`${settings.environment} environment`} />
          <span className="text-xs font-bold text-muted-foreground">last changed {formatDateTime(settings.updated_at)}</span>
        </div>

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
          className="sm:w-72"
        />

        <Field id="settings-categories" label="supported vendor categories" hint="separate with commas">
          <Input
            id="settings-categories"
            value={categories}
            onChange={(event) => setCategories(event.target.value)}
            placeholder="e.g. electronics, school fees, groceries"
            className="h-12 text-sm"
          />
        </Field>

        <ActionError error={save.error} />
        {saved && <Alert variant="info" title="settings saved">the change is recorded in your audit log.</Alert>}

        <Button type="submit" loading={save.isPending} className="sm:self-start">
          save settings
        </Button>
      </form>

      <Section title="security settings" description="managed with sura during onboarding. read only here.">
        <CodeBlock code={JSON.stringify(settings.security_settings, null, 2)} />
      </Section>
    </div>
  )
}
