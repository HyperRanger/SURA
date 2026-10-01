import { isDemoEnabled } from "@/config/env"
import { Alert } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"

type DemoCodeHintProps = {
  code?: string
  onUse: (code: string) => void
  disabled?: boolean
}

// non-production only. the api returns the code in the response so the demo works
// without a real sms provider
export function DemoCodeHint({ code, onUse, disabled }: DemoCodeHintProps) {
  if (!isDemoEnabled || !code) return null

  return (
    <Alert
      variant="gold"
      title="demo code"
      action={
        <Button type="button" variant="outline" size="sm" disabled={disabled} onClick={() => onUse(code)}>
          use it
        </Button>
      }
    >
      <span className="font-mono text-base font-black tracking-[0.3em]">{code}</span>
      <span className="block text-xs">shown outside production only.</span>
    </Alert>
  )
}
