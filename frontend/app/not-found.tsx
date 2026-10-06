import Link from "next/link"
import { routes } from "@/config/routes"
import { Logo } from "@/components/layout/logo"
import { buttonVariants } from "@/components/ui/button"

// U2
export default function NotFound() {
  return (
    <main className="flex min-h-dvh flex-1 flex-col items-center justify-center px-5 py-16 text-center">
      <Logo />
      <p className="mt-12 text-7xl font-black tracking-tight text-link">404</p>
      <h1 className="mt-4 text-2xl font-black sm:text-3xl">We couldn&apos;t find that page</h1>
      <p className="mt-3 max-w-sm text-sm leading-relaxed font-semibold text-muted-foreground">
        The link may be old, or the page may not be built yet.
      </p>
      <Link href={routes.home} className={buttonVariants({ size: "lg", className: "mt-8" })}>
        Back to home
      </Link>
    </main>
  )
}
