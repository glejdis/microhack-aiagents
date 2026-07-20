#!/usr/bin/env python
"""Build-time generator for the CLM sample contract PDFs.

Produces the **executed contract portfolio** (one PDF per row in
`data/contracts_seed.json`) plus the **inbound counterparty draft** — all as
real, text-extractable PDFs. This is authoring tooling (like
`scripts/make_banner.py`); it is NOT a runtime dependency of the hack.

The full contract text lives here so it is reviewable in source control; the
generated PDFs are what get seeded into Blob + Azure AI Search (Challenge 0).

Requires:  pip install reportlab
Run:       python scripts/make_sample_contracts.py
"""
from __future__ import annotations

from pathlib import Path

from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.lib import colors

REPO_ROOT = Path(__file__).resolve().parents[1]
CONTRACTS_DIR = REPO_ROOT / "data" / "contracts"
DRAFTS_DIR = REPO_ROOT / "data" / "counterparty_drafts"

# --------------------------------------------------------------------------- styles
_ss = getSampleStyleSheet()
TITLE = ParagraphStyle("title", parent=_ss["Title"], fontSize=15, spaceAfter=4, alignment=TA_CENTER)
SUBTITLE = ParagraphStyle("subtitle", parent=_ss["Normal"], fontSize=9, alignment=TA_CENTER,
                          textColor=colors.HexColor("#555555"), spaceAfter=10)
H = ParagraphStyle("h", parent=_ss["Heading2"], fontSize=10.5, spaceBefore=8, spaceAfter=2,
                   textColor=colors.HexColor("#1F3864"))
BODY = ParagraphStyle("body", parent=_ss["Normal"], fontSize=9.5, leading=13, alignment=TA_JUSTIFY)
META = ParagraphStyle("meta", parent=_ss["Normal"], fontSize=9, leading=13)
NOTE = ParagraphStyle("note", parent=_ss["Normal"], fontSize=9, leading=13,
                      textColor=colors.HexColor("#B00020"))
SIGN = ParagraphStyle("sign", parent=_ss["Normal"], fontSize=9, leading=16)


def _meta_table(rows):
    t = Table([[Paragraph(f"<b>{k}</b>", META), Paragraph(v, META)] for k, v in rows],
              colWidths=[1.4 * inch, 4.9 * inch])
    t.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#BBBBBB")),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#DDDDDD")),
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F3F2F1")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return t


def build_pdf(path: Path, title: str, subtitle: str, meta_rows, sections,
              parties, note: str | None = None):
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(path), pagesize=LETTER,
        leftMargin=0.9 * inch, rightMargin=0.9 * inch,
        topMargin=0.8 * inch, bottomMargin=0.8 * inch,
        title=title, author="Contoso Global, Inc.",
    )
    flow = [Paragraph(title, TITLE), Paragraph(subtitle, SUBTITLE)]
    if note:
        flow += [Paragraph(note, NOTE), Spacer(1, 6)]
    flow += [_meta_table(meta_rows), Spacer(1, 10)]
    for i, (heading, body) in enumerate(sections, 1):
        flow.append(Paragraph(f"{i}. {heading}", H))
        flow.append(Paragraph(body, BODY))
    flow.append(Spacer(1, 16))
    flow.append(Paragraph("IN WITNESS WHEREOF, the parties have executed this Agreement as of the "
                          "Effective Date.", BODY))
    flow.append(Spacer(1, 10))
    sig = Table(
        [[Paragraph(f"<b>{parties[0]}</b><br/>By: ____________________<br/>"
                    "Name: A. Rivera<br/>Title: General Counsel<br/>Date: ______________", SIGN),
          Paragraph(f"<b>{parties[1]}</b><br/>By: ____________________<br/>"
                    "Name: Authorized Signatory<br/>Title: ______________<br/>Date: ______________", SIGN)]],
        colWidths=[3.15 * inch, 3.15 * inch])
    sig.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    flow.append(sig)
    flow.append(Spacer(1, 14))
    flow.append(Paragraph(f"Contoso Global, Inc. — CONFIDENTIAL · {meta_rows[0][1]} · "
                          "Fictitious document for the CLM microhack.",
                          ParagraphStyle("foot", parent=BODY, fontSize=7.5,
                                         textColor=colors.HexColor("#888888"), alignment=TA_CENTER)))
    doc.build(flow)
    print(f"  [ok] {path.relative_to(REPO_ROOT)}")


