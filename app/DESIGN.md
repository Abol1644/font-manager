---
name: Obsidian Gazette
colors:
  surface: '#131313'
  surface-dim: '#131313'
  surface-bright: '#3a3939'
  surface-container-lowest: '#0e0e0e'
  surface-container-low: '#1c1b1b'
  surface-container: '#201f1f'
  surface-container-high: '#2a2a2a'
  surface-container-highest: '#353534'
  on-surface: '#e5e2e1'
  on-surface-variant: '#bbcac2'
  inverse-surface: '#e5e2e1'
  inverse-on-surface: '#313030'
  outline: '#85948d'
  outline-variant: '#3c4a44'
  surface-tint: '#41deb3'
  primary: '#42dfb5'
  on-primary: '#00382a'
  primary-container: '#03c39a'
  on-primary-container: '#004a39'
  inverse-primary: '#006b54'
  secondary: '#c6c6c7'
  on-secondary: '#2f3131'
  secondary-container: '#454747'
  on-secondary-container: '#b4b5b5'
  tertiary: '#ffb6a3'
  on-tertiary: '#5f1501'
  tertiary-container: '#ff8d6d'
  on-tertiary-container: '#75250d'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#65fbcf'
  primary-fixed-dim: '#41deb3'
  on-primary-fixed: '#002117'
  on-primary-fixed-variant: '#00513e'
  secondary-fixed: '#e2e2e2'
  secondary-fixed-dim: '#c6c6c7'
  on-secondary-fixed: '#1a1c1c'
  on-secondary-fixed-variant: '#454747'
  tertiary-fixed: '#ffdbd1'
  tertiary-fixed-dim: '#ffb5a0'
  on-tertiary-fixed: '#3b0900'
  on-tertiary-fixed-variant: '#7e2b13'
  background: '#131313'
  on-background: '#e5e2e1'
  surface-variant: '#353534'
typography:
  display-xl:
    fontFamily: Bodoni Moda
    fontSize: 56px
    fontWeight: '700'
    lineHeight: 64px
    letterSpacing: -0.03em
  display-xl-mobile:
    fontFamily: Bodoni Moda
    fontSize: 36px
    fontWeight: '700'
    lineHeight: 42px
    letterSpacing: -0.02em
  display-lg:
    fontFamily: Bodoni Moda
    fontSize: 44px
    fontWeight: '600'
    lineHeight: 52px
    letterSpacing: -0.025em
  display-lg-mobile:
    fontFamily: Bodoni Moda
    fontSize: 28px
    fontWeight: '600'
    lineHeight: 34px
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Bodoni Moda
    fontSize: 28px
    fontWeight: '600'
    lineHeight: 36px
    letterSpacing: -0.015em
  headline-sm:
    fontFamily: Bodoni Moda
    fontSize: 22px
    fontWeight: '500'
    lineHeight: 28px
    letterSpacing: -0.01em
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 26px
    letterSpacing: -0.01em
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 22px
    letterSpacing: -0.005em
  body-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 18px
    letterSpacing: '0'
  code-md:
    fontFamily: JetBrains Mono
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 20px
    letterSpacing: '0'
  label-caps:
    fontFamily: JetBrains Mono
    fontSize: 11px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.08em
  label-sm:
    fontFamily: JetBrains Mono
    fontSize: 10px
    fontWeight: '400'
    lineHeight: 14px
    letterSpacing: 0.05em
spacing:
  gutter: 1rem
  gutter-desktop: 1.5rem
  margin: 1rem
  margin-desktop: 2.5rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2.5rem
---

## Brand & Style

This design system blends Swiss typographic discipline with high-contrast Editorial Neo-Brutalism in a nocturnal context. It targets engineers, cultural curators, and analytical operators who demand dense information architecture without superfluous ornamentation.

The visual style is characterized by:
- **Architectural Zero-Radius Grid:** Strict 0px corner radii across every viewport element, framing data in absolute structural compartments.
- **Editorial High-Low Tension:** High-contrast dramatic serif titles contrasted with utilitarian, cold monospaced metrics and structural labels.
- **Controlled Luminescence:** A deep void palette illuminated by surgical strikes of high-voltage mint/teal for active systems and critical callouts.
- **Precision Lineation:** 1px hair-thin rules replace drop shadows to define plane transitions and visual containers.

## Colors

The palette operates in strict tonal layers to preserve pitch-black fidelity while retaining readability and depth across layered panels.

