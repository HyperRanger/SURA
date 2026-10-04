"use client"

import { useState } from "react"
import { UserGroupIcon } from "@hugeicons/core-free-icons"
import { listBankUsers } from "@/actions/bank"
import { commitmentStatuses, flagStatuses, scoreTiers } from "@/config/bank"
import { routes } from "@/config/routes"
import { useDebouncedValue } from "@/hooks/use-debounced-value"
import { useQuery } from "@/hooks/use-query"
import { DataTable, TableSkeleton, type Column } from "@/components/bank/data-table"
import { FilterBar, SearchFilter, SelectFilter, TextFilter, toOptions } from "@/components/bank/filters"
import { PageHeader } from "@/components/bank/page-header"
import { QueryState } from "@/components/bank/query-state"
import { StatusBadge } from "@/components/bank/status-badge"
import { EmptyState } from "@/components/shared/empty-state"
import type { BankUserFilters, BankUserRow, FlagStatus, ScoreTier } from "@/types"
import { formatPercent } from "@/utils/format"

const columns: Column<BankUserRow>[] = [
  { header: "customer", cell: (row) => row.name },
  {
    header: "bank reference",
    cell: (row) => <span className="font-mono normal-case">{row.bank_customer_id ?? "—"}</span>,
  },
  { header: "score", cell: (row) => row.score, align: "right" },
  { header: "tier", cell: (row) => <StatusBadge status={row.tier} /> },
  {
    header: "verification",
    cell: (row) => <StatusBadge status={row.verified ? "verified" : "unverified"} />,
  },
  { header: "active locks", cell: (row) => row.active_commitments, align: "right" },
  { header: "on time", cell: (row) => formatPercent(row.on_time_contribution_rate), align: "right" },
  {
    header: "open flags",
    cell: (row) => (row.open_flags > 0 ? <StatusBadge status="open" label={String(row.open_flags)} /> : "0"),
    align: "right",
  },
]

type Verification = "verified" | "unverified"
type FloatEligibility = NonNullable<BankUserFilters["float_eligibility"]>
type CommitmentStatus = (typeof commitmentStatuses)[number]

const verificationOptions: { value: Verification; label: string }[] = [
  { value: "verified", label: "verified" },
  { value: "unverified", label: "unverified" },
]

const floatOptions: { value: FloatEligibility; label: string }[] = [
  { value: "eligible", label: "eligible" },
  { value: "locked", label: "locked" },
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

  return (
    <>
      <PageHeader
        title="customers"
        description="your customers on sura, with their score and tier. identifiers are masked."
      />

      <FilterBar>
        <SearchFilter
          id="customer-search"
          label="search customers"
          placeholder="name, phone, sura id, bank reference or commitment id"
          value={search}
          onChange={setSearch}
        />
        <TextFilter
          id="customer-reference"
          label="bank customer id (exact)"
          placeholder="your full customer reference"
          value={reference}
          onChange={setReference}
        />
      </FilterBar>

      <FilterBar>
        <SelectFilter id="customer-tier" label="score tier" value={tier} onChange={setTier} options={scoreTiers} />
        <SelectFilter
          id="customer-flags"
          label="flag status"
          value={flagStatus}
          onChange={setFlagStatus}
          options={flagStatuses}
          allLabel="any"
        />
        <SelectFilter
          id="customer-verified"
          label="verification"
          value={verification}
          onChange={setVerification}
          options={verificationOptions}
          allLabel="any"
        />
        <SelectFilter
          id="customer-float"
          label="float eligibility"
          value={floatEligibility}
          onChange={setFloatEligibility}
          options={floatOptions}
          allLabel="any"
        />
        <SelectFilter
          id="customer-commitment-status"
          label="has a lock that is"
          value={commitmentStatus}
          onChange={setCommitmentStatus}
          options={commitmentStatusOptions}
          allLabel="any"
        />
      </FilterBar>

      <QueryState
        query={query}
        noun="customers"
        skeleton={<TableSkeleton />}
        isEmpty={(rows) => rows.length === 0}
        empty={
          <EmptyState
            icon={UserGroupIcon}
            title={bankCustomerId ? "no customer with that reference" : filtered ? "no customers match" : "no customers yet"}
            description={
              bankCustomerId
                ? "the reference must match exactly, and belong to a customer of your bank."
                : filtered
                ? "try a different search or clear the filters."
                : "customers appear here once they sign up to sura through your bank."
            }
          />
        }
      >
        {(rows) => (
          <DataTable
            caption="customers"
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
