import Image from "next/image"
import Link from "next/link"
import { routes } from "@/config/routes"
import { cn } from "@/lib/utils"

type LogoProps = {
  className?: string
  // "inverse" is for iris surfaces
  tone?: "default" | "inverse"
}

// the horizontal lockup is 3898 x 1513, so 88px wide sits at ~34px tall
const width = 88
const height = 34

const indigo = "/sura-logo-horizontal.svg"
const ivory = "/sura-logo-horizontal-dark.svg"

export function Logo({ className, tone = "default" }: LogoProps) {
  return (
    <Link href={routes.home} aria-label="Sura home" title="Sura home" className={cn("flex shrink-0 items-center", className)}>
      {tone === "inverse" ? (
        <Image src={ivory} alt="" width={width} height={height} priority unoptimized />
      ) : (
        // the indigo wordmark disappears at night, so dark mode swaps in the ivory one
        <>
          <Image src={indigo} alt="" width={width} height={height} priority unoptimized className="dark:hidden" />
          <Image src={ivory} alt="" width={width} height={height} priority unoptimized className="hidden dark:block" />
        </>
      )}
    </Link>
  )
}
