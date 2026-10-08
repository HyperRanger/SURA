import type { Metadata } from "next"
import { UsersScreen } from "@/components/bank/users-screen"

export const metadata: Metadata = { title: "Customers — Sura bank console" }

// B5
export default function BankUsersPage() {
  return <UsersScreen />
}
