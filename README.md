# August 2026 Member Newsletter Drafts

This is the internal working pack for the August 2026 member newsletter.

The live hub links to six newsletter drafts. Each draft groups industries with a similar operating model, buyer, or hiring pattern. Each draft uses the same conversion path:

1. Show the hiring activity in the member's own industry.
2. Show the relevant AI builds that shipped in August.
3. Recommend a hire and AI combination.
4. Position Global Pay Direct as the operating layer after the offer.
5. Ask for the next hiring request.

## Verified August facts

- 77 CORE accepted-offer hires from active members.
- 5 GTC hires.
- 76 of 77 CORE hires have an intro video confirmed in the source export.
- 10 separate White Glove placement invoices.
- 10 included customer AI builds.
- 0 August CORE hires matched an August installment invoice.
- 0 August CORE hires enrolled in GPD during August.
- 2 July-signed hires started through GPD in August.

## Deliberate limits

The August export does not include accepted compensation. The pages do not present candidate profile rates as member-paid compensation.

The source confirms whether an intro video exists. A video is linked only when the local candidate mirror provides a conservative name match and a URL. All other records show `Intro video ready` without a link.

## Project files

- `index.html`: internal hub.
- `clusters/*/index.html`: 6 grouped industry drafts.
- `assets/styles.css`: shared design system.
- `data/august-2026.json`: normalized source data.
- `data/august-2026-enriched.json`: conservative local candidate-profile enrichment.
- `generate_pages.py`: deterministic static page generator.
- `enrich_august.py`: candidate enrichment script.

## Regenerate

```bash
python3 enrich_august.py > /tmp/august-2026-enriched.json
python3 generate_pages.py
```

The committed enriched data is the reviewed input. Do not replace it without checking the match counts and unresolved names.

## Primary metric

Qualified hiring requests created within 30 days of a send.

Track placement revenue, AI build revenue, GPD adoption, and hire-plus-build combinations as supporting measures.

## Newsletter groups

- Home & Field Services — 27 hires.
- Consumer, Sports & Hospitality — 14 hires.
- Property, Construction & Engineering — 12 hires.
- Finance & Business Services — 10 hires.
- Health, Wellness & Care — 9 hires.
- Logistics & Industrial Operations — 5 hires.
