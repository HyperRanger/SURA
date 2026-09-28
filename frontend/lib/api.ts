import axios from "axios"
import { siteConfig } from "@/config/site"

export const api = axios.create({
  baseURL: siteConfig.apiUrl,
  timeout: 8000,
  headers: { "Content-Type": "application/json" },
})
