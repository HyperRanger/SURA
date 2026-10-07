import type { Metadata } from "next"
import Link from "next/link"
import { routes } from "@/config/routes"
import { SignupForm } from "@/components/auth/signup-form"
import { parseSignupRole, safeNextPath, withNext } from "@/utils/redirect"

export const metadata: Metadata = {
  title: "Create your account — Sura",
}

export default async function SignupPage({ searchParams }: PageProps<"/signup">) {
  const params = await searchParams
  const next = safeNextPath(params.next)

  return (
    <SignupForm
      next={next}
      initialRole={parseSignupRole(params.role)}
      footer={
        <>
          Already have an account?{" "}
          <Link href={withNext(routes.login, next)} className="font-bold text-link underline-offset-4 hover:underline">
            Log in
          </Link>
        </>
      }
    />
  )
}
