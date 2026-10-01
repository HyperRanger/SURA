"use client"

import { useState } from "react"
import { RepeatIcon } from "@hugeicons/core-free-icons"
import { listBankCommitments } from "@/actions/bank"
import { commitmentStatuses } from "@/config/bank"
import { routes } from "@/config/routes"
import { useDebouncedValue } from "@/hooks/use-debounced-value"
import { useQuery } from "@/hooks/use-query"
import { DataTable, TableSkeleton, type Column } from "@/components/bank/data-table"
import { FilterBar, SearchFilter, SelectFilter, toOptions } from "@/components/bank/filters"
import { PageHeader } from "@/components/bank/page-header"
import { QueryState } from "@/components/bank/query-state"
import { StatusBadge } from "@/components/bank/status-badge"
import { EmptyState } from "@/components/shared/empty-state"
import type { BankCommitmentRow } from "@/types"
import { formatDateTime, formatNaira, humanize } from "@/utils/format"

const columns: Column<BankCommitmentRow>[] = [
  { header: "commitment", cell: (row) => row.title },
  { header: "status", cell: (row) => <StatusBadge status={row.status} /> },
  { header: "type", cell: (row) => humanize(row.type) },
  { header: "members", cell: (row) => row.member_count, align: "right" },
  { header: "cycles done", cell: (row) => `${row.completed_cycle_count} of ${row.cycles}`, align: "right" },
  { header: "contributed", cell: (row) => formatNaira(row.total_contributed), align: "right" },
  { header: "created", cell: (row) => formatDateTime(row.created_at) },
]

const statusOptions = toOptions(commitmentStatuses)

// B3
export function CommitmentsScreen() {
  const [search, setSearch] = useState("")
  const [status, setStatus] = useState<(typeof commitmentStatuses)[number] | "">("")
  const q = useDebouncedValue(search.trim())
  const query = useQuery(listBankCommitments, [{ q, status }])
  const filtered = Boolean(q || status)

  return (
    <>
      <PageHeader
        title="commitments"
        description="every sura lock with at least one of your customers in it. read only."
      />

      <FilterBar>
        <SearchFilter
          id="commitment-search"
          label="search commitments"
          placeholder="title, commitment id, vendor or member id"
          value={search}
          onChange={setSearch}
        />
        <SelectFilter id="commitment-status" label="status" value={status} onChange={setStatus} options={statusOptions} />
      </FilterBar>

      <QueryState
        query={query}
        noun="commitments"
        skeleton={<TableSkeleton />}
        isEmpty={(rows) => rows.length === 0}
        empty={
          <EmptyState
            icon={RepeatIcon}
            title={filtered ? "no commitments match" : "no commitments yet"}
            description={
              filtered
                ? "try a different search or clear the status filter."
                : "they appear here once one of your customers creates or joins a sura lock."
            }
          />
        }
      >
        {(rows) => (
          <DataTable
            caption="commitments"
            columns={columns}
            rows={rows}
            rowKey={(row) => row.commitment_id}
            rowHref={(row) => routes.bank.commitment(row.commitment_id)}
          />
        )}
      </QueryState>
    </>
  )
}
