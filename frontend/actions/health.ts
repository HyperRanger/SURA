import { api } from "@/lib/api"
import { endpoints } from "@/config/endpoints"
import type { HealthResponse } from "@/types"

export async function getApiHealth(): Promise<boolean> {
  try {
    const { data } = await api.get<HealthResponse>(endpoints.health, { timeout: 8000 })
    return data.status === "ok"
  } catch {
    return false
  }
}
