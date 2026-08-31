# HRFlow — Deep Equity Design System

The shipped interface uses the **Deep Equity** system: a compact, stable administrative UI optimized for legibility and repeatable payroll/HR workflows.

The executable token and component source is `static/css/src/input.css`. This document explains how to apply it. Keep both files synchronized.

## 1. Visual principles

- Prefer precision, stability, and quiet authority over decorative effects.
- Use flat tonal layers and one-pixel borders; do not add gradients, glass effects, or routine drop shadows.
- Keep layouts compact and aligned to a four-pixel rhythm.
- Use semantic color only for status, validation, or critical feedback.
- Reuse shared utilities before adding one-off class combinations.
- Preserve readable focus, disabled, error, empty, and loading states.

## 2. Color tokens

Use token utilities such as `bg-primary` and `text-on-surface`; do not copy arbitrary hex colors into templates.

### Surfaces and text

| Token | Value | Typical use |
|---|---:|---|
| `background`, `surface`, `surface-bright` | `#F8F9FF` | Page background |
| `surface-dim` | `#CCDBF3` | Stronger tonal separation |
| `surface-container-lowest` | `#FFFFFF` | Header and highest-contrast content |
| `surface-container-low` | `#EFF4FF` | Hover or quiet container |
| `surface-container` | `#E6EEFF` | Secondary container |
| `surface-container-high` | `#DCE9FF` | Stronger container |
| `surface-container-highest`, `surface-variant` | `#D5E3FC` | Highest tonal container |
| `on-surface`, `on-background` | `#0D1C2E` | Primary text |
| `on-surface-variant` | `#41484B` | Secondary text |
| `outline` | `#71787C` | Strong border/text outline |
| `outline-variant` | `#C1C7CB` | Default card/input border |

### Brand and semantic colors

| Token | Value | Typical use |
|---|---:|---|
| `primary` | `#00222C` | Sidebar, primary button, strong brand surface |
| `on-primary` | `#FFFFFF` | Text on primary |
| `primary-container` | `#0C3846` | Active navigation and primary hover |
| `on-primary-container` | `#7BA1B2` | Quiet content on primary container |
| `secondary` | `#18677A` | Focus border and secondary interaction |
| `on-secondary` | `#FFFFFF` | Text on secondary |
| `secondary-container` | `#A3E7FE` | Positive/informational badge background |
| `on-secondary-container` | `#1C697D` | Badge text |
| `tertiary` | `#00222B` | Reserved accent |
| `tertiary-container` | `#003945` | Reserved accent container |
| `error` | `#BA1A1A` | Error text/action |
| `on-error` | `#FFFFFF` | Text on error |
| `error-container` | `#FFDAD6` | Error message background |
| `on-error-container` | `#93000A` | Error message text |

The CSS also defines inverse and fixed color variants. Use them only when an interface state specifically needs them; consult `@theme` in `input.css` for the exact token.

## 3. Typography

Google Fonts currently loads Hanken Grotesk weights 400, 600, and 700 plus JetBrains Mono 400.

| Utility | Size / line | Weight | Use |
|---|---:|---:|---|
| `text-display` | 32 / 40px | 700 | Dashboard totals and rare page emphasis |
| `text-headline-lg` | 24 / 32px | 600 | Major page heading |
| `text-headline-md` | 20 / 28px | 600 | Section/card heading |
| `text-body-lg` | 16 / 24px | 400 | Prominent body copy |
| `text-body-md` | 14 / 20px | 400 | Default application text |
| `text-body-sm` | 13 / 18px | 400 | Supporting text, labels, hints |
| `text-label-caps` | 12 / 16px | 700 | Table headers and badges; uppercase |
| `text-data-mono` | 13 / 18px | 400 | Currency, identifiers, and aligned numeric data |

Do not use monospace for ordinary prose. Use it consistently for financial values and IDs in tables.

## 4. Spacing, shape, and layout

- Base spacing unit: `4px` (`0.25rem`).
- Default control/card radius: `4px` via `rounded`.
- Small radius: `2px`; medium: `6px`; large: `8px`; extra large: `12px`.
- Avoid `rounded-lg`/`rounded-xl` on routine controls and cards.
- Main desktop sidebar: fixed `240px`; hidden below Tailwind's `md` breakpoint in the current shell.
- Top header: `64px` high.
- Page padding: `16px` on small screens and `24px` from `md` upward.
- Default content gutter: `16px`.
- Dense table row target: `32px`; standard table row target: `48px`.

The current mobile shell hides the sidebar and does not yet provide a replacement navigation control. Treat mobile navigation as a scoped UI task, not as already implemented behavior.

## 5. Shipped component utilities

These utilities are defined in `static/css/src/input.css` and should be reused directly.

### Buttons

- `btn-primary`: primary background, white text, primary-container hover.
- `btn-secondary`: transparent background, primary outline/text, low-surface hover.
- `btn-ghost`: no border, primary text, low-surface hover.

All include inline-flex alignment, 4px radius, compact padding, disabled opacity, and disabled pointer behavior.

### Card

`card` provides a white surface, `outline-variant` border, 4px radius, and 24px padding. It intentionally has no shadow.

### Input

`input` provides a white background, one-pixel `outline-variant` border, body typography, and a two-pixel `secondary` focus border without an outer glow.

Use `templates/components/field.html` for standard form labels, required markers, help text, widget styling, and errors.

### Badge

`badge` provides layout, compact spacing, radius, and label typography. Pair it with semantic token utilities, for example:

```html
<span class="badge bg-secondary-container text-on-secondary-container">Done</span>
<span class="badge bg-error-container text-on-error-container">Failed</span>
```

## 6. Planned patterns

The following conventions are approved but do not yet have shared utilities/components:

- data tables with label-caps headers, numeric `text-data-mono` cells, horizontal dividers, and optional dense/standard spacing;
- subtle semantic status chips;
- multi-line employee list rows using body-md plus body-sm metadata;
- 20px or 24px outline icons with an approximately 1.5px stroke;
- pagination, modal, empty-state, and loading-state patterns.

Create these only when a task needs them, then add a reusable component or utility and document it here.

## 7. Template rules

- Auth pages extend `templates/auth_base.html`.
- Authenticated application pages extend `templates/base.html`.
- Reuse `templates/components/field.html` for Django form fields.
- Use the shared `{% block title %}`, `{% block page_title %}`, and `{% block content %}` structure.
- Keep authorization in views/services; hiding navigation is not authorization.
- Keep forms keyboard accessible, retain visible focus, and associate labels and errors with fields.

## 8. Tailwind workflow

Tailwind 4 uses CSS-first configuration; there is no JavaScript Tailwind config file.

```powershell
npm ci
npm run watch:css
```

For a reviewable build:

```powershell
npm run build:css
```

Source: `static/css/src/input.css`  
Generated artifact: `static/css/dist/output.css`

The generated artifact is tracked. Any change to tokens, utilities, or template class names must include a rebuilt `output.css` and a visual check at relevant desktop/mobile widths.

## 9. UI review checklist

- Uses only design tokens or documented semantic colors.
- Reuses shipped utilities/components.
- Maintains the 4px rhythm and restrained radius.
- Uses JetBrains Mono for financial/identifier data.
- Includes hover, focus, disabled, validation, and empty states where relevant.
- Has no routine gradients, glass effects, or shadows.
- Works with keyboard navigation and readable contrast.
- Rebuilds and commits `output.css`.
- Preserves server-side permissions independent of navigation visibility.
