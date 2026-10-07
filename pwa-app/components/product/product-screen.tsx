"use client"

import Link from "next/link"
import Image from "next/image"
import { usePathname, useRouter } from "next/navigation"
import { useEffect, useMemo, useState } from "react"
import { sessionStore, endSession } from "@/lib/session"
import { useStoredValue } from "@/hooks/use-stored-value"
import { createStoredValue } from "@/lib/storage"
import { requestLoginCode } from "@/actions/auth"
import { rememberChallenge } from "@/lib/session"
import { Button } from "@/components/ui/button"
import { Logo } from "@/components/layout/logo"
import { ThemeToggle } from "@/components/layout/theme-toggle"
import { formatDate, formatNaira } from "@/utils/format"
import {
  cancelCommitment, contribute, createLock, getCommitment, getCommitmentActivity, getCommitments, getInvitePreview, getRedemption, getScoreEntry,
  getMemberHome, getMe, getNotifications, getRedemptions, getScore, getScoreHistory, getVoucher,
  getVendorHome, getVendors, joinCommitment, logout, previewLock, recordConsent, resolveMember,
  redeemVoucher, validateVoucher,
} from "@/actions/app"

type Role = "individual" | "vendor"
// Screen payloads follow the backend's per-route response contracts.
// eslint-disable-next-line @typescript-eslint/no-explicit-any
type Row = Record<string, any>
type LockDraft = { form: Row; members: Row[]; step: number; consentAccepted: boolean; lockPreview: Row | null }
const lockDraftStore = createStoredValue<LockDraft>("session", "sura.lock-draft")
const emptyLockDraft: LockDraft = { form: { title: "", vendor_id: "", contribution_amount: "", contribution_frequency: "weekly", cycles: 2 }, members: [], step: 0, consentAccepted: false, lockPreview: null }

const memberNav = [
  ["Home", "/app", "⌂"], ["Locks", "/app/commitments", "▤"], ["Score", "/app/score", "◉"], ["Profile", "/app/profile", "○"],
]
const vendorNav = [
  ["Terminal", "/vendor", "⌂"], ["Redeem", "/vendor/redeem", "▣"], ["History", "/vendor/history", "↻"],
]

