import { ProductScreen } from "@/components/product/product-screen"

export default async function MemberAppPage({ params }: PageProps<"/app/[[...path]]">) {
  const { path = [] } = await params
  return <ProductScreen role="individual" segments={path} />
}
