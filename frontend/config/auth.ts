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
    label: "i'm saving",
    description: "join or start savings circles",
    icon: UserIcon,
  },
  {
    value: "vendor",
    label: "i'm a vendor",
    description: "accept sura vouchers at my shop",
    icon: Store01Icon,
  },
]

export const incomeContextOptions: ChoiceOption<IncomeContext>[] = [
  { value: "trader", label: "trader", description: "daily or weekly sales", icon: Store01Icon },
  { value: "student", label: "student", description: "allowance or fees", icon: StudentIcon },
  { value: "freelancer", label: "freelancer", description: "paid per gig", icon: LaptopIcon },
  { value: "other", label: "other", description: "something else", icon: MoreHorizontalCircle01Icon },
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
  title: "what brings you to sura?",
  description: "you can't switch later, so pick the one that fits.",
}

export const signupSteps: Record<SelfServiceRole, SignupStep[]> = {
  individual: [
    accountStep,
    {
      id: "details",
      title: "tell us who you are",
      description: "we'll text a 6-digit code to this number to confirm it's yours.",
    },
    {
      id: "earning",
      title: "how do you earn?",
      description: "this helps us shape sura around your income. it never limits what you can do.",
    },
  ],
  vendor: [
    accountStep,
    {
      id: "details",
      title: "who runs the shop?",
      description: "we'll text a 6-digit code to this number to confirm it's yours.",
    },
    {
      id: "business",
      title: "about your business",
      description: "we verify every vendor before they can accept vouchers.",
    },
  ],
}

export const incomeContexts =incomeContextOptions.map((option) => option.value)
