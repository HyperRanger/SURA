import { Button as ButtonPrimitive } from "@base-ui/react/button"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "group/button inline-flex shrink-0 items-center justify-center gap-2 rounded-full font-extrabold whitespace-nowrap transition-all duration-150 outline-none select-none focus-visible:ring-4 focus-visible:ring-ring/30 disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        default:
          "border-b-4 border-primary-deep bg-primary text-primary-foreground hover:bg-primary-bright active:translate-y-0.5 active:border-b-2",
        orange:
          "border-b-4 border-orange-deep bg-orange text-white hover:brightness-105 active:translate-y-0.5 active:border-b-2",
        outline:
          "border-2 border-b-4 border-hairline bg-card text-link hover:border-hairline-strong hover:bg-cloud active:translate-y-0.5 active:border-b-2",
        inverse:
          "border-b-4 border-hairline-strong bg-white text-primary hover:bg-blue-soft active:translate-y-0.5 active:border-b-2 dark:border-primary-deep dark:bg-background dark:text-link",
        ghost: "text-muted-foreground hover:bg-cloud hover:text-link",
        link: "text-link underline-offset-4 hover:underline",
      },
      size: {
        default: "h-12 px-6 text-sm",
        sm: "h-10 px-4 text-sm",
        lg: "h-14 px-8 text-base",
        icon: "size-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

function Button({
  className,
  variant = "default",
  size = "default",
  ...props
}: ButtonPrimitive.Props & VariantProps<typeof buttonVariants>) {
  return (
    <ButtonPrimitive
      data-slot="button"
      className={cn(buttonVariants({ variant, size, className }))}
      {...props}
    />
  )
}

export { Button, buttonVariants }
