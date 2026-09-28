import { faqs } from "@/config/landing"
import { siteConfig } from "@/config/site"
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion"
import { SectionHeading } from "@/components/shared/section-heading"

export function Faq() {
  return (
    <section id="faq" className="py-20 md:py-28">
      <div className="container-page">
        <SectionHeading
          title="frequently asked questions"
          description={
            <>
              can&apos;t find what you&apos;re looking for? email{" "}
              <a href={`mailto:${siteConfig.contactEmail}`} className="font-bold text-link hover:underline">
                {siteConfig.contactEmail}
              </a>
            </>
          }
        />

        <Accordion className="mx-auto mt-12 max-w-3xl gap-3">
          {faqs.map((faq) => (
            <AccordionItem
              key={faq.question}
              value={faq.question}
              className="card-raised rounded-[1.75rem] px-6 not-last:border-b-[5px]"
            >
              <AccordionTrigger className="text-base sm:text-lg">{faq.question}</AccordionTrigger>
              <AccordionContent className="text-[15px] leading-relaxed text-muted-foreground">
                {faq.answer}
              </AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>
      </div>
    </section>
  )
}
