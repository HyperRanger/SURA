"use client"

import { useState, type FormEvent, type ReactNode } from "react"
import { getCommitmentGroupHealth, openCommitmentCase, resolveCommitmentCase } from "@/actions/bank"
import { useBankAccess } from "@/hooks/use-bank-access"
import { useMutation } from "@/hooks/use-mutation"
import { useQuery } from "@/hooks/use-query"
import { ActionError } from "@/components/bank/action-kit"
import { Section } from "@/components/bank/page-header"
import { StatusBadge } from "@/components/bank/status-badge"
import { Alert } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { Field } from "@/components/ui/field"
import { Skeleton } from "@/components/ui/skeleton"
import { Textarea } from "@/components/ui/textarea"
import type { BankCommitment, CommitmentCase } from "@/types"
import { formatDateTime, formatNaira, formatPercent, humanize } from "@/utils/format"

const TEXT_MAX = 2000

// advisory and aggregate. it never names a member as risky or makes a lending call
export function GroupHealthPanel({ commitmentId, status }: { commitmentId: string; status: string }) {
  // the api refuses health for a cancelled lock, so it isn't asked
  const health = useQuery(getCommitmentGroupHealth, status === "cancelled" ? null : [commitmentId])

  if (status === "cancelled") return null

  return (
    <Section title="Group health" description="Advisory only. It never blocks a contribution or changes payout order.">
      {health.isLoading ? (
        <Skeleton className="h-36 rounded-2xl" />
      ) : health.error ? (
        <Alert variant="info" title="Group health isn't available">
          {health.error.message}
        </Alert>
      ) : health.data ? (
        <div className="card-raised flex flex-col gap-4 rounded-2xl p-4 sm:p-5">
          <div className="flex flex-wrap items-center gap-2">
            <StatusBadge status={health.data.group_health} />
            <StatusBadge status={health.data.confidence} label={`${health.data.confidence} confidence`} tone="neutral" />
          </div>
          <ul className="flex list-disc flex-col gap-1 pl-5 text-sm font-semibold text-muted-foreground">
            {health.data.reasons.map((reason) => (
              <li key={reason}>{reason}</li>
            ))}
          </ul>
          <dl className="grid grid-cols-2 gap-x-4 gap-y-3 sm:grid-cols-4">
            <Metric label="Joined" value={`${health.data.metrics.joined_member_count} of ${health.data.metrics.member_count}`} />
            <Metric label="Cycles paid" value={health.data.metrics.completed_cycles} />
            <Metric label="Cycles missed" value={health.data.metrics.missed_cycles} />
            <Metric label="Completion" value={formatPercent(health.data.metrics.historical_cycle_completion_rate)} />
            <Metric
              label="This cycle"
              value={`${formatNaira(health.data.metrics.current_cycle_contributed_total)} of ${formatNaira(health.data.metrics.current_cycle_required_total)}`}
            />
            <Metric label="Deadline" value={humanize(health.data.metrics.current_cycle_deadline_state)} />
            <Metric label="Due" value={formatDateTime(health.data.metrics.current_cycle_due_at)} />
            <Metric label="Grace" value={`${health.data.metrics.current_cycle_grace_period_hours}h`} />
          </dl>
          <p className="text-xs font-bold text-muted-foreground">{health.data.policy_note}</p>
        </div>
      ) : null}
    </Section>
  )
}

function Metric({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="min-w-0">
      <dt className="text-xs font-extrabold tracking-wide text-muted-foreground">{label}</dt>
      <dd className="mt-1 text-sm font-bold break-words">{value}</dd>
    </div>
  )
}

