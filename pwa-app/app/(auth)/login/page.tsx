import type { Metadata } from "next"
import Link from "next/link"
import { routes } from "@/config/routes"
import { AuthCard } from "@/components/auth/auth-card"
import { LoginForm } from "@/components/auth/login-form"
import { safeNextPath, withNext } from "@/utils/redirect"

export const metadata: Metadata = {
  title: "Log in — Sura",
}

// P3
export default async function LoginPage({ searchParams }: PageProps<"/login">) {
  const next = safeNextPath((await searchParams).next)

  return (
    <AuthCard
      title="Welcome back"
      description="Use your email address or phone number and password. We ask for an SMS code only on a new device or after five days."
      footer={
        <>
          New to Sura?{" "}
          <Link href={withNext(routes.signup, next)} className="font-bold text-link underline-offset-4 hover:underline">
            Create an account
          </Link>
        </>
      }
    >
      <LoginForm next={next} />
    </AuthCard>
  )
}
