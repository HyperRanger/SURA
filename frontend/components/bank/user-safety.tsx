"use client"

import { useState, type FormEvent } from "react"
import { ShieldUserIcon } from "@hugeicons/core-free-icons"
import {
  applyBankUserRestriction,
  listBankUserActivity,
  listBankUserRestrictions,
  revokeBankUserSessions,
} from "@/actions/bank"
import { restrictionActions } from "@/config/bank"
import { useBankAccess } from "@/hooks/use-bank-access"
import { useMutation } from "@/hooks/use-mutation"
import { useQuery } from "@/hooks/use-query"
import { ActionError, ConfirmButton } from "@/components/bank/action-kit"
import { DataTable, TableSkeleton, type Column } from "@/components/bank/data-table"
import { Section } from "@/components/bank/page-header"
import { QueryState } from "@/components/bank/query-state"
import { StatusBadge } from "@/components/bank/status-badge"
import { Timeline } from "@/components/bank/timeline"
import { EmptyState } from "@/components/shared/empty-state"
import { Alert } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { Field } from "@/components/ui/field"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Skeleton } from "@/components/ui/skeleton"
import { Textarea } from "@/components/ui/textarea"
import { cn } from "@/lib/utils"
import type { BankUserActivity, BankUserProfile, Restriction, RestrictionAction, RiskFlag } from "@/types"
import { formatDateTime, humanize } from "@/utils/format"

const REASON_MAX = 1000

const restrictionColumns: Column<Restriction>[] = [
  { header: "Action", cell: (row) => <StatusBadge status={row.action} /> },
  { header: "Reason", cell: (row) => row.reason },
  {
    header: "Flag",
    cell: (row) => <span className="font-mono text-xs">{row.flag_id ?? "—"}</span>,
  },
  { header: "By", cell: (row) => <span className="font-mono text-xs">{row.actor_id}</span> },
  { header: "When", cell: (row) => formatDateTime(row.created_at) },
]

// the actions that make sense from where the account is now
function actionsFor(status: BankUserProfile["account_status"]) {
  return restrictionActions.filter((option) =>
    status === "active" ? option.value !== "reinstated" : option.value !== status
  )
}

type AccountSafetyProps = {
  user: BankUserProfile
  flags: RiskFlag[] | null
  onChanged: () => void
}

// restrictions are explicit human decisions with an audit trail. rules only open flags
export function AccountSafety({ user, flags, onChanged }: AccountSafetyProps) {
  const { can } = useBankAccess()
  const canRead = can("bank:flags:read")
  const canWrite = can("bank:flags:write")
  const history = useQuery(listBankUserRestrictions, canRead ? [user.user_id] : null)
  const revoke = useMutation(revokeBankUserSessions)
  const [revokedAt, setRevokedAt] = useState<string | null>(null)

  if (!canRead && !canWrite) return null

  async function handleRevoke() {
    const result = await revoke.mutate(user.user_id)
    if (result.ok) setRevokedAt(result.data.at)
  }

  return (
    <Section
      title="Account safety"
      description="Restrict, suspend or reinstate this customer. Each decision is written to the audit log."
      action={
        canWrite && (
          <ConfirmButton confirmLabel="Yes, sign them out" loading={revoke.isPending} onConfirm={handleRevoke}>
            Revoke sessions
          </ConfirmButton>
        )
      }
    >
      <div className="flex flex-col gap-4">
        <div className="card-raised flex flex-wrap items-center gap-3 rounded-2xl p-4">
          <span className="text-sm font-extrabold">Account status</span>
          <StatusBadge status={user.account_status} />
          {user.restriction_reason && (
            <span className="text-sm font-semibold text-muted-foreground">{user.restriction_reason}</span>
          )}
        </div>

        <ActionError error={revoke.error} />
        {revokedAt && (
          <Alert variant="info" title="Every session ended">
            The customer has to sign in again on every device. Revoked {formatDateTime(revokedAt)}.
          </Alert>
        )}

        {canWrite && (
          <RestrictionForm
            user={user}
            flags={flags}
            onApplied={() => {
              history.retry()
              onChanged()
            }}
          />
        )}

        {canRead && (
          <QueryState
            query={history}
            noun="restriction history"
            skeleton={<TableSkeleton rows={2} />}
            isEmpty={(rows) => rows.length === 0}
            empty={
              <EmptyState
                icon={ShieldUserIcon}
                title="No restrictions on record"
                description="This account has never been restricted or suspended."
              />
            }
          >
            {(rows) => (
              <DataTable
                caption="Restriction history"
                columns={restrictionColumns}
                rows={rows}
                rowKey={(row) => row.restriction_id}
              />
            )}
          </QueryState>
        )}
      </div>
    </Section>
  )
}

