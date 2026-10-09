"use client"

import Link from "next/link"
import Image from "next/image"
import { usePathname, useRouter } from "next/navigation"
import { useEffect, useMemo, useRef, useState } from "react"
import { Select } from "@base-ui/react/select"
import { sessionStore, endSession } from "@/lib/session"
import { useStoredValue } from "@/hooks/use-stored-value"
import { createStoredValue } from "@/lib/storage"
import { Button } from "@/components/ui/button"
import { Logo } from "@/components/layout/logo"
import { ThemeToggle } from "@/components/layout/theme-toggle"
import { formatDate, formatNaira } from "@/utils/format"
import {
  cancelCommitment, contribute, createLock, getAccountSimulation, getBanks, getCommitment, getCommitmentActivity, getCommitments, getInvitePreview, getLinkedAccount, getRedemption, getScoreEntry,
  getMemberHome, getMe, getNotifications, getRedemptions, getScore, getScoreHistory, getVoucher,
  addVendorProduct, getMyVendorProducts, getVendorHome, getVendorPayoutAccount, getVendorPayoutAccountSimulation, getVendorProducts, getVendors, joinCommitment, linkAccount, logout, previewLock, recordConsent, removeVendorProduct, resolveLinkedAccount, resolveMember, resolveVendorPayoutAccount, saveVendorPayoutAccount, updateVendorProduct,
  redeemVoucher, validateVoucher,
} from "@/actions/app"

type Role = "individual" | "vendor"
// Screen payloads follow the backend's per-route response contracts.
// eslint-disable-next-line @typescript-eslint/no-explicit-any
type Row = Record<string, any>
type LockDraft = { form: Row; members: Row[]; step: number; consentAccepted: boolean; lockPreview: Row | null }
const lockDraftStore = createStoredValue<LockDraft>("session", "sura.lock-draft")
const fundingReturnStore = createStoredValue<string>("session", "sura.funding-return")
const emptyLockDraft: LockDraft = { form: { type: "rotating", title: "", vendor_id: "", product_id: "", contribution_amount: "", target_amount: "", contribution_frequency: "weekly", cycles: 2, beneficiary_id: "" }, members: [], step: 0, consentAccepted: false, lockPreview: null }

