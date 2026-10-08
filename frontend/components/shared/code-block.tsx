import { cn } from "@/lib/utils"

type CodeBlockProps = {
  code: string
  label?: string
  className?: string
}

export function CodeBlock({ code, label, className }: CodeBlockProps) {
  return (
    <figure className={cn("overflow-hidden rounded-2xl bg-primary-deep", className)}>
      {label && (
        <figcaption className="border-b border-primary-foreground/10 px-4 py-2.5 text-xs font-bold tracking-wide text-gold">
          {label}
        </figcaption>
      )}
      <pre className="scrollbar-inverse overflow-x-auto p-4 text-[13px] leading-relaxed text-primary-foreground/90">
        <code className="font-mono">{code}</code>
      </pre>
    </figure>
  )
}
