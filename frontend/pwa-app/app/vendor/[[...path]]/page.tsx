import { ProductScreen } from "@/components/product/product-screen"

export default async function VendorAppPage({ params }: PageProps<"/vendor/[[...path]]">) {
  const { path = [] } = await params
  return <ProductScreen role="vendor" segments={path} />
}
