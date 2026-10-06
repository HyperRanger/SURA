import type { LegalDocument } from "@/types"

// plain-language drafts for the demo. they need a review by counsel before launch

export const termsOfUse: LegalDocument = {
  title: "Terms of use",
  updated: "2026-10-01",
  summary:
    "These terms cover how you use Sura to save in a group, redeem payouts at a vendor and build a Sura score. Please read them before you create an account.",
  sections: [
    {
      heading: "Who we are",
      paragraphs: [
        "Sura is software that banks and fintechs use to run savings circles and keep a record of how members keep their commitments. Sura is not a bank and never holds your money. Your funds stay with the bank or fintech that offers Sura to you.",
      ],
    },
    {
      heading: "Your account",
      paragraphs: ["To use Sura you need a Nigerian mobile number that you control. You agree to:"],
      bullets: [
        "Give your real name and keep your details up to date",
        "Keep the codes we text you private and never share them with anyone, including people who say they work for Sura",
        "Hold only one personal account",
        "Tell us straight away if you think someone else has used your account",
      ],
    },
    {
      heading: "Savings circles",
      paragraphs: [
        "A circle has a fixed amount, a schedule, a number of cycles and a payout order. Once a circle starts, these cannot be changed. Each cycle, every member pays in, and one member receives that cycle's pot.",
        "If everyone in a circle is new to Sura, the first payout is capped at a small amount until everyone has completed one full rotation. The payout order and any cap are set by the rules the bank has agreed, not by any one member.",
      ],
    },
    {
      heading: "Vendor-locked payouts",
      paragraphs: [
        "Payouts are never paid out as cash. Each circle chooses a verified vendor when it is created, and a payout can only be redeemed with a voucher at that vendor. Vouchers can expire, and an expired or already redeemed voucher cannot be used again.",
      ],
    },
    {
      heading: "Missed contributions",
      paragraphs: [
        "If you miss a contribution, it is recorded against your account, other members can see that the current cycle is not fully paid, and your Sura score can go down. Sura does not charge hidden penalties.",
      ],
    },
    {
      heading: "Fair use",
      paragraphs: ["You must not use Sura to:"],
      bullets: [
        "Join a circle with no intention of paying in",
        "Create accounts for other people without their permission",
        "Try to collect a payout that is not yours, or redeem a voucher at a vendor it was not issued for",
        "Interfere with the service or try to access data that is not yours",
      ],
    },
    {
      heading: "When we can restrict an account",
      paragraphs: [
        "If our fraud rules flag activity on an account, we may limit what it can do while the bank reviews it. We will tell you what is limited and how to get help. You can still see your history while a review is open.",
      ],
    },
    {
      heading: "Changes and contact",
      paragraphs: [
        "We may update these terms. If a change affects you, we will tell you before it takes effect. If you have a question about these terms, contact the bank or fintech that gave you access to Sura.",
      ],
    },
  ],
}

export const privacyNotice: LegalDocument = {
  title: "Privacy notice",
  updated: "2026-10-01",
  summary:
    "This notice explains what Sura collects, how your Sura score is worked out from it, who can see it and the rights you have under the Nigeria Data Protection Act 2023.",
  sections: [
    {
      heading: "What we collect",
      bullets: [
        "Your name, phone number and how you earn (trader, student, freelancer or other)",
        "The circles you create or join, and each contribution you make, with its date and amount",
        "The vouchers issued to you and where they were redeemed",
        "Basic security data, such as when and how you signed in",
      ],
    },
    {
      heading: "What we do not collect",
      bullets: [
        "Your bank account balance or your transactions outside Sura",
        "Your contacts, location or photos",
        "Your BVN or NIN, unless the bank you signed up with asks you to verify with them",
      ],
    },
    {
      heading: "How your Sura score is processed",
      paragraphs: [
        "Your Sura score is a number from 0 to 1000. It is worked out automatically by fixed rules, from five named pillars: commitment behaviour (35%), repayment behaviour (25%), transaction stability (20%), institutional verification (12%) and social reliability (8%).",
        "Every change to your score is written to an audit log with the reason, the pillar it affected and the event that caused it. You can see every entry yourself, and so can the bank that offers Sura to you.",
        "We process your data this way with your consent, which we ask for before you create or join your first circle. You can withdraw it at any time from your profile. Withdrawing it stops new score changes, but it does not erase records we must keep by law.",
      ],
    },
    {
      heading: "Who can see your score",
      bullets: [
        "You, with the full breakdown and history",
        "The bank or fintech that offers Sura to you, to decide what products they can offer you",
        "Never other members of your circle. They only see your name and whether you have paid this cycle",
        "Never vendors. They only see your first name when you redeem a voucher",
      ],
    },
    {
      heading: "Automated decisions",
      paragraphs: [
        "Your score is calculated automatically, but Sura does not decide on its own whether you get credit. Any lending decision is made by the bank, and you have the right to ask them for a person to review it and to explain the reasons.",
      ],
    },
    {
      heading: "How long we keep it",
      paragraphs: [
        "We keep your circle and contribution records for as long as your account is open, and afterwards for as long as financial record-keeping law requires. Sign-in codes are never stored in a readable form and expire within minutes.",
      ],
    },
    {
      heading: "Your rights",
      paragraphs: ["Under the Nigeria Data Protection Act 2023 you can:"],
      bullets: [
        "Ask for a copy of the data we hold about you",
        "Ask us to correct anything that is wrong",
        "Withdraw your consent to score processing",
        "Object to automated processing and ask for a human review",
        "Complain to the Nigeria Data Protection Commission",
      ],
    },
    {
      heading: "Contact",
      paragraphs: [
        "To use any of these rights, contact the bank or fintech that gave you access to Sura. They will pass your request to us where needed.",
      ],
    },
  ],
}
