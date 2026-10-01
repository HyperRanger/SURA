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
    title: "rotating savings circles",
    description:
      "create a circle, enrol members and record every contribution. retries carry an idempotency key, so a double tap never counts twice.",
    icon: RepeatIcon,
    tone: "indigo",
  },
  {
    title: "vendor-locked vouchers",
    description:
      "each payout becomes a voucher that only the chosen vendor can redeem. wrong vendor, expired or reused vouchers are refused.",
    icon: Store01Icon,
    tone: "gold",
  },
  {
    title: "an explainable score",
    description:
      "read a 0 to 1000 sura score for any customer, split into five pillars, with every change traceable to the event that caused it.",
    icon: ChartIncreaseIcon,
    tone: "gold",
  },
  {
    title: "fraud flags with evidence",
    description:
      "rule-based flags arrive with the pattern detected and its evidence. your analysts dismiss, confirm or escalate, and each action is audited.",
    icon: Alert02Icon,
    tone: "indigo",
  },
  {
    title: "scoped api keys",
    description:
      "issue, rotate and revoke keys per system, each limited to the scopes it needs, such as score:read or commitments:read.",
    icon: Key01Icon,
    tone: "indigo",
  },
  {
    title: "signed webhooks",
    description:
      "subscribe to contributions, completed cycles, redemptions and flags instead of polling, with delivery logs and test sends.",
    icon: CodeIcon,
    tone: "indigo",
  },
]

export const integrationSteps: Step[] = [
  {
    title: "connect",
    description: "create an api key and a webhook endpoint from the bank console.",
    icon: Key01Icon,
  },
  {
    title: "offer",
    description: "your app shows circles to customers under your brand, using sura's rules.",
    icon: RepeatIcon,
  },
  {
    title: "decide",
    description: "read each customer's score and history, then make your own credit decision.",
    icon: ChartIncreaseIcon,
  },
]

export const bankGuarantees = [
  "funds never leave your accounts. sura only sends instructions",
  "every score point traces back to a named rule",
  "members never see each other's scores",
  "a full audit log your risk team can export",
]

// GET /v1/integrations/customers/{user_id}/commitments with a placeholder key.
// the response is trimmed to one circle from the seeded demo story
export const sampleRequest = {
  label: "list a customer's circles",
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
