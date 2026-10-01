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

export function Logo({ className, tone = "default" }: LogoProps) {
  return (
    <Link href="/" aria-label="sura home" className={cn("flex shrink-0 items-center", className)}>
      <Image
        src={tone === "inverse" ? "/sura-logo-horizontal-dark.svg" : "/sura-logo-horizontal.svg"}
        alt=""
        width={width}
        height={height}
        priority
        unoptimized
      />
    </Link>
  )
}