const memberNav = [
  ["Home", "/app", "⌂"], ["Locks", "/app/commitments", "▤"], ["Score", "/app/score", "◉"], ["Profile", "/app/profile", "○"],
]
const vendorNav = [
  ["Terminal", "/vendor", "⌂"], ["Catalogue", "/vendor/catalogue", "▤"], ["Redeem", "/vendor/redeem", "▣"], ["Payout", "/vendor/payout", "₦"], ["History", "/vendor/history", "↻"],
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
  const [draftState, setDraftState] = useState<LockDraft>(() => lockDraftStore.read() ?? emptyLockDraft)
  const [data, setData] = useState<Row | Row[] | null>(null)
  const [loading, setLoading] = useState(!(role === "vendor" && segments[0] === "login"))
  const [error, setError] = useState("")
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState("")
  const currentDraft = draftState
  const form = currentDraft.form
  const members = currentDraft.members
  const step = currentDraft.step
  const consentAccepted = currentDraft.consentAccepted
  const lockPreview = currentDraft.lockPreview
  const updateDraft = (updates: Partial<LockDraft>) => lockDraftStore.write({ ...(lockDraftStore.read() ?? emptyLockDraft), ...updates })
  const setForm = (value: Row | ((current: Row) => Row)) => setDraftState((current) => ({ ...current, form: typeof value === "function" ? value(current.form) : value }))
  const setMembers = (value: Row[] | ((current: Row[]) => Row[])) => setDraftState((current) => ({ ...current, members: typeof value === "function" ? value(current.members) : value }))
  const setStep = (value: number | ((current: number) => number)) => setDraftState((current) => ({ ...current, step: typeof value === "function" ? value(current.step) : value }))
  const setConsentAccepted = (value: boolean) => setDraftState((current) => ({ ...current, consentAccepted: value }))
  const setLockPreview = (value: Row | null) => setDraftState((current) => ({ ...current, lockPreview: value }))

  useEffect(() => {
    updateDraft(draftState)
  }, [draftState])
  const [code, setCode] = useState("")
  const [vendorList, setVendorList] = useState<Row[]>([])
  const [vendorPage, setVendorPage] = useState(0)
  const [vendorProducts, setVendorProducts] = useState<Row[]>([])
  const [listTab, setListTab] = useState("active")
  const [memberPhone, setMemberPhone] = useState("")
  const [fundingBank, setFundingBank] = useState("")
  const fundingNumberRef = useRef("")
  const [fundingBanks, setFundingBanks] = useState<string[]>([])
  const [fundingPartners, setFundingPartners] = useState<Row[]>([])
  const [fundingPartnerId, setFundingPartnerId] = useState("")
  const [shareWithPartner, setShareWithPartner] = useState(false)
  const [fundingPreview, setFundingPreview] = useState<Row | null>(null)
  const [fundingSimulation, setFundingSimulation] = useState<Row | null>(null)
  const [loadedPath, setLoadedPath] = useState("")
  const page = segments.join("/")
  const isVendor = role === "vendor"
  const screenLoading = loading || (loadedPath !== pathname && !(isVendor && !session && segments[0] === "login"))
  const nav = isVendor ? vendorNav : memberNav
  const focused = ["commitments/new", "join", "consent"].includes(page) || page.startsWith("join/") || (isVendor && segments[0] === "login") || page.includes("/contribute") || page.includes("/voucher") || page.startsWith("redeem")
  const screenTitle = useMemo(() => {
    if (isVendor) return page === "" ? "Merchant terminal" : page.startsWith("catalogue") ? "Product catalogue" : page.startsWith("payout") ? "Settlement account" : page.startsWith("redeem") ? "Redeem voucher" : page.startsWith("history") ? "Settlement history" : titleCase(page)
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
        if (segments[0] === "catalogue") return getVendorHome()
        if (segments[0] === "payout") {
          const [payout, banks, simulation] = await Promise.all([getVendorPayoutAccount(), getBanks(), getVendorPayoutAccountSimulation()])
          return { ...(payout as Row), ...(banks as Row), simulation }
        }
        if (segments[0] === "redeem") return null
        return getVendorHome()
      }
      if (!segments.length) {
        const [home, linkedAccount] = await Promise.all([getMemberHome(), getLinkedAccount()])
        return { ...(home as Row), linked_account: (linkedAccount as Row).account }
      }
      if (segments[0] === "welcome") return getMemberHome()
      if (segments[0] === "account" && segments[1] === "link") {
        const [banks, simulation] = await Promise.all([getBanks(), getAccountSimulation()])
        return { ...(banks as Row), simulation }
      }
      if (segments[0] === "account" && segments[1] === "linked") return getLinkedAccount()
      if (segments[0] === "commitments" && segments.includes("voucher")) return getVoucher(segments[1], segments.at(-2) || "1")
      if (segments[0] === "commitments" && segments[1] && segments[1] !== "new") {
        const [lock, activity, linkedAccount] = await Promise.all([getCommitment(id), getCommitmentActivity(id), getLinkedAccount()])
        if (segments.at(-1) === "contribute" && !(linkedAccount as Row).account) {
          return { needs_funding_source: true, funding_return: pathname }
        }
        const events = Array.isArray(activity) ? activity : (activity as Row).activities ?? []
        const commitment = lock as Row
        const cycle = commitment.current_cycle ?? {}
        return { ...commitment, linked_account: (linkedAccount as Row).account, activity: events, progress_percent: cycle.progress_percent ?? 0, paid_count: cycle.paid_member_count ?? 0, paid_percent: cycle.progress_percent ?? 0, member_count: cycle.member_count ?? commitment.members?.length ?? 0, next_payout: { beneficiary_name: cycle.beneficiary_first_name } }
      }
      if (segments[0] === "commitments") return getCommitments()
      if (segments[0] === "join" && segments[1]) return getInvitePreview(segments[1])
      if (segments[0] === "score") return segments[1] === "history" ? segments[2] ? getScoreEntry(session.userId, segments[2]) : getScoreHistory(session.userId) : getScore(session.userId)
      if (segments[0] === "profile") return getMe()
      if (segments[0] === "notifications") return getNotifications()
      if (segments[0] === "consent") return null
      return null
    }
    load().then((result) => {
      if (active && result !== null) {
        const loaded = result as Row | Row[]
        if (!isVendor && (loaded as Row).needs_funding_source) {
          fundingReturnStore.write((loaded as Row).funding_return as string)
          router.replace("/app/account/link")
          return
        }
        setData(loaded)
        if (!isVendor && segments[0] === "account" && segments[1] === "link") {
          setFundingBanks(((result as Row).banks ?? []) as string[])
          setFundingPartners(((result as Row).sura_supported_banks ?? []) as Row[])
          setFundingSimulation(((result as Row).simulation ?? null) as Row | null)
        }
        setError("")
      }
    }).catch((reason) => {
      if (active) setError(reason instanceof Error ? reason.message : "We could not load this screen.")
    }).finally(() => { if (active) { setLoading(false); setLoadedPath(pathname) } })
    if (!isVendor && segments[0] === "commitments" && segments[1] === "new") getVendors().then((items) => { if (active) { setVendorList(items as Row[]); setVendorPage(0) } }).catch(() => active && setVendorList([]))
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
    if (segments[0] === "login") return <Panel><p className="text-xs font-extrabold uppercase tracking-wider text-primary">Merchant access</p><h2 className="mt-2 text-xl font-extrabold">Sign in to your terminal</h2><p className="mt-2 text-sm text-muted-foreground">Use the email address or phone number and password on your verified Sura vendor account.</p><Button className="mt-5 w-full" onClick={() => router.push("/login?next=/vendor")}>Go to sign in</Button></Panel>
    if (segments[0] === "catalogue") return <VendorCatalogue merchant={(data as Row)?.merchant}/>
    if (segments[0] === "payout") return <VendorPayout value={data as Row}/>
    if (segments[0] === "redeem" && segments[1] === "review") return <VendorReview />
    if (segments[0] === "redeem" && segments[1] === "success") return <Panel><p className="text-4xl text-success">✓</p><h2 className="mt-3 text-xl font-extrabold">Handover confirmed</h2><p className="mt-2 text-sm text-muted-foreground">{(data as Row)?.commitment_title || "Voucher redemption"}</p><p className="mt-4 text-2xl font-extrabold">{money((data as Row)?.amount)}</p><p className="mt-2 text-xs text-muted-foreground">{(data as Row)?.redeemed_at ? formatDate((data as Row).redeemed_at) : "Just now"} · Ref {(data as Row)?.redemption_id || "Recorded"}</p><p className="mt-4 rounded-lg bg-gold-soft p-3 text-xs text-gold-deep">Settlement is simulated in this MVP.</p><Link className="mt-5 inline-flex font-bold text-primary" href="/vendor/history">View settlement history →</Link></Panel>
    if (segments[0] === "redeem" && segments[1] === "rejected") return <Panel><h2 className="text-xl font-extrabold">Voucher not accepted</h2><p className="mt-2 text-sm text-muted-foreground">{message || "This voucher could not be redeemed. Check the code and try again."}</p><Button className="mt-5" onClick={() => router.replace("/vendor/redeem")}>Try another code</Button></Panel>
    if (segments[0] === "redeem") return <div className="space-y-5"><div><p className="text-sm text-muted-foreground">Scan the member’s voucher or enter its code.</p></div><Panel><label className="mb-2 block text-sm font-extrabold" htmlFor="voucher">Voucher code</label><input id="voucher" value={code} onChange={(e) => setCode(e.target.value.toUpperCase())} className="h-14 w-full rounded-lg border border-hairline bg-background px-4 text-lg font-bold tracking-[.1em] outline-none focus:ring-4 focus:ring-primary/15" placeholder="Enter code" autoCapitalize="characters"/><Button className="mt-4 w-full" loading={busy} disabled={!code.trim()} onClick={() => run(() => validateVoucher(code.trim()), (result) => { setData(result as Row); router.push("/vendor/redeem/review") })}>Validate voucher</Button><p className="mt-3 text-xs text-muted-foreground">The code is checked against your verified merchant account.</p></Panel><p className="text-center text-sm text-muted-foreground">Camera scanning can be used when a QR scanner is available on this device.</p></div>
    if (segments[0] === "history" && segments[1]) return <SimpleDetail value={data as Row} title="Redemption receipt"/>
    if (segments[0] === "history") return <div className="space-y-4"><SectionTitle title="Settled redemptions"/><Rows rows={rows} empty="No settled vouchers yet." moneyKey="amount"/></div>
    const home = data as Row | null
    return <div className="space-y-6"><div><p className="text-sm text-muted-foreground">{home?.merchant?.name || "Your verified business"}</p><h2 className="mt-1 text-2xl font-extrabold">Ready to serve?</h2></div><Button className="h-16 w-full justify-between rounded-xl px-5 text-base" onClick={() => router.push("/vendor/redeem")}>Redeem a voucher <span className="text-xl">→</span></Button><div className="grid grid-cols-2 gap-3"><Panel className="p-4"><p className="text-xs font-bold text-muted-foreground">Settled today</p><p className="mt-2 text-xl font-extrabold">{money(home?.today_settled_amount)}</p></Panel><Panel className="p-4"><p className="text-xs font-bold text-muted-foreground">Vouchers today</p><p className="mt-2 text-xl font-extrabold">{home?.today_redemption_count ?? 0}</p></Panel></div><Link href="/vendor/catalogue" className="flex items-center justify-between rounded-xl border border-hairline bg-card p-4"><span><strong className="block">Product catalogue</strong><span className="mt-1 block text-xs text-muted-foreground">Set up the items members can plan for.</span></span><span className="text-primary">→</span></Link><div><SectionTitle title="Recent activity" action={<Link className="text-sm font-bold text-primary" href="/vendor/history">See all</Link>}/><Rows rows={rows.slice(0, 4)} empty="Completed voucher handovers will show here." moneyKey="amount"/></div></div>
  }

  function VendorReview() {
    const response = (data as Row) ?? {}
    const voucher = response.voucher ?? {}
    return <Panel><p className="text-sm font-bold text-muted-foreground">Check the voucher before handover</p><h2 className="mt-2 text-xl font-extrabold">{response.commitment_title || "Sura Lock"}</h2><dl className="mt-4 divide-y divide-hairline">{[["Beneficiary", response.beneficiary_first_name || "Member"], ["Cycle", voucher.cycle_number ?? "—"], ["Amount", money(voucher.amount)], ["Voucher status", titleCase(voucher.status || "ready")]].map(([label, value]) => <div key={label} className="flex justify-between gap-4 py-3 text-sm"><dt className="text-muted-foreground">{label}</dt><dd className="font-extrabold">{value}</dd></div>)}</dl><p className="mt-2 rounded-lg bg-gold-soft p-3 text-sm text-gold-deep">Confirm only after the goods or service have been handed over.</p><Button className="mt-5 w-full" loading={busy} onClick={() => run(() => redeemVoucher(code), (result) => { setData(result); router.push("/vendor/redeem/success") })}>Confirm handover</Button><button className="mt-4 w-full text-sm font-bold text-destructive" onClick={() => router.push("/vendor/redeem/rejected")}>Reject voucher</button></Panel>
  }

  function VendorCatalogue({ merchant }: { merchant?: Row }) {
    const [products, setProducts] = useState<Row[]>([])
    const [name, setName] = useState("")
    const [price, setPrice] = useState("")
    const [notice, setNotice] = useState("")
    const [catalogueBusy, setCatalogueBusy] = useState(false)
    const [editingProduct, setEditingProduct] = useState<Row | null>(null)
    const [editingName, setEditingName] = useState("")
    const [editingPrice, setEditingPrice] = useState("")
    const loadProducts = () => getMyVendorProducts().then((result) => setProducts((result as Row).products ?? [])).catch((reason) => setNotice(reason instanceof Error ? reason.message : "We could not load your products."))
    useEffect(() => { void loadProducts() }, [])
    const add = async () => {
      setCatalogueBusy(true); setNotice("")
      try { await addVendorProduct(name.trim(), Number(price)); setName(""); setPrice(""); await loadProducts(); setNotice("Product added to your catalogue.") }
      catch (reason) { setNotice(reason instanceof Error ? reason.message : "We could not add that product.") }
      finally { setCatalogueBusy(false) }
    }
    const remove = async (productId: string) => {
      setCatalogueBusy(true); setNotice("")
      try { await removeVendorProduct(productId); await loadProducts(); setNotice("Product removed from future Lock choices.") }
      catch (reason) { setNotice(reason instanceof Error ? reason.message : "We could not remove that product.") }
      finally { setCatalogueBusy(false) }
    }
    const saveEdit = async () => {
      if (!editingProduct) return
      setCatalogueBusy(true); setNotice("")
      try { await updateVendorProduct(editingProduct.product_id, editingName.trim(), Number(editingPrice)); await loadProducts(); setEditingProduct(null); setNotice("Product updated.") }
      catch (reason) { setNotice(reason instanceof Error ? reason.message : "We could not update that product.") }
      finally { setCatalogueBusy(false) }
    }
    return <div className="space-y-4"><Panel><p className="text-xs font-extrabold uppercase tracking-wider text-primary">{merchant?.verified ? "Verified merchant" : "Merchant"}</p><h2 className="mt-2 text-xl font-extrabold">What do you sell?</h2><p className="mt-2 text-sm leading-6 text-muted-foreground">Members can choose an active item while creating a Lock. Existing Lock terms keep their original item and price.</p></Panel><Panel><h3 className="text-base font-extrabold">Add product</h3><div className="mt-3 grid gap-3 sm:grid-cols-[minmax(0,1fr)_140px_auto]"><input value={name} onChange={(event) => setName(event.target.value)} className="h-11 rounded-lg border border-hairline bg-background px-3" placeholder="Product name" maxLength={200}/><input value={price} onChange={(event) => setPrice(event.target.value.replace(/\D/g, ""))} inputMode="numeric" className="h-11 rounded-lg border border-hairline bg-background px-3" placeholder="Price"/><Button loading={catalogueBusy} disabled={!name.trim() || !Number(price)} onClick={add}>Add</Button></div></Panel>{editingProduct && <Panel><h3 className="text-base font-extrabold">Edit product</h3><div className="mt-3 grid gap-3 sm:grid-cols-[minmax(0,1fr)_140px_auto]"><input value={editingName} onChange={(event) => setEditingName(event.target.value)} className="h-11 rounded-lg border border-hairline bg-background px-3" maxLength={200}/><input value={editingPrice} onChange={(event) => setEditingPrice(event.target.value.replace(/\D/g, ""))} inputMode="numeric" className="h-11 rounded-lg border border-hairline bg-background px-3"/><Button loading={catalogueBusy} disabled={!editingName.trim() || !Number(editingPrice)} onClick={saveEdit}>Save</Button></div><button type="button" className="mt-3 text-sm font-bold text-muted-foreground" onClick={() => setEditingProduct(null)}>Cancel</button></Panel>}<div><SectionTitle title="Your products"/><div className="divide-y divide-hairline overflow-hidden rounded-xl border border-hairline bg-card">{products.filter((product) => product.status === "active").map((product) => <div key={product.product_id} className="flex items-center justify-between gap-3 px-4 py-4"><div className="min-w-0"><p className="truncate text-sm font-extrabold">{product.name}</p><p className="mt-1 text-xs text-muted-foreground">{merchant?.category || "Vendor item"}</p></div><div className="shrink-0 text-right"><p className="text-sm font-extrabold">{money(product.price)}</p><div className="mt-1 flex justify-end gap-3"><button type="button" disabled={catalogueBusy} onClick={() => { setEditingProduct(product); setEditingName(product.name); setEditingPrice(String(product.price)) }} className="text-xs font-bold text-primary disabled:opacity-50">Edit</button><button type="button" disabled={catalogueBusy} onClick={() => void remove(product.product_id)} className="text-xs font-bold text-destructive disabled:opacity-50">Remove</button></div></div></div>)}{!products.some((product) => product.status === "active") && <p className="p-4 text-sm text-muted-foreground">Add an active product for members to choose from.</p>}</div></div>{notice && <p role="status" className="rounded-lg bg-gold-soft p-3 text-sm text-gold-deep">{notice}</p>}</div>
  }

  function VendorPayout({ value }: { value: Row | null }) {
    const current = value?.account as Row | undefined
    const [banks, setBanks] = useState<string[]>((value?.banks ?? []) as string[])
    const [bank, setBank] = useState(current?.bank_name ?? "")
    const [number, setNumber] = useState("")
    const [preview, setPreview] = useState<Row | null>(null)
    const [saved, setSaved] = useState<Row | null>(current ?? null)
    const simulation = value?.simulation as Row | undefined

    useEffect(() => {
      setBanks((value?.banks ?? []) as string[])
      setSaved((value?.account ?? null) as Row | null)
    }, [value])

    const resolve = () => void run(() => resolveVendorPayoutAccount(bank, number), (result) => setPreview(result))
    const save = () => void run(() => saveVendorPayoutAccount(bank, number), (result) => {
      setSaved(result)
      setPreview(null)
      setNumber("")
      setMessage("Settlement account saved.")
    })

    return <div className="space-y-4">
      <Panel><p className="text-xs font-extrabold uppercase tracking-wider text-primary">Vendor settlement</p><h2 className="mt-2 text-xl font-extrabold">Settlement account</h2><p className="mt-2 text-sm leading-6 text-muted-foreground">Save the masked bank label for a future payout. This demo does not connect to a bank or transfer money.</p></Panel>
      {saved && <Panel><p className="text-xs font-extrabold uppercase tracking-wider text-success">Current settlement label</p><h3 className="mt-2 text-lg font-extrabold">{saved.bank_name} · {saved.account_number_masked}</h3><p className="mt-1 text-sm text-muted-foreground">{saved.display_name}</p></Panel>}
      <Panel>{simulation && <div className="mb-5 rounded-lg bg-muted p-3 text-sm"><p className="text-xs font-bold uppercase tracking-wide text-muted-foreground">Demo account holder</p><p className="mt-1 font-extrabold">{simulation.account_holder_name}</p><p className="mt-1 text-xs text-muted-foreground">Use account number <strong>{simulation.account_number}</strong>. It is accepted only for this vendor account.</p></div>}<label className="block text-sm font-bold" htmlFor="vendor-payout-bank">Bank</label><select id="vendor-payout-bank" value={bank} onChange={(event) => { setBank(event.target.value); setPreview(null) }} className="mt-2 h-12 w-full rounded-lg border border-hairline bg-background px-3"><option value="">Choose your bank</option>{banks.map((item) => <option key={item} value={item}>{item}</option>)}</select><label className="mt-4 block text-sm font-bold" htmlFor="vendor-payout-number">Account number</label><input id="vendor-payout-number" value={number} inputMode="numeric" autoComplete="off" maxLength={10} onChange={(event) => { setNumber(event.target.value.replace(/\D/g, "").slice(0, 10)); setPreview(null) }} className="mt-2 h-12 w-full rounded-lg border border-hairline bg-background px-3" placeholder="10-digit account number"/><Button className="mt-4 w-full" variant="outline" loading={busy} disabled={!bank || number.length !== 10} onClick={resolve}>Resolve account</Button></Panel>
      {preview && <Panel><p className="text-xs font-extrabold uppercase tracking-wider text-success">Simulated lookup</p><h3 className="mt-2 text-lg font-extrabold">{preview.display_name}</h3><p className="mt-1 text-sm text-muted-foreground">{preview.bank_name} · {preview.account_number_masked}</p><Button className="mt-5 w-full" loading={busy} onClick={save}>Save settlement account</Button></Panel>}
    </div>
  }

  function renderMember(): React.ReactNode {
    const obj = Array.isArray(data) ? null : data as Row | null
    const rows = (Array.isArray(data) ? data : obj?.commitments ?? obj?.entries ?? obj?.notifications ?? []) as Row[]
    if (page === "welcome") return <Welcome />
    if (!page) return <MemberHome value={obj}/>
    if (page === "account/link") return <LinkFundingAccount />
    if (page === "account/linked") return <AccountLinked value={obj}/>
    if (page === "commitments") return <Commitments rows={rows}/>
    if (page === "commitments/new") return NewCommitment()
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
    const linkedAccount = value?.linked_account as Row | undefined
    return <div className="space-y-6"><div className="flex items-start justify-between gap-3"><div><p className="text-sm text-muted-foreground">Good morning,</p><h2 className="mt-1 text-2xl font-extrabold">{firstName(profile.name) || "there"}</h2></div><Link href="/app/score" className="rounded-full border border-hairline bg-card px-3 py-2 text-xs font-extrabold text-primary">Score {score.score ?? "—"}</Link></div><Panel className="overflow-hidden border-0 bg-primary text-white"><div className="flex items-start justify-between"><div><p className="text-xs font-bold text-white/75">YOUR NEXT STEP</p><h3 className="mt-2 text-xl font-extrabold">{active?.title || "Start with a Sura Lock"}</h3><p className="mt-2 text-sm text-white/80">{active ? `${money(active.contribution_amount)} · ${active.contribution_frequency}` : "Save together with people you trust."}</p></div><span className="grid size-10 place-items-center rounded-full bg-white/15 text-xl">↗</span></div><Link href={active ? `/app/commitments/${active.commitment_id}` : "/app/commitments/new"} className="mt-5 inline-flex rounded-lg bg-white px-4 py-3 text-sm font-extrabold text-primary">{active ? "View your Lock" : "Create a Lock"}</Link></Panel><div className="grid grid-cols-2 gap-3"><Link href="/app/commitments/new" className="rounded-xl border border-hairline bg-card p-4"><span className="text-xl text-primary">＋</span><p className="mt-2 font-extrabold">Create Lock</p><p className="mt-1 text-xs text-muted-foreground">Start saving together</p></Link><Link href="/app/join" className="rounded-xl border border-hairline bg-card p-4"><span className="text-xl text-primary">↗</span><p className="mt-2 font-extrabold">Join a Lock</p><p className="mt-1 text-xs text-muted-foreground">Use an invite code</p></Link></div><Link href="/app/account/link" className="flex items-center justify-between rounded-xl border border-hairline bg-card p-4"><span><strong className="block">{linkedAccount ? "Funding source" : "Link a bank account"}</strong><span className="mt-1 block text-xs text-muted-foreground">{linkedAccount ? `${linkedAccount.bank_name} · ${linkedAccount.account_number_masked}` : "Add the masked funding source shown before a contribution."}</span></span><span className="text-primary">{linkedAccount ? "Change →" : "Link →"}</span></Link><div><SectionTitle title="Your commitments" action={<Link href="/app/commitments" className="text-sm font-bold text-primary">See all</Link>}/>{list.length ? <Rows rows={(list as Row[]).slice(0, 3)} empty="" linkPrefix="/app/commitments/"/> : <Panel><p className="text-sm text-muted-foreground">Your Locks will appear here once you create or join one.</p></Panel>}</div><Link href="/app/float" className="flex items-center justify-between rounded-xl border border-hairline bg-card p-4"><div><p className="font-extrabold">Sura Float</p><p className="mt-1 text-xs text-muted-foreground">A future benefit for consistent members</p></div><span className="rounded-full bg-gold-soft px-2 py-1 text-[10px] font-extrabold text-gold-deep">COMING SOON</span></Link></div>
  }

  function Commitments({ rows }: { rows: Row[] }) {
    const filtered = rows.filter((item) => listTab === "active" ? ["active", "pending_members"].includes(item.status) : listTab === "completed" ? item.status === "completed" : item.status !== "active" && item.status !== "pending_members" && item.status !== "completed")
    return <div><div className="mb-5 flex items-center justify-between"><p className="text-sm text-muted-foreground">All your group Locks in one place.</p><Link href="/app/commitments/new" className="grid size-10 place-items-center rounded-full bg-primary text-xl font-bold text-white" aria-label="Create a Lock">＋</Link></div><div className="mb-5 grid grid-cols-3 rounded-lg bg-muted p-1">{["active", "pending", "completed"].map((value) => <button key={value} onClick={() => setListTab(value)} className={`rounded-md py-2 text-xs font-extrabold capitalize ${listTab === value ? "bg-card text-primary shadow-sm" : "text-muted-foreground"}`}>{value}</button>)}</div>{filtered.length ? <Rows rows={filtered} empty="" linkPrefix="/app/commitments/"/> : <Panel className="py-8 text-center"><div className="mx-auto grid size-12 place-items-center rounded-full bg-primary-soft text-xl text-primary">▤</div><h2 className="mt-4 font-extrabold">No {listTab} commitments</h2><p className="mx-auto mt-2 max-w-xs text-sm text-muted-foreground">Create your first Lock or join one with an invite code.</p><div className="mt-5 flex justify-center gap-2"><Button size="sm" onClick={() => router.push("/app/commitments/new")}>Create Lock</Button><Button size="sm" variant="outline" onClick={() => router.push("/app/join")}>Join a Lock</Button></div></Panel>}</div>
  }

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  function LegacyNewCommitment() {
    const fields = (key: string, value: unknown) => setForm((current) => ({ ...current, [key]: value }))
    const commitmentType = String(form.type || "rotating")
    const isGoal = commitmentType === "collective_goal" || commitmentType === "individual_goal"
    const isIndividualGoal = commitmentType === "individual_goal"
    const selectedBeneficiaryId = isIndividualGoal ? session?.userId : (form.beneficiary_id || session?.userId)
    const payload = {
      ...form,
      type: commitmentType,
      contribution_amount: Number(form.contribution_amount),
      ...(isGoal ? { target_amount: Number(form.target_amount), cycles: 1, members: isIndividualGoal ? [] : members.map((member) => member.user_id), beneficiary_id: selectedBeneficiaryId, payout_order: [] } : { cycles: Number(form.cycles), members: members.map((member) => member.user_id), payout_order: lockPreview?.payout_order ?? [] }),
    }
    const chooseType = (type: "rotating" | "collective_goal" | "individual_goal") => {
      setForm((current) => ({ ...current, type, cycles: type === "rotating" ? Math.max(2, members.length + 1) : 1, beneficiary_id: type === "individual_goal" ? session?.userId || "" : current.beneficiary_id }))
      if (type === "individual_goal") setMembers([])
      setLockPreview(null)
    }
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
    const commitmentType = String(form.type || "rotating")
    const isGoal = commitmentType === "collective_goal" || commitmentType === "individual_goal"
    const isIndividualGoal = commitmentType === "individual_goal"
    const selectedBeneficiaryId = isIndividualGoal ? session?.userId : (form.beneficiary_id || session?.userId)
    const chooseType = (type: "rotating" | "collective_goal" | "individual_goal") => {
      setForm((current) => ({ ...current, type, cycles: type === "rotating" ? Math.max(2, members.length + 1) : 1, beneficiary_id: type === "individual_goal" ? session?.userId || "" : current.beneficiary_id }))
      if (type === "individual_goal") setMembers([])
      setLockPreview(null)
    }
    const vendorsPerPage = 5
    const vendorPageCount = Math.max(1, Math.ceil(vendorList.length / vendorsPerPage))
    const visibleVendors = vendorList.slice(vendorPage * vendorsPerPage, (vendorPage + 1) * vendorsPerPage)
    const payload = {
      ...form,
      type: commitmentType,
      contribution_amount: Number(form.contribution_amount),
      ...(isGoal ? { target_amount: Number(form.target_amount), cycles: 1, members: isIndividualGoal ? [] : members.map((member) => member.user_id), beneficiary_id: selectedBeneficiaryId, payout_order: [] } : { cycles: Number(form.cycles), members: members.map((member) => member.user_id), payout_order: lockPreview?.payout_order ?? [] }),
    }
    const chooseVendor = (vendor: Row) => {
      fields("vendor_id", vendor.vendor_id)
      fields("product_id", "")
      setVendorProducts([])
      void getVendorProducts(vendor.vendor_id)
        .then((result) => setVendorProducts(((result as Row).products ?? []) as Row[]))
        .catch((reason) => setError(reason instanceof Error ? reason.message : "We could not load this vendor's products."))
    }
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
      {step === 0 && <Panel><h2 className="text-lg font-extrabold">Name your commitment</h2><label htmlFor="lock-title" className="mt-4 block text-sm font-bold">Name</label><input id="lock-title" value={form.title} onChange={(event) => fields("title", event.target.value)} placeholder="e.g. Laptop fund" className="mt-2 h-12 w-full rounded-lg border border-hairline bg-background px-3 outline-none focus:ring-4 focus:ring-primary/15"/><p className="mt-5 text-sm font-extrabold">Commitment type</p><div className="mt-2 grid gap-2">{([['rotating', 'Rotating Sura Lock', 'Members contribute regularly and take turns receiving each cycle pool.'], ['collective_goal', 'Collective goal', 'A group saves toward one target. The nominated member receives one vendor voucher at the target.'], ['individual_goal', 'Individual goal', 'You save toward one target yourself and receive one vendor voucher at the target.']] as const).map(([type, name, detail]) => <button type="button" key={type} aria-pressed={commitmentType === type} onClick={() => chooseType(type)} className={`rounded-lg border-2 p-3 text-left transition ${commitmentType === type ? 'border-primary bg-primary-soft' : 'border-hairline bg-card hover:border-primary/40'}`}><p className="font-extrabold">{name}</p><p className="mt-1 text-xs text-muted-foreground">{detail}</p></button>)}</div></Panel>}
      {step === 1 && <Panel className="min-w-0 overflow-hidden">
        <h2 className="text-lg font-extrabold">Choose a verified vendor</h2>
        <p className="mt-1 text-sm text-muted-foreground">Choose the business and item your eventual payout is for. Both are locked after creation.</p>
        <div className="mt-4 grid min-w-0 gap-2">{visibleVendors.map((vendor) => { const selected = form.vendor_id === vendor.vendor_id; return <button key={vendor.vendor_id} type="button" aria-pressed={selected} onClick={() => chooseVendor(vendor)} className={`grid w-full min-w-0 grid-cols-[minmax(0,1fr)_auto] items-center gap-3 rounded-xl border-2 px-4 py-3.5 text-left transition-colors ${selected ? "border-primary bg-primary-soft shadow-sm" : "border-hairline bg-card hover:border-primary/40 hover:bg-muted/50"}`}><span className="min-w-0"><strong className="block break-words text-sm font-extrabold">{vendor.name}</strong><span className="mt-1 block text-xs font-semibold text-muted-foreground">{vendor.category}</span></span><span className={`flex shrink-0 items-center gap-1.5 text-xs font-extrabold ${selected ? "text-primary" : "text-success"}`}><span aria-hidden="true" className="grid size-5 place-items-center rounded-full bg-success-soft">✓</span>Verified</span></button> })}</div>
        {vendorList.length > vendorsPerPage && <div className="mt-3 flex items-center justify-between rounded-lg border border-hairline bg-muted/40 p-2 text-xs font-bold"><button type="button" className="rounded px-2 py-1 text-primary disabled:opacity-40" disabled={vendorPage === 0} onClick={() => setVendorPage((current) => Math.max(0, current - 1))}>Previous</button><span className="text-muted-foreground">{vendorPage + 1} of {vendorPageCount}</span><button type="button" className="rounded px-2 py-1 text-primary disabled:opacity-40" disabled={vendorPage >= vendorPageCount - 1} onClick={() => setVendorPage((current) => Math.min(vendorPageCount - 1, current + 1))}>Next</button></div>}
        {form.vendor_id && <div className="mt-5 border-t border-hairline pt-4"><p className="text-sm font-extrabold">Choose an item</p><div className="mt-2 grid gap-2">{vendorProducts.map((product) => { const selected = form.product_id === product.product_id; return <button type="button" key={product.product_id} aria-pressed={selected} onClick={() => fields("product_id", product.product_id)} className={`flex items-center justify-between gap-3 rounded-lg border px-3 py-3 text-left ${selected ? "border-primary bg-primary-soft" : "border-hairline bg-card"}`}><span className="min-w-0 truncate text-sm font-bold">{product.name}</span><span className="shrink-0 text-sm font-extrabold">{money(product.price)}</span></button> })}</div>{!vendorProducts.length && <p className="mt-3 rounded-lg bg-muted p-3 text-sm text-muted-foreground">This vendor has no active products yet. Choose another verified vendor.</p>}</div>}
        {!vendorList.length && <p className="mt-4 rounded-lg bg-muted p-4 text-sm text-muted-foreground">No verified vendors are available yet.</p>}
      </Panel>}
      {step === 2 && <Panel><h2 className="text-lg font-extrabold">Set your contribution</h2><label htmlFor="amount" className="mt-4 block text-sm font-bold">{isGoal ? 'Suggested contribution' : 'Amount per member'}</label><div className="mt-2 flex h-12 items-center rounded-lg border border-hairline px-3"><span className="font-bold text-muted-foreground">₦</span><input id="amount" inputMode="numeric" type="number" min="1" step="1" value={form.contribution_amount} onChange={(event) => fields("contribution_amount", event.target.value)} className="h-full min-w-0 flex-1 bg-transparent px-2 outline-none" placeholder="5,000"/></div>{isGoal && <><label htmlFor="target-amount" className="mt-4 block text-sm font-bold">Target amount</label><div className="mt-2 flex h-12 items-center rounded-lg border border-hairline px-3"><span className="font-bold text-muted-foreground">₦</span><input id="target-amount" inputMode="numeric" type="number" min="1" step="1" value={form.target_amount} onChange={(event) => fields("target_amount", event.target.value)} className="h-full min-w-0 flex-1 bg-transparent px-2 outline-none" placeholder="180,000"/></div><p className="mt-2 text-xs text-muted-foreground">The voucher releases exactly this saved amount. A vendor price difference is handled directly with the vendor.</p></>}<label id="frequency-label" className="mt-4 block text-sm font-bold">Frequency</label><Select.Root value={form.contribution_frequency} onValueChange={(value) => value && fields("contribution_frequency", value)}><Select.Trigger aria-labelledby="frequency-label" className="mt-2 flex h-12 w-full items-center justify-between rounded-lg border border-hairline bg-background px-3 text-left text-sm font-semibold outline-none transition focus-visible:ring-4 focus-visible:ring-primary/15"><Select.Value>{titleCase(String(form.contribution_frequency))}</Select.Value><Select.Icon className="text-muted-foreground">⌄</Select.Icon></Select.Trigger><Select.Portal><Select.Positioner sideOffset={6} className="z-50 outline-none"><Select.Popup className="min-w-[var(--anchor-width)] overflow-hidden rounded-lg border border-hairline bg-card p-1 text-foreground shadow-lg outline-none"><Select.List><Select.Item value="weekly" className="flex h-10 cursor-pointer items-center rounded-md px-3 text-sm outline-none data-[highlighted]:bg-primary-soft data-[highlighted]:text-primary"><Select.ItemText>Weekly</Select.ItemText></Select.Item><Select.Item value="daily" className="flex h-10 cursor-pointer items-center rounded-md px-3 text-sm outline-none data-[highlighted]:bg-primary-soft data-[highlighted]:text-primary"><Select.ItemText>Daily</Select.ItemText></Select.Item><Select.Item value="monthly" className="flex h-10 cursor-pointer items-center rounded-md px-3 text-sm outline-none data-[highlighted]:bg-primary-soft data-[highlighted]:text-primary"><Select.ItemText>Monthly</Select.ItemText></Select.Item></Select.List></Select.Popup></Select.Positioner></Select.Portal></Select.Root>{isGoal ? <p className="mt-4 rounded-lg bg-muted p-3 text-sm">Goal target <strong className="float-right">{money(Number(form.target_amount || 0))}</strong></p> : <><p className="mt-4 rounded-lg bg-muted p-3 text-sm">Pool per cycle <strong className="float-right">{money(Number(form.contribution_amount || 0) * Number(form.cycles || 0))}</strong></p><p className="mt-2 text-xs text-muted-foreground">Cycle count will match the confirmed group size.</p></>}</Panel>}
      {step === 3 && (isIndividualGoal ? <Panel><h2 className="text-lg font-extrabold">Your individual goal</h2><p className="mt-2 text-sm leading-6 text-muted-foreground">Only you contribute to this target and only you can retrieve the vendor voucher once the target is reached.</p><p className="mt-4 rounded-lg bg-primary-soft p-3 text-sm font-bold text-primary">Beneficiary: you</p></Panel> : <Panel><h2 className="text-lg font-extrabold">{isGoal ? 'Invite goal members' : 'Invite members'}</h2><p className="mt-1 text-sm text-muted-foreground">Add members by their Sura phone number. Sura confirms each account.</p><label htmlFor="member-phone" className="mt-4 block text-sm font-bold">Member phone</label><div className="mt-2 flex gap-2"><input id="member-phone" type="tel" value={memberPhone} onChange={(event) => setMemberPhone(event.target.value)} className="h-12 min-w-0 flex-1 rounded-lg border border-hairline bg-background px-3" placeholder="080 0000 0000"/><Button size="sm" loading={busy} disabled={memberPhone.trim().length < 7} onClick={addMember}>Add</Button></div><p className="mt-3 text-xs font-bold text-muted-foreground">{members.length + 1} confirmed {isGoal ? 'goal members' : `· ${Number(form.cycles)} required`}</p><div className="mt-3 divide-y divide-hairline">{members.map((person) => <div key={person.user_id} className="flex items-center justify-between py-3 text-sm"><span className="font-bold">{person.first_name}</span><button className="text-xs font-bold text-destructive" onClick={() => { const updated = members.filter((member) => member.user_id !== person.user_id); setMembers(updated); if (!isGoal) fields("cycles", Math.max(2, updated.length + 1)); if (form.beneficiary_id === person.user_id) fields("beneficiary_id", "") }}>Remove</button></div>)}</div>{isGoal && <><label htmlFor="goal-beneficiary" className="mt-5 block text-sm font-bold">Voucher beneficiary</label><select id="goal-beneficiary" value={selectedBeneficiaryId || ""} onChange={(event) => fields("beneficiary_id", event.target.value)} className="mt-2 h-12 w-full rounded-lg border border-hairline bg-background px-3"><option value={session?.userId || ""}>You</option>{members.map((member) => <option key={member.user_id} value={member.user_id}>{member.first_name}</option>)}</select><p className="mt-2 text-xs text-muted-foreground">This nominated member alone can retrieve the vendor voucher when the target is reached.</p></>}<p className="mt-3 rounded-lg bg-gold-soft p-3 text-xs text-gold-deep">You are included automatically. {isGoal ? 'Add at least one other member for a collective goal.' : 'Add at least one other member to start.'}</p></Panel>)}
      {step === 4 && <Panel><h2 className="text-lg font-extrabold">Review the agreement</h2><dl className="mt-3 divide-y divide-hairline">{[["Type", titleCase(commitmentType)], ["Name", form.title], ["Vendor", vendorList.find((vendor) => vendor.vendor_id === form.vendor_id)?.name || "—"], ["Item", vendorProducts.find((product) => product.product_id === form.product_id)?.name || "—"], ["Suggested contribution", `${money(Number(form.contribution_amount))} · ${form.contribution_frequency}`], ...(isGoal ? [["Target", money(Number(form.target_amount))], ["Beneficiary", selectedBeneficiaryId === session?.userId ? "You" : members.find((member) => member.user_id === selectedBeneficiaryId)?.first_name || "Not selected"]] : [["Members", Number(form.cycles)], ["Pool per cycle", money(Number(form.contribution_amount) * Number(form.cycles))]])].map(([label, value]) => <div key={String(label)} className="flex justify-between gap-4 py-3 text-sm"><dt className="text-muted-foreground">{label}</dt><dd className="text-right font-extrabold">{value}</dd></div>)}</dl><p className="mt-3 rounded-lg bg-gold-soft p-3 text-xs leading-5 text-gold-deep">{isGoal ? 'The vendor voucher releases exactly the target saved. Any price gap is settled directly with the vendor.' : 'Sura’s suggested payout order and first payout safety cap are shown below.'}</p>{lockPreview && <><p className="mt-4 text-sm font-extrabold">{isGoal ? 'Goal beneficiary' : 'Suggested payout order'}</p>{isGoal ? <p className="mt-2 text-sm">{selectedBeneficiaryId === session?.userId ? 'You' : members.find((member) => member.user_id === selectedBeneficiaryId)?.first_name || 'Member'}</p> : <ol className="mt-2 list-inside list-decimal text-sm">{(lockPreview.payout_order ?? []).map((id: string, index: number) => <li key={`${id}-${index}`}>{members.find((member) => member.user_id === id)?.first_name || (id === session?.userId ? "You" : "Member")}</li>)}</ol>}<p className={`mt-3 rounded-lg p-3 text-xs font-bold ${lockPreview.can_create ? "bg-success-soft text-success" : "bg-red-50 text-red-700"}`}>{lockPreview.can_create ? (isGoal ? 'This goal is ready to create.' : 'This Lock is within the current first payout cap.') : lockPreview.blocking_reason}</p></>}<label className="mt-4 flex gap-3 text-sm leading-5"><input type="checkbox" checked={consentAccepted} onChange={(event) => setConsentAccepted(event.target.checked)} className="mt-1 size-4 accent-primary"/><span>I agree to Sura processing my Lock activity to calculate my private Sura Score. <Link href="/app/consent" className="font-bold text-primary">Read details</Link></span></label></Panel>}
      <div className="flex gap-3"><Button variant="outline" className="flex-1" disabled={step === 0 || busy} onClick={() => setStep((current) => current - 1)}>Back</Button><Button className="flex-1" loading={busy} disabled={step === 0 ? !String(form.title).trim() : step === 1 ? !form.vendor_id || !form.product_id : step === 2 ? !Number(form.contribution_amount) || (isGoal && !Number(form.target_amount)) : step === 3 ? (isIndividualGoal ? false : members.length === 0 || (isGoal && !selectedBeneficiaryId)) : !consentAccepted || lockPreview?.can_create === false} onClick={step === 4 ? create : next}>{step < 4 ? "Continue" : (isGoal ? "Create goal" : "Create Lock")}</Button></div>
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
    return <div className="space-y-4"><Panel><div className="flex items-start justify-between gap-3"><div><span className="rounded-full bg-primary-soft px-2.5 py-1 text-[10px] font-extrabold uppercase text-primary">{titleCase(status)}</span><h2 className="mt-3 text-xl font-extrabold">{lock.title || "Your Sura Lock"}</h2><p className="mt-1 text-sm text-muted-foreground">{money(lock.contribution_amount)} · {lock.contribution_frequency || "weekly"}</p></div><span className="grid size-11 place-items-center rounded-full bg-gold-soft text-lg text-gold-deep">↻</span></div><div className="mt-5 h-2 overflow-hidden rounded-full bg-muted"><div className="h-full rounded-full bg-primary" style={{ width: `${Math.min(100, Number(lock.progress_percent ?? 22))}%` }}/></div><div className="mt-2 flex justify-between text-xs text-muted-foreground"><span>Cycle {lock.current_cycle_number ?? 1} of {lock.cycles ?? "—"}</span><span>{lock.completed_cycle_count ?? 0} completed</span></div><Button className="mt-5 w-full" onClick={() => router.push(`/app/commitments/${segments[1]}/contribute`)}>{status === "pending_members" ? "Share invite" : "Contribute"}</Button></Panel><div className="grid grid-cols-4 rounded-lg bg-muted p-1">{tabs.map((name) => <button key={name} onClick={() => setTab(name)} className={`rounded-md py-2 text-[10px] font-extrabold ${tab === name ? "bg-card text-primary shadow-sm" : "text-muted-foreground"}`}>{name}</button>)}</div><Panel><SectionTitle title={tab}/>{tab === "Overview" ? <dl className="divide-y divide-hairline">{[["Members", lock.member_count ?? lock.members?.length ?? "—"], ["Next payout", lock.next_payout?.beneficiary_name || "See schedule"], ["Vendor", lock.vendor_name || lock.vendor?.name || "Verified vendor"], ["Item", lock.product?.name || "No item selected"], ["Item price", lock.product?.price ? money(lock.product.price) : "—"], ["Funding source", lock.linked_account ? `${lock.linked_account.bank_name} · ${lock.linked_account.account_number_masked}` : "Link an account to contribute"], ["Invite code", lock.invite_code || "—"]].map(([label, value]) => <div key={label} className="flex justify-between gap-3 py-3 text-sm"><span className="text-muted-foreground">{label}</span><strong>{value}</strong></div>)}</dl> : <Rows rows={tab === "Members" ? lock.members ?? [] : tab === "Schedule" ? lock.cycle_states ?? lock.payout_schedule ?? [] : lock.activity ?? []} empty={`No ${tab.toLowerCase()} details yet.`}/>}</Panel>{status === "pending_members" && <Button variant="outline" className="w-full" onClick={() => run(() => cancelCommitment(segments[1]), () => router.push("/app/commitments"))}>Cancel pending Lock</Button>}</div>
  }
  function Contribute({ value }: { value: Row | null }) {
    const lock = value ?? {}
    const id = segments[1]
    const isGoal = lock.type === "collective_goal" || lock.type === "individual_goal"
    const [goalAmount, setGoalAmount] = useState("")
    const [goalEventId, setGoalEventId] = useState("")
    const amount = Number(isGoal ? (goalAmount || lock.contribution_amount || 0) : (lock.contribution_due ?? lock.contribution_amount ?? 0))
    const account = lock.linked_account ?? {}
    const submit = () => {
      const eventId = isGoal ? (goalEventId || `sura-goal-${id}-${session?.userId}-${crypto.randomUUID()}`) : `sura-${id}-${session?.userId}-${lock.current_cycle_number ?? 1}`
      if (isGoal) setGoalEventId(eventId)
      run(() => contribute(id, amount, eventId), (result) => {
        const replay = Boolean((result as Row)?.idempotent_replay)
        setMessage(replay ? "Already recorded" : "Contribution recorded")
        router.push(`/app/commitments/${id}/contribute/receipt`)
      })
    }
    const goal = lock.goal ?? {}
    const remaining = Number(goal.remaining_total ?? 0)
    return <div className="space-y-4"><Panel><p className="text-xs font-bold uppercase tracking-wider text-primary">{isGoal ? 'Target contribution' : `Current cycle · ${lock.current_cycle_number ?? 1}`}</p>{isGoal ? <><label htmlFor="goal-contribution" className="mt-4 block text-sm font-bold">Contribution amount</label><div className="mt-2 flex h-12 items-center rounded-lg border border-hairline px-3"><span className="font-bold text-muted-foreground">₦</span><input id="goal-contribution" value={goalAmount} onChange={(event) => { setGoalAmount(event.target.value.replace(/\D/g, "")); setGoalEventId("") }} inputMode="numeric" className="h-full min-w-0 flex-1 bg-transparent px-2 outline-none" placeholder={String(lock.contribution_amount || '')}/></div><p className="mt-2 text-xs text-muted-foreground">Up to {money(remaining)} remains toward {money(goal.target_amount)}.</p></> : <><h2 className="mt-3 text-3xl font-extrabold">{money(amount)}</h2><p className="mt-1 text-sm text-muted-foreground">Locked contribution due for {lock.title || "this Lock"}</p></>}<div className="mt-5 rounded-lg bg-muted p-3 text-sm"><p className="text-xs font-bold uppercase tracking-wide text-muted-foreground">Funding source</p><p className="mt-1 font-extrabold">{account.bank_name} · {account.account_number_masked}</p><p className="mt-1 text-xs text-muted-foreground">Simulated only. No money leaves this account.</p></div><div className="mt-5 border-t border-hairline pt-4"><div className="flex justify-between text-sm"><span className="text-muted-foreground">{isGoal ? 'Target progress' : 'Cycle progress'}</span><strong>{isGoal ? `${money(goal.contributed_total)} of ${money(goal.target_amount)}` : `${lock.paid_count ?? 0} of ${lock.member_count ?? lock.cycles ?? "—"} paid`}</strong></div><div className="mt-2 h-2 rounded-full bg-muted"><div className="h-full rounded-full bg-success" style={{ width: `${isGoal ? Math.min(100, Number(goal.progress_percent ?? 0)) : Math.min(100, Number(lock.paid_percent ?? 0))}%` }}/></div></div></Panel><Button className="w-full" loading={busy} disabled={!amount || (isGoal && (amount > remaining || !remaining))} onClick={submit}>Confirm contribution</Button><p className="text-center text-xs text-muted-foreground">A retry uses the same reference and will never create a second contribution.</p></div>
  }

  function LinkFundingAccount() {
    const selectedPartner = fundingPartners.find((partner) => partner.bank_id === fundingPartnerId)
    const resolve = () => void run(() => resolveLinkedAccount(fundingBank, fundingNumberRef.current, fundingPartnerId || undefined), (result) => setFundingPreview(result))
    const confirm = () => void run(() => linkAccount(fundingBank, fundingNumberRef.current, fundingPartnerId || undefined, shareWithPartner), () => router.push("/app/account/linked"))
    return <div className="space-y-4">
      <Panel><p className="text-xs font-bold uppercase tracking-wider text-primary">Funding source</p><h2 className="mt-2 text-xl font-extrabold">Link a bank account</h2><p className="mt-2 text-sm leading-6 text-muted-foreground">Choose the label shown before a simulated contribution. Sura does not connect to this bank, access its balance, or move money.</p>{fundingSimulation && <div className="mt-4 rounded-lg bg-muted p-3 text-sm"><p className="text-xs font-bold uppercase tracking-wide text-muted-foreground">Demo account holder</p><p className="mt-1 font-extrabold">{fundingSimulation.account_holder_name}</p><p className="mt-1 text-xs text-muted-foreground">Use account number <strong>{fundingSimulation.account_number}</strong>. The simulated lookup accepts it only for your Sura name.</p></div>}<label className="mt-5 block text-sm font-bold" htmlFor="funding-bank">Bank</label><select id="funding-bank" value={fundingBank} onChange={(event) => { setFundingBank(event.target.value); setFundingPreview(null) }} className="mt-2 h-12 w-full rounded-lg border border-hairline bg-background px-3"><option value="">Choose your bank</option>{fundingBanks.map((bank) => <option key={bank} value={bank}>{bank}</option>)}</select><label className="mt-4 block text-sm font-bold" htmlFor="funding-account-number">Account number</label><input id="funding-account-number" defaultValue="" inputMode="numeric" autoComplete="off" maxLength={10} onChange={(event) => { const digits = event.currentTarget.value.replace(/\D/g, "").slice(0, 10); event.currentTarget.value = digits; fundingNumberRef.current = digits }} className="mt-2 h-12 w-full rounded-lg border border-hairline bg-background px-3" placeholder="10-digit account number"/><Button className="mt-4 w-full" variant="outline" loading={busy} disabled={!fundingBank} onClick={resolve}>Resolve account</Button></Panel>
      {fundingPartners.length > 0 && <Panel><p className="text-xs font-bold uppercase tracking-wider text-primary">Optional Sura partner link</p><h3 className="mt-2 text-lg font-extrabold">Banks Sura supports</h3><p className="mt-1 text-sm text-muted-foreground">Choose only if you want this simulated account linked to that bank’s Sura portal.</p><select value={fundingPartnerId} onChange={(event) => { const id = event.target.value; setFundingPartnerId(id); const partner = fundingPartners.find((item) => item.bank_id === id); if (partner) setFundingBank(partner.name); setShareWithPartner(Boolean(id)); setFundingPreview(null) }} className="mt-4 h-12 w-full rounded-lg border border-hairline bg-background px-3"><option value="">Do not share with a partner bank</option>{fundingPartners.map((partner) => <option key={partner.bank_id} value={partner.bank_id}>{partner.name}</option>)}</select>{selectedPartner && <label className="mt-4 flex gap-3 text-sm leading-5"><input type="checkbox" checked={shareWithPartner} onChange={(event) => setShareWithPartner(event.target.checked)} className="mt-1 size-4 accent-primary"/><span>I agree that <strong>{selectedPartner.name}</strong> may see my Sura profile and Lock evidence in this simulated partner portal. It does not access my bank account or move money.</span></label>}</Panel>}
      {fundingPreview && <Panel><p className="text-xs font-bold uppercase tracking-wider text-success">Simulated lookup</p><h3 className="mt-2 text-lg font-extrabold">{fundingPreview.display_name}</h3><p className="mt-1 text-sm text-muted-foreground">{fundingPreview.bank_name} · {fundingPreview.account_number_masked}</p><Button className="mt-5 w-full" loading={busy} onClick={confirm}>Confirm and link account</Button></Panel>}
    </div>
  }

  function AccountLinked({ value }: { value: Row | null }) {
    const account = value?.account ?? {}
    const returnTo = fundingReturnStore.read() ?? "/app/commitments"
    return <Panel><p className="text-4xl text-success">✓</p><p className="mt-4 text-xs font-bold uppercase tracking-wider text-primary">Funding source linked</p><h2 className="mt-2 text-xl font-extrabold">{account.bank_name || "Bank account"} · {account.account_number_masked || "ending ••••"}</h2><p className="mt-2 text-sm text-muted-foreground">{account.display_name || "Your account"}. This is a display-only label for the simulated settlement demo.</p>{account.sura_partner && <p className="mt-4 rounded-lg bg-primary-soft p-3 text-sm text-primary">Shared with your selected Sura partner for this demo. You can change or remove this link at any time.</p>}<Button className="mt-5 w-full" onClick={() => { fundingReturnStore.clear(); router.push(returnTo) }}>Continue to contribution</Button></Panel>
  }

  function Voucher({ value }: { value: Row | null }) {
    const voucher = value ?? {}
    return <Panel className="text-center"><p className="text-xs font-extrabold uppercase tracking-wider text-primary">{titleCase(voucher.status || "voucher")}</p><h2 className="mt-3 text-xl font-extrabold">{voucher.vendor_name || "Your locked vendor"}</h2><p className="mt-1 text-sm text-muted-foreground">{voucher.product?.name ? `${voucher.product.name} · ` : ""}Cycle {segments.at(-2)} · {money(voucher.amount)}</p>{voucher.product?.price && <p className="mt-2 text-xs text-muted-foreground">Locked item price: {money(voucher.product.price)}</p>}<div className="mx-auto my-6 grid size-48 place-items-center border-4 border-dashed border-hairline bg-muted text-center"><div><span className="text-3xl">▦</span><p className="mt-2 text-xs text-muted-foreground">Show this code<br/>at the counter</p></div></div><p className="text-xl font-extrabold tracking-[.15em]">{voucher.code || voucher.voucher_code || "••••••"}</p><p className="mt-3 text-xs text-muted-foreground">Expires {voucher.expires_at ? formatDate(voucher.expires_at) : "as shown in your Lock terms"}</p><p className="mt-5 rounded-lg bg-success-soft p-3 text-sm font-bold text-success">After vendor confirmation, this voucher will show as redeemed.</p></Panel>
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
    return <div className="space-y-4"><Panel><div className="flex items-center gap-4"><span className="grid size-14 place-items-center rounded-full bg-primary-soft text-lg font-extrabold text-primary">{firstName(profile.name).slice(0, 1) || "S"}</span><div><h2 className="font-extrabold">{profile.name || "Sura member"}</h2><p className="mt-1 text-sm text-muted-foreground">{profile.phone || "Verified account"}</p></div></div><p className="mt-4 border-t border-hairline pt-4 text-sm">Sura Score tier <strong>{profile.tier || "Building history"}</strong></p></Panel><div className="grid gap-2">{[["Linked bank account", "/app/account/link"], ["Verification", "/app/profile/verification"], ["Privacy and consent", "/app/profile/privacy"], ["Settings", "/app/profile/settings"], ["Help and support", "/app/help"]].map(([label, href]) => <Link href={href} key={href} className="flex items-center justify-between rounded-lg border border-hairline bg-card p-4 text-sm font-bold">{label}<span className="text-primary">→</span></Link>)}</div><Button variant="outline" className="w-full" onClick={signOut}>Sign out</Button></div>
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
