# Symbol reference sources

Research checked 2026-10-08 against publisher sources. This is an acquisition and provenance note, not a claim that the project's starter packs reproduce or exhaust these standards.

## ISA

The relevant instrumentation standard is **ANSI/ISA-5.1-2024, Instrumentation and Control - Symbols and Identification**. ISA also publishes **ISA-TR5.1.03-2024**, its graphic-symbol application guidance, and **ISA-TR5.1.02-2024**, identification-system guidance. Record the exact edition and table/row when importing an authorized copy; a generic `ISA` source does not establish provenance for a particular drawing. [ISA committee catalog](https://www.isa.org/standards-and-publications/isa-standards/isa-standards-committees/isa5-1), [ISA-5 series](https://www.isa.org/standards-and-publications/isa-standards/isa-5-standard).

The public catalog establishes document identity and scope but does not supply the complete symbol artwork. ISA member access is read-only and for individual use; it is not a downloadable open symbol dataset. No complete, openly licensed ISA symbol set was identified in this research. [ISA member access](https://www.isa.org/standards-and-publications/isa-standards/member-access-to-standards).

## IEC

**IEC 60617** is the diagram-symbol database for electrotechnical objects. Its current publisher listing is **IEC 60617:2026 DB**. IEC describes GIF, DWG and EPS artwork with classifications and search. Complete database access requires a subscription. This is distinct from IEC 60417, whose symbols are for use on equipment. [IEC catalog](https://webstore.iec.ch/en/publication/2723).

The [official 2026 preview PDF](https://webstore.iec.ch/en/iec_catalog/product/preview/?id=L3B1Yi9wZGYvcHJldmlldy9pbmZvX2llYzYwNjE3e2VkMS4wfWIucGRm) is publicly readable. It contains introductory material and an ID/name index, rather than the individual symbol graphic sheets. The sample below records exact metadata from that index. These are metadata references only; do not render an invented drawing and label it a verified IEC asset. The preview identifies the database itself as the authoritative source and describes symbol identifiers as `S` followed by five digits.

Eight metadata records suitable for an `image_unavailable` sample, with one-based PDF page numbers:

- `S00823`: Series motor, DC (page 28).
- `S00894`: Rectifier (page 30).
- `S00896`: Inverter (page 30).
- `S00909`: Closed-loop controller (page 30).
- `S00913`: Voltmeter (page 31).
- `S00925`: Salinity meter (page 31).
- `S00927`: Tachometer (page 31).
- `S00952`: Thermocouple (page 32).

All eight should have no local graphic asset, no inferred mapping to an existing project drawing, and be excluded from visual detection references. Their source is the official preview linked above, edition IEC 60617:2026 DB, checked 2026-10-08.

IEC's database rules require source attribution and, where practicable, a reference link. Replicating all or a substantial part requires a commercial arrangement. Publicly reachable older snapshot PDFs are not evidence of an open redistribution licence. No IEC graphic asset was downloaded or ingested by this research. [IEC copyright and database terms](https://webstore.iec.ch/copyright).

## ISO

**ISO 10628-2:2012, Diagrams for the chemical and petrochemical industry - Part 2: Graphical symbols** is the P&ID-relevant application standard. ISO confirmed it in 2024. It applies the ISO 14617 series and excludes electrotechnical diagrams, referring those to IEC 60617. [ISO 10628-2 catalog](https://www.iso.org/standard/51841.html).

The current general industrial diagram-symbol library is **ISO 14617-2:2025**, accompanied by **ISO 14617-1:2025** general rules. The 2025 part 2 consolidates/replaces the old parts 2 through 15 and contains 149 symbol tables. Preserve old editions as historical sources rather than silently remapping their identifiers to the new edition. [ISO 14617-2 catalog and replacement history](https://www.iso.org/standard/83364.html), [ISO 14617-1 catalog](https://www.iso.org/standard/85641.html).

ISO offers previews through its Online Browsing Platform; the catalog pages do not provide a complete freely downloadable artwork library. ISO's symbol-use terms distinguish implementation under a selected licence from distributing symbol collections. No exact ISO symbol graphic was acquired here. [ISO graphical-symbol help](https://www.iso.org/contact-iso.html), [ISO licence agreement, section 5](https://www.iso.org/terms-conditions-licence-agreement.html).

## Database implications

- Keep document identity, edition, publisher URL, and access/coverage status even when artwork is unavailable. Such source rows are not populated symbol coverage.
- For each actual graphic, retain its local asset, original name, source document, page/table or symbol identifier, and extraction/review status.
- Preserve project legend variants separately, with the source drawing and crop coordinates. Machine-extracted legend labels remain machine-extracted until checked.
- Treat existing generic standard starter packs as unverified starter material unless each record has been checked against an identifiable source. A familiar symbol name is not proof of a standard-specific visual match.
- Populate exact standards artwork from authorized source files when available. This research found authoritative catalogs and limited public metadata, not an openly licensed complete ISA/IEC/ISO artwork corpus.
