import { Button as ButtonPrimitive } from "@base-ui/react/button"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"
import { Spinner } from "@/components/ui/spinner"

const buttonVariants = cva(
  "group/button inline-flex shrink-0 items-center justify-center gap-2 rounded-full font-extrabold whitespace-nowrap transition-all duration-150 outline-none select-none focus-visible:ring-4 focus-visible:ring-ring/30 disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        default:
          "border-b-4 border-primary-deep bg-primary text-primary-foreground hover:bg-primary-bright active:translate-y-0.5 active:border-b-2",
        gold:
          "border-b-4 border-[#a97a24] bg-gold text-gold-foreground hover:brightness-105 active:translate-y-0.5 active:border-b-2",
        outline:
          "border-2 border-b-4 border-hairline bg-card text-link hover:border-hairline-strong hover:bg-cloud active:translate-y-0.5 active:border-b-2",
        inverse:
          "border-b-4 border-hairline-strong bg-ivory text-primary hover:bg-indigo-soft dark:hover:bg-ivory/85 active:translate-y-0.5 active:border-b-2",
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

type ButtonProps = ButtonPrimitive.Props &
  VariantProps<typeof buttonVariants> & {
    // disables the button and shows a spinner, e.g. while a request is in flight
    loading?: boolean
  }

function Button({
  className,
  variant = "default",
  size = "default",
  loading = false,
  disabled,
  children,
  ...props
}: ButtonProps) {
  return (
    <ButtonPrimitive
      data-slot="button"
      aria-busy={loading || undefined}
      disabled={disabled || loading}
      className={cn(buttonVariants({ variant, size, className }))}
      {...props}
    >
      {loading && <Spinner />}
      {children}
    </ButtonPrimitive>
  )
}

export { Button, buttonVariants }
