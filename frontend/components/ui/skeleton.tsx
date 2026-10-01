import { cn } from "@/lib/utils"

// U10. a pulsing placeholder in the shape of the content it stands in for
export function Skeleton({ className }: { className?: string }) {
  return <div aria-hidden="true" className={cn("animate-pulse rounded-xl bg-cloud", className)} />
}
