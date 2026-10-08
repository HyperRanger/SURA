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
  { header: "Commitment", cell: (row) => row.title },
  { header: "Status", cell: (row) => <StatusBadge status={row.status} /> },
  { header: "Type", cell: (row) => humanize(row.type) },
  { header: "Members", cell: (row) => row.member_count, align: "right" },
  { header: "Cycles done", cell: (row) => `${row.completed_cycle_count} of ${row.cycles}`, align: "right" },
  { header: "Contributed", cell: (row) => formatNaira(row.total_contributed), align: "right" },
  { header: "Created", cell: (row) => formatDateTime(row.created_at) },
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
        title="Commitments"
        description="Every Sura lock with at least one of your customers in it. Open one to review its health or raise a support case."
      />

      <FilterBar>
        <SearchFilter
          id="commitment-search"
          label="Search commitments"
          placeholder="Title, commitment ID, vendor or member ID"
          value={search}
          onChange={setSearch}
        />
        <SelectFilter id="commitment-status" label="Status" value={status} onChange={setStatus} options={statusOptions} />
      </FilterBar>

      <QueryState
        query={query}
        noun="commitments"
        skeleton={<TableSkeleton />}
        isEmpty={(rows) => rows.length === 0}
        empty={
          <EmptyState
            icon={RepeatIcon}
            title={filtered ? "No commitments match" : "No commitments yet"}
            description={
              filtered
                ? "Try a different search or clear the status filter."
                : "They appear here once one of your customers creates or joins a Sura lock."
            }
          />
        }
      >
        {(rows) => (
          <DataTable
            caption="Commitments"
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
