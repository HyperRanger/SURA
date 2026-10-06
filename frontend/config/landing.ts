import {
  Alert02Icon,
  BankIcon,
  ChartIncreaseIcon,
  Coins01Icon,
  LaptopIcon,
  RepeatIcon,
  ShieldUserIcon,
  Store01Icon,
  StudentIcon,
  Ticket01Icon,
  UserAdd01Icon,
} from "@hugeicons/core-free-icons"
import type { Audience, Faq, Feature, Step } from "@/types"

export const heroStats = [
  {
    value: "93%",
    label: "of employed Nigerians work outside formal payroll",
    source: "NESG, 2025",
  },
  {
    value: "0",
    label: "cash withdrawals. Every payout goes to a verified vendor",
    source: "By design",
  },
  {
    value: "5",
    label: "named pillars behind every Sura score point",
    source: "Fully explainable",
  },
]

export const features: Feature[] = [
  {
    title: "Rotating savings circles",
    description:
      "Members agree on an amount, a schedule and a payout order. Sura tracks every contribution and releases each cycle's pot to the right person, automatically.",
    icon: RepeatIcon,
    tone: "indigo",
  },
  {
    title: "Payouts locked to a vendor",
    description:
      "A payout never becomes cash. It is redeemed with a voucher at the verified vendor the group picked on day one, so nobody can collect and disappear.",
    icon: Store01Icon,
    tone: "gold",
  },
  {
    title: "A score banks can read",
    description:
      "Sura score runs from 0 to 1000 and is built from contribution history, not payslips. Every point traces back to one of five named pillars.",
    icon: ChartIncreaseIcon,
    tone: "gold",
  },
  {
    title: "A safe start for new groups",
    description:
      "If nobody in a circle has a track record yet, the first payout is capped. Members with proven history can take early slots, new members start later.",
    icon: ShieldUserIcon,
    tone: "indigo",
  },
  {
    title: "Missed payments, on record",
    description:
      "When a member misses a contribution, Sura flags it and it shows in their score. No hidden penalties and no insurance add-ons.",
    icon: Alert02Icon,
    tone: "indigo",
  },
  {
    title: "Runs on the bank's own rails",
    description:
      "Sura never holds money. It instructs the bank's existing accounts to move funds, and plugs into your product through one API.",
    icon: BankIcon,
    tone: "indigo",
  },
]

export const audiences: Audience[] = [
  {
    title: "Traders",
    description: "Daily cash income, and already saving in ajo circles.",
    icon: Store01Icon,
  },
  {
    title: "Students",
    description: "Allowances and fees that land once a term.",
    icon: StudentIcon,
  },
  {
    title: "Freelancers",
    description: "Paid in bursts, between gigs and projects.",
    icon: LaptopIcon,
  },
  {
    title: "Banks and fintechs",
    description: "A new product to launch, without new underwriting risk.",
    icon: BankIcon,
  },
]

export const steps: Step[] = [
  {
    title: "Create a circle",
    description:
      "Set the amount, how often everyone pays, the number of cycles and the vendor payouts go to. Invite members with a code.",
    icon: UserAdd01Icon,
  },
  {
    title: "Contribute on schedule",
    description:
      "Each member pays in daily or weekly. Everyone can see who has paid for the current cycle.",
    icon: Coins01Icon,
  },
  {
    title: "Redeem at the vendor",
    description:
      "Once a cycle is fully funded, that cycle's member gets a voucher for the chosen vendor. No cash changes hands.",
    icon: Ticket01Icon,
  },
  {
    title: "Build your score",
    description:
      "Every on-time payment and completed circle adds to your Sura score, which a bank can use to offer you credit.",
    icon: ChartIncreaseIcon,
  },
]

export const bankPoints = [
  "One API to launch savings circles under your own brand",
  "Funds stay in your accounts. Sura only sends instructions",
  "A rule-based score your credit team can audit line by line",
  "A clear answer for new users with zero history",
]

export const faqs: Faq[] = [
  {
    question: "What is Sura?",
    answer:
      "Sura is infrastructure that banks and fintechs use to offer savings circles and credit to people without a monthly salary. You use it through your bank's app. The bank uses Sura to run the rules and read your track record.",
  },
  {
    question: "Is Sura a bank? Does it hold my money?",
    answer:
      "No. Sura never holds funds. Your money stays with the bank or fintech you signed up with. Sura only tells their systems when to move money and where it is allowed to go.",
  },
  {
    question: "How is this different from a normal ajo or esusu?",
    answer:
      "The idea is the same: a group contributes on a schedule and one member receives the pot each cycle. The difference is that the rules are enforced by software, every contribution is recorded, and payouts go to an agreed vendor instead of into someone's hand.",
  },
  {
    question: "Who gets paid first?",
    answer:
      "Members with a proven Sura score can take the early slots, highest score first. If everyone in the group is new, the group decides the order itself, and the first payout is capped at a small amount until everyone has completed one full rotation.",
  },
  {
    question: "Why can't I withdraw the payout as cash?",
    answer:
      "Because vendor-locked payouts are what make the circle safe to join. The group chooses a verified vendor when the circle is created, and each payout can only be redeemed there. That removes the risk of someone collecting early and walking away.",
  },
  {
    question: "How is my Sura score calculated?",
    answer:
      "It is a weighted sum of five pillars: commitment behaviour (35%), repayment behaviour (25%), transaction stability (20%), institutional verification (12%) and social reliability (8%). You can see the full breakdown, not just one number.",
  },
  {
    question: "I have no credit history. Can I still use Sura?",
    answer:
      "Yes. A newly verified member starts at 120 points from institutional verification alone. You can join circles straight away, and your score grows with every on-time contribution.",
  },
  {
    question: "What happens if someone misses a contribution?",
    answer:
      "Sura flags the missed payment and it is reflected in that member's score. The rest of the group can see the status of the current cycle at any time.",
  },
]

export const scorePreview = {
  total: 750,
  max: 1000,
  pillars: [
    { label: "Commitment", points: 350, max: 350 },
    { label: "Repayment", points: 0, max: 250 },
    { label: "Stability", points: 200, max: 200 },
    { label: "Verification", points: 120, max: 120 },
    { label: "Social", points: 80, max: 80 },
  ],
}

export const circlePreview = {
  title: "Shop restock circle",
  frequency: "weekly",
  amount: 10000,
  cycle: 3,
  cycles: 5,
  vendor: "Adeola Provisions",
  members: [
    { name: "Amaka", paid: true },
    { name: "Tunde", paid: true },
    { name: "Zainab", paid: true },
    { name: "Ifeanyi", paid: false },
    { name: "Bisi", paid: false },
  ],
  beneficiary: "Tunde",
}
