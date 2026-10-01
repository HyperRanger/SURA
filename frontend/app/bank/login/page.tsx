import type { Metadata } from "next"
import Link from "next/link"
import { routes } from "@/config/routes"
import { AuthCard } from "@/components/auth/auth-card"
import { AuthShell } from "@/components/auth/auth-shell"
import { BankLoginForm } from "@/components/bank/bank-login-form"
import { safeNextPath } from "@/utils/redirect"

export const metadata: Metadata = {
  title: "bank console sign in — sura",
}

// B1
export default async function BankLoginPage({ searchParams }: PageProps<"/bank/login">) {
  const next = safeNextPath((await searchParams).next)

  return (
    <AuthShell>
      <AuthCard
        title="bank console"
        description="sign in with the staff account your institution provisioned for you."
        footer={
          <>
            not a bank partner?{" "}
            <Link href={routes.forBanks} className="font-extrabold text-link underline-offset-4 hover:underline">
              see what the api does
            </Link>
          </>
        }
      >
        <BankLoginForm next={next} />
      </AuthCard>
    </AuthShell>
  )
}
