import Link from "next/link"
import { cn } from "@/lib/utils"

type LogoProps = {
  className?: string
}

export function Logo({ className }: LogoProps) {
  return (
    <Link
      href="/"
      aria-label="sura home"
      className={cn("flex items-center gap-2.5", className)}
    >
      <LogoMark />
      <span className="text-2xl font-black tracking-tight">sura</span>
    </Link>
  )
}

export function LogoMark({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 36 36"
      aria-hidden="true"
      className={cn("size-9 shrink-0", className)}
    >
      <circle cx="18" cy="18" r="18" className="fill-primary" />
      <path
        d="M10.5 15.5a8 8 0 0 1 13.4-4.6"
        fill="none"
        stroke="white"
        strokeWidth="3.2"
        strokeLinecap="round"
      />
      <path
        d="M25.5 20.5a8 8 0 0 1-13.4 4.6"
        fill="none"
        stroke="white"
        strokeWidth="3.2"
        strokeLinecap="round"
      />
      <circle cx="26" cy="12.5" r="2.4" fill="#ff8a1f" />
      <circle cx="10" cy="23.5" r="2.4" fill="white" />
    </svg>
  )
}
