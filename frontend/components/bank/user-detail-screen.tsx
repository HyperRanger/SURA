"use client"

import Link from "next/link"
import { Audit01Icon, Flag02Icon, RepeatIcon } from "@hugeicons/core-free-icons"
import { getBankUser, getBankUserScore, listBankUserCommitments, listBankUserFlags } from "@/actions/bank"
import { customerTabs, isCustomerTab, type CustomerTab } from "@/config/bank"
import { routes } from "@/config/routes"
import { useBankAccess } from "@/hooks/use-bank-access"
import { useQuery } from "@/hooks/use-query"
import { useUrlTab } from "@/hooks/use-url-tab"
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
import { Tabs, TabsCount, TabsList, TabsPanel, TabsTab } from "@/components/ui/tabs"
import type { BankUserCommitment, BankUserProfile, RiskFlag, ScoreHistoryEntry } from "@/types"
import { formatDateTime, formatNaira, formatPercent, humanize } from "@/utils/format"

const historyColumns: Column<ScoreHistoryEntry>[] = [
  { header: "Change", cell: (row) => row.reason ?? humanize(row.event_type) },
  { header: "Event", cell: (row) => humanize(row.event_type) },
  { header: "Points", cell: (row) => <ScoreDelta before={row.score_before} after={row.score} />, align: "right" },
  { header: "Score", cell: (row) => row.score, align: "right" },
  { header: "When", cell: (row) => formatDateTime(row.computed_at) },
]

const commitmentColumns: Column<BankUserCommitment>[] = [
  { header: "Commitment", cell: (row) => row.title },
  { header: "Status", cell: (row) => <StatusBadge status={row.status} /> },
  { header: "Payout slot", cell: (row) => (row.payout_cycle ? `Cycle ${row.payout_cycle}` : "—") },
  { header: "Payout", cell: (row) => <StatusBadge status={row.payout_status} /> },
  { header: "Contributed", cell: (row) => formatNaira(row.contributed_amount), align: "right" },
  { header: "Voucher", cell: (row) => <StatusBadge status={row.voucher_status} /> },
]

const flagColumns: Column<RiskFlag>[] = [
  { header: "Rule", cell: (row) => humanize(row.rule) },
  { header: "Severity", cell: (row) => <StatusBadge status={row.severity} /> },
  { header: "Status", cell: (row) => <StatusBadge status={row.status} /> },
  { header: "Raised", cell: (row) => formatDateTime(row.created_at) },
]

// B6. opening this screen is itself written to the bank's audit log. each part of
// the profile sits in its own tab; the open one lives in ?tab=
export function UserDetailScreen({ id, initialTab }: { id: string; initialTab?: CustomerTab }) {
  const profile = useQuery(getBankUser, [id])

  return (
    <QueryState query={profile} noun="this customer" skeleton={<ProfileSkeleton />}>
      {(user) => <UserDetail user={user} initialTab={initialTab} onChanged={profile.retry} />}
    </QueryState>
  )
}

type UserDetailProps = {
  user: BankUserProfile
  initialTab?: CustomerTab
  onChanged: () => void
}

