import {
  Alert02Icon,
  ChartIncreaseIcon,
  CodeIcon,
  Key01Icon,
  RepeatIcon,
  Store01Icon,
} from "@hugeicons/core-free-icons"
import type { Feature, Step } from "@/types"

export const bankCapabilities: Feature[] = [
  {
    title: "Rotating savings circles",
    description:
      "Create a circle, enrol members and record every contribution. Retries carry an idempotency key, so a double tap never counts twice.",
    icon: RepeatIcon,
    tone: "indigo",
  },
  {
    title: "Vendor-locked vouchers",
    description:
      "Each payout becomes a voucher that only the chosen vendor can redeem. Wrong vendor, expired or reused vouchers are refused.",
    icon: Store01Icon,
    tone: "gold",
  },
  {
    title: "An explainable score",
    description:
      "Read a 0 to 1000 Sura score for any customer, split into five pillars, with every change traceable to the event that caused it.",
    icon: ChartIncreaseIcon,
    tone: "gold",
  },
  {
    title: "Fraud flags with evidence",
    description:
      "Rule-based flags arrive with the pattern detected and its evidence. Your analysts dismiss, confirm or escalate, and each action is audited.",
    icon: Alert02Icon,
    tone: "indigo",
  },
  {
    title: "Scoped API keys",
    description:
      "Issue, rotate and revoke keys per system, each limited to the scopes it needs, such as score:read or commitments:read.",
    icon: Key01Icon,
    tone: "indigo",
  },
  {
    title: "Signed webhooks",
    description:
      "Subscribe to contributions, completed cycles, redemptions and flags instead of polling, with delivery logs and test sends.",
    icon: CodeIcon,
    tone: "indigo",
  },
]

export const integrationSteps: Step[] = [
  {
    title: "Connect",
    description: "Create an API key and a webhook endpoint from the bank console.",
    icon: Key01Icon,
  },
  {
    title: "Offer",
    description: "Your app shows circles to customers under your brand, using Sura's rules.",
    icon: RepeatIcon,
  },
  {
    title: "Decide",
    description: "Read each customer's score and history, then make your own credit decision.",
    icon: ChartIncreaseIcon,
  },
]

export const bankGuarantees = [
  "Funds never leave your accounts. Sura only sends instructions",
  "Every score point traces back to a named rule",
  "Members never see each other's scores",
  "A full audit log your risk team can export",
]

// GET /v1/integrations/customers/{user_id}/commitments with a placeholder key.
// the response is trimmed to one circle from the seeded demo story
export const sampleRequest = {
  label: "List a customer's circles",
  path: "/v1/integrations/customers/usr_demo_amara/commitments",
  apiKeyHeader: "X-Sura-API-Key",
  placeholderKey: "sk_sura_sandbox_xxxxxxxx",
  response: `[
  {
    "commitment_id": "cmt_demo_laptop_rotation",
    "title": "Laptop Fund — Demo Rotation",
    "status": "active",
    "type": "rotating",
    "contribution_amount": 5000,
    "completed_cycle_count": 1,
    "payout_cycle": 1,
    "payout_status": "redeemed",
    "voucher_status": "redeemed"
  }
]`,
}
