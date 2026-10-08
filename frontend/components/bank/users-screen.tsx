"use client"

import { useState } from "react"
import { HugeiconsIcon } from "@hugeicons/react"
import { FilterHorizontalIcon, UserGroupIcon } from "@hugeicons/core-free-icons"
import { listBankUsers } from "@/actions/bank"
import { commitmentStatuses, flagStatuses, scoreTiers } from "@/config/bank"
import { routes } from "@/config/routes"
import { useDebouncedValue } from "@/hooks/use-debounced-value"
import { useQuery } from "@/hooks/use-query"
import { DataTable, TableSkeleton, type Column } from "@/components/bank/data-table"
import { FilterGrid, SearchFilter, SelectFilter, TextFilter, toOptions } from "@/components/bank/filters"
import { PageHeader } from "@/components/bank/page-header"
import { QueryState } from "@/components/bank/query-state"
import { StatusBadge } from "@/components/bank/status-badge"
import { EmptyState } from "@/components/shared/empty-state"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import type { BankUserFilters, BankUserRow, FlagStatus, ScoreTier } from "@/types"
import { formatPercent } from "@/utils/format"

const columns: Column<BankUserRow>[] = [
  { header: "Customer", cell: (row) => row.name },
  {
    header: "Bank reference",
    cell: (row) => <span className="font-mono">{row.bank_customer_id ?? "—"}</span>,
  },
  { header: "Score", cell: (row) => row.score, align: "right" },
  { header: "Tier", cell: (row) => <StatusBadge status={row.tier} /> },
  {
    header: "Verification",
    cell: (row) => <StatusBadge status={row.verified ? "verified" : "unverified"} />,
  },
  { header: "Active locks", cell: (row) => row.active_commitments, align: "right" },
  { header: "On time", cell: (row) => formatPercent(row.on_time_contribution_rate), align: "right" },
  {
    header: "Open flags",
    cell: (row) => (row.open_flags > 0 ? <StatusBadge status="open" label={String(row.open_flags)} /> : "0"),
    align: "right",
  },
]

type Verification = "verified" | "unverified"
type FloatEligibility = NonNullable<BankUserFilters["float_eligibility"]>
type CommitmentStatus = (typeof commitmentStatuses)[number]

const verificationOptions: { value: Verification; label: string }[] = [
  { value: "verified", label: "Verified" },
  { value: "unverified", label: "Unverified" },
]

const floatOptions: { value: FloatEligibility; label: string }[] = [
  { value: "eligible", label: "Eligible" },
  { value: "locked", label: "Locked" },
]

const commitmentStatusOptions = toOptions(commitmentStatuses)

// B5
export function UsersScreen() {
  const [search, setSearch] = useState("")
  const [reference, setReference] = useState("")
  const [tier, setTier] = useState<ScoreTier | "">("")
  const [flagStatus, setFlagStatus] = useState<FlagStatus | "">("")
  const [verification, setVerification] = useState<Verification | "">("")
  const [floatEligibility, setFloatEligibility] = useState<FloatEligibility | "">("")
  const [commitmentStatus, setCommitmentStatus] = useState<CommitmentStatus | "">("")
  const q = useDebouncedValue(search.trim())
  const bankCustomerId = useDebouncedValue(reference.trim())
  const query = useQuery(listBankUsers, [
    {
      q,
      bank_customer_id: bankCustomerId,
      score_tier: tier || undefined,
      flag_status: flagStatus || undefined,
      verified: verification ? verification === "verified" : undefined,
      float_eligibility: floatEligibility || undefined,
      commitment_status: commitmentStatus || undefined,
    },
  ])
  const filtered = Boolean(q || bankCustomerId || tier || flagStatus || verification || floatEligibility || commitmentStatus)
  // on phones the filters fold behind a button, so the list isn't pushed a screen down
  const [showFilters, setShowFilters] = useState(false)
  const activeFilters = [reference, tier, flagStatus, verification, floatEligibility, commitmentStatus].filter(Boolean).length

  return (
    <>
      <PageHeader
        title="Customers"
        description="Your customers on Sura, with their score and tier. Identifiers are masked."
      />

      <div className="mb-3 flex flex-col gap-3 sm:mb-5 sm:flex-row sm:items-end">
        <div className="flex min-w-0 items-end gap-2 sm:flex-1">
          <SearchFilter
            id="customer-search"
            label="Search customers"
            placeholder="Name, phone, Sura ID, bank reference or commitment ID"
            value={search}
            onChange={setSearch}
            className="flex-1"
          />
          <Button
            type="button"
            variant="outline"
            aria-expanded={showFilters}
            aria-controls="customer-filters"
            title={showFilters ? "Hide filters" : "Show filters"}
            onClick={() => setShowFilters((open) => !open)}
            className="relative h-12 px-4 sm:hidden"
          >
            <HugeiconsIcon icon={FilterHorizontalIcon} size={18} strokeWidth={2.2} />
            <span className="sr-only">Filters</span>
            {activeFilters > 0 && (
              <span className="absolute -top-1.5 -right-1.5 flex size-5 items-center justify-center rounded-full bg-gold text-[0.65rem] font-bold text-gold-foreground">
                {activeFilters}
              </span>
            )}
          </Button>
        </div>
        <TextFilter
          id="customer-reference"
          label="Bank customer ID (exact)"
          placeholder="Your full customer reference"
          value={reference}
          onChange={setReference}
          className={cn(!showFilters && "hidden", "sm:flex")}
        />
      </div>

      <FilterGrid id="customer-filters" className={cn(!showFilters && "hidden", "sm:grid")}>
        <SelectFilter id="customer-tier" label="Score tier" value={tier} onChange={setTier} options={scoreTiers} className="sm:w-auto" />
        <SelectFilter
          id="customer-flags"
          label="Flag status"
          value={flagStatus}
          onChange={setFlagStatus}
          options={flagStatuses}
          allLabel="Any"
          className="sm:w-auto"
        />
        <SelectFilter
          id="customer-verified"
          label="Verification"
          value={verification}
          onChange={setVerification}
          options={verificationOptions}
          allLabel="Any"
          className="sm:w-auto"
        />
        <SelectFilter
          id="customer-float"
          label="Float eligibility"
          value={floatEligibility}
          onChange={setFloatEligibility}
          options={floatOptions}
          allLabel="Any"
          className="sm:w-auto"
        />
        <SelectFilter
          id="customer-commitment-status"
          label="Has a lock that is"
          value={commitmentStatus}
          onChange={setCommitmentStatus}
          options={commitmentStatusOptions}
          allLabel="Any"
          className="col-span-2 sm:col-span-1 sm:w-auto"
        />
      </FilterGrid>

      <QueryState
        query={query}
        noun="customers"
        skeleton={<TableSkeleton />}
        isEmpty={(rows) => rows.length === 0}
        empty={
          <EmptyState
            icon={UserGroupIcon}
            title={bankCustomerId ? "No customer with that reference" : filtered ? "No customers match" : "No customers yet"}
            description={
              bankCustomerId
                ? "The reference must match exactly, and belong to a customer of your bank."
                : filtered
                ? "Try a different search or clear the filters."
                : "Customers appear here once they sign up to Sura through your bank."
            }
          />
        }
      >
        {(rows) => (
          <DataTable
            caption="Customers"
            columns={columns}
            rows={rows}
            rowKey={(row) => row.user_id}
            rowHref={(row) => routes.bank.user(row.user_id)}
          />
        )}
      </QueryState>
    </>
  )
}
