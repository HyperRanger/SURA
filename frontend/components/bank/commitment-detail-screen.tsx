"use client"

import Link from "next/link"
import { LockIcon } from "@hugeicons/core-free-icons"
import { getBankCommitment } from "@/actions/bank"
import { commitmentTabs, isCommitmentTab, type CommitmentTab } from "@/config/bank"
import { routes } from "@/config/routes"
import { useBankAccess } from "@/hooks/use-bank-access"
import { useQuery } from "@/hooks/use-query"
import { useUrlTab } from "@/hooks/use-url-tab"
import { GroupHealthPanel, SupportCases } from "@/components/bank/commitment-review"
import { DataTable, TableSkeleton, type Column } from "@/components/bank/data-table"
import { DetailList, PageHeader, Section } from "@/components/bank/page-header"
import { QueryState } from "@/components/bank/query-state"
import { StatusBadge } from "@/components/bank/status-badge"
import { Timeline } from "@/components/bank/timeline"
import { Alert } from "@/components/ui/alert"
import { buttonVariants } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { Tabs, TabsCount, TabsList, TabsPanel, TabsTab } from "@/components/ui/tabs"
import type { BankCommitment } from "@/types"
import { formatDateTime, formatNaira, humanize } from "@/utils/format"

type Member = BankCommitment["members"][number]
type Payout = BankCommitment["payout_schedule"][number]
type Contribution = BankCommitment["contributions"][number]

// B4. each part of the lock sits in its own tab; the open one lives in ?tab=
export function CommitmentDetailScreen({ id, initialTab }: { id: string; initialTab?: CommitmentTab }) {
  const query = useQuery(getBankCommitment, [id])

  return (
    <QueryState query={query} noun="this commitment" skeleton={<DetailSkeleton />}>
      {(commitment) => <CommitmentDetail commitment={commitment} initialTab={initialTab} onChanged={query.retry} />}
    </QueryState>
  )
}

type CommitmentDetailProps = {
  commitment: BankCommitment
  initialTab?: CommitmentTab
  onChanged: () => void
}