- **Void (Canvas):** `#0a0a0a` — Base layer for primary page surfaces.
- **Surface Container (Tier 1):** `#141414` — Primary modular cards, sidebars, and structural blocks.
- **Surface High (Tier 2):** `#1e1e1e` — Elevated panels, active rows, dialog sheets, and hover planes.
- **Structural Lines:** `#262626` (recessed/subtle grid borders) and `#333333` (active framing borders and divider lines).
- **Ink Primary:** `#ffffff` — Headers, core titles, primary values.
- **Ink Muted:** `#8e8e8e` — Body descriptions, static labels, inactive tab titles.
- **Signal Mint / Teal:** `#03c39a` — Pure functional accent; strictly reserved for active states, live indicators, focus outlines, selection badges, and hyper-prominent callouts. Never used for large passive backgrounds.

## Typography

The type system stages an intentional tension between classical high-fashion editorial display and uncompromising terminal-grade utility.

- **Headings (`Bodoni Moda`):** Delivers dramatic scale and high vertical-stroke contrast. Titles should lean toward title casing or sentence casing, eschewing soft aesthetics for severe elegance.
- **Reading Body (`Inter`):** Neutral, neutral-density grotesk selected to allow comfortable long-form scanability alongside high-contrast serif headlines.
- **Metadata & Structural Data (`JetBrains Mono`):** Applied to badges, table numbers, timestamps, system outputs, breadcrumbs, and categorizations. Always rendered uppercase when tagged as `label-caps`.

## Layout & Spacing

The layout is grounded in a fluid-responsive modular grid with visible structural seams.

- **Column System:** 12-column layout on desktop (breakpoint 1024px+), 8-column layout on tablet (640px-1023px), and 4-column layout on mobile (<640px).
- **Rhythm & Rules:** Grid boundaries are made explicit with 1px `#262626` hairline borders across intersecting columns and horizontal shelf dividers. Content docks directly to perimeter lines.
- **Margins & Gutters:** Mobile views use condensed `1rem` margins and gutters; desktop expands to `2.5rem` margins and `1.5rem` gutters to enhance editorial pacing and whitespace contrast.

## Elevation & Depth

No drop shadows, blurred glows, or faux depth gradients are permitted. Visual elevation is communicated exclusively through plane brightness and linear contrast:

- **Level 0 (Canvas):** Pure `#0a0a0a`.
- **Level 1 (Docked/Inset):** `#141414` with a 1px solid `#262626` border.
- **Level 2 (Hovered/Active Panels):** `#1e1e1e` with a 1px solid `#333333` border.
- **Active Focus Elevation:** A 1px crisp outline in `#03c39a`, offset by 2px in `#0a0a0a` to maintain separation between surface and boundary.

## Shapes

The geometric rule is absolute: **0px border radius across all elements**. Buttons, inputs, modals, tooltips, tags, chips, and cards maintain hard 90-degree right angles.

## Components

- **Buttons:**
  - *Primary:* Background `#03c39a`, text `#0a0a0a`, font `JetBrains Mono` 12px uppercase semibold. Hover shifts background to `#ffffff`.
  - *Secondary:* Background `#141414`, text `#ffffff`, 1px border `#333333`. Hover upgrades border to `#ffffff` with background `#1e1e1e`.
  - *Destructive / Danger:* Background transparent, border 1px `#ff4a4a`, text `#ff4a4a`.
- **Chips & Status Badges:**
  - Constructed with `label-caps` in `JetBrains Mono`. Height 22px, padding `0 8px`.
  - Inactive/neutral: `#141414` fill with `#333333` border and `#8e8e8e` text.
  - Active/Live: `#03c39a` text, `#141414` fill, 1px border `#03c39a`, preceded by a solid 4px square glyph indicator.
- **Input Fields:**
  - Background `#0a0a0a`, border 1px `#262626`, text `#ffffff`, placeholder `#8e8e8e`.
  - Focus state: Border instantly snaps to 1px `#03c39a` with no glow or transition blur.
- **Cards & Editorial Frames:**
  - Surface `#141414` surrounded by 1px `#262626`.
  - Card headers include a separate metadata rack: monospaced taxonomy key at top left, numerical counter at top right, underlined by a 1px `#262626` dividing rule.
- **Selection Controls (Checkboxes & Radios):**
  - Checkboxes are 16x16px boxes with 0px radius, `#0a0a0a` interior, 1px `#333333` border. When checked: solid `#03c39a` background with `#0a0a0a` check mark.
  - Radio buttons retain the brutalist sharp shape: a 14x14px outer square with an inner 6x6px solid `#03c39a` center block when active.
- **Data Tables:**
  - Edge-to-edge `#141414` surface. Header cells styled with `label-caps` in `#8e8e8e` over 1px `#262626` bottom borders. Rows shift to `#1e1e1e` on pointer hover with an electric `#03c39a` left tick mark (2px wide).