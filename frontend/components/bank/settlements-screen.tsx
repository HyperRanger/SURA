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
import type { Settlement } from "@/types"
import { formatDateTime, formatNaira } from "@/utils/format"

const columns: Column<Settlement>[] = [
  { header: "amount", cell: (row) => formatNaira(row.amount) },
  { header: "status", cell: (row) => <StatusBadge status={row.status} /> },
  { header: "voucher", cell: (row) => <span className="font-mono text-xs normal-case">{row.voucher_code}</span> },
  { header: "vendor", cell: (row) => <span className="font-mono text-xs normal-case">{row.vendor_id}</span> },
  {
    header: "commitment",
    cell: (row) => (
      <Link
        href={routes.bank.commitment(row.commitment_id)}
        className="font-mono text-xs text-link normal-case underline-offset-4 hover:underline"
      >
        {row.commitment_id}
      </Link>
    ),
  },
  { header: "redeemed", cell: (row) => formatDateTime(row.redeemed_at) },
]

const statusOptions = toOptions(settlementStatuses)

// B10. opened from B4 with ?commitment_id= to show one commitment's settlements
export function SettlementsScreen({ commitmentId }: { commitmentId?: string }) {
  const [search, setSearch] = useState("")
  const [status, setStatus] = useState<(typeof settlementStatuses)[number] | "">("")
  const [scope, setScope] = useState(commitmentId)
  const q = useDebouncedValue(search.trim())
  const query = useQuery(listSettlements, [{ q, status, commitment_id: scope }])
  const filtered = Boolean(q || status || scope)

  return (
    <>
      <PageHeader
        title="settlements"
        description="vendor payouts from redeemed vouchers. your bank moves the money on its own rails; sura records it."
        meta={<StatusBadge status="simulated" label="simulated settlement" tone="gold" />}
      />

      {scope && (
        <Alert
          variant="info"
          title="one commitment"
          className="mb-5"
          action={
            <Button type="button" variant="outline" size="sm" onClick={() => setScope(undefined)}>
              show all
            </Button>
          }
        >
          <span className="font-mono text-xs normal-case">{scope}</span>
        </Alert>
      )}

      <FilterBar>
        <SearchFilter
          id="settlement-search"
          label="search settlements"
          placeholder="voucher, vendor, customer, commitment or settlement id"
          value={search}
          onChange={setSearch}
        />
        <SelectFilter id="settlement-status" label="status" value={status} onChange={setStatus} options={statusOptions} />
      </FilterBar>

      <QueryState
        query={query}
        noun="settlements"
        skeleton={<TableSkeleton />}
        isEmpty={(rows) => rows.length === 0}
        empty={
          <EmptyState
            icon={MoneyExchange01Icon}
            title={filtered ? "no settlements match" : "no settlements yet"}
            description={
              filtered
                ? "try a different search or clear the filters."
                : "a settlement is recorded each time a vendor redeems a voucher."
            }
          />
        }
      >
        {(rows) => (
          <DataTable caption="settlements" columns={columns} rows={rows} rowKey={(row) => row.settlement_id} />
        )}
      </QueryState>
    </>
  )
}