function money(value: unknown) { return formatNaira(Number(value ?? 0)) }
function titleCase(value: string) { return value.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase()) }
function Panel({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return <section className={`rounded-xl border border-hairline bg-card p-5 shadow-[0_3px_12px_-10px_rgba(22,20,43,.24)] ${className}`}>{children}</section>
}
function SectionTitle({ title, action }: { title: string; action?: React.ReactNode }) {
  return <div className="mb-3 flex items-center justify-between"><h2 className="text-base font-extrabold">{title}</h2>{action}</div>
}

export function ProductScreen({ role, segments }: { role: Role; segments: string[] }) {
  const router = useRouter()
  const pathname = usePathname()
  const session = useStoredValue(sessionStore)
  const draft = useStoredValue(lockDraftStore)
  const [data, setData] = useState<Row | Row[] | null>(null)
  const [loading, setLoading] = useState(!(role === "vendor" && segments[0] === "login"))
  const [error, setError] = useState("")
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState("")
  const currentDraft = draft ?? emptyLockDraft
  const form = currentDraft.form
  const members = currentDraft.members
  const step = currentDraft.step
  const consentAccepted = currentDraft.consentAccepted
  const lockPreview = currentDraft.lockPreview
  const updateDraft = (updates: Partial<LockDraft>) => lockDraftStore.write({ ...(lockDraftStore.read() ?? emptyLockDraft), ...updates })
  const setForm = (value: Row | ((current: Row) => Row)) => updateDraft({ form: typeof value === "function" ? value(form) : value })
  const setMembers = (value: Row[] | ((current: Row[]) => Row[])) => updateDraft({ members: typeof value === "function" ? value(members) : value })
  const setStep = (value: number | ((current: number) => number)) => updateDraft({ step: typeof value === "function" ? value(step) : value })
  const setConsentAccepted = (value: boolean) => updateDraft({ consentAccepted: value })
  const setLockPreview = (value: Row | null) => updateDraft({ lockPreview: value })
  const [code, setCode] = useState("")
  const [phone, setPhone] = useState("")
  const [vendorList, setVendorList] = useState<Row[]>([])
  const [listTab, setListTab] = useState("active")
  const [memberPhone, setMemberPhone] = useState("")
  const [loadedPath, setLoadedPath] = useState("")
  const page = segments.join("/")
  const isVendor = role === "vendor"
  const screenLoading = loading || (loadedPath !== pathname && !(isVendor && !session && segments[0] === "login"))
  const nav = isVendor ? vendorNav : memberNav
  const focused = ["commitments/new", "join", "consent"].includes(page) || page.startsWith("join/") || (isVendor && segments[0] === "login") || page.includes("/contribute") || page.includes("/voucher") || page.startsWith("redeem")
  const screenTitle = useMemo(() => {
    if (isVendor) return page === "" ? "Merchant terminal" : page.startsWith("redeem") ? "Redeem voucher" : page.startsWith("history") ? "Settlement history" : titleCase(page)
    if (!page) return "Home"
    if (page.startsWith("commitments/new")) return "Create a Lock"
    if (page.startsWith("commitments/")) return page.includes("contribute") ? "Contribution" : page.includes("voucher") ? "Your voucher" : "Lock details"
    if (page.startsWith("join")) return "Join a Lock"
    return titleCase(page.split("/").at(-1) || "Home")
  }, [page, isVendor])

  useEffect(() => {
    if (!session) { router.replace("/login"); return }
    if (session.role !== role) { router.replace(session.role === "vendor" ? "/vendor" : "/app"); return }
    let active = true
    const id = segments[1]
    const load = async () => {
      if (isVendor) {
        if (segments[0] === "login") return null
        if (segments[0] === "history") return segments[1] ? getRedemption(segments[1]) : getRedemptions()
        if (segments[0] === "redeem") return null
        return getVendorHome()
      }
      if (!segments.length || segments[0] === "welcome") return getMemberHome()
      if (segments[0] === "commitments" && segments.includes("voucher")) return getVoucher(segments[1], segments.at(-2) || "1")
      if (segments[0] === "commitments" && segments[1] && segments[1] !== "new") {
        const [lock, activity] = await Promise.all([getCommitment(id), getCommitmentActivity(id)])
        const events = Array.isArray(activity) ? activity : (activity as Row).activities ?? []
        const commitment = lock as Row
        const cycle = commitment.current_cycle ?? {}
        return { ...commitment, activity: events, progress_percent: cycle.progress_percent ?? 0, paid_count: cycle.paid_member_count ?? 0, paid_percent: cycle.progress_percent ?? 0, member_count: cycle.member_count ?? commitment.members?.length ?? 0, next_payout: { beneficiary_name: cycle.beneficiary_first_name } }
      }
      if (segments[0] === "commitments") return getCommitments()
      if (segments[0] === "join" && segments[1]) return getInvitePreview(segments[1])
      if (segments[0] === "score") return segments[1] === "history" ? segments[2] ? getScoreEntry(session.userId, segments[2]) : getScoreHistory(session.userId) : getScore(session.userId)
      if (segments[0] === "profile") return getMe()
      if (segments[0] === "notifications") return getNotifications()
      if (segments[0] === "consent") return null
      return null
    }
    load().then((result) => { if (active && result !== null) { setData(result as Row | Row[]); setError("") } }).catch((reason) => {
      if (active) setError(reason instanceof Error ? reason.message : "We could not load this screen.")
    }).finally(() => { if (active) { setLoading(false); setLoadedPath(pathname) } })
    if (!isVendor && segments[0] === "commitments" && segments[1] === "new") getVendors().then((items) => active && setVendorList(items as Row[])).catch(() => active && setVendorList([]))
    return () => { active = false }
  }, [pathname, session, role, router, isVendor, segments])

  const run = async (action: () => Promise<unknown>, done?: (result: Row) => void) => {
    setBusy(true); setError(""); setMessage("")
    try { const result = await action(); done?.(result as Row) }
    catch (reason) { setError(reason instanceof Error ? reason.message : "That did not go through. Please try again.") }
    finally { setBusy(false) }
  }
  const signOut = async () => { try { await logout() } catch { /* local sign-out still clears this device */ } endSession(); router.replace("/login") }
  const navLink = (item: string[]) => {
    const active = pathname === item[1] || (!(["/app", "/vendor"].includes(item[1])) && pathname.startsWith(`${item[1]}/`))
    return <Link key={item[1]} href={item[1]} aria-current={active ? "page" : undefined} className={`flex min-w-0 flex-col items-center gap-1 px-2 py-1 text-[11px] font-bold transition-colors ${active ? "text-primary" : "text-muted-foreground"}`}><span className="text-[21px] leading-5" aria-hidden>{item[2]}</span><span>{item[0]}</span></Link>
  }

  return <div className="min-h-dvh bg-background text-foreground">
    <div className="mx-auto min-h-dvh max-w-6xl md:grid md:grid-cols-[220px_minmax(0,1fr)]">
      {!focused && <aside className="hidden border-r border-hairline bg-card px-5 py-7 md:flex md:flex-col">
        <Link href={isVendor ? "/vendor" : "/app"} aria-label="Sura home" className="mb-10 flex items-center gap-3"><Logo /></Link>
        <nav className="grid gap-2">{nav.map((item) => <Link key={item[1]} href={item[1]} className={`flex items-center gap-3 rounded-lg px-3 py-3 text-sm font-bold ${pathname === item[1] ? "bg-primary-soft text-primary" : "text-muted-foreground hover:bg-muted"}`}><span aria-hidden className="w-5 text-center text-lg">{item[2]}</span>{item[0]}</Link>)}</nav>
        <button className="mt-auto rounded-lg px-3 py-3 text-left text-sm font-bold text-muted-foreground hover:bg-muted" onClick={signOut}>Sign out</button>
      </aside>}
      <div className="min-w-0">
        <header className="sticky top-0 z-20 border-b border-hairline/80 bg-background/90 text-foreground backdrop-blur">
          <div className="mx-auto flex h-16 max-w-3xl items-center justify-between px-5">
            <div className="flex min-w-0 items-center gap-2">{focused && <Link href={isVendor ? "/vendor" : "/app"} className="grid size-9 shrink-0 place-items-center rounded-full border border-hairline text-lg" aria-label="Back">‹</Link>}<Image src="/sura-mark.svg" alt="Sura" width={32} height={32} priority className="shrink-0 sm:hidden"/><div className="hidden sm:block"><Logo /></div><div className="min-w-0"><p className="text-[10px] font-extrabold uppercase tracking-[.08em] text-muted-foreground sm:text-[11px] sm:tracking-[.12em]">{isVendor ? "Sura for business" : "Sura Lock"}</p><h1 className="truncate text-sm font-extrabold">{screenTitle}</h1></div></div>
            <div className="flex shrink-0 items-center gap-2">
              <ThemeToggle />
              {!focused && <Link href={isVendor ? "/vendor/history" : "/app/notifications"} className="grid size-10 place-items-center rounded-full border border-hairline bg-card text-lg" aria-label={isVendor ? "History" : "Notifications"}>{isVendor ? "↻" : "♧"}</Link>}
              {isVendor && <button type="button" onClick={signOut} className="rounded-full border border-hairline px-3 py-2 text-xs font-extrabold text-foreground hover:bg-muted" aria-label="Sign out of vendor account">Sign out</button>}
            </div>
          </div>
        </header>
        <main className={`mx-auto max-w-3xl px-5 pb-28 pt-6 ${focused ? "md:pb-10 md:pt-8" : ""}`}>
          {error && <div role="alert" className="mb-5 flex items-start justify-between gap-3 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-800"><p>{error}</p><button className="shrink-0 font-bold underline" onClick={() => router.refresh()}>Retry</button></div>}
          {message && <div role="status" className="mb-5 rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm font-bold text-emerald-800">{message}</div>}
          {screenLoading ? <div className="grid gap-4" aria-label="Loading"><div className="h-36 animate-pulse rounded-xl bg-muted"/><div className="h-24 animate-pulse rounded-xl bg-muted"/><div className="h-24 animate-pulse rounded-xl bg-muted"/></div> : isVendor ? renderVendor() : renderMember()}
        </main>
      </div>
    </div>
    {!focused && <nav aria-label="Main navigation" className="fixed inset-x-0 bottom-0 z-30 border-t border-hairline bg-card/95 pb-[env(safe-area-inset-bottom)] backdrop-blur md:hidden"><div className="mx-auto flex h-[68px] max-w-lg items-center justify-around">{nav.map(navLink)}</div></nav>}
  </div>

  function renderVendor(): React.ReactNode {
    const rows = (Array.isArray(data) ? data : (data as Row)?.recent_redemptions ?? []) as Row[]
    if (segments[0] === "login") return <Panel><p className="text-xs font-extrabold uppercase tracking-wider text-primary">Merchant access</p><h2 className="mt-2 text-xl font-extrabold">Sign in to your terminal</h2><p className="mt-2 text-sm text-muted-foreground">Use the verified business account phone number.</p><label className="mt-5 block text-sm font-bold" htmlFor="vendor-phone">Phone number</label><input id="vendor-phone" type="tel" autoComplete="tel" value={phone} onChange={(e) => setPhone(e.target.value)} className="mt-2 h-12 w-full rounded-lg border border-hairline bg-background px-3 outline-none focus:ring-4 focus:ring-primary/15" placeholder="080 0000 0000"/><Button className="mt-4 w-full" loading={busy} disabled={phone.trim().length < 7} onClick={() => run(async () => { const challenge = await requestLoginCode({ phone }); rememberChallenge(challenge, { phone, next: "/vendor", isNewAccount: false }); router.push("/verify") })}>Continue</Button><p className="mt-3 text-center text-xs text-muted-foreground">Access is granted by the role on your Sura account.</p></Panel>
    if (segments[0] === "redeem" && segments[1] === "review") return <VendorReview />
    if (segments[0] === "redeem" && segments[1] === "success") return <Panel><p className="text-4xl text-success">✓</p><h2 className="mt-3 text-xl font-extrabold">Handover confirmed</h2><p className="mt-2 text-sm text-muted-foreground">{(data as Row)?.commitment_title || "Voucher redemption"}</p><p className="mt-4 text-2xl font-extrabold">{money((data as Row)?.amount)}</p><p className="mt-2 text-xs text-muted-foreground">{(data as Row)?.redeemed_at ? formatDate((data as Row).redeemed_at) : "Just now"} · Ref {(data as Row)?.redemption_id || "Recorded"}</p><p className="mt-4 rounded-lg bg-gold-soft p-3 text-xs text-gold-deep">Settlement is simulated in this MVP.</p><Link className="mt-5 inline-flex font-bold text-primary" href="/vendor/history">View settlement history →</Link></Panel>
    if (segments[0] === "redeem" && segments[1] === "rejected") return <Panel><h2 className="text-xl font-extrabold">Voucher not accepted</h2><p className="mt-2 text-sm text-muted-foreground">{message || "This voucher could not be redeemed. Check the code and try again."}</p><Button className="mt-5" onClick={() => router.replace("/vendor/redeem")}>Try another code</Button></Panel>
    if (segments[0] === "redeem") return <div className="space-y-5"><div><p className="text-sm text-muted-foreground">Scan the member’s voucher or enter its code.</p></div><Panel><label className="mb-2 block text-sm font-extrabold" htmlFor="voucher">Voucher code</label><input id="voucher" value={code} onChange={(e) => setCode(e.target.value.toUpperCase())} className="h-14 w-full rounded-lg border border-hairline bg-background px-4 text-lg font-bold tracking-[.1em] outline-none focus:ring-4 focus:ring-primary/15" placeholder="Enter code" autoCapitalize="characters"/><Button className="mt-4 w-full" loading={busy} disabled={!code.trim()} onClick={() => run(() => validateVoucher(code.trim()), (result) => { setData(result as Row); router.push("/vendor/redeem/review") })}>Validate voucher</Button><p className="mt-3 text-xs text-muted-foreground">The code is checked against your verified merchant account.</p></Panel><p className="text-center text-sm text-muted-foreground">Camera scanning can be used when a QR scanner is available on this device.</p></div>
    if (segments[0] === "history" && segments[1]) return <SimpleDetail value={data as Row} title="Redemption receipt"/>
    if (segments[0] === "history") return <div className="space-y-4"><SectionTitle title="Settled redemptions"/><Rows rows={rows} empty="No settled vouchers yet." moneyKey="amount"/></div>
    const home = data as Row | null
    return <div className="space-y-6"><div><p className="text-sm text-muted-foreground">{home?.merchant?.name || "Your verified business"}</p><h2 className="mt-1 text-2xl font-extrabold">Ready to serve?</h2></div><Button className="h-16 w-full justify-between rounded-xl px-5 text-base" onClick={() => router.push("/vendor/redeem")}>Redeem a voucher <span className="text-xl">→</span></Button><div className="grid grid-cols-2 gap-3"><Panel className="p-4"><p className="text-xs font-bold text-muted-foreground">Settled today</p><p className="mt-2 text-xl font-extrabold">{money(home?.today_settled_amount)}</p></Panel><Panel className="p-4"><p className="text-xs font-bold text-muted-foreground">Vouchers today</p><p className="mt-2 text-xl font-extrabold">{home?.today_redemption_count ?? 0}</p></Panel></div><div><SectionTitle title="Recent activity" action={<Link className="text-sm font-bold text-primary" href="/vendor/history">See all</Link>}/><Rows rows={rows.slice(0, 4)} empty="Completed voucher handovers will show here." moneyKey="amount"/></div></div>
  }

  function VendorReview() {
    const response = (data as Row) ?? {}
    const voucher = response.voucher ?? {}
    return <Panel><p className="text-sm font-bold text-muted-foreground">Check the voucher before handover</p><h2 className="mt-2 text-xl font-extrabold">{response.commitment_title || "Sura Lock"}</h2><dl className="mt-4 divide-y divide-hairline">{[["Beneficiary", response.beneficiary_first_name || "Member"], ["Cycle", voucher.cycle_number ?? "—"], ["Amount", money(voucher.amount)], ["Voucher status", titleCase(voucher.status || "ready")]].map(([label, value]) => <div key={label} className="flex justify-between gap-4 py-3 text-sm"><dt className="text-muted-foreground">{label}</dt><dd className="font-extrabold">{value}</dd></div>)}</dl><p className="mt-2 rounded-lg bg-gold-soft p-3 text-sm text-gold-deep">Confirm only after the goods or service have been handed over.</p><Button className="mt-5 w-full" loading={busy} onClick={() => run(() => redeemVoucher(code), (result) => { setData(result); router.push("/vendor/redeem/success") })}>Confirm handover</Button><button className="mt-4 w-full text-sm font-bold text-destructive" onClick={() => router.push("/vendor/redeem/rejected")}>Reject voucher</button></Panel>
  }

  function renderMember(): React.ReactNode {
    const obj = Array.isArray(data) ? null : data as Row | null
    const rows = (Array.isArray(data) ? data : obj?.commitments ?? obj?.entries ?? obj?.notifications ?? []) as Row[]
    if (page === "welcome") return <Welcome />
    if (!page) return <MemberHome value={obj}/>
    if (page === "commitments") return <Commitments rows={rows}/>
    if (page === "commitments/new") return <NewCommitment />
    if (page === "join") return <Join />
    if (page.startsWith("join/") && !page.endsWith("/done")) return <JoinPreview value={obj}/>
    if (page.endsWith("/done")) return <Panel><p className="text-4xl">✓</p><h2 className="mt-3 text-xl font-extrabold">You’re in</h2><p className="mt-2 text-sm text-muted-foreground">Your Lock membership is confirmed.</p><Link href="/app/commitments" className="mt-5 inline-flex font-bold text-primary">Go to commitments →</Link></Panel>
    if (page.startsWith("commitments/") && page.includes("/contribute/receipt")) return <Panel><p className="text-4xl">✓</p><h2 className="mt-3 text-xl font-extrabold">{message || "Contribution recorded"}</h2><p className="mt-2 text-sm text-muted-foreground">The contribution event is protected against duplicate retries.</p><Link href={`/app/commitments/${segments[1]}`} className="mt-5 inline-flex font-bold text-primary">Return to Lock →</Link></Panel>
    if (page.startsWith("commitments/") && page.endsWith("/contribute")) return <Contribute value={obj}/>
    if (page.startsWith("commitments/") && page.includes("/voucher")) return <Voucher value={obj}/>
    if (page.startsWith("commitments/") && segments[1]) return <Commitment value={obj}/>
    if (page === "consent") return <Consent />
    if (page === "score") return <Score value={obj}/>
    if (page === "score/history") return <ScoreHistory rows={rows}/>
    if (page.startsWith("score/history/")) return <SimpleDetail value={obj} title="Score change"/>
    if (page === "score/how-it-works") return <HowScore />
    if (page === "float") return <Panel><span className="rounded-full bg-gold-soft px-3 py-1 text-xs font-extrabold text-gold-deep">COMING SOON</span><h2 className="mt-4 text-xl font-extrabold">Sura Float</h2><p className="mt-2 text-sm text-muted-foreground">Float is not available yet. Keep building a steady Lock history to prepare for future eligibility.</p></Panel>
    if (page === "profile") return <Profile value={obj}/>
    if (page.startsWith("profile/")) return <ProfileDetail page={page}/>
    if (page === "notifications") return <Rows rows={rows} empty="You’re all caught up."/>
    if (page === "help") return <Help />
    if (page === "account-review") return <Panel><h2 className="text-xl font-extrabold">Account review</h2><p className="mt-2 text-sm text-muted-foreground">Some actions are temporarily unavailable while your account is reviewed. Your records remain available.</p><Link className="mt-4 inline-flex font-bold text-primary" href="/app/help">Contact support →</Link></Panel>
    return <Panel><h2 className="text-lg font-extrabold">{titleCase(segments.at(-1) || "Home")}</h2><p className="mt-2 text-sm text-muted-foreground">This area is being prepared.</p></Panel>
  }

  function MemberHome({ value }: { value: Row | null }) {
    const profile = value?.profile ?? {}
    const score = value?.score ?? {}
    const list = value?.commitments ?? []
    const active = (list as Row[]).find((item) => item.status === "active")
    return <div className="space-y-6"><div className="flex items-start justify-between gap-3"><div><p className="text-sm text-muted-foreground">Good morning,</p><h2 className="mt-1 text-2xl font-extrabold">{firstName(profile.name) || "there"}</h2></div><Link href="/app/score" className="rounded-full border border-hairline bg-card px-3 py-2 text-xs font-extrabold text-primary">Score {score.score ?? "—"}</Link></div><Panel className="overflow-hidden border-0 bg-primary text-white"><div className="flex items-start justify-between"><div><p className="text-xs font-bold text-white/75">YOUR NEXT STEP</p><h3 className="mt-2 text-xl font-extrabold">{active?.title || "Start with a Sura Lock"}</h3><p className="mt-2 text-sm text-white/80">{active ? `${money(active.contribution_amount)} · ${active.contribution_frequency}` : "Save together with people you trust."}</p></div><span className="grid size-10 place-items-center rounded-full bg-white/15 text-xl">↗</span></div><Link href={active ? `/app/commitments/${active.commitment_id}` : "/app/commitments/new"} className="mt-5 inline-flex rounded-lg bg-white px-4 py-3 text-sm font-extrabold text-primary">{active ? "View your Lock" : "Create a Lock"}</Link></Panel><div className="grid grid-cols-2 gap-3"><Link href="/app/commitments/new" className="rounded-xl border border-hairline bg-card p-4"><span className="text-xl text-primary">＋</span><p className="mt-2 font-extrabold">Create Lock</p><p className="mt-1 text-xs text-muted-foreground">Start saving together</p></Link><Link href="/app/join" className="rounded-xl border border-hairline bg-card p-4"><span className="text-xl text-primary">↗</span><p className="mt-2 font-extrabold">Join a Lock</p><p className="mt-1 text-xs text-muted-foreground">Use an invite code</p></Link></div><div><SectionTitle title="Your commitments" action={<Link href="/app/commitments" className="text-sm font-bold text-primary">See all</Link>}/>{list.length ? <Rows rows={(list as Row[]).slice(0, 3)} empty="" linkPrefix="/app/commitments/"/> : <Panel><p className="text-sm text-muted-foreground">Your Locks will appear here once you create or join one.</p></Panel>}</div><Link href="/app/float" className="flex items-center justify-between rounded-xl border border-hairline bg-card p-4"><div><p className="font-extrabold">Sura Float</p><p className="mt-1 text-xs text-muted-foreground">A future benefit for consistent members</p></div><span className="rounded-full bg-gold-soft px-2 py-1 text-[10px] font-extrabold text-gold-deep">COMING SOON</span></Link></div>
  }

  function Commitments({ rows }: { rows: Row[] }) {
    const filtered = rows.filter((item) => listTab === "active" ? ["active", "pending_members"].includes(item.status) : listTab === "completed" ? item.status === "completed" : item.status !== "active" && item.status !== "pending_members" && item.status !== "completed")
    return <div><div className="mb-5 flex items-center justify-between"><p className="text-sm text-muted-foreground">All your group Locks in one place.</p><Link href="/app/commitments/new" className="grid size-10 place-items-center rounded-full bg-primary text-xl font-bold text-white" aria-label="Create a Lock">＋</Link></div><div className="mb-5 grid grid-cols-3 rounded-lg bg-muted p-1">{["active", "pending", "completed"].map((value) => <button key={value} onClick={() => setListTab(value)} className={`rounded-md py-2 text-xs font-extrabold capitalize ${listTab === value ? "bg-card text-primary shadow-sm" : "text-muted-foreground"}`}>{value}</button>)}</div>{filtered.length ? <Rows rows={filtered} empty="" linkPrefix="/app/commitments/"/> : <Panel className="py-8 text-center"><div className="mx-auto grid size-12 place-items-center rounded-full bg-primary-soft text-xl text-primary">▤</div><h2 className="mt-4 font-extrabold">No {listTab} commitments</h2><p className="mx-auto mt-2 max-w-xs text-sm text-muted-foreground">Create your first Lock or join one with an invite code.</p><div className="mt-5 flex justify-center gap-2"><Button size="sm" onClick={() => router.push("/app/commitments/new")}>Create Lock</Button><Button size="sm" variant="outline" onClick={() => router.push("/app/join")}>Join a Lock</Button></div></Panel>}</div>
  }

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  function LegacyNewCommitment() {
    const fields = (key: string, value: unknown) => setForm((current) => ({ ...current, [key]: value }))
    const payload = { ...form, type: "rotating", contribution_amount: Number(form.contribution_amount), cycles: Number(form.cycles), members: members.map((member) => member.user_id), payout_order: lockPreview?.payout_order ?? [] }
    const submit = () => run(async () => {
      if (consentAccepted) await recordConsent(true)
      return createLock(payload)
    }, (result) => { lockDraftStore.clear(); router.push(`/app/commitments/${result.commitment_id}`) })
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    const advance = () => {
      if (step === 3) {
        run(() => previewLock(payload), (result) => { setLockPreview(result as Row); setStep(4) })
        return
      }
      setStep((current) => current + 1)
    }
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    const addMember = () => run(() => resolveMember(memberPhone.trim()), (result) => {
      const person = result as Row
      if (members.some((member) => member.user_id === person.user_id)) { setError("That person is already on this Lock."); return }
      const nextMembers = [...members, person]
      setMembers(nextMembers)
      setForm((current) => ({ ...current, cycles: nextMembers.length + 1 }))
      setMemberPhone("")
    })
    return <div className="space-y-5"><div className="flex items-center justify-between"><p className="text-sm font-bold text-muted-foreground">Step {step + 1} of 4</p><span className="text-xs font-bold text-primary">{["Basics", "Vendor", "Contribution", "Review"][step]}</span></div><div className="h-1.5 overflow-hidden rounded-full bg-muted"><div className="h-full rounded-full bg-primary transition-all" style={{ width: `${(step + 1) * 25}%` }}/></div>{step === 0 && <Panel><h2 className="text-lg font-extrabold">Give your Lock a name</h2><label htmlFor="lock-title" className="mt-4 block text-sm font-bold">Lock name</label><input id="lock-title" value={form.title} onChange={(e) => fields("title", e.target.value)} placeholder="e.g. Laptop fund" className="mt-2 h-12 w-full rounded-lg border border-hairline bg-background px-3 outline-none focus:ring-4 focus:ring-primary/15"/><p className="mt-5 text-sm font-extrabold">Commitment type</p><div className="mt-2 grid gap-2"><div className="rounded-lg border-2 border-primary bg-primary-soft p-3"><p className="font-extrabold">Rotating Sura Lock</p><p className="mt-1 text-xs text-muted-foreground">Members contribute regularly and take turns receiving the pool.</p></div>{["Collective goal", "Individual goal"].map((name) => <div key={name} className="flex items-center justify-between rounded-lg border border-hairline p-3 opacity-60"><span className="text-sm font-bold">{name}</span><span className="text-[10px] font-extrabold text-muted-foreground">COMING SOON</span></div>)}</div></Panel>}{step === 1 && <Panel><h2 className="text-lg font-extrabold">Choose a verified vendor</h2><p className="mt-1 text-sm text-muted-foreground">Your payout is locked to this vendor after creation.</p><div className="mt-4 grid gap-2">{vendorList.map((vendor) => <button key={vendor.vendor_id} onClick={() => fields("vendor_id", vendor.vendor_id)} className={`flex items-center justify-between rounded-lg border p-4 text-left ${form.vendor_id === vendor.vendor_id ? "border-primary bg-primary-soft" : "border-hairline bg-card"}`}><span><span className="block font-extrabold">{vendor.name}</span><span className="text-xs text-muted-foreground">{vendor.category}</span></span><span className="text-xs font-bold text-success">Verified ✓</span></button>)}</div>{!vendorList.length && <p className="mt-4 text-sm text-muted-foreground">No verified vendors are available yet.</p>}</Panel>}{step === 2 && <Panel><h2 className="text-lg font-extrabold">Set your contribution</h2><label className="mt-4 block text-sm font-bold" htmlFor="amount">Amount per member</label><div className="mt-2 flex h-12 items-center rounded-lg border border-hairline bg-background px-3"><span className="font-bold text-muted-foreground">₦</span><input id="amount" inputMode="numeric" type="number" min="1" step="1" value={form.contribution_amount} onChange={(e) => fields("contribution_amount", e.target.value)} className="h-full min-w-0 flex-1 bg-transparent px-2 outline-none" placeholder="5,000"/></div><label className="mt-4 block text-sm font-bold" htmlFor="frequency">Frequency</label><select id="frequency" value={form.contribution_frequency} onChange={(e) => fields("contribution_frequency", e.target.value)} className="mt-2 h-12 w-full rounded-lg border border-hairline bg-background px-3"><option value="weekly">Weekly</option><option value="daily">Daily</option></select><label className="mt-4 block text-sm font-bold" htmlFor="cycles">Number of cycles / members</label><input id="cycles" type="number" min="2" max="20" value={form.cycles} onChange={(e) => fields("cycles", e.target.value)} className="mt-2 h-12 w-full rounded-lg border border-hairline bg-background px-3"/><div className="mt-4 flex justify-between rounded-lg bg-muted p-3 text-sm"><span className="font-bold">Pool per cycle</span><strong>{money(Number(form.contribution_amount || 0) * Number(form.cycles || 0))}</strong></div></Panel>}{step === 3 && <Panel><h2 className="text-lg font-extrabold">Review your Lock</h2><p className="mt-1 text-sm text-muted-foreground">Payout order and safety limits are decided by Sura policy.</p><dl className="mt-4 divide-y divide-hairline">{[["Lock", form.title], ["Vendor", vendorList.find((v) => v.vendor_id === form.vendor_id)?.name || "Not selected"], ["Contribution", `${money(Number(form.contribution_amount || 0))} · ${form.contribution_frequency}`], ["Cycles", form.cycles], ["Pool per cycle", money(Number(form.contribution_amount || 0) * Number(form.cycles || 0))]].map(([label, value]) => <div key={label} className="flex justify-between gap-4 py-3 text-sm"><dt className="text-muted-foreground">{label}</dt><dd className="text-right font-extrabold">{value}</dd></div>)}</dl><p className="mt-3 rounded-lg bg-gold-soft p-3 text-xs leading-5 text-gold-deep">Your first payout may be capped under the current safety policy. The final schedule is returned by Sura when your Lock is created.</p></Panel>}<div className="flex gap-3"><Button variant="outline" className="flex-1" disabled={step === 0 || busy} onClick={() => setStep((n) => n - 1)}>Back</Button><Button className="flex-1" loading={busy} disabled={step === 0 ? !String(form.title).trim() : step === 1 ? !form.vendor_id : step === 2 ? !Number(form.contribution_amount) || Number(form.cycles) < 2 : false} onClick={() => step < 3 ? setStep((n) => n + 1) : submit()}>{step < 3 ? "Continue" : "Create Lock"}</Button></div></div>
  }

  function NewCommitment() {
    const fields = (key: string, value: unknown) => setForm((current) => ({ ...current, [key]: value }))
    const payload = { ...form, type: "rotating", contribution_amount: Number(form.contribution_amount), cycles: Number(form.cycles), members: members.map((member) => member.user_id), payout_order: lockPreview?.payout_order ?? [] }
    const next = () => {
      if (step === 3) {
        void run(() => previewLock(payload), (result) => { setLockPreview(result as Row); setStep(4) })
      } else setStep((current) => current + 1)
    }
    const addMember = () => void run(() => resolveMember(memberPhone.trim()), (result) => {
      const person = result as Row
      if (members.some((member) => member.user_id === person.user_id)) { setError("This member is already on the Lock."); return }
      const updated = [...members, person]
      setMembers(updated)
      setForm((current) => ({ ...current, cycles: updated.length + 1 }))
      setMemberPhone("")
    })
    const create = () => void run(async () => {
      if (consentAccepted) await recordConsent(true)
      return createLock(payload)
    }, (result) => { lockDraftStore.clear(); router.push(`/app/commitments/${result.commitment_id}`) })
    return <div className="space-y-5">
      <div className="flex items-center justify-between text-xs font-bold"><span className="text-muted-foreground">Step {step + 1} of 5</span><span className="text-primary">{["Basics", "Vendor", "Contribution", "Members", "Review"][step]}</span></div>
      <div className="h-1.5 rounded-full bg-muted"><div className="h-full rounded-full bg-primary" style={{ width: `${(step + 1) * 20}%` }}/></div>
      {step === 0 && <Panel><h2 className="text-lg font-extrabold">Name your Lock</h2><label htmlFor="lock-title" className="mt-4 block text-sm font-bold">Lock name</label><input id="lock-title" value={form.title} onChange={(event) => fields("title", event.target.value)} placeholder="e.g. Laptop fund" className="mt-2 h-12 w-full rounded-lg border border-hairline bg-background px-3 outline-none focus:ring-4 focus:ring-primary/15"/><p className="mt-5 text-sm font-extrabold">Commitment type</p><div className="mt-2 rounded-lg border-2 border-primary bg-primary-soft p-3"><p className="font-extrabold">Rotating Sura Lock</p><p className="mt-1 text-xs text-muted-foreground">Members contribute regularly and take turns receiving the pool.</p></div><p className="mt-2 text-xs text-muted-foreground">Collective and individual goals are coming soon.</p></Panel>}
      {step === 1 && <Panel><h2 className="text-lg font-extrabold">Choose a verified vendor</h2><p className="mt-1 text-sm text-muted-foreground">This vendor is locked after the commitment is created.</p><div className="mt-4 grid gap-2">{vendorList.map((vendor) => <button key={vendor.vendor_id} onClick={() => fields("vendor_id", vendor.vendor_id)} className={`flex items-center justify-between rounded-lg border p-4 text-left ${form.vendor_id === vendor.vendor_id ? "border-primary bg-primary-soft" : "border-hairline"}`}><span><strong className="block">{vendor.name}</strong><span className="text-xs text-muted-foreground">{vendor.category}</span></span><span className="text-xs font-bold text-success">Verified ✓</span></button>)}</div>{!vendorList.length && <p className="mt-4 text-sm text-muted-foreground">No verified vendors are available yet.</p>}</Panel>}
      {step === 2 && <Panel><h2 className="text-lg font-extrabold">Set your contribution</h2><label htmlFor="amount" className="mt-4 block text-sm font-bold">Amount per member</label><div className="mt-2 flex h-12 items-center rounded-lg border border-hairline px-3"><span className="font-bold text-muted-foreground">₦</span><input id="amount" inputMode="numeric" type="number" min="1" step="1" value={form.contribution_amount} onChange={(event) => fields("contribution_amount", event.target.value)} className="h-full min-w-0 flex-1 bg-transparent px-2 outline-none" placeholder="5,000"/></div><label htmlFor="frequency" className="mt-4 block text-sm font-bold">Frequency</label><select id="frequency" value={form.contribution_frequency} onChange={(event) => fields("contribution_frequency", event.target.value)} className="mt-2 h-12 w-full rounded-lg border border-hairline bg-background px-3"><option value="weekly">Weekly</option><option value="daily">Daily</option></select><p className="mt-4 rounded-lg bg-muted p-3 text-sm">Pool per cycle <strong className="float-right">{money(Number(form.contribution_amount || 0) * Number(form.cycles || 0))}</strong></p><p className="mt-2 text-xs text-muted-foreground">Cycle count will match the confirmed group size.</p></Panel>}
      {step === 3 && <Panel><h2 className="text-lg font-extrabold">Invite members</h2><p className="mt-1 text-sm text-muted-foreground">Add members by their Sura phone number. Sura confirms each account.</p><label htmlFor="member-phone" className="mt-4 block text-sm font-bold">Member phone</label><div className="mt-2 flex gap-2"><input id="member-phone" type="tel" value={memberPhone} onChange={(event) => setMemberPhone(event.target.value)} className="h-12 min-w-0 flex-1 rounded-lg border border-hairline bg-background px-3" placeholder="080 0000 0000"/><Button size="sm" loading={busy} disabled={memberPhone.trim().length < 7} onClick={addMember}>Add</Button></div><p className="mt-3 text-xs font-bold text-muted-foreground">{members.length + 1} confirmed · {Number(form.cycles)} required</p><div className="mt-3 divide-y divide-hairline">{members.map((person) => <div key={person.user_id} className="flex items-center justify-between py-3 text-sm"><span className="font-bold">{person.first_name}</span><button className="text-xs font-bold text-destructive" onClick={() => { const updated = members.filter((member) => member.user_id !== person.user_id); setMembers(updated); fields("cycles", Math.max(2, updated.length + 1)) }}>Remove</button></div>)}</div><p className="mt-3 rounded-lg bg-gold-soft p-3 text-xs text-gold-deep">You are included automatically. Add at least one other member to start.</p></Panel>}
      {step === 4 && <Panel><h2 className="text-lg font-extrabold">Review the agreement</h2><dl className="mt-3 divide-y divide-hairline">{[["Lock", form.title], ["Vendor", vendorList.find((vendor) => vendor.vendor_id === form.vendor_id)?.name || "—"], ["Contribution", `${money(Number(form.contribution_amount))} · ${form.contribution_frequency}`], ["Members", Number(form.cycles)], ["Pool per cycle", money(Number(form.contribution_amount) * Number(form.cycles))]].map(([label, value]) => <div key={label} className="flex justify-between gap-4 py-3 text-sm"><dt className="text-muted-foreground">{label}</dt><dd className="text-right font-extrabold">{value}</dd></div>)}</dl><p className="mt-3 rounded-lg bg-gold-soft p-3 text-xs leading-5 text-gold-deep">Sura’s suggested payout order and first payout safety cap are shown below.</p>{lockPreview && <><p className="mt-4 text-sm font-extrabold">Suggested payout order</p><ol className="mt-2 list-inside list-decimal text-sm">{(lockPreview.payout_order ?? []).map((id: string, index: number) => <li key={`${id}-${index}`}>{members.find((member) => member.user_id === id)?.first_name || (id === session?.userId ? "You" : "Member")}</li>)}</ol><p className={`mt-3 rounded-lg p-3 text-xs font-bold ${lockPreview.can_create ? "bg-success-soft text-success" : "bg-red-50 text-red-700"}`}>{lockPreview.can_create ? "This Lock is within the current first payout cap." : lockPreview.blocking_reason}</p></>}<label className="mt-4 flex gap-3 text-sm leading-5"><input type="checkbox" checked={consentAccepted} onChange={(event) => setConsentAccepted(event.target.checked)} className="mt-1 size-4 accent-primary"/><span>I agree to Sura processing my Lock activity to calculate my private Sura Score. <Link href="/app/consent" className="font-bold text-primary">Read details</Link></span></label></Panel>}
      <div className="flex gap-3"><Button variant="outline" className="flex-1" disabled={step === 0 || busy} onClick={() => setStep((current) => current - 1)}>Back</Button><Button className="flex-1" loading={busy} disabled={step === 0 ? !String(form.title).trim() : step === 1 ? !form.vendor_id : step === 2 ? !Number(form.contribution_amount) : step === 3 ? members.length === 0 : !consentAccepted || lockPreview?.can_create === false} onClick={step === 4 ? create : next}>{step < 4 ? "Continue" : "Create Lock"}</Button></div>
    </div>
  }

  function Join() {
    return <Panel><h2 className="text-lg font-extrabold">Enter an invite code</h2><p className="mt-1 text-sm text-muted-foreground">Ask the Lock creator to share their code with you.</p><label htmlFor="invite-code" className="mt-5 block text-sm font-bold">Invite code</label><input id="invite-code" autoCapitalize="characters" value={code} onChange={(e) => setCode(e.target.value.toUpperCase())} className="mt-2 h-12 w-full rounded-lg border border-hairline bg-background px-3 font-bold tracking-[.08em] outline-none focus:ring-4 focus:ring-primary/15" placeholder="SURA-XXXX"/><Button className="mt-4 w-full" disabled={!code.trim()} onClick={() => router.push(`/app/join/${encodeURIComponent(code.trim())}`)}>Preview Lock</Button></Panel>
  }
  function JoinPreview({ value }: { value: Row | null }) {
    const preview = value ?? {}
    return <div className="space-y-4"><Panel><p className="text-xs font-bold uppercase tracking-wider text-primary">Invite preview</p><h2 className="mt-2 text-xl font-extrabold">{preview.title || "Sura Lock"}</h2><p className="mt-1 text-sm text-muted-foreground">Vendor · {preview.vendor_name || preview.vendor?.name || "Verified vendor"}</p><dl className="mt-5 divide-y divide-hairline">{[["Contribution", `${money(preview.contribution_amount)} · ${preview.contribution_frequency || "weekly"}`], ["Cycles", preview.cycles], ["Members", `${preview.member_count ?? "—"} / ${preview.cycles ?? "—"}`], ["Your payout slot", preview.proposed_payout_slot ?? "Assigned by Sura policy"]].map(([label, content]) => <div key={label} className="flex justify-between gap-4 py-3 text-sm"><dt className="text-muted-foreground">{label}</dt><dd className="text-right font-extrabold">{content}</dd></div>)}</dl></Panel><Panel><p className="text-sm">Joining means you agree to contribute on the schedule shown. Score processing consent may be required before joining.</p><Button className="mt-4 w-full" loading={busy} onClick={() => run(() => joinCommitment(segments[1]), () => router.push(`/app/join/${segments[1]}/done`))}>Join this Lock</Button><button onClick={() => router.push("/app/consent")} className="mt-3 w-full text-sm font-bold text-primary">Review score consent</button></Panel></div>
  }
  function Consent() {
    return <Panel><p className="text-xs font-bold uppercase tracking-wider text-primary">Your choice</p><h2 className="mt-2 text-xl font-extrabold">Score processing consent</h2><p className="mt-3 text-sm leading-6 text-muted-foreground">Sura records your Lock participation, contribution timing, and verification signals to calculate your private Sura Score. The score helps explain reliability for future financial services. It is not a guarantee of credit or a public rating.</p><div className="mt-5 grid gap-3"><Button loading={busy} onClick={() => run(() => recordConsent(true), () => { setMessage("Consent saved."); router.back() })}>Agree and continue</Button><Button variant="outline" loading={busy} onClick={() => run(() => recordConsent(false), () => router.push("/app/help"))}>Decline</Button></div><Link href="/app/profile/privacy" className="mt-4 inline-flex text-sm font-bold text-primary">Read about your privacy</Link></Panel>
  }
  function Commitment({ value }: { value: Row | null }) {
    const lock = value ?? {}
    const [tab, setTab] = useState("Overview")
    const status = lock.status ?? "active"
    const tabs = ["Overview", "Schedule", "Members", "Activity"]
    return <div className="space-y-4"><Panel><div className="flex items-start justify-between gap-3"><div><span className="rounded-full bg-primary-soft px-2.5 py-1 text-[10px] font-extrabold uppercase text-primary">{titleCase(status)}</span><h2 className="mt-3 text-xl font-extrabold">{lock.title || "Your Sura Lock"}</h2><p className="mt-1 text-sm text-muted-foreground">{money(lock.contribution_amount)} · {lock.contribution_frequency || "weekly"}</p></div><span className="grid size-11 place-items-center rounded-full bg-gold-soft text-lg text-gold-deep">↻</span></div><div className="mt-5 h-2 overflow-hidden rounded-full bg-muted"><div className="h-full rounded-full bg-primary" style={{ width: `${Math.min(100, Number(lock.progress_percent ?? 22))}%` }}/></div><div className="mt-2 flex justify-between text-xs text-muted-foreground"><span>Cycle {lock.current_cycle_number ?? 1} of {lock.cycles ?? "—"}</span><span>{lock.completed_cycle_count ?? 0} completed</span></div><Button className="mt-5 w-full" onClick={() => router.push(`/app/commitments/${segments[1]}/contribute`)}>{status === "pending_members" ? "Share invite" : "Contribute"}</Button></Panel><div className="grid grid-cols-4 rounded-lg bg-muted p-1">{tabs.map((name) => <button key={name} onClick={() => setTab(name)} className={`rounded-md py-2 text-[10px] font-extrabold ${tab === name ? "bg-card text-primary shadow-sm" : "text-muted-foreground"}`}>{name}</button>)}</div><Panel><SectionTitle title={tab}/>{tab === "Overview" ? <dl className="divide-y divide-hairline">{[["Members", lock.member_count ?? lock.members?.length ?? "—"], ["Next payout", lock.next_payout?.beneficiary_name || "See schedule"], ["Vendor", lock.vendor_name || "Verified vendor"], ["Invite code", lock.invite_code || "—"]].map(([label, value]) => <div key={label} className="flex justify-between gap-3 py-3 text-sm"><span className="text-muted-foreground">{label}</span><strong>{value}</strong></div>)}</dl> : <Rows rows={tab === "Members" ? lock.members ?? [] : tab === "Schedule" ? lock.cycle_states ?? lock.payout_schedule ?? [] : lock.activity ?? []} empty={`No ${tab.toLowerCase()} details yet.`}/>}</Panel>{status === "pending_members" && <Button variant="outline" className="w-full" onClick={() => run(() => cancelCommitment(segments[1]), () => router.push("/app/commitments"))}>Cancel pending Lock</Button>}</div>
  }
  function Contribute({ value }: { value: Row | null }) {
    const lock = value ?? {}
    const id = segments[1]
    const amount = Number(lock.contribution_due ?? lock.contribution_amount ?? 0)
    const submit = () => {
      const eventId = `sura-${id}-${session?.userId}-${lock.current_cycle_number ?? 1}`
      run(() => contribute(id, amount, eventId), (result) => {
        const replay = Boolean((result as Row)?.idempotent_replay)
        setMessage(replay ? "Already recorded" : "Contribution recorded")
        router.push(`/app/commitments/${id}/contribute/receipt`)
      })
    }
    return <div className="space-y-4"><Panel><p className="text-xs font-bold uppercase tracking-wider text-primary">Current cycle · {lock.current_cycle_number ?? 1}</p><h2 className="mt-3 text-3xl font-extrabold">{money(amount)}</h2><p className="mt-1 text-sm text-muted-foreground">Locked contribution due for {lock.title || "this Lock"}</p><div className="mt-5 border-t border-hairline pt-4"><div className="flex justify-between text-sm"><span className="text-muted-foreground">Cycle progress</span><strong>{lock.paid_count ?? 0} of {lock.member_count ?? lock.cycles ?? "—"} paid</strong></div><div className="mt-2 h-2 rounded-full bg-muted"><div className="h-full rounded-full bg-success" style={{ width: `${Math.min(100, Number(lock.paid_percent ?? 0))}%` }}/></div></div></Panel><Button className="w-full" loading={busy} disabled={!amount} onClick={submit}>Confirm contribution</Button><p className="text-center text-xs text-muted-foreground">A retry uses the same reference and will never create a second contribution.</p></div>
  }
  function Voucher({ value }: { value: Row | null }) {
    const voucher = value ?? {}
    return <Panel className="text-center"><p className="text-xs font-extrabold uppercase tracking-wider text-primary">{titleCase(voucher.status || "voucher")}</p><h2 className="mt-3 text-xl font-extrabold">{voucher.vendor_name || "Your locked vendor"}</h2><p className="mt-1 text-sm text-muted-foreground">Cycle {segments.at(-2)} · {money(voucher.amount)}</p><div className="mx-auto my-6 grid size-48 place-items-center border-4 border-dashed border-hairline bg-muted text-center"><div><span className="text-3xl">▦</span><p className="mt-2 text-xs text-muted-foreground">Show this code<br/>at the counter</p></div></div><p className="text-xl font-extrabold tracking-[.15em]">{voucher.code || voucher.voucher_code || "••••••"}</p><p className="mt-3 text-xs text-muted-foreground">Expires {voucher.expires_at ? formatDate(voucher.expires_at) : "as shown in your Lock terms"}</p><p className="mt-5 rounded-lg bg-success-soft p-3 text-sm font-bold text-success">After vendor confirmation, this voucher will show as redeemed.</p></Panel>
  }
  function Score({ value }: { value: Row | null }) {
    const score = value ?? {}
    const breakdown = score.breakdown ?? {}
    const pillars = [["Commitment behaviour", breakdown.commitment_behaviour], ["Repayment behaviour", breakdown.repayment_behaviour], ["Transaction stability", breakdown.transaction_stability], ["Institutional verification", breakdown.institutional_verification], ["Social reliability", breakdown.social_reliability]] as const
    return <div className="space-y-5"><Panel className="text-center"><div className="mx-auto grid size-32 place-items-center rounded-full border-[9px] border-primary-soft border-t-primary text-4xl font-extrabold text-primary">{score.score ?? "—"}</div><p className="mt-3 text-sm font-extrabold">{score.tier || "Building your history"}</p><p className="mt-1 text-xs text-muted-foreground">Private to you · updated {score.last_updated ? formatDate(score.last_updated) : "recently"}</p><Link href="/app/score/how-it-works" className="mt-4 inline-flex text-sm font-bold text-primary">How your score works →</Link></Panel><Panel><SectionTitle title="Five pillars"/>{pillars.map(([label, value]) => <div key={label} className="mb-4 last:mb-0"><div className="mb-1 flex justify-between text-xs"><span className="font-bold">{label}</span><span className="text-muted-foreground">{value ?? "—"}</span></div><div className="h-1.5 rounded-full bg-muted"><div className="h-full rounded-full bg-primary" style={{ width: `${Math.min(100, Number(value ?? 0))}%` }}/></div></div>)}</Panel><Link href="/app/score/history" className="flex items-center justify-between rounded-xl border border-hairline bg-card p-4"><span className="font-extrabold">Score history</span><span className="text-primary">→</span></Link><Link href="/app/float" className="flex items-center justify-between rounded-xl border border-hairline bg-card p-4"><span className="font-extrabold">Float eligibility</span><span className="text-[10px] font-extrabold text-gold-deep">COMING SOON</span></Link></div>
  }
  function ScoreHistory({ rows }: { rows: Row[] }) {
    return <div className="space-y-4"><p className="text-sm text-muted-foreground">Every recorded score update, with the reason behind it.</p>{rows.map((row) => <Link key={row.id} href={`/app/score/history/${row.id}`} className="flex items-center justify-between rounded-xl border border-hairline bg-card p-4"><span><strong className="block">{titleCase(row.event_type || "Score update")}</strong><span className="mt-1 block text-xs text-muted-foreground">{row.computed_at ? formatDate(row.computed_at) : ""}</span></span><span className="font-extrabold text-primary">{row.score_before ?? "—"} → {row.score}</span></Link>)}{!rows.length && <Panel><p className="text-sm text-muted-foreground">Your score history will appear as your Lock activity is recorded.</p></Panel>}</div>
  }
  function SimpleDetail({ value, title }: { value: Row | null; title: string }) {
    return <Panel><h2 className="text-lg font-extrabold">{title}</h2><dl className="mt-4 divide-y divide-hairline">{Object.entries(value ?? {}).filter(([key]) => key !== "user_id").map(([key, content]) => <div key={key} className="py-3"><dt className="text-xs font-bold text-muted-foreground">{titleCase(key)}</dt><dd className="mt-1 break-words text-sm font-bold">{typeof content === "object" ? JSON.stringify(content) : String(content ?? "—")}</dd></div>)}</dl></Panel>
  }
  function HowScore() {
    return <div className="space-y-4"><Panel><p className="text-xs font-bold uppercase tracking-wider text-primary">A private reliability signal</p><h2 className="mt-2 text-xl font-extrabold">How Sura Score works</h2><p className="mt-3 text-sm leading-6 text-muted-foreground">Your score summarizes observed financial and commitment behaviour. It belongs to you; members in your Lock never see it.</p></Panel><Panel>{[["Commitment behaviour", "Keeping to agreed Lock schedules"], ["Repayment behaviour", "Completing contributions on time"], ["Transaction stability", "Consistency of recorded activity"], ["Institutional verification", "Verified identity signals"], ["Social reliability", "Reliable participation in groups"]].map(([name, description]) => <div key={name} className="border-b border-hairline py-3 last:border-0"><p className="font-extrabold">{name}</p><p className="mt-1 text-xs text-muted-foreground">{description}</p></div>)}<p className="mt-3 text-xs leading-5 text-muted-foreground">Weights and current rules are supplied by Sura policy. A new member starts with limited history. The score is not a guarantee of credit and does not measure personal worth.</p></Panel></div>
  }
  function Profile({ value }: { value: Row | null }) {
    const profile = value ?? {}
    return <div className="space-y-4"><Panel><div className="flex items-center gap-4"><span className="grid size-14 place-items-center rounded-full bg-primary-soft text-lg font-extrabold text-primary">{firstName(profile.name).slice(0, 1) || "S"}</span><div><h2 className="font-extrabold">{profile.name || "Sura member"}</h2><p className="mt-1 text-sm text-muted-foreground">{profile.phone || "Verified account"}</p></div></div><p className="mt-4 border-t border-hairline pt-4 text-sm">Sura Score tier <strong>{profile.tier || "Building history"}</strong></p></Panel><div className="grid gap-2">{[["Verification", "/app/profile/verification"], ["Privacy and consent", "/app/profile/privacy"], ["Settings", "/app/profile/settings"], ["Help and support", "/app/help"]].map(([label, href]) => <Link href={href} key={href} className="flex items-center justify-between rounded-lg border border-hairline bg-card p-4 text-sm font-bold">{label}<span className="text-primary">→</span></Link>)}</div><Button variant="outline" className="w-full" onClick={signOut}>Sign out</Button></div>
  }
  function ProfileDetail({ page: current }: { page: string }) {
    const detail = current.split("/").at(-1) || "profile"
    const copy: Row = {
      verification: ["Your account verification status is managed by Sura and your approved identity partners.", "Verification signals may contribute to your private score."],
      privacy: ["Sura uses your Lock activity and verification data to operate commitments and calculate your private score.", "You can withdraw score consent. Some features may then be unavailable."],
      settings: ["Manage your notification preferences and account session."],
    }
    return <div className="space-y-4"><Panel><h2 className="text-lg font-extrabold">{titleCase(detail)}</h2>{(copy[detail] || []).map((paragraph: string) => <p key={paragraph} className="mt-3 text-sm leading-6 text-muted-foreground">{paragraph}</p>)}{detail === "privacy" && <Button variant="outline" className="mt-5 w-full" loading={busy} onClick={() => run(() => recordConsent(false), () => setMessage("Consent withdrawal recorded."))}>Withdraw score consent</Button>}</Panel>{detail === "settings" && <Button variant="outline" className="w-full" onClick={signOut}>Sign out</Button>}</div>
  }
  function Help() {
    return <div className="space-y-4"><Panel><h2 className="text-lg font-extrabold">How can we help?</h2><p className="mt-2 text-sm text-muted-foreground">Answers to common questions about your Sura Lock.</p></Panel><Panel>{[["When do I contribute?", "Your contribution date and amount are shown on each Lock. The group moves forward when the cycle is complete."], ["Can I change my vendor?", "The vendor is locked when a commitment is created to protect the payout."], ["Who sees my Sura Score?", "Your score is private. Other members and vendors do not see it."], ["What if I miss a contribution?", "Your Lock shows the current status and next available action. Contact support if you need help."]].map(([question, answer]) => <details key={question} className="border-b border-hairline py-3 last:border-0"><summary className="font-extrabold">{question}</summary><p className="mt-2 text-sm leading-6 text-muted-foreground">{answer}</p></details>)}</Panel></div>
  }
  function Welcome() { return <div className="space-y-4"><Panel className="bg-primary text-white"><p className="text-xs font-bold uppercase tracking-wider text-white/70">Welcome to Sura</p><h2 className="mt-2 text-2xl font-extrabold">Save with a plan.</h2><p className="mt-2 text-sm leading-6 text-white/80">A Sura Lock helps a trusted group contribute regularly and take turns receiving a payout for a chosen purchase.</p></Panel><Panel><h3 className="font-extrabold">Vendor locked. Payout protected.</h3><p className="mt-2 text-sm text-muted-foreground">Every Lock chooses a verified vendor before the group begins. Vouchers can only be redeemed there.</p></Panel><Panel><h3 className="font-extrabold">Your score stays private.</h3><p className="mt-2 text-sm text-muted-foreground">Sura Score explains your observed reliability. It is visible only to you.</p></Panel><Button className="w-full" onClick={() => router.push("/app/commitments/new")}>Create your first Lock</Button></div> }

  function Rows({ rows, empty, linkPrefix, moneyKey }: { rows: Row[]; empty: string; linkPrefix?: string; moneyKey?: string }) {
    if (!rows?.length) return <Panel><p className="text-sm text-muted-foreground">{empty}</p></Panel>
    return <div className="divide-y divide-hairline overflow-hidden rounded-xl border border-hairline bg-card">{rows.map((row, index) => {
      const label = row.title || row.commitment_title || row.event_type || row.beneficiary_first_name || row.beneficiary_name || "Sura activity"
      const href = linkPrefix ? `${linkPrefix}${row.commitment_id || row.id}` : undefined
      const content = <div className="flex items-center justify-between gap-3 px-4 py-4"><div className="min-w-0"><p className="truncate text-sm font-extrabold">{label}</p><p className="mt-1 truncate text-xs capitalize text-muted-foreground">{titleCase(row.status || row.category || row.cycle_number || "")}{row.redeemed_at ? ` · ${formatDate(row.redeemed_at)}` : ""}</p></div><div className="shrink-0 text-right"><p className="text-sm font-extrabold">{moneyKey ? money(row[moneyKey]) : row.amount ? money(row.amount) : ""}</p><span className="text-xs text-primary">{href ? "View →" : ""}</span></div></div>
      return href ? <Link href={href} key={row.id || row.commitment_id || index} className="block hover:bg-muted/60">{content}</Link> : <div key={row.id || index}>{content}</div>
    })}</div>
  }
}

function firstName(name: unknown) { return typeof name === "string" ? name.trim().split(/\s+/)[0] : "" }
