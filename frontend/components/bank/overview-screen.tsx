"use client"

import { useState, type ReactNode } from "react"
import Link from "next/link"
import { HugeiconsIcon, type IconSvgElement } from "@hugeicons/react"
import { ArrowRight01Icon, Audit01Icon, Flag02Icon, RepeatIcon, UserGroupIcon } from "@hugeicons/core-free-icons"
import { getBankOverview } from "@/actions/bank"
import type { BankPermission } from "@/config/bank"
import { routes } from "@/config/routes"
import { useBankAccess } from "@/hooks/use-bank-access"
import { useQuery } from "@/hooks/use-query"
import { DateFilter, endOfDay, FilterBar, startOfDay } from "@/components/bank/filters"
import { PageHeader, Section } from "@/components/bank/page-header"
import { QueryState } from "@/components/bank/query-state"
import { StatusBadge } from "@/components/bank/status-badge"
import { IconTile } from "@/components/shared/icon-tile"
import { Skeleton } from "@/components/ui/skeleton"
import { cn } from "@/lib/utils"
import type { BankOverview, Tone } from "@/types"
import { formatDateTime, formatNaira, formatPercent, humanize } from "@/utils/format"

type Shortcut = {
  title: string
  description: string
  href: string
  icon: IconSvgElement
  tone: Tone
  permission: BankPermission
}

const shortcuts: Shortcut[] = [
  {
    title: "audit log",
    description: "every score change and staff action, with the reason behind it.",
    href: routes.bank.auditLog,
    icon: Audit01Icon,
    tone: "gold",
    permission: "bank:audit:read",
  },
  {
    title: "risk flags",
    description: "patterns the fraud rules caught, waiting for an analyst.",
    href: routes.bank.flags,
    icon: Flag02Icon,
    tone: "indigo",
    permission: "bank:flags:read",
  },
  {
    title: "commitments",
    description: "every savings circle your customers belong to.",
    href: routes.bank.commitments,
    icon: RepeatIcon,
    tone: "indigo",
    permission: "bank:commitments:read",
  },
  {
    title: "customers",
    description: "scores, tiers and contribution history per customer.",
    href: routes.bank.users,
    icon: UserGroupIcon,
    tone: "gold",
    permission: "bank:users:read",
  },
]

type Range = { from: string; to: string }

// B2
export function OverviewScreen() {
  const [range, setRange] = useState<Range>({ from: "", to: "" })
  const query = useQuery(getBankOverview, [{ date_from: startOfDay(range.from), date_to: endOfDay(range.to) }])
  // keeps the last overview on screen while a new range loads, so the date inputs don't vanish
  const [kept, setKept] = useState<BankOverview | null>(null)
  if (query.data && query.data !== kept) setKept(query.data)

  if (kept && !query.error) {
    return <Overview overview={kept} range={range} onRangeChange={setRange} refreshing={query.isLoading} />
  }

  return (
    <QueryState query={query} noun="the overview" skeleton={<OverviewSkeleton />}>
      {(overview) => <Overview overview={overview} range={range} onRangeChange={setRange} refreshing={false} />}
    </QueryState>
  )
}

type OverviewProps = {
  overview: BankOverview
  range: Range
  onRangeChange: (range: Range) => void
  refreshing: boolean
}

