# venturecompany — Report Design Template

A reusable design system for producing consulting-grade `.docx` or `.md` reports.

This template preserves only the design layout, color system, typography, reusable components, and document structure. It does not include company-specific business content, market assumptions, product names, or strategic claims.

Implementation reference: `generate.js` or any document generator that supports styled headings, tables, headers, footers, and page breaks.

---

## 1. Design Principles

1. **Confidence through restraint.** White space is a structural element. Never crowd the page.
2. **Hierarchy is visual, not decorative.** Every type size, color, and spacing choice maps to an information level.
3. **Color is signal, not ornament.** Use the palette purposefully — primarily for navigation, secondarily for emphasis. No gradients, no shadows, no decorative shapes.
4. **Evidence over claims.** When used for reports, each section should contain at least one structured artifact such as a KPI strip, data table, or callout.
5. **Consistency across volumes.** Reports in a series share identical typography, margins, header/footer, and component spacing — only content changes.

---

## 2. Color Palette

| Token | Hex | Role |
| --- | --- | --- |
| WHITE | `#FFFFFF` | Primary background |
| NAVY | `#051C2A` | Primary brand color — H1, body emphasis, header bars |
| BLUE | `#163E93` | Secondary brand color — H2 / section headings, callouts |
| CYAN | `#30A3DA` | Accent — eyebrow labels, accent rules, KPI tile #3 |
| BLACK | `#060200` | Body copy |
| GRAY_LIGHT | `#F2F2F2` | Alternating table rows, callout background |
| GRAY_BORDER | `#D9D9D9` | Subtle dividers and table borders |

### Rules

- Body text is always `BLACK`.
- H1 headings use `NAVY`; H2 headings use `BLUE`.
- `CYAN` is reserved for eyebrows, accent bars, and the third KPI tile only.
- Never use more than three brand colors in any single component.
- Avoid gradients, drop shadows, decorative icons, and non-functional color usage.

---

## 3. Typography

| Style | Family | Size | Weight | Color | Usage |
| --- | --- | --- | --- | --- | --- |
| Cover Title | Arial | 32 pt | Bold | NAVY | Cover only |
| Cover Subtitle | Arial | 14 pt | Regular | NAVY | Cover only |
| Eyebrow | Arial | 8 pt | Bold, tracked +40 | CYAN | Above every H1 |
| H1 | Arial | 18 pt | Bold | NAVY | Section title |
| H2 | Arial | 13 pt | Bold | BLUE | Subsection |
| H3 | Arial | 11 pt | Bold | NAVY | Sub-subsection |
| Body | Arial | 10.5 pt | Regular | BLACK | Default paragraph |
| Bullet | Arial | 10.5 pt | Regular | BLACK | List items |
| Lead-in Bullet | Arial | 10.5 pt | Bold lead-in + regular body | NAVY / BLACK | Emphasized list items |
| Caption / Footer | Arial | 8 pt | Regular | NAVY | Header, footer, fine print |

### Rules

- Use a single font family throughout: **Arial**.
- Body line spacing: **1.25**.
- Body alignment: **justified**.
- Use structured list styling instead of manually typed bullet symbols where the implementation supports it.
- Level 0 bullet marker: square `■` in `CYAN`.
- Level 1 bullet marker: en dash `–` in `BLUE`.

---

## 4. Page Layout

| Property | Value |
| --- | --- |
| Paper size | US Letter, 12240 × 15840 DXA |
| Margins | Top/Bottom 1440 DXA, Left/Right 1080 DXA |
| Header offset | 720 DXA |
| Footer offset | 720 DXA |
| Content width | 10080 DXA |
| Title page | Distinct first-page header/footer suppressed |

---

## 5. Page Furniture

### 5.1 Cover Page

The cover page should always use the following sequence:

1. Top thick navy bar.
2. Thin cyan accent bar below the navy bar.
3. Vertical whitespace.
4. Eyebrow in cyan: `STRATEGIC BRIEFING | VOLUME [N]`.
5. Cover title in `NAVY`, 32 pt bold.
6. Cover subtitle in `NAVY`, 14 pt regular.
7. Blue divider rule.
8. Metadata stack:
   - Prepared For
   - Prepared By
   - Date
9. Page break.

### 5.2 Running Header

Used on every page after the cover.

- Left: `venturecompany` in bold `NAVY`.
- Right: report title in `BLUE`.
- Bottom: cyan rule.

### 5.3 Running Footer

Used on every page after the cover.

- Top: gray separator rule.
- Left: `Confidential | © venturecompany`.
- Right: `Page X of Y`.

---

## 6. Document Structure

Recommended section order:

1. Cover Page
2. Executive Summary
   - Eyebrow
   - H1
   - Cyan accent bar
   - Context paragraph
   - KPI Strip
   - Key Takeaway callout
   - Page break