function CommitmentDetail({ commitment, initialTab, onChanged }: CommitmentDetailProps) {
  const { can } = useBankAccess()
  const underReview = commitment.status === "under_review"
  // a lock under review opens on its support case, since that's what needs doing
  const [tab, setTab] = useUrlTab<CommitmentTab>(initialTab ?? (underReview ? "support" : "overview"))
  const openCases = (commitment.support_cases ?? []).filter((item) => item.status === "open").length
  const counts: Partial<Record<CommitmentTab, { value: number; alert?: boolean }>> = {
    members: { value: commitment.members.length },
    contributions: { value: commitment.contributions.length },
    ...(openCases > 0 && { support: { value: openCases, alert: true } }),
  }
  const names = new Map(commitment.members.map((member) => [member.user_id, member.name]))
  const nameOf = (userId: string) => names.get(userId) ?? userId
  const totalContributed = commitment.contributions.reduce((sum, row) => sum + row.amount, 0)

  const memberColumns: Column<Member>[] = [
    { header: "Member", cell: (row) => row.name },
    { header: "Role", cell: (row) => humanize(row.role) },
    { header: "Score", cell: (row) => row.score, align: "right" },
    { header: "Tier", cell: (row) => <StatusBadge status={row.tier} /> },
    { header: "Joined", cell: (row) => formatDateTime(row.joined_at) },
  ]

  const payoutColumns: Column<Payout>[] = [
    { header: "Cycle", cell: (row) => `Cycle ${row.cycle_number}` },
    { header: "Beneficiary", cell: (row) => nameOf(row.beneficiary_id) },
    { header: "Amount", cell: (row) => formatNaira(row.amount), align: "right" },
    { header: "Payout", cell: (row) => <StatusBadge status={row.status} /> },
    { header: "Voucher", cell: (row) => <StatusBadge status={row.voucher_status} /> },
    { header: "Settlement", cell: (row) => <StatusBadge status={row.settlement_status} /> },
  ]

  const contributionColumns: Column<Contribution>[] = [
    { header: "Member", cell: (row) => nameOf(row.user_id) },
    { header: "Cycle", cell: (row) => row.cycle_number, align: "right" },
    { header: "Amount", cell: (row) => formatNaira(row.amount), align: "right" },
    { header: "Status", cell: (row) => <StatusBadge status={row.status} /> },
    { header: "Paid", cell: (row) => formatDateTime(row.paid_at) },
  ]

  return (
    <>
      <PageHeader
        title={commitment.title}
        backHref={routes.bank.commitments}
        backLabel="Commitments"
        meta={
          <>
            <StatusBadge status={commitment.status} />
            <StatusBadge status={commitment.type} tone="neutral" />
            <span className="font-mono text-xs font-semibold text-muted-foreground">
              {commitment.commitment_id}
            </span>
          </>
        }
        actions={
          can("bank:settlements:read") && (
            <Link
              href={`${routes.bank.settlements}?commitment_id=${encodeURIComponent(commitment.commitment_id)}`}
              className={buttonVariants({ variant: "outline", size: "sm" })}
            >
              Settlements
            </Link>
          )
        }
      />

      {underReview && (
        <Alert variant="error" title="Under review" className="mb-6">
          A support case is open. Contributions and payouts wait until it&apos;s resolved
          {tab === "support" ? (
            " below."
          ) : (
            <>
              {" "}in the{" "}
              <button
                type="button"
                title="Open the support tab"
                onClick={() => setTab("support")}
                className="cursor-pointer font-extrabold underline underline-offset-4"
              >
                Support tab
              </button>
              .
            </>
          )}
        </Alert>
      )}

      <Tabs value={tab} onValueChange={(value) => isCommitmentTab(value) && setTab(value)}>
        <TabsList aria-label="Commitment sections">
          {commitmentTabs.map((item) => {
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
            <DetailList
              items={[
                { label: "Locked vendor", value: commitment.vendor.name ?? commitment.vendor.vendor_id },
                { label: "Contribution", value: `${formatNaira(commitment.contribution_amount)} ${humanize(commitment.frequency).toLowerCase()}` },
                { label: "Cycles done", value: `${commitment.completed_cycle_count} of ${commitment.cycles}` },
                { label: "Current cycle", value: commitment.current_cycle_number },
                { label: "Contributed so far", value: formatNaira(totalContributed) },
                { label: "Members", value: commitment.members.length },
                { label: "Created", value: formatDateTime(commitment.created_at) },
              ]}
            />
            <GroupHealthPanel commitmentId={commitment.commitment_id} status={commitment.status} />
          </div>
        </TabsPanel>

        <TabsPanel value="payouts">
          <div className="flex flex-col gap-10">
            <PayoutDecision commitment={commitment} nameOf={nameOf} />
            <Section title="Payout schedule" description="Who receives each cycle's pool, and where that voucher is now.">
              <DataTable
                caption="Payout schedule"
                columns={payoutColumns}
                rows={commitment.payout_schedule}
                rowKey={(row) => String(row.cycle_number)}
              />
            </Section>
          </div>
        </TabsPanel>

        <TabsPanel value="members">
          <Section title="Members" description="Bank staff may see scores here. Members never see each other's.">
            <DataTable
              caption="Members"
              columns={memberColumns}
              rows={commitment.members}
              rowKey={(row) => row.user_id}
              rowHref={(row) => routes.bank.user(row.user_id)}
            />
          </Section>
        </TabsPanel>

        <TabsPanel value="contributions">
          <Section title="Contributions" description={`${formatNaira(totalContributed)} paid in so far.`}>
            {commitment.contributions.length === 0 ? (
              <p className="rounded-2xl border-2 border-dashed border-hairline px-4 py-6 text-center text-sm font-semibold text-muted-foreground">
                No contributions recorded yet.
              </p>
            ) : (
              <DataTable
                caption="Contributions"
                columns={contributionColumns}
                rows={commitment.contributions}
                rowKey={(row) => row.contribution_id}
              />
            )}
          </Section>
        </TabsPanel>

        <TabsPanel value="support">
          <SupportCases commitment={commitment} onChanged={onChanged} />
        </TabsPanel>

        <TabsPanel value="activity">
          <Section title="Activity">
            <Timeline
              items={commitment.activity.map((item) => ({
                id: item.activity_id,
                title: humanize(item.type),
                detail: [nameOf(item.actor_user_id), item.cycle_number ? `Cycle ${item.cycle_number}` : null]
                  .filter(Boolean)
                  .join(" · "),
                at: item.occurred_at,
              }))}
              empty="Nothing has happened on this commitment yet."
            />
          </Section>
        </TabsPanel>
      </Tabs>
    </>
  )
}

// the anchor and cap rule (trd 5.1). the api stores the resulting order and amounts,
// not the decision itself, so this explains what the persisted schedule shows
function PayoutDecision({ commitment, nameOf }: { commitment: BankCommitment; nameOf: (id: string) => string }) {
  const [first, ...later] = commitment.payout_schedule
  const regular = later.length ? Math.max(...later.map((row) => row.amount)) : null
  const capped = first && regular !== null && first.amount < regular

  return (
    <Section title="Payout order and cap">
      <div className="flex flex-col gap-3">
        {commitment.payout_order.length > 0 && (
          <ol className="card-raised flex flex-wrap gap-2 rounded-2xl p-4">
            {commitment.payout_order.map((userId, index) => (
              <li key={`${userId}-${index}`} className="flex items-center gap-2 rounded-full bg-cloud py-1 pr-3 pl-1 text-sm font-bold">
                <span className="flex size-6 items-center justify-center rounded-full bg-primary text-xs font-black text-primary-foreground">
                  {index + 1}
                </span>
                {nameOf(userId)}
              </li>
            ))}
          </ol>
        )}
        {!first ? (
          <Alert variant="info" title="No payout schedule yet">
            The schedule is fixed once every invited member has joined.
          </Alert>
        ) : capped ? (
          <Alert variant="gold" icon={LockIcon} title={`Cycle 1 is capped at ${formatNaira(first.amount)}`}>
            Later cycles pay {formatNaira(regular)}. A group where nobody has history above the entry tier chooses its own
            order, and its first payout is capped, so a stranger can&apos;t take the first pool and leave.
          </Alert>
        ) : (
          <Alert variant="info" title="No first-payout cap">
            Every cycle pays the same pool. In a group where someone already had history above the entry tier, early
            slots go to members by score, highest first.
          </Alert>
        )}
      </div>
    </Section>
  )
}

function DetailSkeleton() {
  return (
    <>
      <Skeleton className="mb-3 h-5 w-28" />
      <Skeleton className="mb-8 h-10 w-72" />
      <Skeleton className="mb-8 h-10 w-full max-w-xl rounded-xl" />
      <Skeleton className="mb-10 h-32 rounded-2xl" />
      <TableSkeleton rows={4} />
    </>
  )
}
