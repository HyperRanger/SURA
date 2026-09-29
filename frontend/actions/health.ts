import { api } from "@/lib/api"
import type { HealthResponse } from "@/types"

export async function getApiHealth(): Promise<boolean> {
  try {
    const { data } = await api.get<HealthResponse>("/health")
    return data.status === "ok"
  } catch {
    return false
  }
}
