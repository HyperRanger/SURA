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
    label: "of employed nigerians work outside formal payroll",
    source: "nesg, 2025",
  },
  {
    value: "0",
    label: "cash withdrawals. every payout goes to a verified vendor",
    source: "by design",
  },
  {
    value: "5",
    label: "named pillars behind every sura score point",
    source: "fully explainable",
  },
]

export const features: Feature[] = [
  {
    title: "rotating savings circles",
    description:
      "members agree on an amount, a schedule and a payout order. sura tracks every contribution and releases each cycle's pot to the right person, automatically.",
    icon: RepeatIcon,
    tone: "blue",
  },
  {
    title: "payouts locked to a vendor",
    description:
      "a payout never becomes cash. it is redeemed with a voucher at the verified vendor the group picked on day one, so nobody can collect and disappear.",
    icon: Store01Icon,
    tone: "orange",
  },
  {
    title: "a score banks can read",
    description:
      "sura score runs from 0 to 1000 and is built from contribution history, not payslips. every point traces back to one of five named pillars.",
    icon: ChartIncreaseIcon,
    tone: "green",
  },
  {
    title: "a safe start for new groups",
    description:
      "if nobody in a circle has a track record yet, the first payout is capped. members with proven history can take early slots, new members start later.",
    icon: ShieldUserIcon,
    tone: "blue",
  },
  {
    title: "missed payments, on record",
    description:
      "when a member misses a contribution, sura flags it and it shows in their score. no hidden penalties and no insurance add-ons.",
    icon: Alert02Icon,
    tone: "orange",
  },
  {
    title: "runs on the bank's own rails",
    description:
      "sura never holds money. it instructs the bank's existing accounts to move funds, and plugs into your product through one api.",
    icon: BankIcon,
    tone: "green",
  },
]

export const audiences: Audience[] = [
  {
    title: "traders",
    description: "daily cash income, and already saving in ajo circles.",
    icon: Store01Icon,
  },
  {
    title: "students",
    description: "allowances and fees that land once a term.",
    icon: StudentIcon,
  },
  {
    title: "freelancers",
    description: "paid in bursts, between gigs and projects.",
    icon: LaptopIcon,
  },
  {
    title: "banks and fintechs",
    description: "a new product to launch, without new underwriting risk.",
    icon: BankIcon,
  },
]

export const steps: Step[] = [
  {
    title: "create a circle",
    description:
      "set the amount, how often everyone pays, the number of cycles and the vendor payouts go to. invite members with a code.",
    icon: UserAdd01Icon,
  },
  {
    title: "contribute on schedule",
    description:
      "each member pays in daily or weekly. everyone can see who has paid for the current cycle.",
    icon: Coins01Icon,
  },
  {
    title: "redeem at the vendor",
    description:
      "once a cycle is fully funded, that cycle's member gets a voucher for the chosen vendor. no cash changes hands.",
    icon: Ticket01Icon,
  },
  {
    title: "build your score",
    description:
      "every on-time payment and completed circle adds to your sura score, which a bank can use to offer you credit.",
    icon: ChartIncreaseIcon,
  },
]

export const bankPoints = [
  "one api to launch savings circles under your own brand",
  "funds stay in your accounts. sura only sends instructions",
  "a rule-based score your credit team can audit line by line",
  "a clear answer for new users with zero history",
]

export const faqs: Faq[] = [
  {
    question: "what is sura?",
    answer:
      "sura is infrastructure that banks and fintechs use to offer savings circles and credit to people without a monthly salary. you use it through your bank's app. the bank uses sura to run the rules and read your track record.",
  },
  {
    question: "is sura a bank? does it hold my money?",
    answer:
      "no. sura never holds funds. your money stays with the bank or fintech you signed up with. sura only tells their systems when to move money and where it is allowed to go.",
  },
  {
    question: "how is this different from a normal ajo or esusu?",
    answer:
      "the idea is the same: a group contributes on a schedule and one member receives the pot each cycle. the difference is that the rules are enforced by software, every contribution is recorded, and payouts go to an agreed vendor instead of into someone's hand.",
  },
  {
    question: "who gets paid first?",
    answer:
      "members with a proven sura score can take the early slots, highest score first. if everyone in the group is new, the group decides the order itself, and the first payout is capped at a small amount until everyone has completed one full rotation.",
  },
  {
    question: "why can't i withdraw the payout as cash?",
    answer:
      "because vendor-locked payouts are what make the circle safe to join. the group chooses a verified vendor when the circle is created, and each payout can only be redeemed there. that removes the risk of someone collecting early and walking away.",
  },
  {
    question: "how is my sura score calculated?",
    answer:
      "it is a weighted sum of five pillars: commitment behaviour (35%), repayment behaviour (25%), transaction stability (20%), institutional verification (12%) and social reliability (8%). you can see the full breakdown, not just one number.",
  },
  {
    question: "i have no credit history. can i still use sura?",
    answer:
      "yes. a newly verified member starts at 120 points from institutional verification alone. you can join circles straight away, and your score grows with every on-time contribution.",
  },
  {
    question: "what happens if someone misses a contribution?",
    answer:
      "sura flags the missed payment and it is reflected in that member's score. the rest of the group can see the status of the current cycle at any time.",
  },
]

export const scorePreview = {
  total: 750,
  max: 1000,
  pillars: [
    { label: "commitment", points: 350, max: 350 },
    { label: "repayment", points: 0, max: 250 },
    { label: "stability", points: 200, max: 200 },
    { label: "verification", points: 120, max: 120 },
    { label: "social", points: 80, max: 80 },
  ],
}

export const circlePreview = {
  title: "shop restock circle",
  frequency: "weekly",
  amount: 10000,
  cycle: 3,
  cycles: 5,
  vendor: "adeola provisions",
  members: [
    { name: "amaka", paid: true },
    { name: "tunde", paid: true },
    { name: "zainab", paid: true },
    { name: "ifeanyi", paid: false },
    { name: "bisi", paid: false },
  ],
  beneficiary: "tunde",
}
