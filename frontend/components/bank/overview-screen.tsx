"use client"

import { useState, type ReactNode } from "react"
import Link from "next/link"
import { HugeiconsIcon, type IconSvgElement } from "@hugeicons/react"
import {
  Activity01Icon,
  Alert02Icon,
  ArrowRight01Icon,
  Audit01Icon,
  Flag02Icon,
  MoneyExchange01Icon,
  RepeatIcon,
  UserGroupIcon,
} from "@hugeicons/core-free-icons"
import { getBankOverview } from "@/actions/bank"
import type { BankPermission } from "@/config/bank"
import { routes } from "@/config/routes"
import { useBankAccess } from "@/hooks/use-bank-access"
import { useQuery } from "@/hooks/use-query"
import { DateFilter, endOfDay, startOfDay } from "@/components/bank/filters"
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
  const ranged = Boolean(range.from || range.to)

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

      <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-end">
        <div className="grid grid-cols-2 gap-3 sm:flex">
          <DateFilter id="overview-from" label="activity from" value={range.from} onChange={(from) => onRangeChange({ ...range, from })} />
          <DateFilter id="overview-to" label="activity to" value={range.to} onChange={(to) => onRangeChange({ ...range, to })} />
        </div>
        {ranged && (
          <button
            type="button"
            title="show activity from every day"
            onClick={() => onRangeChange({ from: "", to: "" })}
            className="h-12 cursor-pointer self-start rounded-full px-3 text-sm font-extrabold text-link underline-offset-4 hover:underline sm:self-auto"
          >
            all time
          </button>
        )}
      </div>

      <div className={cn("grid gap-3 transition-opacity lg:grid-cols-3", refreshing && "opacity-60")} aria-busy={refreshing}>
        <ContributionHero overview={overview} />

        <div className="grid grid-cols-2 gap-3 lg:grid-cols-1">
          <StatCard
            label="open fraud flags"
            value={overview.open_flags}
            icon={overview.open_flags > 0 ? Alert02Icon : Flag02Icon}
            hint={overview.open_flags > 0 ? "waiting for an analyst" : "nothing to review"}
            href={can("bank:flags:read") ? routes.bank.flags : undefined}
            alert={overview.open_flags > 0}
          />
          <StatCard
            label="pending settlements"
            value={overview.pending_settlements}
            icon={MoneyExchange01Icon}
            hint="vouchers not yet settled"
            href={can("bank:settlements:read") ? routes.bank.settlements : undefined}
          />
        </div>
      </div>

      {visibleShortcuts.length > 0 && (
        <Section title="jump to" className="mt-10">
          <ul className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {visibleShortcuts.map((shortcut) => (
              <li key={shortcut.href}>
                <Link
                  href={shortcut.href}
                  title={`open ${shortcut.title}`}
                  className="card-raised group flex h-full items-center gap-4 rounded-2xl p-4 transition-all hover:-translate-y-0.5 hover:border-hairline-strong active:translate-y-0.5 active:border-b-2 lg:flex-col lg:items-start lg:gap-3"
                >
                  <IconTile icon={shortcut.icon} tone={shortcut.tone} />
                  <span className="min-w-0 flex-1">
                    <span className="flex items-center gap-1 text-base font-black">
                      {shortcut.title}
                      <HugeiconsIcon
                        icon={ArrowRight01Icon}
                        size={16}
                        strokeWidth={2.5}
                        className="hidden text-muted-foreground transition-transform group-hover:translate-x-0.5 group-hover:text-link lg:block"
                      />
                    </span>
                    <span className="mt-0.5 block text-sm leading-snug font-semibold text-muted-foreground">
                      {shortcut.description}
                    </span>
                  </span>
                  <HugeiconsIcon
                    icon={ArrowRight01Icon}
                    size={18}
                    strokeWidth={2.5}
                    className="shrink-0 text-muted-foreground transition-colors group-hover:text-link lg:hidden"
                  />
                </Link>
              </li>
            ))}
          </ul>
        </Section>
      )}

      <div className="mt-10 grid gap-8 lg:grid-cols-2">
        <Section
          title="recent activity"
          action={can("bank:audit:read") && <ViewAll href={routes.bank.auditLog} label="the audit log" />}
        >
          {overview.recent_activity.length === 0 ? (
            <EmptyLine>no staff activity yet.</EmptyLine>
          ) : (
            <ul className="card-raised divide-y-2 divide-hairline overflow-hidden rounded-2xl">
              {overview.recent_activity.map((event) => (
                <li key={event.event_id} className="flex items-center gap-3 px-4 py-3">
                  <RowIcon icon={Activity01Icon} />
                  <span className="min-w-0 flex-1">
                    <span className="block truncate text-sm font-extrabold">{humanize(event.event_type)}</span>
                    <span
                      className="block truncate font-mono text-xs font-semibold text-muted-foreground normal-case"
                      title={event.subject_id}
                    >
                      {event.subject_id}
                    </span>
                  </span>
                  <span className="shrink-0 text-right text-xs font-bold text-muted-foreground">
                    {formatDateTime(event.occurred_at)}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </Section>

        <Section
          title="recent settlements"
          description="simulated. sura never holds or moves money."
          action={can("bank:settlements:read") && <ViewAll href={routes.bank.settlements} label="settlements" />}
        >
          {overview.recent_settlements.length === 0 ? (
            <EmptyLine>no vouchers have been redeemed yet.</EmptyLine>
          ) : (
            <ul className="card-raised divide-y-2 divide-hairline overflow-hidden rounded-2xl">
              {overview.recent_settlements.map((settlement) => (
                <li
                  key={settlement.settlement_id}
                  className="relative flex items-center gap-3 px-4 py-3 transition-colors hover:bg-cloud"
                >
                  <RowIcon icon={MoneyExchange01Icon} tone="gold" />
                  <span className="min-w-0 flex-1">
                    <Link
                      href={routes.bank.commitment(settlement.commitment_id)}
                      title="open the commitment this settlement belongs to"
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

// the headline: money locked toward goals, with how often circles finish beneath it
function ContributionHero({ overview }: { overview: BankOverview }) {
  const completion = Math.min(Math.max(overview.completion_rate, 0), 1)

  return (
    <div className="relative isolate overflow-hidden rounded-3xl border-b-4 border-primary-deep bg-primary p-5 text-primary-foreground sm:p-6 lg:col-span-2">

      <p className="text-xs font-extrabold tracking-wide text-primary-foreground/70">total contributed</p>
      <p className="mt-1 text-4xl font-black tracking-tight text-gold tabular-nums sm:text-5xl">
        {formatNaira(overview.total_contributed)}
      </p>

      <dl className="mt-6 grid grid-cols-2 gap-4 sm:max-w-md">
        <div>
          <dt className="text-xs font-extrabold text-primary-foreground/70">active commitments</dt>
          <dd className="mt-0.5 text-2xl font-black tabular-nums">{overview.active_commitments}</dd>
        </div>
        <div>
          <dt className="text-xs font-extrabold text-primary-foreground/70">customers</dt>
          <dd className="mt-0.5 text-2xl font-black tabular-nums">{overview.customers}</dd>
        </div>
      </dl>

      <div className="mt-6">
        <div className="flex items-baseline justify-between gap-3">
          <p className="text-xs font-extrabold text-primary-foreground/70">completion rate</p>
          <p className="text-sm font-black tabular-nums">{formatPercent(overview.completion_rate)}</p>
        </div>
        <div
          role="meter"
          aria-label="completion rate"
          aria-valuemin={0}
          aria-valuemax={100}
          aria-valuenow={Math.round(completion * 100)}
          title={`${formatPercent(overview.completion_rate)} of commitments run to the end`}
          className="mt-2 h-3 overflow-hidden rounded-full bg-primary-deep/60"
        >
          <div className="h-full rounded-full bg-gold transition-[width] duration-500" style={{ width: `${completion * 100}%` }} />
        </div>
      </div>
    </div>
  )
}

type StatCardProps = {
  label: string
  value: ReactNode
  icon: IconSvgElement
  hint?: string
  alert?: boolean
  href?: string
}

function StatCard({ label, value, icon, hint, alert, href }: StatCardProps) {
  const body = (
    <>
      <span className="flex items-start justify-between gap-2">
        <span className="text-xs font-extrabold tracking-wide text-muted-foreground">{label}</span>
        <span
          className={cn(
            "flex size-9 shrink-0 items-center justify-center rounded-full",
            alert ? "bg-destructive/10 text-destructive" : "bg-indigo-soft text-link"
          )}
        >
          <HugeiconsIcon icon={icon} size={18} strokeWidth={2.2} />
        </span>
      </span>
      <span>
        <span className={cn("block text-3xl font-black tracking-tight tabular-nums", alert && "text-destructive")}>{value}</span>
        {hint && (
          <span className="mt-0.5 flex items-center gap-1 text-xs font-bold text-muted-foreground">
            {hint}
            {href && (
              <HugeiconsIcon
                icon={ArrowRight01Icon}
                size={14}
                strokeWidth={2.5}
                className="transition-transform group-hover:translate-x-0.5 group-hover:text-link"
              />
            )}
          </span>
        )}
      </span>
    </>
  )
  const className = cn(
    "card-raised flex h-full flex-col justify-between gap-4 rounded-2xl p-4 sm:p-5",
    alert && "border-destructive/30"
  )

  return href ? (
    <Link
      href={href}
      title={`open ${label}`}
      className={cn(className, "group transition-all hover:-translate-y-0.5 hover:border-hairline-strong active:translate-y-0.5 active:border-b-2")}
    >
      {body}
    </Link>
  ) : (
    <div className={className}>{body}</div>
  )
}

function RowIcon({ icon, tone = "indigo" }: { icon: IconSvgElement; tone?: Tone }) {
  return (
    <span
      className={cn(
        "flex size-9 shrink-0 items-center justify-center rounded-full",
        tone === "gold" ? "bg-gold-soft text-gold-deep" : "bg-indigo-soft text-link"
      )}
    >
      <HugeiconsIcon icon={icon} size={16} strokeWidth={2.2} />
    </span>
  )
}

function ViewAll({ href, label }: { href: string; label: string }) {
  return (
    <Link
      href={href}
      title={`open ${label}`}
      className="shrink-0 text-sm font-extrabold text-link underline-offset-4 hover:underline"
    >
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
      <Skeleton className="mb-3 h-10 w-56" />
      <Skeleton className="mb-8 h-5 w-80 max-w-full" />
      <div className="grid gap-3 lg:grid-cols-3">
        <Skeleton className="h-64 rounded-3xl lg:col-span-2" />
        <div className="grid grid-cols-2 gap-3 lg:grid-cols-1">
          <Skeleton className="h-32 rounded-2xl" />
          <Skeleton className="h-32 rounded-2xl" />
        </div>
      </div>
      <div className="mt-10 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {Array.from({ length: 4 }, (_, i) => (
          <Skeleton key={i} className="h-24 rounded-2xl lg:h-36" />
        ))}
      </div>
    </>
  )
}