# =========================================================================== contracts
def contract_ct4821():
    build_pdf(
        CONTRACTS_DIR / "CT-4821_Acme_MSA.pdf",
        "MASTER SERVICES AGREEMENT",
        "between Contoso Global, Inc. and Acme Corp",
        [("Contract ID", "CT-4821"), ("Counterparty", "Acme Corp"), ("Type", "MSA — Master Services Agreement"),
         ("Status", "Active"), ("Effective date", "2024-09-01"), ("Renewal date", "2026-09-01"),
         ("Auto-renew", "Yes"), ("Non-renewal notice", "90 days"),
         ("Internal risk rating", "High"), ("Contract owner", "legal@contoso.com")],
        [
            ("Payment Terms", "Contoso Global (\u201cClient\u201d) shall pay undisputed invoices "
             "<b>Net 30</b> from receipt. Late amounts accrue interest at 1.0% per month."),
            ("Limitation of Liability", "Each party\u2019s aggregate liability is capped at the fees "
             "paid in the <b>trailing six (6) months</b>. No carve-outs are stated for confidentiality "
             "or IP infringement."),
            ("Indemnification", "The parties provide <b>mutual</b> indemnification for third-party "
             "claims arising from negligence. Intellectual-property infringement is <b>not</b> covered."),
            ("Term &amp; Auto-Renewal", "Initial term of <b>two (2) years</b> from the Effective Date, "
             "renewing automatically for successive one-year terms unless either party gives 90 days\u2019 "
             "written notice of non-renewal."),
            ("Governing Law", "This Agreement is governed by the laws of the State of New York, USA."),
            ("Intellectual Property", "Deliverables created for Client are works made for hire; ownership "
             "vests in Client upon payment."),
            ("Data Protection", "Provider processes Client data per Client instructions under the attached "
             "Data Processing Addendum; GDPR terms apply where relevant."),
            ("Confidentiality", "Confidentiality obligations survive <b>five (5) years</b> after disclosure."),
            ("Termination", "Either party may terminate for material breach with a 30-day cure period, or "
             "for convenience on 60 days\u2019 notice."),
            ("Insurance", "Provider maintains commercial general liability insurance of not less than "
             "USD 2,000,000."),
        ],
        ("Contoso Global, Inc.", "Acme Corp"),
        note="High-risk executed agreement: Net 30 payment, 6-month liability cap, and mutual "
             "indemnity without IP coverage deviate from the Standard Clause Library.",
    )


def contract_ct3390():
    build_pdf(
        CONTRACTS_DIR / "CT-3390_Globex_NDA.pdf",
        "MUTUAL NON-DISCLOSURE AGREEMENT",
        "between Contoso Global, Inc. and Globex Ltd",
        [("Contract ID", "CT-3390"), ("Counterparty", "Globex Ltd"), ("Type", "NDA — Mutual Non-Disclosure"),
         ("Status", "Active"), ("Effective date", "2025-02-15"), ("Renewal date", "2027-02-15"),
         ("Auto-renew", "No"), ("Non-renewal notice", "30 days"),
         ("Internal risk rating", "Low"), ("Contract owner", "procurement@contoso.com")],
        [
            ("Purpose", "The parties wish to exchange Confidential Information to evaluate a potential "
             "business relationship."),
            ("Definition of Confidential Information", "Non-public business, technical, and financial "
             "information disclosed in any form and marked or reasonably understood as confidential."),
            ("Obligations", "Each party protects the other\u2019s Confidential Information with the same "
             "care it uses for its own (no less than reasonable care) and uses it solely for the Purpose."),
            ("Term &amp; Renewal", "Two (2) year term; <b>no automatic renewal</b>. Either party may "
             "decline renewal on 30 days\u2019 notice."),
            ("Confidentiality Survival", "Confidentiality obligations survive <b>three (3) years</b> after "
             "disclosure \u2014 consistent with the enterprise standard."),
            ("Governing Law", "This Agreement is governed by the laws of the State of Washington, USA."),
            ("No License", "No license or IP rights are granted except the limited right to use "
             "Confidential Information for the Purpose."),
            ("Return or Destruction", "Upon request, each party returns or destroys the other\u2019s "
             "Confidential Information."),
        ],
        ("Contoso Global, Inc.", "Globex Ltd"),
    )