function UserDetail({ user, initialTab, onChanged }: UserDetailProps) {
  const { can } = useBankAccess()
  const canReadFlags = can("bank:flags:read")
  // matches AccountSafety, which renders for either flag permission
  const canSeeSafety = canReadFlags || can("bank:flags:write")
  const tabs = customerTabs.filter(
    (item) => (item.value !== "flags" || canReadFlags) && (item.value !== "safety" || canSeeSafety)
  )
  const [tab, setTab] = useUrlTab<CustomerTab>(
    initialTab && tabs.some((item) => item.value === initialTab) ? initialTab : "overview"
  )
  const score = useQuery(getBankUserScore, [user.user_id])
  const flags = useQuery(listBankUserFlags, canReadFlags ? [user.user_id] : null)
  const commitments = useQuery(listBankUserCommitments, [user.user_id])
  const report = user.score_report
  const counts: Partial<Record<CustomerTab, { value: number; alert?: boolean }>> = {
    ...(commitments.data && { commitments: { value: commitments.data.length } }),
    ...(user.open_flags > 0 && { flags: { value: user.open_flags, alert: true } }),
  }

  return (
    <>
      <PageHeader
        title={user.name}
        backHref={routes.bank.users}
        backLabel="Customers"
        actions={
          can("bank:settlements:read") && (
            <Link
              href={`${routes.bank.settlements}?user_id=${encodeURIComponent(user.user_id)}`}
              className={buttonVariants({ variant: "outline", size: "sm" })}
            >
              Settlements
            </Link>
          )
        }
        meta={
          <>
            <StatusBadge status={user.verified ? "verified" : "unverified"} />
            {user.account_status !== "active" && <StatusBadge status={user.account_status} />}
            {user.context && <StatusBadge status={user.context} tone="neutral" />}
            <span className="font-mono text-xs font-semibold text-muted-foreground">{user.user_id}</span>
          </>
        }
      />

      {user.open_flags > 0 && (
        <Alert
          variant="error"
          title={`${user.open_flags} open risk ${user.open_flags === 1 ? "flag" : "flags"}`}
          className="mb-6"
        >
          This customer is under account review until an analyst resolves them
          {canReadFlags && tab !== "flags" ? (
            <>
              {" "}in the{" "}
              <button
                type="button"
                title="Open the flags tab"
                onClick={() => setTab("flags")}
                className="cursor-pointer font-bold underline underline-offset-4"
              >
                Flags tab
              </button>
              .
            </>
          ) : (
            "."
          )}
        </Alert>
      )}

      <Tabs value={tab} onValueChange={(value) => isCustomerTab(value) && setTab(value)}>
        <TabsList aria-label="Customer sections">
          {tabs.map((item) => {
            const count = counts[item.value]
            return (
              <TabsTab key={item.value} value={item.value} title={`Show ${item.label.toLowerCase()}`}>
                {item.label}
                {count && <TabsCount alert={count.alert}>{count.value}</TabsCount>}
              </TabsTab>
            )
          })}
        </TabsList>

        <TabsPanel value="overview">
          <div className="flex flex-col gap-10">
            <div className="grid gap-4 lg:grid-cols-[minmax(0,2fr)_minmax(0,3fr)]">
              <div className="card-raised rounded-2xl p-5">
                <p className="text-xs font-bold tracking-wide text-muted-foreground">Sura score</p>
                <div className="mt-2">
                  <ScoreFigure report={report} />
                </div>
                <div className="mt-3 flex flex-wrap items-center gap-2">
                  <StatusBadge status={report.tier} />
                  {report.score_version && (
                    <span className="font-mono text-xs font-semibold text-muted-foreground">{report.score_version}</span>
                  )}
                </div>
                <p className="mt-3 text-xs font-bold text-muted-foreground">
                  Computed {formatDateTime(user.score_computed_at)}
                </p>
                {!user.score_processing_consent && (
                  <p className="mt-3 text-xs font-bold text-destructive">Score processing consent not on record.</p>
                )}
              </div>
              <div className="card-raised rounded-2xl p-5">
                <p className="mb-4 text-xs font-bold tracking-wide text-muted-foreground">Five pillars</p>
                <ScorePillars report={report} />
              </div>
            </div>

            <DetailList
              items={[
                { label: "Bank reference", value: <span className="font-mono">{user.bank_customer_id ?? "—"}</span> },
                { label: "Phone", value: <span className="font-mono">{user.phone ?? "—"}</span> },
                { label: "Banks with", value: user.source_institution?.name ?? "—" },
                { label: "Commitments joined", value: user.commitments_joined },
                { label: "Active commitments", value: user.active_commitments },
                { label: "Contributions", value: user.contribution_count },
                { label: "On-time rate", value: formatPercent(user.on_time_contribution_rate) },
                {
                  label: "Float eligibility",
                  value: (
                    <span className="flex flex-col gap-1">
                      <StatusBadge status={user.float_eligibility} />
                      <span className="text-xs font-semibold text-muted-foreground">{user.float_eligibility_reason}</span>
                    </span>
                  ),
                },
              ]}
            />
          </div>
        </TabsPanel>

        <TabsPanel value="commitments">
          <Section title="Commitments">
            <QueryState
              query={commitments}
              noun="commitments"
              skeleton={<TableSkeleton rows={2} />}
              isEmpty={(rows) => rows.length === 0}
              empty={<EmptyState icon={RepeatIcon} title="No commitments yet" />}
            >
              {(rows) => (
                <DataTable
                  caption="Customer commitments"
                  columns={commitmentColumns}
                  rows={rows}
                  rowKey={(row) => row.commitment_id}
                  rowHref={(row) => routes.bank.commitment(row.commitment_id)}
                />
              )}
            </QueryState>
          </Section>
        </TabsPanel>

        <TabsPanel value="score-history">
          <Section title="Score audit log" description="Every change to this score, newest first, with the event that caused it.">
            <QueryState
              query={score}
              noun="score history"
              skeleton={<TableSkeleton rows={4} />}
              isEmpty={(data) => data.history.length === 0}
              empty={<EmptyState icon={Audit01Icon} title="No score changes yet" />}
            >
              {(data) => (
                <DataTable caption="Score history" columns={historyColumns} rows={data.history} rowKey={(row) => row.id} />
              )}
            </QueryState>
          </Section>
        </TabsPanel>

        {canReadFlags && (
          <TabsPanel value="flags">
            <Section title="Flags" description="Fraud rules that fired for this customer.">
              <QueryState
                query={flags}
                noun="flags"
                skeleton={<TableSkeleton rows={2} />}
                isEmpty={(rows) => rows.length === 0}
                empty={<EmptyState icon={Flag02Icon} title="No flags" description="No fraud rule has fired for this customer." />}
              >
                {(rows) => (
                  <DataTable
                    caption="Risk flags"
                    columns={flagColumns}
                    rows={rows}
                    rowKey={(row) => row.flag_id}
                    rowHref={(row) => routes.bank.flag(row.flag_id)}
                  />
                )}
              </QueryState>
            </Section>
          </TabsPanel>
        )}

        {canSeeSafety && (
          <TabsPanel value="safety">
            <AccountSafety user={user} flags={flags.data} onChanged={onChanged} />
          </TabsPanel>
        )}

        <TabsPanel value="activity">
          <UserActivity userId={user.user_id} />
        </TabsPanel>
      </Tabs>
    </>
  )
}

function ProfileSkeleton() {
  return (
    <>
      <Skeleton className="mb-3 h-5 w-28" />
      <Skeleton className="mb-8 h-10 w-64" />
      <Skeleton className="mb-8 h-10 w-full max-w-xl rounded-xl" />
      <div className="grid gap-4 lg:grid-cols-[2fr_3fr]">
        <Skeleton className="h-48 rounded-2xl" />
        <Skeleton className="h-48 rounded-2xl" />
      </div>
    </>
  )
}
