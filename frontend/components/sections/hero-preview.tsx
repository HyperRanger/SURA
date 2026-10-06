"use client"

import { useLayoutEffect, useRef, useState } from "react"
import { gsap } from "gsap"
import { HugeiconsIcon } from "@hugeicons/react"
import { Store01Icon, Tick02Icon, Ticket01Icon } from "@hugeicons/core-free-icons"
import { circlePreview, scorePreview } from "@/config/landing"
import { formatNaira, initials } from "@/utils/format"
import { cn } from "@/lib/utils"

const avatarColors = [
  "bg-primary text-primary-foreground",
  "bg-gold text-gold-foreground",
  "bg-primary-bright text-primary-foreground",
  "bg-primary-deep text-primary-foreground",
  "bg-indigo-soft text-link",
]

const initialPaid = circlePreview.members.map((m) => m.paid)

// an illustrative, animated snapshot of a circle and a score, not live data
export function HeroPreview() {
  const { members, amount, cycle, cycles } = circlePreview
  const [paid, setPaid] = useState(initialPaid)
  const paidCount = initialPaid.filter(Boolean).length
  const pot = amount * members.length
  const progress = Math.round((paidCount / members.length) * 100)

  const rootRef = useRef<HTMLDivElement>(null)
  const barRef = useRef<HTMLDivElement>(null)
  const collectedRef = useRef<HTMLSpanElement>(null)
  const percentRef = useRef<HTMLSpanElement>(null)
  const cycleRef = useRef<HTMLSpanElement>(null)
  const cycleBadgeRef = useRef<HTMLSpanElement>(null)

  useLayoutEffect(() => {
    const mm = gsap.matchMedia(rootRef)

    mm.add("(prefers-reduced-motion: no-preference)", () => {
      // one proxy drives the bar width, the naira total, the percentage and the cycle together
      const state = { paid: 0 }
      let shownCycle = 0
      const render = () => {
        const fill = state.paid / members.length
        gsap.set(barRef.current, { width: `${fill * 100}%` })
        if (collectedRef.current) collectedRef.current.textContent = formatNaira(Math.round(state.paid * amount))
        if (percentRef.current) percentRef.current.textContent = `${Math.round(fill * 100)}%`

        // cycle climbs from 1 to the last cycle as the bar fills, popping on each step
        const nextCycle = Math.round(1 + (cycles - 1) * fill)
        if (nextCycle !== shownCycle && cycleRef.current) {
          cycleRef.current.textContent = String(nextCycle)
          if (shownCycle) {
            gsap.fromTo(cycleBadgeRef.current, { scale: 1.18 }, { scale: 1, duration: 0.4, ease: "back.out(3)" })
          }
          shownCycle = nextCycle
        }
      }
      render()

      const tl = gsap.timeline({ defaults: { ease: "power3.out" } })

      tl.from("[data-anim=card]", { y: 40, autoAlpha: 0, duration: 0.8 })
        .from("[data-anim=head]", { y: 12, autoAlpha: 0, stagger: 0.08, duration: 0.5 }, "-=0.45")
        .from("[data-anim=member]", { x: -16, autoAlpha: 0, stagger: 0.07, duration: 0.45 }, "-=0.3")
        .from("[data-anim=vendor]", { y: 12, autoAlpha: 0, duration: 0.45 }, "-=0.2")
        .from("[data-anim=float]", { y: 24, autoAlpha: 0, scale: 0.94, stagger: 0.12, duration: 0.6, ease: "back.out(1.6)" }, "-=0.35")
        .to(state, { paid: paidCount, duration: 1.2, ease: "power2.inOut", onUpdate: render }, 0.5)

      // the remaining members pay in one by one until the pot is full
      members.forEach((member, i) => {
        if (member.paid) return
        tl.to(state, { paid: "+=1", duration: 0.9, ease: "power2.inOut", onUpdate: render }, "+=0.5")
          .call(() => setPaid((prev) => prev.map((p, j) => (j === i ? true : p))), undefined, "-=0.15")
      })

      tl.fromTo(
        barRef.current,
        { boxShadow: "0 0 0 0 rgb(217 164 65 / 0.55)" },
        { boxShadow: "0 0 0 8px rgb(217 164 65 / 0)", duration: 0.9, ease: "power2.out" }
      )

      tl.from("[data-anim=score-total]", {
        textContent: 0,
        snap: { textContent: 1 },
        duration: 1.4,
        ease: "power2.out",
      }, 1.2)
        .from("[data-anim=pillar]", { width: 0, stagger: 0.1, duration: 0.8, ease: "power2.out" }, 1.3)
    })

    return () => mm.revert()
  }, [members, amount, paidCount, cycles])

  return (
    <div ref={rootRef} className="relative mx-auto w-full max-w-md lg:max-w-none">
      <div data-anim="card" className="card-raised rounded-[2rem] p-5 sm:p-7">
        <div data-anim="head" className="flex items-start justify-between gap-4">
          <div>
            <p className="text-xs font-bold tracking-wide text-muted-foreground">
              Rotating circle · {circlePreview.frequency}
            </p>
            <h3 className="mt-1 text-xl font-bold">{circlePreview.title}</h3>
          </div>
          <span
            ref={cycleBadgeRef}
            className="rounded-full bg-indigo-soft px-3 py-1 text-xs font-bold text-link tabular-nums"
          >
            Cycle <span ref={cycleRef}>{cycle}</span> of {cycles}
          </span>
        </div>

        <div data-anim="head" className="mt-6">
          <div className="flex items-baseline justify-between text-sm font-bold">
            <span>
              <span ref={collectedRef} className="tabular-nums">
                {formatNaira(paidCount * amount)}
              </span>{" "}
              <span className="text-muted-foreground">of {formatNaira(pot)}</span>
            </span>
            <span ref={percentRef} className="text-muted-foreground tabular-nums">
              {progress}%
            </span>
          </div>
          <div className="mt-2 h-4 rounded-full bg-cloud">
            <div
              ref={barRef}
              className="relative h-full rounded-full bg-gold"
              style={{ width: `${progress}%` }}
            >
              <span className="absolute inset-x-2 top-1 h-1 rounded-full bg-white/35" />
            </div>
          </div>
        </div>

        <ul className="mt-6 flex flex-col gap-2.5">
          {members.map((member, i) => (
            <li key={member.name} data-anim="member" className="flex items-center gap-3">
              <span
                className={cn(
                  "flex size-9 items-center justify-center rounded-full text-sm font-bold",
                  avatarColors[i % avatarColors.length]
                )}
              >
                {initials(member.name)}
              </span>
              <span className="flex-1 text-sm font-bold">
                {member.name}
                {member.name === circlePreview.beneficiary && (
                  <span className="ml-2 rounded-full bg-indigo-soft px-2 py-0.5 text-[11px] font-bold text-link">
                    This cycle&apos;s payout
                  </span>
                )}
              </span>
              {paid[i] ? (
                <span
                  className={cn(
                    "flex items-center gap-1 text-xs font-bold text-gold-deep",
                    !member.paid && "animate-in duration-300 fade-in zoom-in-50"
                  )}
                >
                  <HugeiconsIcon icon={Tick02Icon} size={16} strokeWidth={3} />
                  Paid
                </span>
              ) : (
                <span className="text-xs font-bold text-muted-foreground">Pending</span>
              )}
            </li>
          ))}
        </ul>

        <div data-anim="vendor" className="mt-6 flex items-center gap-3 rounded-full bg-cloud p-2 pr-4">
          <span className="flex size-9 shrink-0 items-center justify-center rounded-full bg-gold text-gold-foreground">
            <HugeiconsIcon icon={Store01Icon} size={18} strokeWidth={2.2} />
          </span>
          <p className="text-xs leading-snug font-bold text-muted-foreground">
            Payout redeemable only at{" "}
            <span className="text-foreground">{circlePreview.vendor}</span>
          </p>
        </div>
      </div>

      <div className="relative z-10 -mt-5 flex flex-col items-stretch gap-3 px-3 sm:flex-row sm:items-start sm:justify-between">
        <div data-anim="float" className="card-raised flex items-center gap-2 self-start rounded-full py-2 pr-4 pl-2 sm:mt-10">
          <span className="flex size-8 items-center justify-center rounded-full bg-primary text-primary-foreground">
            <HugeiconsIcon icon={Ticket01Icon} size={16} strokeWidth={2.2} />
          </span>
          <span className="text-xs font-bold whitespace-nowrap">Cycle 1 redeemed by Amaka</span>
        </div>
        <ScoreCard />
      </div>
    </div>
  )
}

function ScoreCard() {
  return (
    <div data-anim="float" className="card-raised w-full rounded-[1.75rem] p-5 sm:max-w-[16rem]">
      <div className="flex items-baseline justify-between">
        <p className="text-xs font-bold tracking-wide text-muted-foreground">Sura score</p>
        <p className="text-xs font-bold text-muted-foreground">/ {scorePreview.max}</p>
      </div>
      <p data-anim="score-total" className="mt-1 text-4xl font-bold tracking-tight text-gold-deep tabular-nums">
        {scorePreview.total}
      </p>
      <ul className="mt-3 flex flex-col gap-2">
        {scorePreview.pillars.map((pillar) => (
          <li key={pillar.label}>
            <div className="flex justify-between text-[11px] font-bold">
              <span>{pillar.label}</span>
              <span className="text-muted-foreground">
                {pillar.points}/{pillar.max}
              </span>
            </div>
            <div className="mt-1 h-2 overflow-hidden rounded-full bg-cloud">
              <div
                data-anim="pillar"
                className="h-full rounded-full bg-ring"
                style={{ width: `${(pillar.points / pillar.max) * 100}%` }}
              />
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}
