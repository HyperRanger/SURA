import { isDemoEnabled } from "@/config/env"
import { Alert } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"

type DemoCodeHintProps = {
  code?: string
  onUse: (code: string) => void
  disabled?: boolean
}

// The API returns this code only from an explicitly configured demo backend.
// It is never an alternative authentication path for a real deployment.
export function DemoCodeHint({ code, onUse, disabled }: DemoCodeHintProps) {
  if (!isDemoEnabled || !code) return null

  return (
    <Alert
      variant="gold"
      title="Demo OTP"
      action={
        <Button type="button" variant="outline" size="sm" disabled={disabled} onClick={() => onUse(code)}>
          Use demo OTP
        </Button>
      }
    >
      <span className="font-mono text-base font-bold tracking-[0.3em]">{code}</span>
      <span className="block text-xs">
        Demo-only access. Never enable this for real customer accounts.
      </span>
    </Alert>
  )
}
