"use client"

import { useState } from "react"
import Link from "next/link"
import { Audit01Icon, Download01Icon } from "@hugeicons/core-free-icons"
import { HugeiconsIcon } from "@hugeicons/react"
import { exportAuditLog, getAuditLog } from "@/actions/bank"
import { routes } from "@/config/routes"
import { useDebouncedValue } from "@/hooks/use-debounced-value"
import { useMutation } from "@/hooks/use-mutation"
import { useQuery } from "@/hooks/use-query"
import { DataTable, TableSkeleton, type Column } from "@/components/bank/data-table"
import { DateFilter, FilterBar, SearchFilter, SelectFilter } from "@/components/bank/filters"
import { PageHeader } from "@/components/bank/page-header"
import { QueryState } from "@/components/bank/query-state"
import { StatusBadge } from "@/components/bank/status-badge"
import { EmptyState } from "@/components/shared/empty-state"
import { Alert } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import type { AuditLogEntry } from "@/types"
import { formatDateTime, humanize } from "@/utils/format"

type Kind = AuditLogEntry["type"]

const kindOptions: { value: Kind; label: string }[] = [
  { value: "score", label: "score changes" },
  { value: "bank_access", label: "staff actions" },
]

const idLink = (href: string, id: string) => (
  <Link href={href} className="font-mono text-xs text-link normal-case underline-offset-4 hover:underline">
    {id}
  </Link>
)

const columns: Column<AuditLogEntry>[] = [
  {
    header: "what happened",
    cell: (row) => (row.type === "score" ? row.reason ?? humanize(row.event_type) : humanize(row.event_type)),
  },
  {
    header: "kind",
    cell: (row) => <StatusBadge status={row.type} label={row.type === "score" ? "score" : "staff"} tone={row.type === "score" ? "gold" : "indigo"} />,
  },
  {
    header: "customer or subject",
    cell: (row) =>
      row.user_id
        ? idLink(routes.bank.user(row.user_id), row.user_id)
        : <span className="font-mono text-xs normal-case">{row.subject_id ?? "—"}</span>,
  },
  {
    header: "actor",
    cell: (row) => <span className="font-mono text-xs normal-case">{row.actor_id ?? "sura"}</span>,
  },
  { header: "when", cell: (row) => formatDateTime(row.occurred_at) },
]

// the date inputs give a calendar day; the api compares full timestamps
const startOfDay = (date: string) => (date ? `${date}T00:00:00` : undefined)
const endOfDay = (date: string) => (date ? `${date}T23:59:59` : undefined)

function downloadCsv(csv: string) {
  const url = URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8" }))
  const link = document.createElement("a")
  link.href = url
  link.download = `sura-audit-log-${new Date().toISOString().slice(0, 10)}.csv`
  link.click()
  URL.revokeObjectURL(url)
}

// B7. pillar-level filtering isn't offered because the api doesn't store which
// pillar moved per row; each row's breakdown is on the customer's profile (B6)
export function AuditLogScreen() {
  const [userSearch, setUserSearch] = useState("")
  const [kind, setKind] = useState<Kind | "">("")
  const [dateFrom, setDateFrom] = useState("")
  const [dateTo, setDateTo] = useState("")
  const userId = useDebouncedValue(userSearch.trim())
  const query = useQuery(getAuditLog, [
    { user_id: userId, date_from: startOfDay(dateFrom), date_to: endOfDay(dateTo) },
  ])
  const exporter = useMutation(exportAuditLog)
  const filtered = Boolean(userId || kind || dateFrom || dateTo)

  async function handleExport() {
    const result = await exporter.mutate()
    if (result.ok) downloadCsv(result.data)
  }

  return (
    <>
      <PageHeader
        title="audit log"
        description="every score change across your customers, and every action your staff took in this console."
        actions={
          <Button type="button" variant="outline" size="sm" loading={exporter.isPending} onClick={handleExport}>
            {!exporter.isPending && <HugeiconsIcon icon={Download01Icon} size={18} strokeWidth={2.2} />}
            export csv
          </Button>
        }
      />

      {exporter.error && (
        <Alert variant="error" title="couldn't export the log" className="mb-5">
          {exporter.error.message}
        </Alert>
      )}

      <FilterBar>
        <SearchFilter
          id="audit-user"
          label="filter by customer id"
          placeholder="exact sura customer id, e.g. usr_demo_amara"
          value={userSearch}
          onChange={setUserSearch}
        />
        <SelectFilter id="audit-kind" label="show" value={kind} onChange={setKind} options={kindOptions} allLabel="everything" />
        <DateFilter id="audit-from" label="from" value={dateFrom} onChange={setDateFrom} />
        <DateFilter id="audit-to" label="to" value={dateTo} onChange={setDateTo} />
      </FilterBar>

      <QueryState
        query={query}
        noun="the audit log"
        skeleton={<TableSkeleton rows={8} />}
        isEmpty={(rows) => !rows.some((row) => !kind || row.type === kind)}
        empty={
          <EmptyState
            icon={Audit01Icon}
            title={filtered ? "nothing matches these filters" : "the log is empty"}
            description={filtered ? "try a wider date range or another customer." : "score changes and staff actions will appear here."}
          />
        }
      >
        {(rows) => (
          <DataTable
            caption="audit log"
            columns={columns}
            rows={kind ? rows.filter((row) => row.type === kind) : rows}
            rowKey={(row) => `${row.type}-${row.id}`}
          />
        )}
      </QueryState>
    </>
  )
}
