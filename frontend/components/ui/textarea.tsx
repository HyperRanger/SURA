import type { ComponentProps } from "react"
import { cn } from "@/lib/utils"

export function Textarea({ className, ...props }: ComponentProps<"textarea">) {
  return (
    <textarea
      data-slot="textarea"
      className={cn(
        "w-full rounded-2xl border-2 border-b-4 border-hairline bg-card px-4 py-3 text-sm font-semibold normal-case outline-none placeholder:font-normal placeholder:text-muted-foreground/70 placeholder:lowercase hover:border-hairline-strong focus-visible:border-ring focus-visible:ring-4 focus-visible:ring-ring/15 aria-invalid:border-destructive",
        className
      )}
      {...props}
    />
  )
}
