"use client"

import { useState, type FormEvent } from "react"
import { HugeiconsIcon } from "@hugeicons/react"
import { ChartLineData01Icon, Key01Icon, RepeatIcon, SentIcon, ViewIcon, ViewOffSlashIcon } from "@hugeicons/core-free-icons"
import { callIntegration, listBankUsers, type IntegrationResponse } from "@/actions/bank"
import { endpoints } from "@/config/endpoints"
import { env } from "@/config/env"
import { sampleRequest } from "@/config/for-banks"
import { useBankAccess } from "@/hooks/use-bank-access"
import { useMutation } from "@/hooks/use-mutation"
import { useQuery } from "@/hooks/use-query"
import { Section } from "@/components/bank/page-header"
import { StatusBadge } from "@/components/bank/status-badge"
import { CodeBlock } from "@/components/shared/code-block"
import { CopyButton } from "@/components/shared/copy-button"
import { Alert } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { ChoiceCards } from "@/components/ui/choice-cards"
import { Field } from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import type { ChoiceOption } from "@/types"

type Endpoint = "score" | "commitments"

const endpointOptions: ChoiceOption<Endpoint>[] = [
  {
    value: "score",
    label: "customer score",
    description: "score, tier and the five-pillar breakdown. needs score:read.",
    icon: ChartLineData01Icon,
  },
  {
    value: "commitments",
    label: "customer commitments",
    description: "locks, payout slot and voucher outcome. needs commitments:read.",
    icon: RepeatIcon,
  },
]

const pathFor = (endpoint: Endpoint, userId: string) =>
  endpoint === "score" ? endpoints.integrations.customerScore(userId) : endpoints.integrations.customerCommitments(userId)

const baseUrl = env.apiUrl || "https://<sura-api>"
// amara, from the seeded demo story, for roles that can't list customers
const sampleCustomer = "usr_demo_amara"
const noFilters: [object] = [{}]

// what a status means for whoever is integrating, in their words
function statusHint(status: number, endpoint: Endpoint) {
  if (status >= 200 && status < 300) return null
  if (status === 401) return "the key is missing, mistyped, expired or revoked."
  if (status === 403) return `this key doesn't hold the ${endpoint === "score" ? "score:read" : "commitments:read"} scope.`
  if (status === 404) return "no customer of your bank has that sura id."
  if (status === 429) return "too many requests. wait a moment and send again."
  return "the api couldn't answer. try again shortly."
}

// keys longer than the stored prefix are shown masked, so a screen share never leaks one
const maskKey = (key: string) => (key.length > 14 ? `${key.slice(0, 14)}••••••••` : key)

type ApiPlaygroundPanelProps = {
  apiKey: string
  onApiKeyChange: (key: string) => void
  onCreateKey: () => void
}

