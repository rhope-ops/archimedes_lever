# R4e: Ion PII detectors against Microsoft Presidio, on a synthetic labelled corpus

Date: 2026-11-23. Program: custom tool retirement, research step R4e, coverage row ION-1
(docs/reviews/2026-11-23-tool-retirement-coverage.md). Evidence only: no change to Ion, no design decision.

## Summary

| | Ion (all hits) | Ion (High and Medium only) | Presidio (defaults, en_core_web_lg) |
|---|---|---|---|
| Precision (overall, micro) | 0.94 | 1.00 | 0.61 |
| Recall (overall, micro) | 0.83 | 0.70 | 0.83 |
| F1 | 0.88 | 0.82 | 0.70 |
| Hits on decoy texts, per 100 texts (126 texts) | 16.7 (all Low) | 0 | 141 (81 for the 9 Ion types alone) |

- Ion and Presidio find the same share of the labelled spans (83%), but Ion is far cleaner: Presidio flags 78 of 126 decoy texts, Ion 21 (all Low confidence).
- The two tools fail in different places. Presidio has no DoD ID type (0 of 38) and no street-address type; Ion has no rule for a name without a label (0 of 27) or for any value whose label sits after it.
- Ion's misses are mostly label rules working as designed (a label is required before the value). The few defects found (name span over line breaks, SSN winning over passport, e-mail span after an underscore) are in "Ion: misses and over-flags", findings 1, 3 and 8.
- The corpus was written by one author who knew Ion's rules, and the variant mix is chosen to probe them. The numbers rank gaps; they do not predict a rate on real documents (see "Limits").

## Method

- Ion: /home/user/rhope-ops/33-332.Z, HEAD 6cbc517 (read-only; no file changed). Entry point `Get-PiiSpan` (the function Find-ChannelPII uses: all detectors, overlap removal, name raise, unreadable-text filter). `Get-AllHits` is not exported by the module and does not remove overlaps, so `Get-PiiSpan` is the scored output. Modules PiiPatterns.psm1 and PiiDetectors.psm1 imported with `Set-StrictMode -Version 2.0` as in the sources. Run on PowerShell 7.4.6 (Linux). Windows PowerShell 5.1 was not available: not tested there.
- Presidio: presidio-analyzer 2.2.366, spaCy 3.8.18, model en_core_web_lg 3.8.0, Python 3.13, all default recognizers, no custom recognizers, no score threshold (a second run at score >= 0.5 is shown), language "en". The 24 default entities are all active.
- Corpus: seed 20261123, generator below. 506 texts: 380 with PII (528 labelled spans) and 126 decoys (no PII). Types (labelled spans): Name 94, SSN 80, Date of birth 80, Phone 60, Personal e-mail 54, Home address 50, Payment card 47, DoD ID 38, Passport 25. Of the 380, 340 are short single-type texts and 40 are form-like records with 3 to 7 fields. Format variants: dashes, spaces, bare digits, label before, label after, no label, label then line break, upper and lower case, many date and address forms.
- Decoy categories (126 texts): order numbers 14, dates in prose 14, Luhn-valid non-card numbers 14, phone-like part numbers 14, place names 14, SSA-invalid SSN-shaped numbers 12, bare 10-digit numbers 12, role mailboxes and sample addresses 12, numbers-and-words (building, section, version) 10, organisation and product names that look like person names 10.
- Validity handling: SSNs are random and valid by the SSA rules Ion applies (area 001-665 or 667-899, group 01-99, serial 0001-9999); SSN-shaped numbers that break those rules are decoys, not labelled PII. Card numbers are Luhn-valid with Visa, Mastercard, Amex and Discover prefixes (random, not issued numbers); Luhn-valid numbers with other prefixes are decoys. Half of the phone numbers use the fictional 555-01xx range, half use random area and exchange codes. E-mail locals are invented; domains are real providers (gmail, yahoo and so on) for personal addresses and reserved ".example" domains for company addresses. Names are drawn from short invented lists (a real person may share one). No value comes from a real record.
- Gold rule: the span of the value only, not its label.
- Presidio entity map: US_SSN to SSN, CREDIT_CARD to Payment card, DATE_TIME to Date of birth (Presidio has no date-of-birth type, so any date counts), US_PASSPORT to Passport, PHONE_NUMBER to Phone, EMAIL_ADDRESS to Personal e-mail, PERSON to Name, LOCATION to Home address. DoD ID has no Presidio type. Other Presidio entities (US_DRIVER_LICENSE, US_BANK_NUMBER, URL, ORGANIZATION, UK_NHS, US_ITIN, MEDICAL_LICENSE) are not scored as errors in the type tables; they are counted separately.
- Overlap rule: a prediction matches a gold span when the types are the same and at least one character overlaps. Per gold span: TP if some prediction matches, else FN. Per prediction (of a scored type): FP if it matches no gold span in its text. Extra predictions on an already matched span are neither TP nor FP. A type-agnostic recall (any entity, any overlap) is shown for the DoD ID gap. Exact-boundary counts are given as a quality note. Micro-averages: counts summed over types.
- A hit on a decoy text is always an FP. FPs on the labelled texts count too (for example a 9-digit passport reported as an SSN).

## Score tables

### Ion, all confidence levels (Low, Medium, High)

| Type | gold | TP | FP | FN | Precision | Recall | F1 |
|---|---|---|---|---|---|---|---|
| SSN | 80 | 80 | 12 | 0 | 0.87 | 1.00 | 0.93 |
| DoD ID | 38 | 28 | 0 | 10 | 1.00 | 0.74 | 0.85 |
| Payment card | 47 | 47 | 0 | 0 | 1.00 | 1.00 | 1.00 |
| Date of birth | 80 | 64 | 0 | 16 | 1.00 | 0.80 | 0.89 |
| Passport | 25 | 12 | 0 | 13 | 1.00 | 0.48 | 0.65 |
| Phone | 60 | 54 | 5 | 6 | 0.92 | 0.90 | 0.91 |
| Personal e-mail | 54 | 49 | 12 | 5 | 0.80 | 0.91 | 0.85 |
| Home address | 50 | 37 | 0 | 13 | 1.00 | 0.74 | 0.85 |
| Name | 94 | 67 | 0 | 27 | 1.00 | 0.71 | 0.83 |
| **Overall (micro)** | 528 | 438 | 29 | 90 | 0.94 | 0.83 | 0.88 |

