import { bankCapabilities, integrationSteps, sampleRequest } from "@/config/for-banks"
import { siteConfig } from "@/config/site"
import { CodeBlock } from "@/components/shared/code-block"
import { FeatureCard } from "@/components/shared/feature-card"
import { IconTile } from "@/components/shared/icon-tile"
import { SectionHeading } from "@/components/shared/section-heading"

const requestCode = `curl ${siteConfig.apiUrl || "https://<sura-api>"}${sampleRequest.path} \\
  -H "${sampleRequest.apiKeyHeader}: ${sampleRequest.placeholderKey}"`

export function ApiCapabilities() {
  return (
    <section className="py-20 md:py-28">
      <div className="container-page">
        <SectionHeading
          title="what the api does"
          description="everything a savings circle needs, from the first contribution to the vendor handover, plus the data to lend on it."
        />
        <div className="mt-14 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {bankCapabilities.map((feature) => (
            <FeatureCard key={feature.title} feature={feature} />
          ))}
        </div>
      </div>
    </section>
  )
}

export function ApiIntegration() {
  return (
    <section className="bg-cloud py-20 md:py-28">
      <div className="container-page grid gap-12 lg:grid-cols-[0.9fr_1.1fr] lg:items-start">
        <div>
          <h2 className="text-3xl font-black tracking-tight text-balance sm:text-4xl">
            how it plugs in
          </h2>
          <p className="mt-4 leading-relaxed text-muted-foreground">
            your systems talk to sura with a scoped api key. sura never touches the money, it tells
            your existing accounts what to move and where it is allowed to go.
          </p>
          <ol className="mt-8 flex flex-col gap-4">
            {integrationSteps.map((step, index) => (
              <li key={step.title} className="card-raised flex items-start gap-4 rounded-3xl p-5">
                <IconTile icon={step.icon} />
                <div>
                  <h3 className="font-black">
                    <span className="text-gold-deep">{index + 1}.</span> {step.title}
                  </h3>
                  <p className="mt-1 text-sm leading-relaxed text-muted-foreground">{step.description}</p>
                </div>
              </li>
            ))}
          </ol>
        </div>

        <div className="flex min-w-0 flex-col gap-4">
          <CodeBlock label={`request: ${sampleRequest.label}`} code={requestCode} />
          <CodeBlock label="response (trimmed)" code={sampleRequest.response} />
          <p className="text-xs font-semibold text-muted-foreground">
            the key above is a placeholder. sandbox keys are issued from the bank console.
          </p>
        </div>
      </div>
    </section>
  )
}
