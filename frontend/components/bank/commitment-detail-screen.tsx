"use client"

import Link from "next/link"
import { LockIcon } from "@hugeicons/core-free-icons"
import { getBankCommitment } from "@/actions/bank"
import { routes } from "@/config/routes"
import { useBankAccess } from "@/hooks/use-bank-access"
import { useQuery } from "@/hooks/use-query"
import { GroupHealthPanel, SupportCases } from "@/components/bank/commitment-review"
import { DataTable, TableSkeleton, type Column } from "@/components/bank/data-table"
import { DetailList, PageHeader, Section } from "@/components/bank/page-header"
import { QueryState } from "@/components/bank/query-state"
import { StatusBadge } from "@/components/bank/status-badge"
import { Timeline } from "@/components/bank/timeline"
import { Alert } from "@/components/ui/alert"
import { buttonVariants } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import type { BankCommitment } from "@/types"
import { formatDateTime, formatNaira, humanize } from "@/utils/format"

type Member = BankCommitment["members"][number]
type Payout = BankCommitment["payout_schedule"][number]
type Contribution = BankCommitment["contributions"][number]

// B4
export function CommitmentDetailScreen({ id }: { id: string }) {
  const query = useQuery(getBankCommitment, [id])

  return (
    <QueryState query={query} noun="this commitment" skeleton={<DetailSkeleton />}>
      {(commitment) => <CommitmentDetail commitment={commitment} onChanged={query.retry} />}
    </QueryState>
  )
}

function CommitmentDetail({ commitment, onChanged }: { commitment: BankCommitment; onChanged: () => void }) {
  const { can } = useBankAccess()
  const names = new Map(commitment.members.map((member) => [member.user_id, member.name]))
  const nameOf = (userId: string) => names.get(userId) ?? userId
  const totalContributed = commitment.contributions.reduce((sum, row) => sum + row.amount, 0)

  const memberColumns: Column<Member>[] = [
    { header: "member", cell: (row) => row.name },
    { header: "role", cell: (row) => humanize(row.role) },
    { header: "score", cell: (row) => row.score, align: "right" },
    { header: "tier", cell: (row) => <StatusBadge status={row.tier} /> },
    { header: "joined", cell: (row) => formatDateTime(row.joined_at) },
  ]

  const payoutColumns: Column<Payout>[] = [
    { header: "cycle", cell: (row) => `cycle ${row.cycle_number}` },
    { header: "beneficiary", cell: (row) => nameOf(row.beneficiary_id) },
    { header: "amount", cell: (row) => formatNaira(row.amount), align: "right" },
    { header: "payout", cell: (row) => <StatusBadge status={row.status} /> },
    { header: "voucher", cell: (row) => <StatusBadge status={row.voucher_status} /> },
    { header: "settlement", cell: (row) => <StatusBadge status={row.settlement_status} /> },
  ]

  const contributionColumns: Column<Contribution>[] = [
    { header: "member", cell: (row) => nameOf(row.user_id) },
    { header: "cycle", cell: (row) => row.cycle_number, align: "right" },
    { header: "amount", cell: (row) => formatNaira(row.amount), align: "right" },
    { header: "status", cell: (row) => <StatusBadge status={row.status} /> },
    { header: "paid", cell: (row) => formatDateTime(row.paid_at) },
  ]

  return (
    <>
      <PageHeader
        title={commitment.title}
        backHref={routes.bank.commitments}
        backLabel="commitments"
        meta={
          <>
            <StatusBadge status={commitment.status} />
            <StatusBadge status={commitment.type} tone="neutral" />
            <span className="font-mono text-xs font-semibold text-muted-foreground normal-case">
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
              settlements
            </Link>
          )
        }
      />

      <div className="flex flex-col gap-10">
        <DetailList
          items={[
            {
              label: "locked vendor",
              value: commitment.vendor.name ?? commitment.vendor.vendor_id,
            },
            { label: "contribution", value: `${formatNaira(commitment.contribution_amount)} ${humanize(commitment.frequency)}` },
            { label: "cycles done", value: `${commitment.completed_cycle_count} of ${commitment.cycles}` },
            { label: "current cycle", value: commitment.current_cycle_number },
            { label: "contributed so far", value: formatNaira(totalContributed) },
            { label: "members", value: commitment.members.length },
            { label: "created", value: formatDateTime(commitment.created_at) },
          ]}
        />

        {commitment.status === "under_review" && (
          <Alert variant="error" title="under review">
            a support case is open. contributions and payouts wait until it&apos;s resolved below.
          </Alert>
        )}

        <GroupHealthPanel commitmentId={commitment.commitment_id} status={commitment.status} />

        <PayoutDecision commitment={commitment} nameOf={nameOf} />

        <Section title="payout schedule" description="who receives each cycle's pool, and where that voucher is now.">
          <DataTable caption="payout schedule" columns={payoutColumns} rows={commitment.payout_schedule} rowKey={(row) => String(row.cycle_number)} />
        </Section>

        <Section title="members" description="bank staff may see scores here. members never see each other's.">
          <DataTable
            caption="members"
            columns={memberColumns}
            rows={commitment.members}
            rowKey={(row) => row.user_id}
            rowHref={(row) => routes.bank.user(row.user_id)}
          />
        </Section>

        <Section title="contributions">
          {commitment.contributions.length === 0 ? (
            <p className="rounded-2xl border-2 border-dashed border-hairline px-4 py-6 text-center text-sm font-semibold text-muted-foreground">
              no contributions recorded yet.
            </p>
          ) : (
            <DataTable
              caption="contributions"
              columns={contributionColumns}
              rows={commitment.contributions}
              rowKey={(row) => row.contribution_id}
            />
          )}
        </Section>

        <SupportCases commitment={commitment} onChanged={onChanged} />

        <Section title="activity">
          <Timeline
            items={commitment.activity.map((item) => ({
              id: item.activity_id,
              title: humanize(item.type),
              detail: [nameOf(item.actor_user_id), item.cycle_number ? `cycle ${item.cycle_number}` : null]
                .filter(Boolean)
                .join(" · "),
              at: item.occurred_at,
            }))}
            empty="nothing has happened on this commitment yet."
          />
        </Section>
      </div>
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
    <Section title="payout order and cap">
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
          <Alert variant="info" title="no payout schedule yet">
            the schedule is fixed once every invited member has joined.
          </Alert>
        ) : capped ? (
          <Alert variant="gold" icon={LockIcon} title={`cycle 1 is capped at ${formatNaira(first.amount)}`}>
            later cycles pay {formatNaira(regular)}. a group where nobody has history above the entry tier chooses its own
            order, and its first payout is capped, so a stranger can&apos;t take the first pool and leave.
          </Alert>
        ) : (
          <Alert variant="info" title="no first-payout cap">
            every cycle pays the same pool. in a group where someone already had history above the entry tier, early
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
      <Skeleton className="mb-10 h-32 rounded-2xl" />
      <TableSkeleton rows={4} />
    </>
  )
}