// a case pauses the lock for review without touching members, amounts or payout order
export function SupportCases({ commitment, onChanged }: { commitment: BankCommitment; onChanged: () => void }) {
  const { can } = useBankAccess()
  const canWrite = can("bank:commitments:write")
  const cases = commitment.support_cases ?? []
  const openCase = cases.find((item) => item.status === "open")
  // resolving a case sets the lock back to active, so a finished lock is never reopened
  const canOpen = canWrite && !openCase && (commitment.status === "active" || commitment.status === "pending_members")

  return (
    <Section title="Support cases" description="Opening a case puts the lock under review until it's resolved.">
      <div className="flex flex-col gap-4">
        {canOpen && <OpenCaseForm commitmentId={commitment.commitment_id} onOpened={onChanged} />}
        {cases.length === 0 && !canOpen && (
          <p className="rounded-2xl border-2 border-dashed border-hairline px-4 py-6 text-center text-sm font-semibold text-muted-foreground">
            No support cases on this lock.
          </p>
        )}
        {cases.map((item) => (
          <CaseCard
            key={item.case_id}
            commitmentId={commitment.commitment_id}
            item={item}
            canResolve={canWrite && item.status === "open"}
            onResolved={onChanged}
          />
        ))}
      </div>
    </Section>
  )
}

function OpenCaseForm({ commitmentId, onOpened }: { commitmentId: string; onOpened: () => void }) {
  const [reason, setReason] = useState("")
  const [error, setError] = useState<string>()
  const open = useMutation(openCommitmentCase)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!reason.trim()) {
      setError("Say what needs reviewing")
      return
    }
    const result = await open.mutate(commitmentId, reason.trim())
    if (result.ok) {
      setReason("")
      onOpened()
    }
  }

  return (
    <form noValidate onSubmit={handleSubmit} className="card-raised flex flex-col gap-4 rounded-2xl p-4 sm:p-5">
      <Field id="case-reason" label="Open a case" error={error} hint={`${reason.length} / ${TEXT_MAX}`}>
        <Textarea
          id="case-reason"
          rows={3}
          maxLength={TEXT_MAX}
          value={reason}
          onChange={(event) => {
            setReason(event.target.value)
            if (error) setError(undefined)
          }}
          aria-invalid={Boolean(error) || undefined}
          aria-describedby={error ? "case-reason-error" : "case-reason-hint"}
          placeholder="e.g. a member disputes a contribution"
        />
      </Field>
      <ActionError error={open.error} />
      <Button type="submit" loading={open.isPending} className="sm:self-start">
        Open case
      </Button>
    </form>
  )
}

type CaseCardProps = {
  commitmentId: string
  item: CommitmentCase
  canResolve: boolean
  onResolved: () => void
}

function CaseCard({ commitmentId, item, canResolve, onResolved }: CaseCardProps) {
  const [note, setNote] = useState("")
  const [error, setError] = useState<string>()
  const resolve = useMutation(resolveCommitmentCase)
  const noteId = `case-note-${item.case_id}`

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!note.trim()) {
      setError("Say how it was resolved")
      return
    }
    const result = await resolve.mutate(commitmentId, item.case_id, note.trim())
    if (result.ok) onResolved()
  }

  return (
    <div className="card-raised flex flex-col gap-3 rounded-2xl p-4 sm:p-5">
      <div className="flex flex-wrap items-center gap-2">
        <StatusBadge status={item.status} />
        <span className="text-xs font-bold text-muted-foreground">Opened {formatDateTime(item.opened_at)}</span>
        {item.resolved_at && (
          <span className="text-xs font-bold text-muted-foreground">· Resolved {formatDateTime(item.resolved_at)}</span>
        )}
      </div>
      <p className="text-sm font-semibold">{item.reason}</p>
      {item.resolution_note && (
        <blockquote className="border-l-4 border-hairline pl-3 text-sm font-semibold text-muted-foreground">
          {item.resolution_note}
        </blockquote>
      )}
      {canResolve && (
        <form noValidate onSubmit={handleSubmit} className="flex flex-col gap-3">
          <Field id={noteId} label="Resolution note" error={error}>
            <Textarea
              id={noteId}
              rows={2}
              maxLength={TEXT_MAX}
              value={note}
              onChange={(event) => {
                setNote(event.target.value)
                if (error) setError(undefined)
              }}
              aria-invalid={Boolean(error) || undefined}
              aria-describedby={error ? `${noteId}-error` : undefined}
              placeholder="What was checked and decided"
            />
          </Field>
          <ActionError error={resolve.error} />
          <Button type="submit" variant="outline" size="sm" loading={resolve.isPending} className="sm:self-start">
            Resolve and reactivate the lock
          </Button>
        </form>
      )}
    </div>
  )
}
