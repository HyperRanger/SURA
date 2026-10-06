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
  { header: "rule that fired", cell: (row) => humanize(row.rule) },
  { header: "severity", cell: (row) => <StatusBadge status={row.severity} /> },
  { header: "status", cell: (row) => <StatusBadge status={row.status} /> },
  { header: "customer", cell: (row) => <span className="font-mono text-xs normal-case">{row.user_id}</span> },
  { header: "raised", cell: (row) => formatDateTime(row.created_at) },
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
        title="risk flags"
        description="patterns sura's fraud rules detected. review the evidence, then dismiss, confirm or escalate."
        actions={
          can("bank:flags:write") && (
            <Button type="button" variant="outline" size="sm" loading={runner.isPending} onClick={handleRun}>
              run review rules
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
          checked {lastRun.members_evaluated} customers against {lastRun.rules_run.length} rules. rules only open flags;
          they never restrict an account.
        </Alert>
      )}

      <FilterBar>
        <SelectFilter id="flag-status" label="status" value={status} onChange={setStatus} options={flagStatuses} />
        <SelectFilter id="flag-severity" label="severity" value={severity} onChange={setSeverity} options={severityOptions} />
        <SelectFilter id="flag-rule" label="rule" value={rule} onChange={setRule} options={ruleOptions} className="sm:w-60" />
      </FilterBar>

      <QueryState
        query={query}
        noun="risk flags"
        skeleton={<TableSkeleton />}
        isEmpty={(rows) => rows.length === 0}
        empty={
          <EmptyState
            icon={Flag02Icon}
            title={status === "open" && !severity && !rule ? "no open flags" : "no flags match"}
            description={
              status === "open" && !severity && !rule
                ? "nothing is waiting for review. set status to all to see resolved flags."
                : "try another status, severity or rule."
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
