"use client"

import Link from "next/link"
import { Audit01Icon, Flag02Icon, RepeatIcon } from "@hugeicons/core-free-icons"
import { getBankUser, getBankUserScore, listBankUserCommitments, listBankUserFlags } from "@/actions/bank"
import { routes } from "@/config/routes"
import { useBankAccess } from "@/hooks/use-bank-access"
import { useQuery } from "@/hooks/use-query"
import { DataTable, TableSkeleton, type Column } from "@/components/bank/data-table"
import { DetailList, PageHeader, Section } from "@/components/bank/page-header"
import { QueryState } from "@/components/bank/query-state"
import { ScoreDelta } from "@/components/bank/score-delta"
import { ScoreFigure, ScorePillars } from "@/components/bank/score-pillars"
import { StatusBadge } from "@/components/bank/status-badge"
import { AccountSafety, UserActivity } from "@/components/bank/user-safety"
import { EmptyState } from "@/components/shared/empty-state"
import { Alert } from "@/components/ui/alert"
import { buttonVariants } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import type { BankUserCommitment, BankUserProfile, RiskFlag, ScoreHistoryEntry } from "@/types"
import { formatDateTime, formatNaira, formatPercent, humanize } from "@/utils/format"

const historyColumns: Column<ScoreHistoryEntry>[] = [
  { header: "change", cell: (row) => row.reason ?? humanize(row.event_type) },
  { header: "event", cell: (row) => humanize(row.event_type) },
  { header: "points", cell: (row) => <ScoreDelta before={row.score_before} after={row.score} />, align: "right" },
  { header: "score", cell: (row) => row.score, align: "right" },
  { header: "when", cell: (row) => formatDateTime(row.computed_at) },
]

const commitmentColumns: Column<BankUserCommitment>[] = [
  { header: "commitment", cell: (row) => row.title },
  { header: "status", cell: (row) => <StatusBadge status={row.status} /> },
  { header: "payout slot", cell: (row) => (row.payout_cycle ? `cycle ${row.payout_cycle}` : "—") },
  { header: "payout", cell: (row) => <StatusBadge status={row.payout_status} /> },
  { header: "contributed", cell: (row) => formatNaira(row.contributed_amount), align: "right" },
  { header: "voucher", cell: (row) => <StatusBadge status={row.voucher_status} /> },
]

const flagColumns: Column<RiskFlag>[] = [
  { header: "rule", cell: (row) => humanize(row.rule) },
  { header: "severity", cell: (row) => <StatusBadge status={row.severity} /> },
  { header: "status", cell: (row) => <StatusBadge status={row.status} /> },
  { header: "raised", cell: (row) => formatDateTime(row.created_at) },
]

// B6. opening this screen is itself written to the bank's audit log
export function UserDetailScreen({ id }: { id: string }) {
  const profile = useQuery(getBankUser, [id])

  return (
    <QueryState query={profile} noun="this customer" skeleton={<ProfileSkeleton />}>
      {(user) => <UserDetail user={user} onChanged={profile.retry} />}
    </QueryState>
  )
}