### Ion, High and Medium only (Low hits dropped)

Ion's report tabs by confidence; this is what is left if the Low tab is ignored.

| Type | gold | TP | FP | FN | Precision | Recall | F1 |
|---|---|---|---|---|---|---|---|
| SSN | 80 | 78 | 0 | 2 | 1.00 | 0.97 | 0.99 |
| DoD ID | 38 | 23 | 0 | 15 | 1.00 | 0.61 | 0.75 |
| Payment card | 47 | 47 | 0 | 0 | 1.00 | 1.00 | 1.00 |
| Date of birth | 80 | 64 | 0 | 16 | 1.00 | 0.80 | 0.89 |
| Passport | 25 | 12 | 0 | 13 | 1.00 | 0.48 | 0.65 |
| Phone | 60 | 30 | 0 | 30 | 1.00 | 0.50 | 0.67 |
| Personal e-mail | 54 | 39 | 0 | 15 | 1.00 | 0.72 | 0.84 |
| Home address | 50 | 34 | 0 | 16 | 1.00 | 0.68 | 0.81 |
| Name | 94 | 40 | 0 | 54 | 1.00 | 0.43 | 0.60 |
| **Overall (micro)** | 528 | 367 | 0 | 161 | 1.00 | 0.70 | 0.82 |

Names are Low unless an identifier is within 80 characters, which is why Name drops most.

### Presidio, defaults, no threshold

| Type | gold | TP | FP | FN | Precision | Recall | F1 |
|---|---|---|---|---|---|---|---|
| SSN | 80 | 80 | 19 | 0 | 0.81 | 1.00 | 0.89 |
| DoD ID | 38 | 0 | 0 | 38 | 0.00 | 0.00 | 0.00 |
| Payment card | 47 | 47 | 6 | 0 | 0.89 | 1.00 | 0.94 |
| Date of birth | 80 | 71 | 141 | 9 | 0.33 | 0.89 | 0.49 |
| Passport | 25 | 13 | 11 | 12 | 0.54 | 0.52 | 0.53 |
| Phone | 60 | 60 | 59 | 0 | 0.50 | 1.00 | 0.67 |
| Personal e-mail | 54 | 44 | 0 | 10 | 1.00 | 0.81 | 0.90 |
| Home address (LOCATION mapped) | 50 | 36 | 25 | 14 | 0.59 | 0.72 | 0.65 |
| Name | 94 | 89 | 21 | 5 | 0.81 | 0.95 | 0.87 |
| **Overall (micro)** | 528 | 440 | 282 | 88 | 0.61 | 0.83 | 0.70 |

- Without the LOCATION mapping Home address is 0 of 50 and overall becomes precision 0.61, recall 0.77, F1 0.68. LOCATION is a place (city, street part), not a street address; mapped, it matches 36 addresses but only by partial overlap (0 of 36 with exact boundaries).
- Presidio e-mail artifact: all 10 Presidio e-mail misses are the company addresses on the reserved ".example" domain, which Presidio's top-level-domain check rejects (confirmed on a hand test: the same local part at a ".com" domain is found with score 1.0). On real top-level domains Presidio found 44 of 44. Adjusted for this (those 10 spans removed from both tools): Presidio recall 0.85 (440 of 518), Ion recall 0.83 (428 of 518); precision unchanged. The same artifact explains Presidio's 0 hits on the 12 role-mailbox decoys.
- Presidio in the same corpus found 97% of all labelled spans as some entity of any type (511 of 528; Ion 84%, 446 of 528). The DoD ID is found as US_DRIVER_LICENSE, US_BANK_NUMBER or PHONE_NUMBER (all 38 get some hit) at low scores, so a type-blind use would still see it.

### Presidio at score >= 0.5

| Type | gold | TP | FP | FN | Precision | Recall | F1 |
|---|---|---|---|---|---|---|---|
| SSN | 80 | 73 | 4 | 7 | 0.95 | 0.91 | 0.93 |
| DoD ID | 38 | 0 | 0 | 38 | 0.00 | 0.00 | 0.00 |
| Payment card | 47 | 47 | 6 | 0 | 0.89 | 1.00 | 0.94 |
| Date of birth | 80 | 71 | 131 | 9 | 0.35 | 0.89 | 0.50 |
| Passport | 25 | 0 | 0 | 25 | 0.00 | 0.00 | 0.00 |
| Phone | 60 | 38 | 3 | 22 | 0.93 | 0.63 | 0.75 |
| Personal e-mail | 54 | 44 | 0 | 10 | 1.00 | 0.81 | 0.90 |
| Home address (LOCATION mapped) | 50 | 36 | 25 | 14 | 0.59 | 0.72 | 0.65 |
| Name | 94 | 89 | 21 | 5 | 0.81 | 0.95 | 0.87 |
| **Overall (micro)** | 528 | 398 | 190 | 130 | 0.68 | 0.75 | 0.71 |

A threshold helps SSN and Phone precision but removes every passport (Presidio scores a labelled passport at 0.40 to 0.45).

### Decoy set (126 texts with no PII)

| | Ion (all) | Ion (High+Medium) | Presidio (all entities) | Presidio (the 9 Ion types only) |
|---|---|---|---|---|
| Hits | 21 | 0 | 178 | 102 |
| Decoy texts with at least one hit | 21 | 0 | 91 | 78 |
| Hits per 100 texts | 16.7 | 0.0 | 141.3 | 81.0 |

Ion's 21 hits, all Low: 4 SSN (bare 9-digit order, invoice, ticket and reference numbers), 5 Phone (3-3-4 part, drawing, SKU and model numbers), 12 Personal e-mail (role mailboxes and sample addresses at company domains: by design Low for any non-personal domain). Dates in prose, Luhn-valid non-cards, place names, SSA-invalid SSN shapes, bare 10-digit numbers and look-alike person names gave 0 Ion hits.

