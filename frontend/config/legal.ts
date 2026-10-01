import type { LegalDocument } from "@/types"

// plain-language drafts for the demo. they need a review by counsel before launch

export const termsOfUse: LegalDocument = {
  title: "terms of use",
  updated: "2026-10-01",
  summary:
    "these terms cover how you use sura to save in a group, redeem payouts at a vendor and build a sura score. please read them before you create an account.",
  sections: [
    {
      heading: "who we are",
      paragraphs: [
        "sura is software that banks and fintechs use to run savings circles and keep a record of how members keep their commitments. sura is not a bank and never holds your money. your funds stay with the bank or fintech that offers sura to you.",
      ],
    },
    {
      heading: "your account",
      paragraphs: ["to use sura you need a nigerian mobile number that you control. you agree to:"],
      bullets: [
        "give your real name and keep your details up to date",
        "keep the codes we text you private and never share them with anyone, including people who say they work for sura",
        "hold only one personal account",
        "tell us straight away if you think someone else has used your account",
      ],
    },
    {
      heading: "savings circles",
      paragraphs: [
        "a circle has a fixed amount, a schedule, a number of cycles and a payout order. once a circle starts, these cannot be changed. each cycle, every member pays in, and one member receives that cycle's pot.",
        "if everyone in a circle is new to sura, the first payout is capped at a small amount until everyone has completed one full rotation. the payout order and any cap are set by the rules the bank has agreed, not by any one member.",
      ],
    },
    {
      heading: "vendor-locked payouts",
      paragraphs: [
        "payouts are never paid out as cash. each circle chooses a verified vendor when it is created, and a payout can only be redeemed with a voucher at that vendor. vouchers can expire, and an expired or already redeemed voucher cannot be used again.",
      ],
    },
    {
      heading: "missed contributions",
      paragraphs: [
        "if you miss a contribution, it is recorded against your account, other members can see that the current cycle is not fully paid, and your sura score can go down. sura does not charge hidden penalties.",
      ],
    },
    {
      heading: "fair use",
      paragraphs: ["you must not use sura to:"],
      bullets: [
        "join a circle with no intention of paying in",
        "create accounts for other people without their permission",
        "try to collect a payout that is not yours, or redeem a voucher at a vendor it was not issued for",
        "interfere with the service or try to access data that is not yours",
      ],
    },
    {
      heading: "when we can restrict an account",
      paragraphs: [
        "if our fraud rules flag activity on an account, we may limit what it can do while the bank reviews it. we will tell you what is limited and how to get help. you can still see your history while a review is open.",
      ],
    },
    {
      heading: "changes and contact",
      paragraphs: [
        "we may update these terms. if a change affects you, we will tell you before it takes effect. if you have a question about these terms, contact the bank or fintech that gave you access to sura.",
      ],
    },
  ],
}

export const privacyNotice: LegalDocument = {
  title: "privacy notice",
  updated: "2026-10-01",
  summary:
    "this notice explains what sura collects, how your sura score is worked out from it, who can see it and the rights you have under the nigeria data protection act 2023.",
  sections: [
    {
      heading: "what we collect",
      bullets: [
        "your name, phone number and how you earn (trader, student, freelancer or other)",
        "the circles you create or join, and each contribution you make, with its date and amount",
        "the vouchers issued to you and where they were redeemed",
        "basic security data, such as when and how you signed in",
      ],
    },
    {
      heading: "what we do not collect",
      bullets: [
        "your bank account balance or your transactions outside sura",
        "your contacts, location or photos",
        "your bvn or nin, unless the bank you signed up with asks you to verify with them",
      ],
    },
    {
      heading: "how your sura score is processed",
      paragraphs: [
        "your sura score is a number from 0 to 1000. it is worked out automatically by fixed rules, from five named pillars: commitment behaviour (35%), repayment behaviour (25%), transaction stability (20%), institutional verification (12%) and social reliability (8%).",
        "every change to your score is written to an audit log with the reason, the pillar it affected and the event that caused it. you can see every entry yourself, and so can the bank that offers sura to you.",
        "we process your data this way with your consent, which we ask for before you create or join your first circle. you can withdraw it at any time from your profile. withdrawing it stops new score changes, but it does not erase records we must keep by law.",
      ],
    },
    {
      heading: "who can see your score",
      bullets: [
        "you, with the full breakdown and history",
        "the bank or fintech that offers sura to you, to decide what products they can offer you",
        "never other members of your circle. they only see your name and whether you have paid this cycle",
        "never vendors. they only see your first name when you redeem a voucher",
      ],
    },
    {
      heading: "automated decisions",
      paragraphs: [
        "your score is calculated automatically, but sura does not decide on its own whether you get credit. any lending decision is made by the bank, and you have the right to ask them for a person to review it and to explain the reasons.",
      ],
    },
    {
      heading: "how long we keep it",
      paragraphs: [
        "we keep your circle and contribution records for as long as your account is open, and afterwards for as long as financial record-keeping law requires. sign-in codes are never stored in a readable form and expire within minutes.",
      ],
    },
    {
      heading: "your rights",
      paragraphs: ["under the nigeria data protection act 2023 you can:"],
      bullets: [
        "ask for a copy of the data we hold about you",
        "ask us to correct anything that is wrong",
        "withdraw your consent to score processing",
        "object to automated processing and ask for a human review",
        "complain to the nigeria data protection commission",
      ],
    },
    {
      heading: "contact",
      paragraphs: [
        "to use any of these rights, contact the bank or fintech that gave you access to sura. they will pass your request to us where needed.",
      ],
    },
  ],
}