function UserDetail({ user, onChanged }: { user: BankUserProfile; onChanged: () => void }) {
  const { can } = useBankAccess()
  const canReadFlags = can("bank:flags:read")
  const score = useQuery(getBankUserScore, [user.user_id])
  const flags = useQuery(listBankUserFlags, canReadFlags ? [user.user_id] : null)
  const commitments = useQuery(listBankUserCommitments, [user.user_id])
  const report = user.score_report

  return (
    <>
      <PageHeader
        title={user.name}
        backHref={routes.bank.users}
        backLabel="customers"
        actions={
          can("bank:settlements:read") && (
            <Link
              href={`${routes.bank.settlements}?user_id=${encodeURIComponent(user.user_id)}`}
              className={buttonVariants({ variant: "outline", size: "sm" })}
            >
              settlements
            </Link>
          )
        }
        meta={
          <>
            <StatusBadge status={user.verified ? "verified" : "unverified"} />
            {user.account_status !== "active" && <StatusBadge status={user.account_status} />}
            {user.context && <StatusBadge status={user.context} tone="neutral" />}
            <span className="font-mono text-xs font-semibold text-muted-foreground normal-case">{user.user_id}</span>
          </>
        }
      />

      <div className="flex flex-col gap-10">
        {user.open_flags > 0 && (
          <Alert variant="error" title={`${user.open_flags} open risk ${user.open_flags === 1 ? "flag" : "flags"}`}>
            this customer is under account review until an analyst resolves them below.
          </Alert>
        )}

        <div className="grid gap-4 lg:grid-cols-[minmax(0,2fr)_minmax(0,3fr)]">
          <div className="card-raised rounded-2xl p-5">
            <p className="text-xs font-extrabold tracking-wide text-muted-foreground">sura score</p>
            <div className="mt-2">
              <ScoreFigure report={report} />
            </div>
            <div className="mt-3 flex flex-wrap items-center gap-2">
              <StatusBadge status={report.tier} />
              {report.score_version && (
                <span className="font-mono text-xs font-semibold text-muted-foreground normal-case">{report.score_version}</span>
              )}
            </div>
            <p className="mt-3 text-xs font-bold text-muted-foreground">
              computed {formatDateTime(user.score_computed_at)}
            </p>
            {!user.score_processing_consent && (
              <p className="mt-3 text-xs font-bold text-destructive">score processing consent not on record.</p>
            )}
          </div>
          <div className="card-raised rounded-2xl p-5">
            <p className="mb-4 text-xs font-extrabold tracking-wide text-muted-foreground">five pillars</p>
            <ScorePillars report={report} />
          </div>
        </div>

        <DetailList
          items={[
            { label: "bank reference", value: <span className="font-mono normal-case">{user.bank_customer_id ?? "—"}</span> },
            { label: "phone", value: <span className="font-mono normal-case">{user.phone ?? "—"}</span> },
            { label: "banks with", value: user.source_institution?.name ?? "—" },
            { label: "commitments joined", value: user.commitments_joined },
            { label: "active commitments", value: user.active_commitments },
            { label: "contributions", value: user.contribution_count },
            { label: "on-time rate", value: formatPercent(user.on_time_contribution_rate) },
            {
              label: "float eligibility",
              value: (
                <span className="flex flex-col gap-1">
                  <StatusBadge status={user.float_eligibility} />
                  <span className="text-xs font-semibold text-muted-foreground">{user.float_eligibility_reason}</span>
                </span>
              ),
            },
          ]}
        />

        {canReadFlags && (
          <Section title="flags" description="fraud rules that fired for this customer.">
            <QueryState
              query={flags}
              noun="flags"
              skeleton={<TableSkeleton rows={2} />}
              isEmpty={(rows) => rows.length === 0}
              empty={<EmptyState icon={Flag02Icon} title="no flags" description="no fraud rule has fired for this customer." />}
            >
              {(rows) => (
                <DataTable
                  caption="risk flags"
                  columns={flagColumns}
                  rows={rows}
                  rowKey={(row) => row.flag_id}
                  rowHref={(row) => routes.bank.flag(row.flag_id)}
                />
              )}
            </QueryState>
          </Section>
        )}

        <AccountSafety user={user} flags={flags.data} onChanged={onChanged} />

        <Section title="score audit log" description="every change to this score, newest first, with the event that caused it.">
          <QueryState
            query={score}
            noun="score history"
            skeleton={<TableSkeleton rows={4} />}
            isEmpty={(data) => data.history.length === 0}
            empty={<EmptyState icon={Audit01Icon} title="no score changes yet" />}
          >
            {(data) => (
              <DataTable caption="score history" columns={historyColumns} rows={data.history} rowKey={(row) => row.id} />
            )}
          </QueryState>
        </Section>

        <Section title="commitments">
          <QueryState
            query={commitments}
            noun="commitments"
            skeleton={<TableSkeleton rows={2} />}
            isEmpty={(rows) => rows.length === 0}
            empty={<EmptyState icon={RepeatIcon} title="no commitments yet" />}
          >
            {(rows) => (
              <DataTable
                caption="customer commitments"
                columns={commitmentColumns}
                rows={rows}
                rowKey={(row) => row.commitment_id}
                rowHref={(row) => routes.bank.commitment(row.commitment_id)}
              />
            )}
          </QueryState>
        </Section>

        <UserActivity userId={user.user_id} />
      </div>
    </>
  )
}

function ProfileSkeleton() {
  return (
    <>
      <Skeleton className="mb-3 h-5 w-28" />
      <Skeleton className="mb-8 h-10 w-64" />
      <div className="grid gap-4 lg:grid-cols-[2fr_3fr]">
        <Skeleton className="h-48 rounded-2xl" />
        <Skeleton className="h-48 rounded-2xl" />
      </div>
    </>
  )
}
