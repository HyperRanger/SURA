import { ProductScreen } from "@/components/product/product-screen"
import { redirect } from "next/navigation"

export default async function VendorAppPage({ params }: PageProps<"/vendor/[[...path]]">) {
  const { path = [] } = await params
  if (path[0] === "login") redirect("/login")
  return <ProductScreen role="vendor" segments={path} />
}