def contract_ct5102():
    build_pdf(
        CONTRACTS_DIR / "CT-5102_Initech_SOW.pdf",
        "STATEMENT OF WORK",
        "under the Master Services Agreement between Contoso Global, Inc. and Initech LLC",
        [("Contract ID", "CT-5102"), ("Counterparty", "Initech LLC"), ("Type", "SOW — Statement of Work"),
         ("Status", "Active"), ("Effective date", "2025-06-01"), ("Renewal date", "2026-06-01"),
         ("Auto-renew", "Yes"), ("Non-renewal notice", "60 days"),
         ("Internal risk rating", "Medium"), ("Contract owner", "legal@contoso.com")],
        [
            ("Scope of Services", "Initech LLC (\u201cSupplier\u201d) will design and implement a data "
             "integration platform, delivered across three milestones over twelve months."),
            ("Deliverables &amp; Milestones", "M1 \u2014 solution design (month 2); M2 \u2014 build and "
             "integration (month 7); M3 \u2014 acceptance and handover (month 12). Each milestone requires "
             "written Client acceptance."),
            ("Fees &amp; Payment", "Fixed fee of USD 240,000, invoiced per milestone. Undisputed invoices "
             "are payable <b>Net 45</b>."),
            ("Limitation of Liability", "Supplier\u2019s aggregate liability is capped at the fees paid in "
             "the trailing twelve (12) months, with carve-outs for confidentiality and IP infringement."),
            ("Intellectual Property", "Custom deliverables are works made for hire owned by Client on "
             "payment; however, <b>Supplier retains ownership of its pre-existing tools and libraries</b> "
             "and grants Client a perpetual, non-exclusive license-back to use them within the deliverables."),
            ("Term &amp; Renewal", "One (1) year term aligned to the delivery window; auto-renews for "
             "one-year support terms unless either party gives 60 days\u2019 notice."),
            ("Governing Law", "Governed by the laws of the State of Washington, USA."),
            ("Data Protection", "Supplier processes Client data under the MSA\u2019s Data Processing "
             "Addendum; sub-processors require prior written notice."),
            ("Termination", "Either party may terminate for material breach with a 30-day cure period, or "
             "for convenience on 60 days\u2019 notice."),
            ("Insurance", "Supplier maintains commercial general liability insurance of USD 2,000,000 and "
             "cyber liability coverage appropriate to a data processor."),
        ],
        ("Contoso Global, Inc.", "Initech LLC"),
        note="Medium-risk executed agreement: the IP license-back for Supplier pre-existing tools "
             "deviates from the standard works-made-for-hire position.",
    )


def contract_ct2765():
    build_pdf(
        CONTRACTS_DIR / "CT-2765_Umbrella_MSA.pdf",
        "MASTER SERVICES AGREEMENT",
        "between Contoso Global, Inc. and Umbrella Inc",
        [("Contract ID", "CT-2765"), ("Counterparty", "Umbrella Inc"), ("Type", "MSA — Master Services Agreement"),
         ("Status", "Expired"), ("Effective date", "2022-01-10"), ("Renewal date", "2024-01-10"),
         ("Auto-renew", "No"), ("Non-renewal notice", "90 days"),
         ("Internal risk rating", "Medium"), ("Contract owner", "legal@contoso.com")],
        [
            ("Payment Terms", "Client pays undisputed invoices <b>Net 60</b> from receipt \u2014 the "
             "enterprise standard."),
            ("Limitation of Liability", "Aggregate liability capped at fees paid in the trailing twelve "
             "(12) months, with carve-outs for confidentiality, IP infringement, and indemnity."),
            ("Indemnification", "Supplier indemnifies Client for third-party claims from negligence, "
             "willful misconduct, and IP infringement."),
            ("Term &amp; Renewal", "Two (2) year initial term expiring on the Renewal date; <b>no "
             "automatic renewal</b>. The parties did not renew; the Agreement lapsed on 2024-01-10."),
            ("Governing Law", "Governed by the laws of the State of Washington, USA."),
            ("Intellectual Property", "Deliverables are works made for hire owned by Client on payment."),
            ("Confidentiality", "Confidentiality obligations survive three (3) years after disclosure."),
            ("Termination", "For material breach with a 30-day cure period, or for convenience on 60 "
             "days\u2019 notice."),
            ("Insurance", "Supplier maintained commercial general liability insurance of USD 2,000,000 "
             "during the term."),
        ],
        ("Contoso Global, Inc.", "Umbrella Inc"),
        note="STATUS: EXPIRED \u2014 this Agreement lapsed on 2024-01-10 and was not renewed. Retained "
             "for records and lifecycle reporting.",
    )