Presidio's 178 hits by entity: DATE_TIME 45, US_DRIVER_LICENSE 34, US_BANK_NUMBER 27, PHONE_NUMBER 19, LOCATION 16, US_SSN 8, ORGANIZATION 10, CREDIT_CARD 6, PERSON 4, US_PASSPORT 4, UK_NHS 2, US_ITIN 2, MEDICAL_LICENSE 1. By decoy category: bare 10-digit numbers 42, order numbers 34, Luhn-valid non-cards 26, place names 25, phone-like part numbers 13, look-alike names and organisations 14, dates in prose 12, SSA-invalid SSN shapes 8 (Presidio rejects area 000 and 666 and group or serial zeros, but flags area 9xx), numbers-and-words 4.

### Where each tool is weak, by variant (gold spans found, of n)

| Type and variant | n | Ion (all) | Ion (H+M) | Presidio |
|---|---|---|---|---|
| Name, label before (alone) | 27 | 27 | 0 | 24 |
| Name, in a form record | 40 | 40 | 40 | 38 |
| Name, no label | 27 | 0 | 0 | 27 |
| DoD ID, label before (DoD ID, EDIPI, CAC), also in a form record | 23 | 23 | 23 | 0 |
| DoD ID, CAC signature | 5 | 5 | 0 | 0 |
| DoD ID, label after or none | 10 | 0 | 0 | 0 |
| Date of birth, in a form record | 40 | 40 | 40 | 39 |
| Date of birth, DOB or "born" before, or on the line before | 24 | 24 | 24 | 17 |
| Date of birth, DOB after, or "birthday" | 16 | 0 | 0 | 15 |
| Passport, label before | 5 | 5 | 5 | 0 |
| Passport, label after, none, or on its own line | 20 | 7 | 7 | 13 |
| Phone, with separators | 54 | 54 | 30 | 54 |
| Phone, 10 bare digits | 6 | 0 | 0 | 6 |
| Home address, mixed case with city, state, ZIP (also ZIP+4, unit, "N." prefix) | 34 | 34 | 34 | 30 |
| Home address, street only | 3 | 3 | 0 | 0 |
| Home address, all caps, all lower case, PO box | 13 | 0 | 0 | 6 |
| E-mail, personal provider | 25 | 25 | 25 | 25 |
| E-mail, company domain (".example") | 10 | 10 | 0 | 0 (artifact) |
| E-mail, government or military domain | 5 | 0 | 0 | 5 |
| SSN, any variant | 80 | 80 | 78 | 80 |
| Payment card, any variant | 47 | 47 | 47 | 47 |

The Ion H+M column shows how much of the recall sits in Low hits (phone without a personal label, company e-mail, signature DoD ID, street-only address, labelled names).

## Ion: misses and over-flags

Misses, by pattern class, largest first. "Design" means the source says the rule is deliberate.

