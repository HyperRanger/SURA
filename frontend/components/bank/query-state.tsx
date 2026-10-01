"use client"

import type { ReactNode } from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { routes } from "@/config/routes"
import type { QueryResult } from "@/hooks/use-query"
import { Alert } from "@/components/ui/alert"
import { Button, buttonVariants } from "@/components/ui/button"
import { withNext } from "@/utils/redirect"

type QueryStateProps<T> = {
  query: QueryResult<T>
  skeleton: ReactNode
  // what the screen calls the thing it loads, e.g. "customers"
  noun: string
  isEmpty?: (data: T) => boolean
  empty?: ReactNode
  children: (data: T) => ReactNode
}

// the four states every data screen needs: loading, error with retry, empty, normal.
// a 401 means the bank session lapsed (U5), a 403 means this role can't see it
export function QueryState<T>({ query, skeleton, noun, isEmpty, empty, children }: QueryStateProps<T>) {
  const pathname = usePathname()
  const { data, error, isLoading, retry } = query

  if (isLoading) {
    return (
      <div role="status" aria-label={`loading ${noun}`}>
        {skeleton}
      </div>
    )
  }

  if (error) {
    if (error.is(401)) {
      return (
        <Alert
          variant="error"
          title="your session has expired"
          action={
            <Link href={withNext(routes.bank.login, pathname)} className={buttonVariants({ size: "sm" })}>
              sign in again
            </Link>
          }
        >
          sign in again and we&apos;ll bring you back here.
        </Alert>
      )
    }
    if (error.is(403)) {
      return (
        <Alert variant="info" title={`your role can't view ${noun}`}>
          ask a bank administrator to grant this permission to your account.
        </Alert>
      )
    }
    if (error.is(404)) {
      return (
        <Alert variant="info" title={`we couldn't find these ${noun}`}>
          {error.message}
        </Alert>
      )
    }
    return (
      <Alert
        variant="error"
        title={`we couldn't load ${noun}`}
        action={
          <Button type="button" variant="outline" size="sm" onClick={retry}>
            retry
          </Button>
        }
      >
        {error.message}
      </Alert>
    )
  }

  if (data === null) return null
  if (isEmpty?.(data) && empty) return <>{empty}</>
  return <>{children(data)}</>
}