function Overview({ overview, range, onRangeChange, refreshing }: OverviewProps) {
  const { can } = useBankAccess()
  const visibleShortcuts = shortcuts.filter((shortcut) => can(shortcut.permission))

  return (
    <>
      <PageHeader
        title={overview.bank_name}
        description="how your customers' commitments are doing, read live from sura."
        meta={
          <>
            <StatusBadge status={overview.environment} tone={overview.environment === "live" ? "gold" : "indigo"} />
            <span className="text-xs font-bold text-muted-foreground">{overview.customers} customers</span>
          </>
        }
      />

      <FilterBar>
        <DateFilter id="overview-from" label="activity from" value={range.from} onChange={(from) => onRangeChange({ ...range, from })} />
        <DateFilter id="overview-to" label="activity to" value={range.to} onChange={(to) => onRangeChange({ ...range, to })} />
      </FilterBar>

      <div className={cn("grid grid-cols-2 gap-3 transition-opacity lg:grid-cols-4", refreshing && "opacity-60")} aria-busy={refreshing}>
        <StatCard label="active commitments" value={overview.active_commitments} />
        <StatCard label="total contributed" value={formatNaira(overview.total_contributed)} highlight />
        <StatCard label="completion rate" value={formatPercent(overview.completion_rate)} />
        <StatCard
          label="open fraud flags"
          value={overview.open_flags}
          href={can("bank:flags:read") ? routes.bank.flags : undefined}
          alert={overview.open_flags > 0}
        />
      </div>

      <ul className="mt-8 grid gap-3 sm:grid-cols-2">
        {visibleShortcuts.map((shortcut) => (
          <li key={shortcut.href}>
            <Link
              href={shortcut.href}
              className="card-raised group flex h-full items-center gap-4 rounded-2xl p-4 transition-all hover:border-hairline-strong active:translate-y-0.5 active:border-b-2"
            >
              <IconTile icon={shortcut.icon} tone={shortcut.tone} />
              <span className="min-w-0 flex-1">
                <span className="block text-base font-black">{shortcut.title}</span>
                <span className="mt-0.5 block text-sm leading-snug font-semibold text-muted-foreground">
                  {shortcut.description}
                </span>
              </span>
              <HugeiconsIcon
                icon={ArrowRight01Icon}
                size={18}
                strokeWidth={2.5}
                className="shrink-0 text-muted-foreground transition-colors group-hover:text-link"
              />
            </Link>
          </li>
        ))}
      </ul>

      <div className="mt-10 grid gap-8 lg:grid-cols-2">
        <Section
          title="recent activity"
          action={can("bank:audit:read") && <ViewAll href={routes.bank.auditLog} />}
        >
          {overview.recent_activity.length === 0 ? (
            <EmptyLine>no staff activity yet.</EmptyLine>
          ) : (
            <ul className="card-raised divide-y divide-hairline rounded-2xl">
              {overview.recent_activity.map((event) => (
                <li key={event.event_id} className="flex items-center justify-between gap-3 px-4 py-3">
                  <span className="min-w-0">
                    <span className="block truncate text-sm font-extrabold">{humanize(event.event_type)}</span>
                    <span className="block truncate font-mono text-xs font-semibold text-muted-foreground normal-case">
                      {event.subject_id}
                    </span>
                  </span>
                  <span className="shrink-0 text-xs font-bold text-muted-foreground">{formatDateTime(event.occurred_at)}</span>
                </li>
              ))}
            </ul>
          )}
        </Section>

        <Section
          title="recent settlements"
          description="simulated. sura never holds or moves money."
          action={can("bank:settlements:read") && <ViewAll href={routes.bank.settlements} />}
        >
          {overview.recent_settlements.length === 0 ? (
            <EmptyLine>no vouchers have been redeemed yet.</EmptyLine>
          ) : (
            <ul className="card-raised divide-y divide-hairline rounded-2xl">
              {overview.recent_settlements.map((settlement) => (
                <li key={settlement.settlement_id} className="relative flex items-center justify-between gap-3 px-4 py-3">
                  <span className="min-w-0">
                    <Link
                      href={routes.bank.commitment(settlement.commitment_id)}
                      className="block text-sm font-extrabold tabular-nums after:absolute after:inset-0"
                    >
                      {formatNaira(settlement.amount)}
                    </Link>
                    <span className="block text-xs font-bold text-muted-foreground">
                      {formatDateTime(settlement.redeemed_at)}
                    </span>
                  </span>
                  <StatusBadge status={settlement.status} />
                </li>
              ))}
            </ul>
          )}
        </Section>
      </div>
    </>
  )
}

type StatCardProps = {
  label: string
  value: ReactNode
  highlight?: boolean
  alert?: boolean
  href?: string
}

function StatCard({ label, value, highlight, alert, href }: StatCardProps) {
  const body = (
    <>
      <span className="block text-xs font-extrabold tracking-wide text-muted-foreground">{label}</span>
      <span
        className={cn(
          "mt-2 block text-2xl font-black tracking-tight tabular-nums sm:text-3xl",
          highlight && "text-gold-deep",
          alert && "text-destructive"
        )}
      >
        {value}
      </span>
    </>
  )
  const className = "card-raised block rounded-2xl p-4 sm:p-5"

  return href ? (
    <Link href={href} className={cn(className, "transition-all hover:border-hairline-strong")}>
      {body}
    </Link>
  ) : (
    <div className={className}>{body}</div>
  )
}

function ViewAll({ href }: { href: string }) {
  return (
    <Link href={href} className="shrink-0 text-sm font-extrabold text-link underline-offset-4 hover:underline">
      view all
    </Link>
  )
}

function EmptyLine({ children }: { children: ReactNode }) {
  return (
    <p className="rounded-2xl border-2 border-dashed border-hairline px-4 py-6 text-center text-sm font-semibold text-muted-foreground">
      {children}
    </p>
  )
}

function OverviewSkeleton() {
  return (
    <>
      <Skeleton className="mb-8 h-10 w-56" />
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        {Array.from({ length: 4 }, (_, i) => (
          <Skeleton key={i} className="h-24 rounded-2xl sm:h-28" />
        ))}
      </div>
      <div className="mt-8 grid gap-3 sm:grid-cols-2">
        {Array.from({ length: 4 }, (_, i) => (
          <Skeleton key={i} className="h-20 rounded-2xl" />
        ))}
      </div>
    </>
  )
}