def contract_ct6033():
    build_pdf(
        CONTRACTS_DIR / "CT-6033_Soylent_MSA.pdf",
        "MASTER SERVICES AGREEMENT",
        "between Contoso Global, Inc. and Soylent Co",
        [("Contract ID", "CT-6033"), ("Counterparty", "Soylent Co"), ("Type", "MSA — Master Services Agreement"),
         ("Status", "Active"), ("Effective date", "2025-08-20"), ("Renewal date", "2026-08-20"),
         ("Auto-renew", "Yes"), ("Non-renewal notice", "90 days"),
         ("Internal risk rating", "High"), ("Contract owner", "procurement@contoso.com")],
        [
            ("Payment Terms", "Client shall pay undisputed invoices <b>Net 30</b> from the invoice date, "
             "with 1.5% monthly interest on late amounts."),
            ("Limitation of Liability", "Each party\u2019s aggregate liability is capped at the fees paid "
             "in the <b>trailing three (3) months</b> \u2014 well below the enterprise standard."),
            ("Indemnification", "Supplier indemnifies Client for third-party negligence claims; IP "
             "infringement indemnity is limited to direct damages only."),
            ("Term &amp; Auto-Renewal", "Initial term of one (1) year, renewing automatically for "
             "successive one-year terms unless either party gives 90 days\u2019 written notice."),
            ("Governing Law", "This Agreement is governed by the laws of the <b>Republic of Ireland</b>."),
            ("Intellectual Property", "Deliverables are works made for hire owned by Client on payment."),
            ("Data Protection", "Supplier may engage sub-processors with prior notice; an EU Standard "
             "Contractual Clauses addendum applies."),
            ("Confidentiality", "Confidentiality obligations are <b>perpetual</b> and survive termination "
             "indefinitely."),
            ("Termination", "For material breach with a 30-day cure period, or for convenience on 90 "
             "days\u2019 notice."),
            ("Insurance", "Supplier maintains commercial general liability insurance of USD 1,000,000."),
        ],
        ("Contoso Global, Inc.", "Soylent Co"),
        note="High-risk executed agreement: non-US/UK governing law (Ireland), perpetual "
             "confidentiality, and a 3-month liability cap are non-standard and require GC sign-off.",
    )


# =========================================================================== inbound draft
def counterparty_draft():
    build_pdf(
        DRAFTS_DIR / "acme_msa_draft.pdf",
        "MASTER SERVICES AGREEMENT — COUNTERPARTY DRAFT",
        "Inbound draft received from Acme Corp — for clause &amp; risk analysis",
        [("Document", "INBOUND counterparty draft"), ("From", "Acme Corp (\u201cProvider\u201d)"),
         ("To", "Contoso Global, Inc. (\u201cClient\u201d)"), ("Type", "MSA — proposed"),
         ("Reviewed by", "Clause &amp; Risk agent (Challenge 3)"),
         ("Benchmark", "Contoso Standard Clause Library CL-01\u2026CL-10")],
        [
            ("Payment Terms", "Client shall pay all invoices within <b>thirty (30) days</b> of the "
             "invoice date. Payments not received within 30 days accrue interest at 1.5% per month."),
            ("Limitation of Liability", "<b>Provider\u2019s liability under this Agreement is unlimited "
             "for all claims.</b> Client\u2019s liability is capped at fees paid in the trailing six (6) "
             "months."),
            ("Indemnification", "Each party shall indemnify the other for third-party claims arising from "
             "its own negligence. <b>No indemnification is provided for intellectual property "
             "infringement.</b>"),
            ("Term and Renewal", "Initial term of <b>three (3) years</b>, renewing automatically for "
             "successive three-year terms unless Client provides <b>one hundred eighty (180) days\u2019</b> "
             "written notice."),
            ("Intellectual Property", "<b>Provider retains all ownership of deliverables</b> and grants "
             "Client a non-exclusive, revocable license to use them during the term."),
            ("Governing Law", "This Agreement is governed by the laws of <b>Ireland</b>."),
            ("Data Protection", "Provider may engage sub-processors at its discretion. A Data Processing "
             "Addendum is <b>not attached</b>."),
            ("Confidentiality", "Confidentiality obligations are <b>perpetual</b> and survive termination "
             "indefinitely."),
            ("Insurance", "Provider maintains commercial general liability insurance of <b>USD "
             "500,000</b>."),
        ],
        ("Acme Corp (Provider)", "Contoso Global, Inc. (Client)"),
        note="This is an unsigned counterparty proposal, deliberately full of deviations from the "
             "Standard Clause Library for the Clause &amp; Risk agent to flag.",
    )


def main():
    print("Generating sample contract PDFs...")
    contract_ct4821()
    contract_ct3390()
    contract_ct5102()
    contract_ct2765()
    contract_ct6033()
    counterparty_draft()
    print("Done.")


if __name__ == "__main__":
    main()