// B11. a live call to the machine api, made from this browser exactly as the bank's
// own server would make it. the key stays in memory on this page and is never stored
export function ApiPlaygroundPanel({ apiKey, onApiKeyChange, onCreateKey }: ApiPlaygroundPanelProps) {
  const { can } = useBankAccess()
  const canListCustomers = can("bank:users:read")
  const customers = useQuery(listBankUsers, canListCustomers ? noFilters : null)
  const [endpoint, setEndpoint] = useState<Endpoint>("score")
  const [picked, setPicked] = useState("")
  const [showKey, setShowKey] = useState(false)
  const [keyError, setKeyError] = useState<string>()
  const [response, setResponse] = useState<(IntegrationResponse & { endpoint: Endpoint; path: string }) | null>(null)
  const send = useMutation(callIntegration)

  // until someone picks, the first customer on the list, or amara from the demo story
  const customerId = (picked || customers.data?.[0]?.user_id || (canListCustomers ? "" : sampleCustomer)).trim()
  const path = pathFor(endpoint, customerId || "{user_id}")
  const curl = (key: string) => `curl ${baseUrl}${path} \\\n  -H "${sampleRequest.apiKeyHeader}: ${key}"`

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!apiKey.trim()) {
      setKeyError("paste an api key, or create one first")
      return
    }
    if (!customerId) return
    const result = await send.mutate(path, apiKey.trim())
    if (result.ok) setResponse({ ...result.data, endpoint, path })
  }

  const ok = response && response.status >= 200 && response.status < 300
  const hint = response && statusHint(response.status, response.endpoint)

  return (
    <Section
      title="try the api"
      description="make a real request with one of your keys and see exactly what your servers would get back."
    >
      <div className="grid gap-4 lg:grid-cols-[minmax(0,5fr)_minmax(0,6fr)] lg:items-start">
        <form noValidate onSubmit={handleSubmit} className="card-raised flex flex-col gap-5 rounded-2xl p-4 sm:p-5">
          <Field
            id="playground-key"
            label="api key"
            error={keyError}
            hint={
              <>
                kept on this page only.{" "}
                <button
                  type="button"
                  title="go to api keys and create a sandbox key"
                  onClick={onCreateKey}
                  className="cursor-pointer font-extrabold text-link underline-offset-4 hover:underline"
                >
                  create a key
                </button>{" "}
                if you don&apos;t have one.
              </>
            }
          >
            <div className="relative">
              <HugeiconsIcon
                icon={Key01Icon}
                size={17}
                strokeWidth={2.2}
                className="pointer-events-none absolute top-1/2 left-4 -translate-y-1/2 text-muted-foreground"
              />
              <Input
                id="playground-key"
                type={showKey ? "text" : "password"}
                value={apiKey}
                onChange={(event) => {
                  onApiKeyChange(event.target.value)
                  if (keyError) setKeyError(undefined)
                }}
                invalid={Boolean(keyError)}
                aria-describedby={keyError ? "playground-key-error" : "playground-key-hint"}
                autoComplete="off"
                spellCheck={false}
                placeholder={sampleRequest.placeholderKey}
                className="h-12 pr-12 pl-11 font-mono text-sm"
              />
              <button
                type="button"
                aria-label={showKey ? "hide key" : "show key"}
                title={showKey ? "hide key" : "show key"}
                onClick={() => setShowKey((value) => !value)}
                className="absolute top-1/2 right-2 flex size-9 -translate-y-[calc(50%+1px)] cursor-pointer items-center justify-center rounded-full text-muted-foreground transition-colors hover:bg-cloud hover:text-link"
              >
                <HugeiconsIcon icon={showKey ? ViewOffSlashIcon : ViewIcon} size={18} strokeWidth={2.2} />
              </button>
            </div>
          </Field>

          <div className="flex flex-col gap-2">
            <span id="playground-endpoint-label" className="text-sm font-extrabold">
              endpoint
            </span>
            <ChoiceCards
              name="playground-endpoint"
              labelledBy="playground-endpoint-label"
              options={endpointOptions}
              value={endpoint}
              onChange={setEndpoint}
            />
          </div>

          {canListCustomers ? (
            <Field id="playground-customer" label="customer">
              <Select
                items={(customers.data ?? []).map((row) => ({ value: row.user_id, label: row.name }))}
                value={customerId || null}
                onValueChange={(next) => setPicked(next ?? "")}
                disabled={!customers.data?.length}
              >
                <SelectTrigger id="playground-customer" title="the customer to look up">
                  <SelectValue placeholder={customers.isLoading ? "loading customers…" : "no customers yet"} />
                </SelectTrigger>
                <SelectContent>
                  {customers.data?.map((row) => (
                    <SelectItem key={row.user_id} value={row.user_id}>
                      <span className="flex min-w-0 items-center justify-between gap-3">
                        <span className="truncate">{row.name}</span>
                        <span className="shrink-0 font-mono text-xs text-muted-foreground normal-case">{row.user_id}</span>
                      </span>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </Field>
          ) : (
            <Field id="playground-customer" label="sura customer id">
              <Input
                id="playground-customer"
                value={picked || sampleCustomer}
                onChange={(event) => setPicked(event.target.value)}
                autoComplete="off"
                spellCheck={false}
                className="h-12 font-mono text-sm"
              />
            </Field>
          )}

          {send.error && (
            <Alert variant="error" title="the request didn't reach sura">
              check your connection, then send again.
            </Alert>
          )}

          <Button type="submit" loading={send.isPending} disabled={!customerId} title={`GET ${path}`}>
            <HugeiconsIcon icon={SentIcon} size={18} strokeWidth={2.2} />
            send request
          </Button>
        </form>

        <div className="flex min-w-0 flex-col gap-4">
          <div className="flex flex-col gap-2">
            <div className="flex items-center justify-between gap-3">
              <p className="text-sm font-extrabold">request</p>
              <CopyButton value={curl(apiKey.trim() || "<your api key>")} label="copy curl" />
            </div>
            <CodeBlock code={curl(apiKey.trim() ? maskKey(apiKey.trim()) : "<your api key>")} />
          </div>

          <div className="flex flex-col gap-2" aria-live="polite">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <p className="text-sm font-extrabold">response</p>
              {response && (
                <span className="flex items-center gap-2">
                  <StatusBadge
                    status={String(response.status)}
                    label={String(response.status)}
                    tone={ok ? "gold" : response.status >= 500 ? "warning" : "danger"}
                  />
                  <span className="text-xs font-bold text-muted-foreground tabular-nums">{response.durationMs} ms</span>
                </span>
              )}
            </div>
            {response ? (
              <>
                {hint && <Alert variant="error">{hint}</Alert>}
                <CodeBlock
                  label={`GET ${response.path}`}
                  code={typeof response.body === "string" ? response.body || "(empty body)" : JSON.stringify(response.body, null, 2)}
                  className="max-h-[32rem] overflow-y-auto"
                />
              </>
            ) : (
              <p className="rounded-2xl border-2 border-dashed border-hairline px-4 py-10 text-center text-sm font-semibold text-muted-foreground">
                send a request to see the live response here.
              </p>
            )}
          </div>
        </div>
      </div>
    </Section>
  )
}
