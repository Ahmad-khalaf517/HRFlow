---
name: Deep Equity System
colors:
  surface: '#f8f9ff'
  surface-dim: '#ccdbf3'
  surface-bright: '#f8f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#eff4ff'
  surface-container: '#e6eeff'
  surface-container-high: '#dce9ff'
  surface-container-highest: '#d5e3fc'
  on-surface: '#0d1c2e'
  on-surface-variant: '#41484b'
  inverse-surface: '#233144'
  inverse-on-surface: '#eaf1ff'
  outline: '#71787c'
  outline-variant: '#c1c7cb'
  surface-tint: '#3d6473'
  primary: '#00222c'
  on-primary: '#ffffff'
  primary-container: '#0c3846'
  on-primary-container: '#7ba1b2'
  inverse-primary: '#a5ccde'
  secondary: '#18677a'
  on-secondary: '#ffffff'
  secondary-container: '#a3e7fe'
  on-secondary-container: '#1c697d'
  tertiary: '#00222b'
  on-tertiary: '#ffffff'
  tertiary-container: '#003945'
  on-tertiary-container: '#54a7be'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#c1e9fb'
  primary-fixed-dim: '#a5ccde'
  on-primary-fixed: '#001f29'
  on-primary-fixed-variant: '#244c5a'
  secondary-fixed: '#b2ebff'
  secondary-fixed-dim: '#8dd0e7'
  on-secondary-fixed: '#001f27'
  on-secondary-fixed-variant: '#004e5f'
  tertiary-fixed: '#b1ecff'
  tertiary-fixed-dim: '#81d2eb'
  on-tertiary-fixed: '#001f27'
  on-tertiary-fixed-variant: '#004e5e'
  background: '#f8f9ff'
  on-background: '#0d1c2e'
  surface-variant: '#d5e3fc'
typography:
  display:
    fontFamily: Hanken Grotesk
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Hanken Grotesk
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  headline-md:
    fontFamily: Hanken Grotesk
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  body-lg:
    fontFamily: Hanken Grotesk
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: Hanken Grotesk
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  body-sm:
    fontFamily: Hanken Grotesk
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
  label-caps:
    fontFamily: Hanken Grotesk
    fontSize: 12px
    fontWeight: '700'
    lineHeight: 16px
    letterSpacing: 0.05em
  data-mono:
    fontFamily: JetBrains Mono
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  unit: 4px
  container-padding: 24px
  gutter: 16px
  row-height-dense: 32px
  row-height-standard: 48px
---

## Brand & Style
The design system is engineered for the high-stakes environment of HR and Payroll management. The brand personality is rooted in **precision, stability, and quiet authority**. It moves away from consumer-grade trends like glassmorphism or playfulness, favoring a **Modern Corporate** aesthetic that prioritizes data legibility and administrative efficiency.

The visual language communicates trustworthiness through structural alignment and a disciplined color palette. The UI should evoke a sense of calm under pressure, ensuring that complex financial data and employee records are accessible without visual fatigue. The focus is on utilitarian beauty—where "good design" is defined by how quickly a user can reconcile a ledger or process a payroll run.

## Colors
The palette is a monochromatic progression of teals and blues designed to create a focused, "heads-down" working environment.

- **Primary (#0C3846):** Used for global navigation, primary actions, and high-level headers to establish authority.
- **Secondary & Tertiary:** Used for interactive elements, active states, and icon accents to guide the eye.
- **Surface Ice (#E4F4F8):** Acts as the primary background color for page sections to reduce the harshness of pure white while maintaining high contrast.
- **Semantic Colors:** Chosen for WCAG AA compliance against both White and Surface Ice backgrounds. Use these sparingly for status indicators, validation messages, and critical alerts.

## Typography
This design system utilizes **Hanken Grotesk** for its contemporary, sharp terminals and exceptional readability in dense layouts. For financial figures, IDs, and tabular data, **JetBrains Mono** is employed to ensure character alignment and prevent "jumping" numbers.

- **Headlines:** Use a tighter letter-spacing to maintain a professional, compact feel.
- **Body Text:** The standard size is 14px (`body-md`) for internal tools, allowing for higher information density without sacrificing legibility.
- **Data Tables:** Always use `data-mono` for currency and numeric values to facilitate easy vertical scanning and comparison.

## Layout & Spacing
The layout follows a **Fluid Grid** model with strict 4px increments (the "Base 4" system). This ensures components remain compact but comfortable.

- **Desktop Layout:** 12-column grid with 16px gutters. Left-hand navigation is fixed at 240px.
- **Density:** Provide two density modes. "Standard" for general browsing and "Compact" for large-scale data entry/payroll reconciliation where vertical space is at a premium.
- **Alignment:** All form elements and data points should align to a strict vertical rhythm to emphasize the "precise" nature of the software.

## Elevation & Depth
In alignment with the "no excessive shadows" requirement, this design system uses **Tonal Layering** and **Subtle Borders** instead of elevation.

- **Flat Surface:** The main background is `Surface Ice`. 
- **Raised Surface:** Content cards use `White` with a 1px border of `Light Blue (#9FD3E3)` or a subtle `Slate-200`.
- **Active State:** Elements being hovered or selected do not rise; instead, they receive a 2px interior border or a subtle background shift to `Secondary Blue`.
- **Dividers:** Use 1px solid lines in `Light Blue` for logical separation within cards and lists.

## Shapes
The shape language is primarily **Soft (0.25rem)**. This provides a professional edge that feels modern without being overly clinical or sharp. 

- **Inputs and Buttons:** Use `rounded` (4px).
- **Cards and Containers:** Use `rounded` (4px). Avoid `rounded-lg` or `rounded-xl` to maintain a structured, spreadsheet-adjacent aesthetic.
- **Avatars:** Use circles only for employee photos to provide a single point of organic contrast in the grid.

## Components

### Buttons
- **Primary:** Solid `Deep Teal`, White text, 4px corner radius. No gradient.
- **Secondary:** Outline `Deep Teal` with a 1px border.
- **Ghost:** No border, `Deep Teal` text, light `Surface Ice` background on hover.

### Input Fields
- **Default State:** 1px border in `Light Blue`, `White` background.
- **Focus State:** 2px border in `Secondary Blue`, no outer glow.
- **Labels:** Always top-aligned, using `body-sm` weight 600 for clarity.

### Data Tables
- **Header:** Background `Deep Teal`, text `White`, `label-caps` typography.
- **Rows:** Alternate row striping (Zebra) using `Surface Ice`. 1px horizontal borders only.
- **Cells:** Vertical padding of 8px (Dense) or 12px (Standard).

### Chips & Status Indicators
- Use a "Subtle Tag" style: Light semantic background with high-contrast text (e.g., Light Green background with Dark Green text for "Paid").

### Lists
- Multi-line lists for employee directories should use `body-md` for the name and `body-sm` in `Neutral` for the job title/department.

### Iconography
- Use 20px or 24px **Outline Icons** with a consistent 1.5pt stroke weight. Do not use filled icons unless they represent an active/selected state in the navigation.