function RestrictionForm({
  user,
  flags,
  onApplied,
}: {
  user: BankUserProfile
  flags: RiskFlag[] | null
  onApplied: () => void
}) {
  const options = actionsFor(user.account_status)
  const [action, setAction] = useState<RestrictionAction | null>(null)
  const [reason, setReason] = useState("")
  const [flagId, setFlagId] = useState("")
  const [reasonError, setReasonError] = useState<string>()
  const apply = useMutation(applyBankUserRestriction)
  const chosen = options.find((option) => option.value === action)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!action) return
    if (!reason.trim()) {
      setReasonError("Say why, so the decision can be reviewed later")
      return
    }
    const result = await apply.mutate(user.user_id, {
      action,
      reason: reason.trim(),
      flag_id: flagId || undefined,
    })
    if (result.ok) {
      setAction(null)
      setReason("")
      setFlagId("")
      onApplied()
    }
  }

  return (
    <form noValidate onSubmit={handleSubmit} className="card-raised flex flex-col gap-5 rounded-2xl p-4 sm:p-5">
      <fieldset>
        <legend className="mb-2 text-sm font-extrabold">Decision</legend>
        <div className={cn("grid gap-2", options.length === 3 ? "sm:grid-cols-3" : "sm:grid-cols-2")}>
          {options.map((option) => (
            <label
              key={option.value}
              className={cn(
                "flex cursor-pointer flex-col gap-1 rounded-2xl border-2 border-b-4 border-hairline bg-card p-3 transition-colors hover:border-hairline-strong",
                "has-[:focus-visible]:ring-4 has-[:focus-visible]:ring-ring/20",
                action === option.value && "border-ring bg-indigo-soft hover:border-ring"
              )}
            >
              <input
                type="radio"
                name="restriction-action"
                value={option.value}
                checked={action === option.value}
                onChange={() => setAction(option.value)}
                className="sr-only"
              />
              <span className="text-sm font-black">{option.label}</span>
              <span className="text-xs leading-snug font-semibold text-muted-foreground">{option.description}</span>
            </label>
          ))}
        </div>
      </fieldset>

      {flags && flags.length > 0 && (
        <Field id="restriction-flag" label="Linked flag (optional)">
          <Select
            items={[
              { value: null, label: "No flag" },
              ...flags.map((flag) => ({ value: flag.flag_id, label: `${humanize(flag.rule)} · ${flag.status}` })),
            ]}
            value={flagId || null}
            onValueChange={(next) => setFlagId(next ?? "")}
          >
            <SelectTrigger id="restriction-flag" title="Link this decision to a risk flag">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value={null}>No flag</SelectItem>
              {flags.map((flag) => (
                <SelectItem key={flag.flag_id} value={flag.flag_id}>
                  {humanize(flag.rule)} · {flag.status}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </Field>
      )}

      <Field id="restriction-reason" label="Reason" error={reasonError} hint={`${reason.length} / ${REASON_MAX}`}>
        <Textarea
          id="restriction-reason"
          rows={3}
          maxLength={REASON_MAX}
          value={reason}
          onChange={(event) => {
            setReason(event.target.value)
            if (reasonError) setReasonError(undefined)
          }}
          aria-invalid={Boolean(reasonError) || undefined}
          aria-describedby={reasonError ? "restriction-reason-error" : "restriction-reason-hint"}
          placeholder="What you saw and why this account should change"
        />
      </Field>

      <ActionError error={apply.error} />

      <Button
        type="submit"
        loading={apply.isPending}
        disabled={!action}
        variant={action === "reinstated" ? "outline" : "default"}
        className="sm:self-start"
      >
        {chosen ? `${chosen.label} this account` : "Choose a decision"}
      </Button>
    </form>
  )
}

function activityDetail(event: BankUserActivity) {
  if (event.reason) return event.reason
  if (!event.details) return null
  const parts = Object.entries(event.details)
    .filter(([, value]) => value !== null && typeof value !== "object")
    .map(([key, value]) => `${humanize(key)}: ${String(value)}`)
  return parts.length ? parts.join(" · ") : null
}

// score changes, lock events, consent and flags for one customer, newest first
export function UserActivity({ userId }: { userId: string }) {
  const activity = useQuery(listBankUserActivity, [userId])

  return (
    <Section title="Activity" description="Score changes, lock events, consent and flags, newest first.">
      <QueryState query={activity} noun="activity" skeleton={<Skeleton className="h-40 rounded-2xl" />}>
        {(events) => (
          <Timeline
            items={events.slice(0, 50).map((event) => ({
              id: `${event.type}-${event.id}`,
              title: humanize(event.type),
              detail: activityDetail(event),
              at: event.occurred_at,
            }))}
            empty="Nothing has happened on this account yet."
          />
        )}
      </QueryState>
    </Section>
  )
}
