import {
  LaptopIcon,
  MoreHorizontalCircle01Icon,
  Store01Icon,
  StudentIcon,
  UserIcon,
} from "@hugeicons/core-free-icons"
import type { ChoiceOption, IncomeContext, SelfServiceRole } from "@/types"

export const OTP_LENGTH = 6

export const accountTypeOptions: ChoiceOption<SelfServiceRole>[] = [
  {
    value: "individual",
    label: "I'm saving",
    description: "Join or start savings circles",
    icon: UserIcon,
  },
  {
    value: "vendor",
    label: "I'm a vendor",
    description: "Accept Sura vouchers at my shop",
    icon: Store01Icon,
  },
]

export const incomeContextOptions: ChoiceOption<IncomeContext>[] = [
  { value: "trader", label: "Trader", description: "Daily or weekly sales", icon: Store01Icon },
  { value: "student", label: "Student", description: "Allowance or fees", icon: StudentIcon },
  { value: "freelancer", label: "Freelancer", description: "Paid per gig", icon: LaptopIcon },
  { value: "other", label: "Other", description: "Something else", icon: MoreHorizontalCircle01Icon },
]

// signup is split into short steps. savers end on how they earn, vendors on their business
export type SignupStepId = "account" | "details" | "earning" | "business"

export type SignupStep = {
  id: SignupStepId
  title: string
  description: string
}

const accountStep: SignupStep = {
  id: "account",
  title: "What brings you to Sura?",
  description: "You can't switch later, so pick the one that fits.",
}

export const signupSteps: Record<SelfServiceRole, SignupStep[]> = {
  individual: [
    accountStep,
    {
      id: "details",
      title: "Tell us who you are",
      description: "We'll text a 6-digit code to this number to confirm it's yours.",
    },
    {
      id: "earning",
      title: "How do you earn?",
      description: "This helps us shape Sura around your income. It never limits what you can do.",
    },
  ],
  vendor: [
    accountStep,
    {
      id: "details",
      title: "Who runs the shop?",
      description: "We'll text a 6-digit code to this number to confirm it's yours.",
    },
    {
      id: "business",
      title: "About your business",
      description: "We verify every vendor before they can accept vouchers.",
    },
  ],
}

export const incomeContexts =incomeContextOptions.map((option) => option.value)
