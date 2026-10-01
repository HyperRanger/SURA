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

export const incomeContexts = incomeContextOptions.map((option) => option.value)
