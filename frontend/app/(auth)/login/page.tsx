import type { Metadata } from "next"
import Link from "next/link"
import { routes } from "@/config/routes"
import { AuthCard } from "@/components/auth/auth-card"
import { LoginForm } from "@/components/auth/login-form"
import { safeNextPath, withNext } from "@/utils/redirect"

export const metadata: Metadata = {
  title: "log in — sura",
}

export default async function LoginPage({ searchParams }: PageProps<"/login">) {
  const next = safeNextPath((await searchParams).next)

  return (
    <AuthCard
      title="welcome back"
      description="enter your phone number and we'll text you a code to log in."
      footer={
        <>
          new to sura?{" "}
          <Link href={withNext(routes.signup, next)} className="font-extrabold text-link underline-offset-4 hover:underline">
            create an account
          </Link>
        </>
      }
    >
      <LoginForm next={next} />
    </AuthCard>
  )
}
