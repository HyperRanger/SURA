"use client"

import { useState } from "react"
import { Flag02Icon } from "@hugeicons/core-free-icons"
import { listFlags, runRiskRules } from "@/actions/bank"
import { flagRules, flagSeverities, flagStatuses } from "@/config/bank"
import { routes } from "@/config/routes"
import { useBankAccess } from "@/hooks/use-bank-access"
import { useMutation } from "@/hooks/use-mutation"
import { useQuery } from "@/hooks/use-query"
import { ActionError } from "@/components/bank/action-kit"
import { DataTable, TableSkeleton, type Column } from "@/components/bank/data-table"
import { FilterBar, SelectFilter, toOptions } from "@/components/bank/filters"
import { PageHeader } from "@/components/bank/page-header"
import { QueryState } from "@/components/bank/query-state"
import { StatusBadge } from "@/components/bank/status-badge"
import { EmptyState } from "@/components/shared/empty-state"
import { Alert } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import type { FlagStatus, RiskFlag, RiskRuleRun } from "@/types"
import { formatDateTime, humanize } from "@/utils/format"

const columns: Column<RiskFlag>[] = [
  { header: "Rule that fired", cell: (row) => humanize(row.rule) },
  { header: "Severity", cell: (row) => <StatusBadge status={row.severity} /> },
  { header: "Status", cell: (row) => <StatusBadge status={row.status} /> },
  { header: "Customer", cell: (row) => <span className="font-mono text-xs">{row.user_id}</span> },
  { header: "Raised", cell: (row) => formatDateTime(row.created_at) },
]

const severityOptions = toOptions(flagSeverities)
const ruleOptions = toOptions(flagRules)

// B8. opens on the open flags, since those are the ones waiting on an analyst
export function FlagsScreen() {
  const [status, setStatus] = useState<FlagStatus | "">("open")
  const [severity, setSeverity] = useState<(typeof flagSeverities)[number] | "">("")
  const [rule, setRule] = useState<(typeof flagRules)[number] | "">("")
  const query = useQuery(listFlags, [{ status: status || undefined, severity, rule }])
  const { can } = useBankAccess()
  const runner = useMutation(runRiskRules)
  const [lastRun, setLastRun] = useState<RiskRuleRun | null>(null)

  async function handleRun() {
    const result = await runner.mutate(null)
    if (result.ok) {
      setLastRun(result.data)
      query.retry()
    }
  }

  return (
    <>
      <PageHeader
        title="Risk flags"
        description="Patterns Sura's fraud rules detected. Review the evidence, then dismiss, confirm or escalate."
        actions={
          can("bank:flags:write") && (
            <Button type="button" variant="outline" size="sm" loading={runner.isPending} onClick={handleRun}>
              Run review rules
            </Button>
          )
        }
      />

      <ActionError error={runner.error} className="mb-5" />
      {lastRun && (
        <Alert
          variant="info"
          className="mb-5"
          title={`${lastRun.flags_created_count} new ${lastRun.flags_created_count === 1 ? "flag" : "flags"}`}
        >
          Checked {lastRun.members_evaluated} customers against {lastRun.rules_run.length} rules. Rules only open flags;
          they never restrict an account.
        </Alert>
      )}

      <FilterBar>
        <SelectFilter id="flag-status" label="Status" value={status} onChange={setStatus} options={flagStatuses} />
        <SelectFilter id="flag-severity" label="Severity" value={severity} onChange={setSeverity} options={severityOptions} />
        <SelectFilter id="flag-rule" label="Rule" value={rule} onChange={setRule} options={ruleOptions} className="sm:w-60" />
      </FilterBar>

      <QueryState
        query={query}
        noun="risk flags"
        skeleton={<TableSkeleton />}
        isEmpty={(rows) => rows.length === 0}
        empty={
          <EmptyState
            icon={Flag02Icon}
            title={status === "open" && !severity && !rule ? "No open flags" : "No flags match"}
            description={
              status === "open" && !severity && !rule
                ? "Nothing is waiting for review. Set status to All to see resolved flags."
                : "Try another status, severity or rule."
            }
          />
        }
      >
        {(rows) => (
          <DataTable
            caption="Risk flags"
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
