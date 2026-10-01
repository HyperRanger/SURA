"use client"

import { useState } from "react"
import { UserGroupIcon } from "@hugeicons/core-free-icons"
import { listBankUsers } from "@/actions/bank"
import { flagStatuses, scoreTiers } from "@/config/bank"
import { routes } from "@/config/routes"
import { useDebouncedValue } from "@/hooks/use-debounced-value"
import { useQuery } from "@/hooks/use-query"
import { DataTable, TableSkeleton, type Column } from "@/components/bank/data-table"
import { FilterBar, SearchFilter, SelectFilter } from "@/components/bank/filters"
import { PageHeader } from "@/components/bank/page-header"
import { QueryState } from "@/components/bank/query-state"
import { StatusBadge } from "@/components/bank/status-badge"
import { EmptyState } from "@/components/shared/empty-state"
import type { BankUserRow, FlagStatus, ScoreTier } from "@/types"
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

// B5
export function UsersScreen() {
  const [search, setSearch] = useState("")
  const [tier, setTier] = useState<ScoreTier | "">("")
  const [flagStatus, setFlagStatus] = useState<FlagStatus | "">("")
  const q = useDebouncedValue(search.trim())
  const query = useQuery(listBankUsers, [{ q, score_tier: tier || undefined, flag_status: flagStatus || undefined }])
  const filtered = Boolean(q || tier || flagStatus)

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
        <SelectFilter id="customer-tier" label="score tier" value={tier} onChange={setTier} options={scoreTiers} />
        <SelectFilter
          id="customer-flags"
          label="flag status"
          value={flagStatus}
          onChange={setFlagStatus}
          options={flagStatuses}
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
            title={filtered ? "no customers match" : "no customers yet"}
            description={
              filtered
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
