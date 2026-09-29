import { mergeProps } from "@base-ui/react/merge-props"
import { useRender } from "@base-ui/react/use-render"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const badgeVariants = cva(
  "group/badge inline-flex w-fit shrink-0 items-center justify-center gap-1.5 overflow-hidden rounded-full border-2 px-3.5 py-1 text-xs font-extrabold tracking-wide whitespace-nowrap [&>svg]:pointer-events-none",
  {
    variants: {
      variant: {
        default: "border-hairline-strong bg-blue-soft text-link",
        orange: "border-orange/40 bg-orange-soft text-orange-deep dark:text-orange",
        green: "border-green/40 bg-green-soft text-green-deep dark:text-green",
        outline: "border-hairline bg-card text-muted-foreground",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

function Badge({
  className,
  variant = "default",
  render,
  ...props
}: useRender.ComponentProps<"span"> & VariantProps<typeof badgeVariants>) {
  return useRender({
    defaultTagName: "span",
    props: mergeProps<"span">(
      {
        className: cn(badgeVariants({ variant }), className),
      },
      props
    ),
    render,
    state: {
      slot: "badge",
      variant,
    },
  })
}

export { Badge, badgeVariants }
