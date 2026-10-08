import type { ReactNode } from "react"
import { AuthShell } from "@/components/auth/auth-shell"

// P2, P3, P4 and P8: focused screens with no site navigation
export default function AuthLayout({ children }: { children: ReactNode }) {
  return <AuthShell>{children}</AuthShell>
}
