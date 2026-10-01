"use client"

import { useState } from "react"
import { Flag02Icon } from "@hugeicons/core-free-icons"
import { listFlags } from "@/actions/bank"
import { flagSeverities, flagStatuses } from "@/config/bank"
import { routes } from "@/config/routes"
import { useQuery } from "@/hooks/use-query"
import { DataTable, TableSkeleton, type Column } from "@/components/bank/data-table"
import { FilterBar, SelectFilter, toOptions } from "@/components/bank/filters"
import { PageHeader } from "@/components/bank/page-header"
import { QueryState } from "@/components/bank/query-state"
import { StatusBadge } from "@/components/bank/status-badge"
import { EmptyState } from "@/components/shared/empty-state"
import type { FlagStatus, RiskFlag } from "@/types"
import { formatDateTime, humanize } from "@/utils/format"

const columns: Column<RiskFlag>[] = [
  { header: "rule that fired", cell: (row) => humanize(row.rule) },
  { header: "severity", cell: (row) => <StatusBadge status={row.severity} /> },
  { header: "status", cell: (row) => <StatusBadge status={row.status} /> },
  { header: "customer", cell: (row) => <span className="font-mono text-xs normal-case">{row.user_id}</span> },
  { header: "raised", cell: (row) => formatDateTime(row.created_at) },
]

const severityOptions = toOptions(flagSeverities)

// B8. opens on the open flags, since those are the ones waiting on an analyst
export function FlagsScreen() {
  const [status, setStatus] = useState<FlagStatus | "">("open")
  const [severity, setSeverity] = useState<(typeof flagSeverities)[number] | "">("")
  const query = useQuery(listFlags, [{ status: status || undefined, severity }])

  return (
    <>
      <PageHeader
        title="risk flags"
        description="patterns sura's fraud rules detected. review the evidence, then dismiss, confirm or escalate."
      />

      <FilterBar>
        <SelectFilter id="flag-status" label="status" value={status} onChange={setStatus} options={flagStatuses} />
        <SelectFilter id="flag-severity" label="severity" value={severity} onChange={setSeverity} options={severityOptions} />
      </FilterBar>

      <QueryState
        query={query}
        noun="risk flags"
        skeleton={<TableSkeleton />}
        isEmpty={(rows) => rows.length === 0}
        empty={
          <EmptyState
            icon={Flag02Icon}
            title={status === "open" && !severity ? "no open flags" : "no flags match"}
            description={
              status === "open" && !severity
                ? "nothing is waiting for review. set status to all to see resolved flags."
                : "try another status or severity."
            }
          />
        }
      >
        {(rows) => (
          <DataTable
            caption="risk flags"
            columns={columns}
            rows={rows}
            rowKey={(row) => row.flag_id}
            rowHref={(row) => routes.bank.flag(row.flag_id)}
          />
        )}
      </QueryState>
    </>
  )
}
