import Image from "next/image"
import Link from "next/link"
import { cn } from "@/lib/utils"

type LogoProps = {
  className?: string
  // "inverse" is for indigo surfaces, like the footer
  tone?: "default" | "inverse"
}

// the horizontal lockup is 3898 x 1513, so 96px wide sits at ~37px tall
const width = 96
const height = 37

const indigo = "/sura-logo-horizontal.svg"
const ivory = "/sura-logo-horizontal-dark.svg"

export function Logo({ className, tone = "default" }: LogoProps) {
  return (
    <Link href="/" aria-label="sura home" title="sura home" className={cn("flex shrink-0 items-center", className)}>
      {tone === "inverse" ? (
        <Image src={ivory} alt="" width={width} height={height} priority unoptimized />
      ) : (
        // the indigo wordmark disappears on midnight, so dark mode swaps in the ivory one
        <>
          <Image src={indigo} alt="" width={width} height={height} priority unoptimized className="dark:hidden" />
          <Image src={ivory} alt="" width={width} height={height} priority unoptimized className="hidden dark:block" />
        </>
      )}
    </Link>
  )
}
