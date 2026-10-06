"use client"

import { useState } from "react"
import Link from "next/link"
import { MoneyExchange01Icon } from "@hugeicons/core-free-icons"
import { listSettlements } from "@/actions/bank"
import { settlementStatuses } from "@/config/bank"
import { routes } from "@/config/routes"
import { useDebouncedValue } from "@/hooks/use-debounced-value"
import { useQuery } from "@/hooks/use-query"
import { DataTable, TableSkeleton, type Column } from "@/components/bank/data-table"
import { FilterBar, SearchFilter, SelectFilter, toOptions } from "@/components/bank/filters"
import { PageHeader } from "@/components/bank/page-header"
import { QueryState } from "@/components/bank/query-state"
import { StatusBadge } from "@/components/bank/status-badge"
import { EmptyState } from "@/components/shared/empty-state"
import { Alert } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import type { Settlement, SettlementFilters } from "@/types"
import { formatDateTime, formatNaira } from "@/utils/format"

const columns: Column<Settlement>[] = [
  { header: "Amount", cell: (row) => formatNaira(row.amount) },
  { header: "Status", cell: (row) => <StatusBadge status={row.status} /> },
  { header: "Voucher", cell: (row) => <span className="font-mono text-xs">{row.voucher_code}</span> },
  { header: "Vendor", cell: (row) => <span className="font-mono text-xs">{row.vendor_id}</span> },
  {
    header: "Commitment",
    cell: (row) => (
      <Link
        href={routes.bank.commitment(row.commitment_id)}
        className="font-mono text-xs text-link underline-offset-4 hover:underline"
      >
        {row.commitment_id}
      </Link>
    ),
  },
  { header: "Redeemed", cell: (row) => formatDateTime(row.redeemed_at) },
]

const statusOptions = toOptions(settlementStatuses)

export type SettlementScope = Pick<SettlementFilters, "commitment_id" | "user_id" | "vendor_id">

const scopeLabels: Record<keyof SettlementScope, string> = {
  commitment_id: "One commitment",
  user_id: "One customer",
  vendor_id: "One vendor",
}

// B10. opened from B4 with ?commitment_id=, B6 with ?user_id=, or ?vendor_id=
export function SettlementsScreen({ initialScope = {} }: { initialScope?: SettlementScope }) {
  const [search, setSearch] = useState("")
  const [status, setStatus] = useState<(typeof settlementStatuses)[number] | "">("")
  const [scope, setScope] = useState<SettlementScope>(initialScope)
  const q = useDebouncedValue(search.trim())
  const query = useQuery(listSettlements, [{ q, status, ...scope }])
  const scoped = (Object.keys(scopeLabels) as (keyof SettlementScope)[]).filter((key) => scope[key])
  const filtered = Boolean(q || status || scoped.length)

  return (
    <>
      <PageHeader
        title="Settlements"
        description="Vendor payouts from redeemed vouchers. Your bank moves the money on its own rails; Sura records it."
        meta={<StatusBadge status="simulated" label="Simulated settlement" tone="gold" />}
      />

      {scoped.length > 0 && (
        <Alert
          variant="info"
          title={scoped.map((key) => scopeLabels[key]).join(", ")}
          className="mb-5"
          action={
            <Button type="button" variant="outline" size="sm" onClick={() => setScope({})}>
              Show all
            </Button>
          }
        >
          <span className="font-mono text-xs">{scoped.map((key) => scope[key]).join(" · ")}</span>
        </Alert>
      )}

      <FilterBar>
        <SearchFilter
          id="settlement-search"
          label="Search settlements"
          placeholder="Voucher, vendor, customer, commitment or settlement ID"
          value={search}
          onChange={setSearch}
        />
        <SelectFilter id="settlement-status" label="Status" value={status} onChange={setStatus} options={statusOptions} />
      </FilterBar>

      <QueryState
        query={query}
        noun="settlements"
        skeleton={<TableSkeleton />}
        isEmpty={(rows) => rows.length === 0}
        empty={
          <EmptyState
            icon={MoneyExchange01Icon}
            title={filtered ? "No settlements match" : "No settlements yet"}
            description={
              filtered
                ? "Try a different search or clear the filters."
                : "A settlement is recorded each time a vendor redeems a voucher."
            }
          />
        }
      >
        {(rows) => (
          <DataTable caption="Settlements" columns={columns} rows={rows} rowKey={(row) => row.settlement_id} />
        )}
      </QueryState>
    </>
  )
}