3. Section 01
4. Section 02
5. Section 03
6. Closing Perspective

Each section should open with:

1. Eyebrow
2. H1
3. Cyan accent rule
4. Short framing paragraph
5. Main content components

---

## 7. Component Library

### 7.1 Eyebrow

- Uppercase.
- Bold.
- 8 pt.
- Character-spaced +40.
- Color: `CYAN`.
- Always immediately precedes an H1.

Examples:

- `EXECUTIVE SUMMARY`
- `SECTION 01`
- `SECTION 02`
- `CLOSING PERSPECTIVE`

### 7.2 Accent Bar

- A paragraph or rule with bottom border.
- Size: 18.
- Color: `CYAN`.
- Sits directly below H1.

### 7.3 KPI Strip

- Three equal-width tiles.
- Full content width.
- Tile 1 background: `NAVY`.
- Tile 2 background: `BLUE`.
- Tile 3 background: `CYAN`.
- White borders between tiles.
- Each tile contains:
  - Value: white, 22 pt, bold, centered.
  - Label: white, 9 pt, centered.

Use this component to surface three quantitative indicators or key summary metrics.

### 7.4 Callout Box

- Single full-width cell or box.
- Background: `GRAY_LIGHT`.
- Top border: thick, usually `BLUE` or `NAVY`.
- Internal padding: 200/240 DXA.
- Content structure:
  - Small uppercase label.
  - Short strategic statement in navy text.

Recommended labels:

- `KEY TAKEAWAY`
- `STRATEGIC READ`
- `IMPLICATION`
- `OPERATING PRINCIPLE`
- `FORWARD-LOOKING VIEW`

Use a maximum of 1–2 callout boxes per major section.

### 7.5 Data Table

- Header row:
  - Background: `NAVY`.
  - Text: white, bold, 10 pt.
- Body rows:
  - Alternating row shading using `GRAY_LIGHT`.
- Borders:
  - Thin `GRAY_BORDER`.
- Cell padding:
  - Top/bottom: 120 DXA.
  - Left/right: 160 DXA.
- Vertical alignment:
  - Center.
- Table width:
  - Equal to full content width.
- Column widths:
  - Defined explicitly.
  - Sum of column widths must equal table width.

### 7.6 Lead-in Bullet

For “term — explanation” structures.

- Lead phrase: bold `NAVY`.
- Explanation: regular `BLACK`.
- Inline structure.
- Bullet marker: square `■` in `CYAN`.
- Recommended indent: 360 DXA with 240 DXA hanging indent.

### 7.7 Numbered List

- Marker style: `1.`, `2.`, `3.`.
- Marker color: `BLUE`.
- Marker weight: bold.
- Recommended indent: 420 DXA with 280 DXA hanging indent.

---

## 8. Content and Tone Guidelines

- Use third-person, declarative, evidence-led language.
- Keep hedging minimal.
- Use numbers with units wherever possible.
- Pair quantitative claims with source, test, or comparator where applicable.
- Section openers should be 1–2 sentences.
- Section closers should summarize strategic implication, not merely restate data.
- Closing section should provide a concise synthesis and recommended next actions.

---

## 9. Implementation Notes

When implementing this design in a document generator:

- Set page size explicitly.
- Avoid newline characters inside text runs; use separate paragraphs.
- Use fixed-width tables rather than percentage-based tables where compatibility matters.
- Ensure table width equals the sum of column widths.
- Ensure each cell width matches its corresponding column width.
- Use explicit heading style IDs where the generator supports named styles.
- Wrap page breaks inside paragraphs where required by the document engine.
- Register list numbering and bullet styles before document composition.
- Keep helper functions separate from content functions.

Recommended helper functions:

- `coverPage(eyebrow, title, subtitle, date)`
- `eyebrow(text, color)`
- `h1(text)`
- `h2(text)`
- `h3(text)`
- `body(text, options)`
- `bullet(text, level)`
- `leadInBullet(lead, rest, level)`
- `numbered(children)`
- `accentBar(color, size)`
- `dataTable(headers, rows, columnWidths)`
- `kpiStrip(items)`
- `calloutBox(label, text, color)`
- `pageBreak()`
- `buildHeader(title)`
- `buildFooter()`
- `buildDoc(headerTitle, children)`

---

## 10. Reuse Workflow

1. Copy the document generator or markdown structure into the new project.
2. Replace only content sections.
3. Keep typography, colors, margins, header/footer, and component spacing unchanged.
4. Maintain the cover → executive summary → core sections → closing structure.
5. Validate output before delivery.
6. Use a consistent naming convention.

Recommended naming convention:

`[NN]_venturecompany_[Topic]_Strategic_Briefing.docx`

For markdown references:

`venturecompany_design_template.md`

---

## 11. Versioning

- v1.0 — Initial reusable design template for `venturecompany`.