1. Name without a label: 0 of 27 (design: "a name without a label is not found: that would need a list of real names"). Example: a sentence that tells the reader to forward a file to a first name and last name. A military "LAST, FIRST M" with no dot after the initial loses the initial (the span stops at "FIRST"). A labelled name followed by a line break and another capitalised word swallows that word, and can swallow the next "Name" label so that the next name is lost (found on a docx and a PDF).
2. Date of birth with the label after the value, or "birthday" as the label: 16 of 80 missed (design: the label must be in the 30 characters before). Examples: a date, then "(DOB) per the enrollment form"; "Her birthday is" then a date. Formats in themselves are fine: dashed, slashed, ISO, military 02JAN1990 and long forms were all found with a label before.
3. Passport: 13 of 25 missed, two causes. (a) 10 by design: no "passport" in the 30 characters before the number (label after the number: 5; no label: 5). (b) 3 with the label in the window ("passport" in prose, 1; "PASSPORT NO" then a line break, 2): the 9-digit number is also a valid SSN shape, and the SSN detector wins the overlap, so the number was reported as SSN Low and no Passport hit. In all, 8 passport numbers (3 in (b), 5 in (a)) were reported as SSN Low; they are 8 of the 12 SSN false positives.
4. Home address: 13 of 50 missed. Pattern classes: all-caps street types ("ST", "RD", "AVE", the type list is case-sensitive: 7 spans), all-lower-case street (4), "PO Box" (2). Street-only addresses are found, as Low.
5. DoD ID: 10 of 38 missed (design): the 10 digits need a label before them ("DoD ID", "EDIPI", "CAC", "DoD number"). A label after the value, or no label, is missed. A CAC name before the digits (digital signature) is found, as Low.
6. Phone, 10 bare digits with no separator: 6 of 60 missed (pattern requires a separator).
7. E-mail on a .mil, .gov domain: 5 of 54 not reported (design: "not reported as personal e-mail"). Not an error if the rule stands.
8. E-mail with an underscore in the local part: the detector sees "_" as a space, so the reported value starts after the underscore (for example the part after "first_" only). The overlap rule still counts it as found, but the span is wrong at the start; 12 of 49 e-mail hits had inexact boundaries, mostly this. This is a real defect for masking: the front of the address stays visible. (Evidence only; Ion's masking was not run.)

Over-flags (29 FP in all, all Low):

- 9 digits with no separators in an order, invoice, ticket or reference number: SSN Low (4 on the decoys). No label and no dashes, so a Low hit by design; it shows in the Low tab.
- A 9-digit passport: SSN Low and no Passport (8).
- 3-3-4 numbers that are part, drawing or model numbers: Phone Low (5).
- Role and sample mailboxes at company domains: Personal e-mail Low (12).
- At High and Medium, no false positive on any of the 506 texts.

Ion types this corpus did not cover or that Ion does not know: no driver licence, no bank account or routing number, no ITIN, no IP address, no medical record or health ID, no date of birth without a label (a bare date is not reported), no names without a label, no non-US phone, no non-US passport, no non-US national IDs. Ion's own scope (AFI 33-332 A3) does not list most of these, so they are not defects.

## Presidio: misses and over-flags

Misses (88 of 528):

1. DoD ID: 38 of 38 (no recognizer; all 38 get a hit of another type: US_DRIVER_LICENSE, US_BANK_NUMBER or PHONE_NUMBER).
2. Passport: 12 of 25. With a label before the number, 8-digit numbers and two-letter-plus-seven forms were missed (5 of 5 in that variant); labelled 9-digit passports are found at score 0.40 to 0.45 (so none survive a 0.5 threshold).
3. E-mail on ".example" domains: 10 (test artifact, see above).
4. Home address: 14 of 50 even with LOCATION mapped (caps, lower case, PO box, "N." prefix, street-only, unit forms). There is no street-address recognizer; matches are place-name fragments (0 of 36 exact).
5. Date of birth: 9 missed: 4 in military format (02JAN1990), 4 in "Month day, year" after a line break, 1 in a form record ("6 Jul 1987").
6. Name: 5 missed: 2 all-caps "LAST, FIRST M" forms, 1 mixed-case "Last, First", and 2 plain "First Last" names in form records.

Over-flags (282 FP in all, 102 on decoys and 180 on labelled texts; the labelled-text FPs are mostly digit strings read as another type):

- DATE_TIME on everything date-like or digit-like (141 FP: 45 on decoys): any date in prose, a card expiry such as "09/29", ZIP codes, 10-digit numbers, fragments of card numbers. Presidio has no date-of-birth type, so any date counts as a candidate.
- PHONE_NUMBER on SSNs, card numbers, DoD IDs and bare 10-digit numbers (59 FP).
- LOCATION on place names, "Main Street", "Washington", "Jordan" (25 FP).
- US_SSN on 9-digit numbers that are not SSNs (19 FP): 9 passport numbers, 4 order, invoice or ticket numbers, 4 numbers with area 9xx (which the SSA never issues; Ion rejects them, Presidio scores them 0.5) and 2 ZIP+4 codes.
- PERSON (21 FP): 4 on decoys (two product names, "Jordan Marsh" and "Dr Pepper", each hit twice); on labelled texts, label words ("Traveler" 5, "Email" 4), whole e-mail strings (6) and street fragments (2: "PO Box 7713", "N. Juniper Lane").
- Other entities on all 506 texts: ORGANIZATION 140, US_DRIVER_LICENSE 123, US_BANK_NUMBER 100, URL 54, UK_NHS 14, US_ITIN 2, MEDICAL_LICENSE 1. These are not scored as errors above.
- Strengths: names (0.95 recall, found with no label), dates of birth with any label placement, phone numbers in every format including bare 10 digits, all e-mail on real domains.

## Ion end to end on files (optional step 6)

10 synthetic files built with python-docx 1.2.0, openpyxl 3.1.5 and reportlab 5.0.1: 4 .docx (paragraphs and a table), 3 .xlsx, 3 .pdf (plain text, one font). Each holds 10 texts from the corpus that Ion had found in the plain-text run (132 expected values). Read with `Get-TextFromBytes` from TextExtract.psm1, then `Get-PiiSpan`.

- All 10 files read with Status OK; all 132 expected values were present verbatim in the extracted text (checked on the full text of each file); all reader modules (PiiPatterns, PiiDetectors, PiiMasking, OcrText, OleText, ContainerText, the Pdf modules, TextExtract) imported on PowerShell 7 on Linux; `Add-Type -AssemblyName System.IO.Compression` worked there. OCR was not exercised (it needs Windows OCR); scanned PDFs and images were not tested. Windows PowerShell 5.1 was not available.
- 123 of 132 expected values were found with exactly the same value; 9 differed. In the plain-text run these 9 values all had an overlapping hit, and extraction lost no text, so the differences come from the detectors, not from extraction. 8 of the 9 still got a hit with a different span; 1 got no hit (below). The 9 are span-boundary defects of the detectors: 5 e-mails with an underscore in the local part (value starts after the underscore); 1 name with a middle initial and no dot (the initial is cut); 2 names whose span ran over line breaks into the next word or label (for example "Kenji D. Abernathy", a line break, then "Ship"); and 1 name with no hit at all because the span before it had swallowed its "Name" label (a swallowed label hides the next name).
- So within this small sample, extraction did not lose text. A larger sample (merged cells, text boxes, tables across pages, headers and footers, multi-column PDFs) was not built.

## Limits

- Synthetic and small: 506 texts, 528 spans, one seed. A rate here is not a rate on real documents. Per-type n is 25 to 94, so a difference of a few spans is noise.
- The author knew Ion's rules and built variants to probe them (labels after, caps, bare digits). Ion's recall would be higher on a corpus of mostly labelled forms, and lower on free prose. Presidio was not tuned (no custom recognizers, context words, allow lists or per-entity thresholds), and a tuned Presidio would score better.
- Short single-sentence texts: Presidio's name and location models work better on longer context; Ion's windows (30 and 40 characters) depend on short distances.
- English and ASCII only; no OCR noise, tables, headers or non-US formats.
- Phone numbers are random and may coincide with a real one; Presidio's validity check did not matter here (60 of 60 found in both the 555-01xx and random sets; Ion 17 of 20 in each).
- Scoring maps Presidio's DATE_TIME and LOCATION to Ion types; another mapping changes the Presidio precision. The .example domain artifact lowers Presidio e-mail recall by 10 spans.
- Ion was run on PowerShell 7.4.6 (Linux), not 5.1; the source says it targets both, and no 5.1-only behaviour (regex timeout, culture, `-match` case) was tested.
- Ion's report layer (Low tab, masking, scan queue, per-file confidence handling) was not used; the scored output is `Get-PiiSpan`, which already applies overlap removal, name raising and the unreadable-text filter.
- Presidio could not fetch the public suffix list through the proxy (HTTP 403 from publicsuffix.org); it used its bundled snapshot. Whether that changed any result was not tested; the only effect seen is the ".example" e-mail artifact above.

## Ion limits that bind any follow-up

Paste-only into Windows PowerShell 5.1 ISE, no binaries, no module installs, no Add-Type, no app registration (33-332.Z docs/DECISIONS.md rows near 41, 61, 76). Presidio is a Python package with a spaCy model: it cannot run inside Ion. It can only be a benchmark or a test oracle outside the runtime.

## Candidate follow-ups (no decision here)

| # | Candidate | Gain | Cost and risk |
|---|---|---|---|
| A | Keep Ion's detectors. Add this corpus (or a reduced one) as a regression test in tests/ with expected-hit counts | Locks the 83% recall and 0 High/Medium false positives; catches a rule change that loses a class; the corpus is a code block, so it stays text | A 500-text corpus adds test time; the corpus encodes today's by-design misses, so expected misses must be marked as "known gap" rather than as failures |
| B | Add targeted patterns for the classes above: label after the value (DOB, DoD ID, passport), "birthday" and "b." as DOB labels, 10 bare digits for phone, case-insensitive street types, PO Box, the e-mail underscore span, name span stop at a line break, middle initial without a dot | Recall up on 5 of 9 types; the cheapest ones (case, underscore, line break) are pure fixes | Each loosening raises false positives (a label after a value can attach to the wrong number; bare 10 digits collides with DoD ID and tracking numbers). Every new pattern needs a decoy test. Touches the high-trust SSN and DoD ID detectors if shared |
| C | Fix the SSN over Passport overlap (a 9-digit number with "passport" before it is reported as SSN) | Recovers 3 of the 13 passport misses; removes up to 8 of the 12 SSN FPs (the 5 passport numbers without a passport label would still be missed) | The priority list is a design choice (DetectorOrder); a labelled passport vs a labelled SSN needs a rule for which wins |
| D | Use Presidio offline as a test oracle: run it on a sample of real scan inputs in a safe environment and compare, to find Ion misses on names and unlabelled values | Independent second opinion on free prose and names; finds classes this corpus did not think of | Presidio flags 81 per 100 decoy texts, so it only works as a "disagreement list" for a person to read, not as ground truth; real documents carry PII, so the run must stay on the owner's machine with no output of values; adds a Python and model install in the dev environment (not in Ion) |
| E | Use Presidio on this synthetic corpus only, as a recurring cross-check (for example at release) | No real PII involved; shows whether a rule change moved Ion away from or toward Presidio | Little new signal after the first run; adds a Python dependency to the dev environment |
| F | Do nothing now; record these numbers as the baseline for ION-1 | Zero cost; honest baseline | The defects in B and C stay |

Presidio cannot replace Ion's runtime detectors under Ion's hard limits (it needs Python, a spaCy model and binaries), and on this corpus it would raise the false-positive load fivefold at equal recall, with no DoD ID. The defensible roles are benchmark and oracle.

## Re-run

Files (kept outside the repo, in a temporary directory): the generator below, a PowerShell script that imports `PiiPatterns.psm1` and `PiiDetectors.psm1`, runs `Get-PiiSpan` per text and writes type, confidence, start and end; a Python script that runs `AnalyzerEngine` with `en_core_web_lg`; a scorer that applies the overlap rule above. The corpus is deterministic from the seed (checked by regenerating after a refactor: byte-identical).

## Corpus generator (Python 3, standard library only; seed 20261123)

```python
#!/usr/bin/env python3
"""Synthetic labelled PII corpus for the Ion benchmark. All values invented. Seed fixed.
Usage: python3 gen.py OUT.json"""
import json, random, sys
from collections import Counter

SEED = 20261123
R = random.Random(SEED)

FIRST = ["Alex","Maria","Tomas","Priya","Dana","Ravi","Elena","Marcus","Linh","Omar","Nadia","Peter",
         "Sofia","Kenji","Rosa","Victor","Amara","Hugo","Ines","Dmitri","Leila","Bruno","Tara","Felix"]
LAST = ["Vandermeer","Okafor","Lindqvist","Castellanos","Whitcombe","Brandvold","Nakamura","Petrosyan",
        "Hargreaves","Delacroix","Mbeki","Ostrowski","Fairweather","Quillan","Ashdown","Teixeira",
        "Kowalczyk","Abernathy","Zielinski","Montague","Redfern","Salazar","Thorpe","Yamada"]
MID = list("ABCDEFGHJKLMNPRST")
STREET = ["Maple","Cedar","Lakeview","Hillcrest","Orchard","Sycamore","Birchwood","Ridgeline","Harbor",
          "Willow Creek","Sunset","Pinecone","Meadow Brook","Stonegate","Foxglove","Juniper"]
STYPE = [("Street","St"),("Avenue","Ave"),("Road","Rd"),("Drive","Dr"),("Lane","Ln"),("Court","Ct"),
         ("Boulevard","Blvd"),("Way","Way"),("Circle","Cir"),("Place","Pl")]
CITY = ["Fairview","Oakdale","Riverton","Lakeside","Brookfield","Greenville","Ashford","Clearwater","Eastport"]
STATE = ["TX","OH","CA","NY","VA","WA","GA","CO","PA","NC"]
MON3 = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
MONFULL = ["January","February","March","April","May","June","July","August","September","October","November","December"]
PROV = ["gmail.com","yahoo.com","hotmail.com","outlook.com","icloud.com","aol.com","proton.me"]
CORP = ["acme-widgets.example","northwind-demo.example","contoso-test.example"]

corpus = []


def add(text_parts, decoy=False, ptype="", variant="", cat=""):
    """text_parts: list of str or (type, str) tuples; builds the text and the exact spans."""
    text, spans = "", []
    for p in text_parts:
        if isinstance(p, tuple):
            spans.append({"type": p[0], "start": len(text), "end": len(text) + len(p[1]), "value": p[1]})
            text += p[1]
        else:
            text += p
    corpus.append({"id": len(corpus), "text": text, "spans": spans, "decoy": decoy,
                   "ptype": ptype, "variant": variant, "category": cat})


def ch(l):
    return R.choice(l)


def digits(n):
    return "".join(str(R.randrange(10)) for _ in range(n))


def luhn_complete(prefix, length):
    body = prefix + digits(length - len(prefix) - 1)
    s, dbl = 0, True
    for c in reversed(body):
        d = int(c)
        if dbl:
            d *= 2
            if d > 9:
                d -= 9
        s += d
        dbl = not dbl
    return body + str((10 - s % 10) % 10)


def ssn_digits():
    # Valid by the SSA issuing rules Ion applies: area 001-665 or 667-899, group 01-99, serial 0001-9999.
    # Random, invented; not checked against any real person.
    while True:
        a, g, s = R.randrange(1, 900), R.randrange(1, 100), R.randrange(1, 10000)
        if a != 666:
            return "%03d" % a, "%02d" % g, "%04d" % s


def fmt_ssn(sep):
    return sep.join(ssn_digits())


def person(style):
    f, l, m = ch(FIRST), ch(LAST), ch(MID)
    return {"first-last": "%s %s" % (f, l), "first-mi-last": "%s %s. %s" % (f, m, l),
            "last-first": "%s, %s" % (l, f), "last-first-mi": "%s, %s %s" % (l.upper(), f.upper(), m)}[style]


# ---------- SSN ----------
for i in range(40):
    sep = ch(["-", "-", "-", " ", ""])
    v = fmt_ssn(sep)
    k = i % 5
    if k == 0:
        add([ch(["SSN: ", "SSN ", "Social Security Number: ", "SSAN: ", "Soc Sec # "]), ("SSN", v), ch(["", " on file."])], ptype="SSN", variant="label-before")
    elif k == 1:
        add(["Applicant record. ", ("SSN", v), ch([" (SSN)", " is the SSN", " - social security"])], ptype="SSN", variant="label-after")
    elif k == 2:
        add(["Employee ref ", ("SSN", fmt_ssn("-")), " noted in file."], ptype="SSN", variant="no-label-dashes")
    elif k == 3:
        add([ch(["ssn: ", "Social Security: ", "SOCIAL SECURITY NO. "]), ("SSN", v)], ptype="SSN", variant="label-case")
    else:
        add(["Social Security Number\n", ("SSN", v), "\nSigned by the member."], ptype="SSN", variant="linebreak")
# ---------- DoD ID ----------
for i in range(30):
    v = ch("123456789") + digits(9)
    k = i % 6
    if k == 0:
        add([ch(["DoD ID: ", "DoD ID number: ", "DODID ", "EDIPI: ", "EDIPI "]), ("DoD ID", v)], ptype="DoD ID", variant="label-before")
    elif k == 1:
        add(["CAC ", ("DoD ID", v), " issued at the center."], ptype="DoD ID", variant="label-CAC")
    elif k == 2:
        add(["Service member ID ", ("DoD ID", v), " (DoD ID)"], ptype="DoD ID", variant="label-after")
    elif k == 3:
        add(["Digitally signed by %s.%s.%s." % (ch(LAST).upper(), ch(FIRST).upper(), ch(MID)), ("DoD ID", v)], ptype="DoD ID", variant="cac-signature")
    elif k == 4:
        add(["Member identifier ", ("DoD ID", v), " for the roster."], ptype="DoD ID", variant="no-label")
    else:
        add(["DoD ID\n", ("DoD ID", v)], ptype="DoD ID", variant="linebreak")


# ---------- Payment card ----------
def card(brand):
    if brand == "visa":
        return luhn_complete("4", 16)
    if brand == "mc":
        return luhn_complete(ch(["51", "52", "53", "54", "55"]), 16)
    if brand == "amex":
        return luhn_complete(ch(["34", "37"]), 15)
    return luhn_complete("6011", 16)


def card_fmt(n, style):
    if style == "bare":
        return n
    sep = "-" if style == "dash" else " "
    if len(n) == 15:
        return sep.join([n[:4], n[4:10], n[10:]])
    return sep.join(n[i:i + 4] for i in range(0, 16, 4))


for i in range(40):
    brand = ch(["visa", "visa", "mc", "amex", "disc"])
    v = card_fmt(card(brand), ch(["bare", "dash", "space", "space"]))
    k = i % 4
    if k == 0:
        add([ch(["Visa: ", "Card number: ", "Mastercard ", "Amex: ", "Discover card "]), ("Payment card", v)], ptype="Payment card", variant="label-before")
    elif k == 1:
        add(["Paid with ", ("Payment card", v), " (card on file)."], ptype="Payment card", variant="label-after")
    elif k == 2:
        add(["Please charge ", ("Payment card", v), " for the renewal."], ptype="Payment card", variant="no-label")
    else:
        add(["GPC card number\n", ("Payment card", v), "\nexp 09/29"], ptype="Payment card", variant="linebreak")


# ---------- Date of birth ----------
def date_fmt(style):
    y, m, d = R.randrange(1950, 2006), R.randrange(1, 13), R.randrange(1, 29)
    return {"us": "%02d/%02d/%04d" % (m, d, y), "us-short": "%d/%d/%02d" % (m, d, y % 100),
            "iso": "%04d-%02d-%02d" % (y, m, d), "mil": "%02d%s%04d" % (d, MON3[m - 1].upper(), y),
            "dmy": "%d %s %04d" % (d, MON3[m - 1], y), "long": "%s %d, %04d" % (MONFULL[m - 1], d, y)}[style]


for i in range(40):
    st = ch(["us", "us-short", "iso", "mil", "dmy", "long"])
    v = date_fmt(st)
    k = i % 5
    if k == 0:
        add([ch(["DOB: ", "DOB ", "Date of Birth: ", "date of birth ", "Birth date: ", "D.O.B. "]), ("Date of birth", v)], ptype="Date of birth", variant="label-before:" + st)
    elif k == 1:
        add([ch(["Employee was born on ", "born "]), ("Date of birth", v), "."], ptype="Date of birth", variant="born:" + st)
    elif k == 2:
        add([("Date of birth", v), " (DOB) per the enrollment form."], ptype="Date of birth", variant="label-after:" + st)
    elif k == 3:
        add(["Her birthday is ", ("Date of birth", v), ", send a card."], ptype="Date of birth", variant="birthday-word:" + st)
    else:
        add(["Date of Birth\n", ("Date of birth", v)], ptype="Date of birth", variant="linebreak:" + st)
# ---------- Passport ----------
for i in range(25):
    v = ch([digits(9), ch("ABCDEFGHJK") + digits(8), digits(8), ch("ABCDEFGHJKLMNPRSTUVWXYZ") + ch("ABCDEFGHJKLMNPRSTUVWXYZ") + digits(7)])
    k = i % 5
    if k == 0:
        add([ch(["Passport number: ", "Passport No. ", "passport # ", "Passport: "]), ("Passport", v)], ptype="Passport", variant="label-before")
    elif k == 1:
        add(["Traveler holds US passport ", ("Passport", v), " valid to 2031."], ptype="Passport", variant="label-prose")
    elif k == 2:
        add([("Passport", v), " (passport number)"], ptype="Passport", variant="label-after")
    elif k == 3:
        add(["Travel document ", ("Passport", v), " scanned."], ptype="Passport", variant="no-label")
    else:
        add(["PASSPORT NO\n", ("Passport", v)], ptype="Passport", variant="linebreak")
# ---------- Phone ----------
AREA = ["212", "415", "312", "512", "617", "702", "206", "305", "404", "503"]


def phone(style, fictional):
    a = ch(AREA)
    ex = "555" if fictional else "%d%02d" % (R.randrange(2, 10), R.randrange(0, 100))
    ln = "01%02d" % R.randrange(100) if fictional else digits(4)
    return {"paren": "(%s) %s-%s" % (a, ex, ln), "dash": "%s-%s-%s" % (a, ex, ln), "dot": "%s.%s.%s" % (a, ex, ln),
            "plus1": "+1 %s %s %s" % (a, ex, ln), "bare": a + ex + ln, "1dash": "1-%s-%s-%s" % (a, ex, ln),
            "intl": "+1 (%s) %s-%s" % (a, ex, ln)}[style]


for i in range(40):
    st = ch(["paren", "dash", "dot", "plus1", "bare", "1dash", "intl", "dash"])
    fic = (i % 2 == 0)
    v = phone(st, fic)
    k = i % 4
    var = ("fictional-555" if fic else "random-valid") + ":" + st
    if k == 0:
        add([ch(["Cell: ", "Mobile ", "Home phone: ", "Personal: ", "my number is "]), ("Phone", v)], ptype="Phone", variant="label-personal;" + var)
    elif k == 1:
        add(["Call ", ("Phone", v), " after 5 pm."], ptype="Phone", variant="no-label;" + var)
    elif k == 2:
        add(["Phone\n", ("Phone", v)], ptype="Phone", variant="linebreak;" + var)
    else:
        add(["Reach me at ", ("Phone", v), " or by mail."], ptype="Phone", variant="prose;" + var)


# ---------- E-mail ----------
def local():
    f, l = ch(FIRST).lower(), ch(LAST).lower()
    return ch(["%s.%s" % (f, l), "%s%s" % (f[0], l), "%s_%s%d" % (f, l[:4], R.randrange(10, 99)), "%s-%s" % (f, l)])


for i in range(40):
    k = i % 8
    if k < 4:
        v, var = local() + "@" + ch(PROV), "personal-provider"
    elif k < 6:
        v, var = local() + "@" + ch(CORP), "named-person-company"
    elif k == 6:
        v, var = (local() + "@" + ch(PROV)).upper(), "uppercase"
    else:
        v, var = local() + "@" + ch(["navy.mil", "army.mil", "agency.gov"]), "gov-mil"
    kk = i % 3
    if kk == 0:
        add([ch(["Email: ", "E-mail: ", "Contact me at "]), ("Personal e-mail", v)], ptype="Personal e-mail", variant="label;" + var)
    elif kk == 1:
        add(["Send the file to ", ("Personal e-mail", v), "."], ptype="Personal e-mail", variant="prose;" + var)
    else:
        add(["Email\n", ("Personal e-mail", v), "\nPhone on request"], ptype="Personal e-mail", variant="linebreak;" + var)


# ---------- Home address ----------
def addr(style):
    n = R.randrange(1, 9999)
    s = ch(STREET)
    long_, short = ch(STYPE)
    city, st, z = ch(CITY), ch(STATE), digits(5)
    unit = ch(["Apt 4B", "Unit 12", "#210"])
    return {"full": "%d %s %s, %s, %s %s" % (n, s, long_, city, st, z),
            "abbr": "%d %s %s, %s %s %s" % (n, s, short, city, st, z),
            "unit": "%d %s %s, %s, %s, %s %s" % (n, s, long_, unit, city, st, z),
            "street-only": "%d %s %s" % (n, s, long_),
            "caps": ("%d %s %s, %s, %s %s" % (n, s, short, city, st, z)).upper(),
            "lower": ("%d %s %s" % (n, s, long_)).lower(),
            "zip4": "%d %s %s, %s, %s %s-%s" % (n, s, long_, city, st, z, digits(4)),
            "po-box": "PO Box %d, %s, %s %s" % (n, city, st, z),
            "dirprefix": "%d N. %s %s, %s, %s %s" % (n, s, long_, city, st, z)}[style]


for i in range(40):
    st = ch(["full", "abbr", "unit", "street-only", "caps", "lower", "zip4", "po-box", "dirprefix", "full"])
    v = addr(st)
    k = i % 4
    if k == 0:
        add([ch(["Home address: ", "Mailing address: ", "Residence: ", "lives at "]), ("Home address", v)], ptype="Home address", variant="label-before:" + st)
    elif k == 1:
        add(["Ship to ", ("Home address", v), " by Friday."], ptype="Home address", variant="prose:" + st)
    elif k == 2:
        add(["Address\n", ("Home address", v)], ptype="Home address", variant="linebreak:" + st)
    else:
        add(["Send mail to ", ("Home address", v), "\nAttn: front desk"], ptype="Home address", variant="no-label:" + st)
# ---------- Name ----------
for i in range(45):
    st = ch(["first-last", "first-mi-last", "last-first", "last-first-mi", "first-last"])
    k = i % 5
    if k < 3:
        lab = ch(["Name: ", "Full Name: ", "Member: ", "Employee: ", "Spouse: ", "Dependent: ", "Next of kin: ", "POC: "])
        add([lab, ("Name", person(st))], ptype="Name", variant="labelled:" + st)
    elif k == 3:
        add(["Please forward the file to ", ("Name", person("first-last")), " in the claims office."], ptype="Name", variant="unlabelled-prose")
    else:
        add(["Meeting notes from ", ("Name", person("first-last")), " and ", ("Name", person("first-last")), "."], ptype="Name", variant="unlabelled-two")
# ---------- Multi-PII form-like records ----------
for i in range(40):
    parts = ["Name: ", ("Name", person("first-last")), "\n"]
    parts += [ch(["SSN: ", "SSN "]), ("SSN", fmt_ssn("-")), "\n"]
    parts += ["DOB: ", ("Date of birth", date_fmt(ch(["us", "iso", "dmy"]))), "\n"]
    if i % 2:
        parts += ["Cell: ", ("Phone", phone("dash", True)), "\n"]
    if i % 3 == 0:
        parts += ["Email: ", ("Personal e-mail", local() + "@" + ch(PROV)), "\n"]
    if i % 4 == 0:
        parts += ["Home address: ", ("Home address", addr("full")), "\n"]
    if i % 5 == 0:
        parts += ["DoD ID: ", ("DoD ID", ch("123456789") + digits(9)), "\n"]
    if i % 6 == 0:
        parts += ["Visa: ", ("Payment card", card_fmt(card("visa"), "space")), "\n"]
    add(parts, ptype="multi", variant="form")

NPOS = len(corpus)


# ---------- Decoys (no PII) ----------
def D(cat, text):
    add([text], decoy=True, cat=cat)


for i in range(14):
    D("order-number", ch(["Order #%s shipped on Tuesday.", "Invoice %s is overdue.", "Ticket %s was closed.", "Reference no. %s attached."]) % ch([digits(9), digits(6), "ORD-2025-" + digits(6), "PO" + digits(8)]))
for i in range(14):
    D("date-in-prose", ch(["The review is due %s.", "Contract signed on %s by both sides.", "Delivery expected %s, weather permitting.", "The suspense date is %s."]) % date_fmt(ch(["us", "iso", "dmy", "long", "mil"])))
for i in range(14):
    n = luhn_complete(ch(["1", "7", "8", "9", "2", "31"]), ch([13, 15, 16, 16, 19]))
    D("luhn-non-card", ch(["Tracking number %s delivered.", "Asset tag %s on the rack.", "Serial %s, lot 12.", "Document control no. %s."]) % n)
for i in range(14):
    D("phone-like-part-number", ch(["Part number %s in stock.", "SKU %s backordered.", "Model %s, rev C.", "Drawing no. %s sheet 2."]) % ch(["%s-%s-%s" % (digits(3), digits(3), digits(4)), "%s-%s" % (digits(4), digits(4)), "%s.%s.%s" % (digits(3), digits(3), digits(4)), "X" + digits(10)]))
for i in range(14):
    D("place-name", ch(["We drove to %s last summer.", "The conference is in %s.", "He was stationed at %s.", "Flights to %s resume in May."]) % ch(["Springfield", "Paris, France", "Lake Tahoe", "Fort Bragg", "Johnson City", "Washington", "Jackson Hole", "Main Street", "San Jose", "Jordan"]))
for i in range(12):
    a, g, s = ssn_digits()
    bad = ch(["000-%s-%s" % (g, s), "666-%s-%s" % (g, s), "9%s-%s-%s" % (a[1:], g, s), "%s-00-%s" % (a, s), "%s-%s-0000" % (a, g)])
    D("ssa-invalid-ssn-shape", ch(["Code %s is not assigned.", "Test value %s rejected by the form.", "Batch %s."]) % bad)
for i in range(12):
    D("ten-digit-number", ch(["Shipment %s left the dock.", "Account %s, plan B.", "Call-back ticket %s."]) % digits(10))
for i in range(12):
    D("role-mailbox-or-sample", ch(["Write to %s for support.", "Use %s as the placeholder.", "Questions: %s"]) % ch(["info@acme-widgets.example", "support@northwind-demo.example", "no-reply@contoso-test.example", "user@example.com", "sales@contoso-test.example"]))
for i in range(10):
    D("numbers-and-words", ch(["Building %d, Main Gate, room %d." % (R.randrange(1, 40), R.randrange(100, 999)),
                               "A %d Year Plan covers %d units." % (R.randrange(2, 9), R.randrange(100, 9999)),
                               "Section %d of Title %d applies." % (R.randrange(1, 99), R.randrange(1, 50)),
                               "Passport photo size: 2x2 inch, 600 dpi.",
                               "The company was founded in %d with %d staff." % (R.randrange(1950, 2010), R.randrange(20, 900)),
                               "Version %d.%d.%d released, %d fixes." % (R.randrange(1, 9), R.randrange(0, 9), R.randrange(0, 9), R.randrange(10, 300))]))
for i in range(10):
    D("org-and-product-names", ch(["Johnson Controls renewed the lease.", "Order a Jordan Marsh gift set.", "The Lincoln Memorial and Washington Monument tour.", "Ford Motor and Harley Davidson parts list.", "Hamilton Beach and Kennedy Space Center merch.", "Dr Pepper and Marshall Amps stock."]))
NDEC = len(corpus) - NPOS

json.dump({"seed": SEED, "n_positive_texts": NPOS, "n_decoy_texts": NDEC, "texts": corpus}, open(sys.argv[1], "w"), indent=1)
for c in corpus:
    for s in c["spans"]:
        assert c["text"][s["start"]:s["end"]] == s["value"]
    assert not (c["decoy"] and c["spans"])
print("positive texts", NPOS, "decoy texts", NDEC)
print(Counter(s["type"] for c in corpus for s in c["spans"]))
print(Counter(c["category"] for c in corpus if c["decoy"]))
```
