import type { Metadata } from "next"
import Link from "next/link"
import { routes } from "@/config/routes"
import { SignupForm } from "@/components/auth/signup-form"
import { safeNextPath, withNext } from "@/utils/redirect"

export const metadata: Metadata = {
  title: "create your account — sura",
}

export default async function SignupPage({ searchParams }: PageProps<"/signup">) {
  const next = safeNextPath((await searchParams).next)

  return (
    <SignupForm
      next={next}
      footer={
        <>
          already have an account?{" "}
          <Link href={withNext(routes.login, next)} className="font-extrabold text-link underline-offset-4 hover:underline">
            log in
          </Link>
        </>
      }
    />
  )
}
