"use client"

import { useState, type FormEvent } from "react"
import Link from "next/link"
import { getFlag, resolveFlag } from "@/actions/bank"
import { flagActions } from "@/config/bank"
import { routes } from "@/config/routes"
import { useBankAccess } from "@/hooks/use-bank-access"
import { useMutation } from "@/hooks/use-mutation"
import { useQuery } from "@/hooks/use-query"
import { DetailList, PageHeader, Section } from "@/components/bank/page-header"
import { QueryState } from "@/components/bank/query-state"
import { StatusBadge } from "@/components/bank/status-badge"
import { Timeline, type TimelineItem } from "@/components/bank/timeline"
import { Alert } from "@/components/ui/alert"
import { Button, buttonVariants } from "@/components/ui/button"
import { Field } from "@/components/ui/field"
import { Skeleton } from "@/components/ui/skeleton"
import { cn } from "@/lib/utils"
import type { FlagAction, RiskFlagDetail } from "@/types"
import { formatDateTime, humanize } from "@/utils/format"

const NOTE_MAX = 1000

// B9
export function FlagDetailScreen({ id }: { id: string }) {
  const query = useQuery(getFlag, [id])

  return (
    <QueryState query={query} noun="this flag" skeleton={<FlagSkeleton />}>
      {(flag) => <FlagDetail flag={flag} onResolved={query.retry} />}
    </QueryState>
  )
}

function FlagDetail({ flag, onResolved }: { flag: RiskFlagDetail; onResolved: () => void }) {
  const { can } = useBankAccess()
  const evidence = Object.entries(flag.evidence)
  // an escalated flag is still undecided, so it can be confirmed or dismissed later
  const reviewable = flag.status === "open" || flag.status === "escalated"

  const timeline: TimelineItem[] = [
    ...flag.review_history.map((event, index) => ({
      id: `review-${index}`,
      title: humanize(typeof event.details.action === "string" ? `flag ${event.details.action}` : event.event_type),
      detail: <span className="font-mono text-xs normal-case">{event.actor_id}</span>,
      at: event.occurred_at,
    })),
    { id: "raised", title: `raised by ${humanize(flag.rule)}`, detail: "sura fraud rules", at: flag.created_at },
  ]

  return (
    <>
      <PageHeader
        title={humanize(flag.rule)}
        backHref={routes.bank.flags}
        backLabel="risk flags"
        meta={
          <>
            <StatusBadge status={flag.status} />
            <StatusBadge status={flag.severity} label={`${flag.severity} severity`} />
          </>
        }
        actions={
          <Link href={routes.bank.user(flag.user_id)} className={buttonVariants({ variant: "outline", size: "sm" })}>
            view customer
          </Link>
        }
      />

      <div className="flex flex-col gap-10">
        {flag.status === "open" && (
          <Alert variant="error" title="waiting for review">
            this customer is under account review until an analyst dismisses, confirms or escalates the flag.
          </Alert>
        )}

        <DetailList
          items={[
            {
              label: "customer",
              value: (
                <Link href={routes.bank.user(flag.user_id)} className="font-mono text-link normal-case underline-offset-4 hover:underline">
                  {flag.user_id}
                </Link>
              ),
            },
            { label: "raised", value: formatDateTime(flag.created_at) },
            { label: "resolved", value: formatDateTime(flag.resolved_at) },
            { label: "flag id", value: <span className="font-mono text-xs normal-case">{flag.flag_id}</span> },
          ]}
        />

        <Section title="evidence" description="the signals that made the rule fire.">
          {evidence.length === 0 ? (
            <p className="rounded-2xl border-2 border-dashed border-hairline px-4 py-6 text-center text-sm font-semibold text-muted-foreground">
              no evidence was attached to this flag.
            </p>
          ) : (
            <dl className="card-raised divide-y divide-hairline rounded-2xl">
              {evidence.map(([key, value]) => (
                <div key={key} className="flex flex-col gap-1 px-4 py-3 sm:flex-row sm:gap-6">
                  <dt className="text-sm font-extrabold sm:w-56 sm:shrink-0">{humanize(key)}</dt>
                  <dd className="min-w-0 font-mono text-sm break-words text-muted-foreground normal-case">
                    {typeof value === "string" ? value : JSON.stringify(value)}
                  </dd>
                </div>
              ))}
            </dl>
          )}
        </Section>

        {flag.resolution_note && (
          <Section title="analyst note">
            <blockquote className="card-raised rounded-2xl p-4 text-sm leading-relaxed font-semibold normal-case">
              {flag.resolution_note}
            </blockquote>
          </Section>
        )}

        {reviewable && can("bank:flags:write") && (
          <Section title="review" description="your decision and note are written to the audit log.">
            <ResolveForm flagId={flag.flag_id} onResolved={onResolved} />
          </Section>
        )}

        <Section title="timeline">
          <Timeline items={timeline} empty="no history yet." />
        </Section>
      </div>
    </>
  )
}

function ResolveForm({ flagId, onResolved }: { flagId: string; onResolved: () => void }) {
  const [action, setAction] = useState<FlagAction | null>(null)
  const [note, setNote] = useState("")
  const [noteError, setNoteError] = useState<string>()
  const resolve = useMutation(resolveFlag)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!action) return
    if (!note.trim()) {
      setNoteError("say why, so the next analyst can follow your reasoning")
      return
    }
    const result = await resolve.mutate(flagId, { action, note: note.trim() })
    if (result.ok) onResolved()
  }

  const chosen = flagActions.find((option) => option.value === action)

  return (
    <form noValidate onSubmit={handleSubmit} className="card-raised flex flex-col gap-5 rounded-2xl p-4 sm:p-5">
      <fieldset>
        <legend className="mb-2 text-sm font-extrabold">decision</legend>
        <div className="grid gap-2 sm:grid-cols-3">
          {flagActions.map((option) => (
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
                name="flag-action"
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

      <Field id="flag-note" label="note" error={noteError} hint={`${note.length} / ${NOTE_MAX}`}>
        <textarea
          id="flag-note"
          rows={4}
          maxLength={NOTE_MAX}
          value={note}
          onChange={(event) => {
            setNote(event.target.value)
            if (noteError) setNoteError(undefined)
          }}
          aria-invalid={Boolean(noteError) || undefined}
          aria-describedby={noteError ? "flag-note-error" : "flag-note-hint"}
          placeholder="what you checked and why you decided this"
          className="w-full rounded-2xl border-2 border-b-4 border-hairline bg-card px-4 py-3 text-sm font-semibold normal-case outline-none placeholder:font-normal placeholder:text-muted-foreground/70 placeholder:lowercase hover:border-hairline-strong focus-visible:border-ring focus-visible:ring-4 focus-visible:ring-ring/15 aria-invalid:border-destructive"
        />
      </Field>

      {resolve.error && (
        <Alert variant="error">
          {resolve.error.is(403) ? "your role can't resolve flags. ask a bank administrator." : resolve.error.message}
        </Alert>
      )}

      <Button
        type="submit"
        loading={resolve.isPending}
        disabled={!action}
        variant={action === "dismissed" ? "outline" : "default"}
        className="sm:self-start"
      >
        {chosen ? `${chosen.label} this flag` : "choose a decision"}
      </Button>
    </form>
  )
}

function FlagSkeleton() {
  return (
    <>
      <Skeleton className="mb-3 h-5 w-28" />
      <Skeleton className="mb-8 h-10 w-64" />
      <Skeleton className="mb-10 h-24 rounded-2xl" />
      <Skeleton className="h-40 rounded-2xl" />
    </>
  )
}
