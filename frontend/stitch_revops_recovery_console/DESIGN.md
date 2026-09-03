---
name: Revenue Operations Precision
colors:
  surface: '#121315'
  surface-dim: '#121315'
  surface-bright: '#38393b'
  surface-container-lowest: '#0d0e10'
  surface-container-low: '#1b1c1e'
  surface-container: '#1f2022'
  surface-container-high: '#292a2c'
  surface-container-highest: '#343537'
  on-surface: '#e3e2e5'
  on-surface-variant: '#c7c4d7'
  inverse-surface: '#e3e2e5'
  inverse-on-surface: '#303033'
  outline: '#908fa0'
  outline-variant: '#464554'
  surface-tint: '#c0c1ff'
  primary: '#c0c1ff'
  on-primary: '#1000a9'
  primary-container: '#8083ff'
  on-primary-container: '#0d0096'
  inverse-primary: '#494bd6'
  secondary: '#c4c6d0'
  on-secondary: '#2d3038'
  secondary-container: '#464951'
  on-secondary-container: '#b6b8c1'
  tertiary: '#ffb783'
  on-tertiary: '#4f2500'
  tertiary-container: '#d97721'
  on-tertiary-container: '#452000'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#e1e0ff'
  primary-fixed-dim: '#c0c1ff'
  on-primary-fixed: '#07006c'
  on-primary-fixed-variant: '#2f2ebe'
  secondary-fixed: '#e0e2ec'
  secondary-fixed-dim: '#c4c6d0'
  on-secondary-fixed: '#191c22'
  on-secondary-fixed-variant: '#44474e'
  tertiary-fixed: '#ffdcc5'
  tertiary-fixed-dim: '#ffb783'
  on-tertiary-fixed: '#301400'
  on-tertiary-fixed-variant: '#703700'
  background: '#121315'
  on-background: '#e3e2e5'
  surface-variant: '#343537'
typography:
  display:
    fontFamily: Inter
    fontSize: 36px
    fontWeight: '600'
    lineHeight: 44px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
    letterSpacing: -0.01em
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
    letterSpacing: '0'
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
    letterSpacing: '0'
  body-sm:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
    letterSpacing: '0'
  label-md:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.02em
  label-sm:
    fontFamily: JetBrains Mono
    fontSize: 11px
    fontWeight: '500'
    lineHeight: 14px
    letterSpacing: 0.03em
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
  sidebar-width: 260px
  stack-sm: 8px
  stack-md: 16px
  stack-lg: 32px
---

## Brand & Style

The design system is engineered for high-stakes fintech operations. It prioritizes clarity, speed of thought, and perceived reliability. The brand personality is that of a "Silent Partner"—highly capable, data-driven, and devoid of unnecessary visual noise. 

The aesthetic follows a **Modern Corporate** approach with a heavy emphasis on **Minimalism** and **Precision**. It avoids decorative trends like glassmorphism or vibrant gradients, opting instead for a "Control Center" feel. The emotional response should be one of calm authority, ensuring users feel in total control of complex financial recovery workflows. 

Key attributes:
- **Restraint:** Every pixel must serve a functional purpose.
- **Density:** High information density without visual clutter, achieved through rigorous alignment.
- **Intelligence:** Communicated through crisp typography and a purposeful primary accent that highlights automated insights.

## Colors

The palette is a "Deep Dark" scheme designed for prolonged professional use. It utilizes a layered approach to grayscale to create hierarchy without the need for shadows in every instance.

- **Foundational Neutrals:** The base uses `#0A0B0D` (Charcoal) for the canvas. Secondary containers use `#14161A` (Graphite) to create subtle separation.
- **Primary Accent:** `#6366F1` (Blue-Violet) is reserved strictly for primary actions, active states, and AI-driven insights. It should never be used for large surface areas.
- **Functional Semantics:** Colors follow industry standards but are slightly desaturated to fit the dark theme. Success (`#10B981`) represents recovered revenue, while Error (`#EF4444`) is used sparingly for safety blocks and critical failures.
- **Borders:** Use `#2D3139` for most UI borders to maintain a crisp, schematic look.

## Typography

This design system uses **Inter** for all functional UI elements and **JetBrains Mono** for technical data, IDs, and financial figures. 

- **Hierarchy:** High contrast in weight (SemiBold vs Regular) is preferred over significant size changes.
- **Data Display:** All currency amounts, transaction IDs, and recovery percentages should use the monospaced `label` roles to ensure tabular alignment and a technical feel.
- **Scale:** Sizes are kept conservative to support high-density dashboards. Headlines do not exceed 36px on desktop. 
- **Readability:** Line heights are strictly maintained at 1.4x-1.5x for body text to prevent eye fatigue in data-heavy views.

## Layout & Spacing

The layout is a **Fixed-Fluid Hybrid** designed for a 1440px desktop baseline. 

- **Sidebar Navigation:** A fixed 260px left sidebar handles global navigation. It uses the `surface-low` color to sit behind the main content area.
- **Main Content:** A fluid area with a max-width container of 1200px for readability, centered within the viewport.
- **The 4px Grid:** All spacing (margins, padding, gaps) must be a multiple of 4px. Use 16px for standard gutters between cards and 24px for page-level margins.
- **Density:** Components use tight internal padding (e.g., 8px vertical / 12px horizontal for buttons) to maintain a professional, tool-like feel.

## Elevation & Depth

Depth is conveyed through **Tonal Layering** and **Low-Contrast Outlines** rather than aggressive shadows.

1.  **Level 0 (Canvas):** `#0A0B0D`. The base background.
2.  **Level 1 (Cards/Sidebar):** `#14161A`. Subtle lift achieved via color shift.
3.  **Level 2 (Modals/Popovers):** `#1C1F26`. Highest contrast surface.
4.  **Borders:** Every surface at Level 1 or higher must have a 1px solid border of `#2D3139`.
5.  **Shadows:** Use a single "Deep Shadow" for floating elements (Modals): `0px 8px 24px rgba(0, 0, 0, 0.5)`. Avoid shadows on standard page cards; use borders for definition instead.

## Shapes

The shape language is "Soft-Mechanical." We use low border radii to maintain a serious, enterprise-grade appearance.

- **Standard Elements:** Buttons, inputs, and small cards use a **4px** radius (`rounded`).
- **Large Containers:** Main content cards or modals use a **6px** or **8px** radius (`rounded-lg`).
- **Strictness:** Never use pill-shaped buttons or fully rounded circles except for user avatars. Sharp corners communicate precision; stay within the 4px-8px range.

## Components

- **Buttons:** 
  - *Primary:* Solid `#6366F1` with white text. 4px radius. 
  - *Secondary:* Ghost style with `#2D3139` border and white text.
  - *Tertiary:* Plain text with no background, using the primary accent color for the label.
- **Input Fields:** Dark background (`#0A0B0D`), 1px border (`#2D3139`), and 14px text. Active state uses a 1px primary accent border—no outer glow.
- **Data Tables:** Row-based layout with 1px bottom borders. No vertical grid lines. Header text uses `label-sm` (Monospace) in 50% opacity white.
- **Chips/Badges:** Small, rectangular with 2px radius. Use a subtle background tint of the functional color (e.g., Success green at 10% opacity) with a solid text color.
- **Cards:** No shadows. Use `#14161A` background and `#2D3139` border.
- **AI Insights:** Elements generated or handled by the "Agent" are denoted by a subtle 2px left-border accent in `#6366F1`, never by glowing backgrounds or sparkles.