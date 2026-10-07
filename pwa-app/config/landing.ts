import {
  Coins01Icon,
  EyeIcon,
  LaptopIcon,
  MoreHorizontalCircle01Icon,
  RepeatIcon,
  SquareLock02Icon,
  Store01Icon,
  StudentIcon,
  Ticket01Icon,
  UserAdd01Icon,
  UserBlock01Icon,
  Wallet01Icon,
} from "@hugeicons/core-free-icons"
import type { IconPoint } from "@/types"

// P1 copy and the illustrative previews on it. none of this is live data

export const problems: IconPoint[] = [
  {
    title: "The collector disappears",
    description: "Informal ajo runs on trust in one person. When they vanish, so does everyone's money.",
    icon: UserBlock01Icon,
  },
  {
    title: "The payout melts away",
    description: "Cash in hand gets spent on everything except the thing you were saving for.",
    icon: Wallet01Icon,
  },
  {
    title: "Your discipline goes unseen",
    description: "Years of paying on time leave no record a bank can read, so credit stays out of reach.",
    icon: EyeIcon,
  },
]

export const lockSteps: IconPoint[] = [
  {
    title: "Create a Lock",
    description: "Pick the amount, daily or weekly, how many cycles, and the vendor every payout goes to.",
    icon: SquareLock02Icon,
  },
  {
    title: "Invite your circle",
    description: "Share an invite code. The Lock starts once everyone has joined and agreed to the order.",
    icon: UserAdd01Icon,
  },
  {
    title: "Contribute on time",
    description: "Pay your share each cycle. Everyone can see who has paid, so nobody is left guessing.",
    icon: Coins01Icon,
  },
  {
    title: "Collect at the vendor",
    description: "When it's your cycle and the pot is full, you get a voucher for the agreed vendor.",
    icon: Ticket01Icon,
  },
]

export const commitmentTypes = [
  { title: "Rotating", description: "Take turns collecting the pot", icon: RepeatIcon, available: true },
  { title: "Group goal", description: "Save towards one shared purchase", icon: UserAdd01Icon, available: false },
  { title: "Personal goal", description: "Lock savings for yourself", icon: SquareLock02Icon, available: false },
]

export const vendorLockPoints = [
  "The vendor is chosen when the Lock is created, and it can't be changed later",
  "Only that vendor can redeem the voucher. Anywhere else, it is rejected",
  "The vendor sees your first name only, never your phone number or score",
]

export const scorePoints = [
  { title: "Private to you", description: "Other members and vendors never see it." },
  { title: "Explained, point by point", description: "Every change shows the event and the rule behind it." },
  { title: "A fair start", description: "Once verified, you begin with 120 points and grow from there." },
]

export const audiences = [
  { title: "Students", description: "Allowance or fees", icon: StudentIcon },
  { title: "Traders", description: "Daily or weekly sales", icon: Store01Icon },
  { title: "Freelancers", description: "Paid per gig", icon: LaptopIcon },
  { title: "Everyone else", description: "However you earn", icon: MoreHorizontalCircle01Icon },
]

export const lockPreview = {
  title: "Laptop Fund",
  frequency: "Weekly",
  amount: 17500,
  cycle: 2,
  cycles: 5,
  vendor: "Ade Electronics",
  nextPayout: { name: "Tunde", date: "Fri, 9 Oct" },
  members: [
    { name: "Amara", paid: true },
    { name: "Tunde", paid: true },
    { name: "Zainab", paid: true },
    { name: "Ifeanyi", paid: false },
    { name: "Bisi", paid: false },
  ],
}

export const voucherPreview = {
  code: "SURA-7KQ4-92XD",
  amount: 87500,
  vendor: "Ade Electronics",
  beneficiary: "Tunde",
  cycle: 2,
  expires: "16 Oct",
  wrongVendor: "Mega Gadgets",
}

// tiers and weights match backend/app/services/scoring.py
export const scorePreview = {
  total: 512,
  max: 1000,
  tier: "Building",
  pillars: [
    { label: "Commitment", weight: 35, points: 280, max: 350 },
    { label: "Repayment", weight: 25, points: 0, max: 250 },
    { label: "Stability", weight: 20, points: 112, max: 200 },
    { label: "Verification", weight: 12, points: 120, max: 120 },
    { label: "Social", weight: 8, points: 0, max: 80 },
  ],
}
