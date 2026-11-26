---
name: E-Market Dynamic Commerce
colors:
  surface: '#f8f9ff'
  surface-dim: '#d0dbed'
  surface-bright: '#f8f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#eff4ff'
  surface-container: '#e6eeff'
  surface-container-high: '#dee9fc'
  surface-container-highest: '#d9e3f6'
  on-surface: '#121c2a'
  on-surface-variant: '#5b403b'
  inverse-surface: '#27313f'
  inverse-on-surface: '#eaf1ff'
  outline: '#8f706a'
  outline-variant: '#e4beb7'
  surface-tint: '#b7230a'
  primary: '#b32007'
  on-primary: '#ffffff'
  primary-container: '#d73b20'
  on-primary-container: '#fffbff'
  inverse-primary: '#ffb4a5'
  secondary: '#b22b15'
  on-secondary: '#ffffff'
  secondary-container: '#ff6246'
  on-secondary-container: '#620800'
  tertiary: '#006947'
  on-tertiary: '#ffffff'
  tertiary-container: '#00855b'
  on-tertiary-container: '#f5fff6'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#ffdad3'
  primary-fixed-dim: '#ffb4a5'
  on-primary-fixed: '#3f0400'
  on-primary-fixed-variant: '#8e1200'
  secondary-fixed: '#ffdad3'
  secondary-fixed-dim: '#ffb4a6'
  on-secondary-fixed: '#3f0300'
  on-secondary-fixed-variant: '#8f1000'
  tertiary-fixed: '#6ffbbe'
  tertiary-fixed-dim: '#4edea3'
  on-tertiary-fixed: '#002113'
  on-tertiary-fixed-variant: '#005236'
  background: '#f8f9ff'
  on-background: '#121c2a'
  surface-variant: '#d9e3f6'
typography:
  display:
    fontFamily: Be Vietnam Pro
    fontSize: 48px
    fontWeight: '800'
    lineHeight: 56px
    letterSpacing: -0.02em
  display-mobile:
    fontFamily: Be Vietnam Pro
    fontSize: 32px
    fontWeight: '800'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-lg:
    fontFamily: Be Vietnam Pro
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.015em
  headline-lg-mobile:
    fontFamily: Be Vietnam Pro
    fontSize: 24px
    fontWeight: '700'
    lineHeight: 32px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Be Vietnam Pro
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.01em
  headline-sm:
    fontFamily: Be Vietnam Pro
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  title-md:
    fontFamily: Be Vietnam Pro
    fontSize: 16px
    fontWeight: '600'
    lineHeight: 24px
  body-lg:
    fontFamily: Be Vietnam Pro
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: Be Vietnam Pro
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-lg:
    fontFamily: Be Vietnam Pro
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 20px
  label-md:
    fontFamily: Be Vietnam Pro
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
  caption:
    fontFamily: Be Vietnam Pro
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
  helper:
    fontFamily: Be Vietnam Pro
    fontSize: 11px
    fontWeight: '400'
    lineHeight: 14px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  gutter: 1.5rem
  gutter-mobile: 0.75rem
  margin: 2rem
  margin-mobile: 1rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2.5rem
---

## Brand & Style

This design system establishes an energetic, high-conversion modern e-commerce experience tailored for competitive online retail. The brand personality balances pulse-raising promotional excitement with polished reliability. 

- **Audience:** Discerning digital-native consumers and retail merchants seeking efficiency, visual clarity, and instant trustworthiness during transactions.
- **Emotional Response:** Confidence in product authenticity, immediate visual delight, urgency during flash promotions, and friction-free checkout clarity.
- **Design Philosophy:** Modern Retail Pragmatism blending subtle glass accents, soft tactile elevations, and vivid chromatic focal points. High-velocity visual cues (coral-to-wine gradients) guide the eye to high-intent actions, while serene pearl and slate neutrals maintain pristine product visibility without cognitive fatigue.

## Colors

The palette is engineered around energetic coral-red dynamics layered over soft warm neutrals, calibrated for commercial conversion and legibility under varying lighting conditions.

### Primary Spectrum & Brand Gradients
- **Primary Brand Coral (`#E8472B`):** Anchors primary calls-to-action, active indicator states, flash badges, and conversion touchpoints.
- **Secondary Wine Red (`#B82F19`):** Deep anchor used alongside primary coral to produce dynamic gradient accents (`linear-gradient(135deg, #E8472B 0%, #B82F19 100%)`) across marketing hero banners, loyalty tiers, and VIP badges.
- **Vibrant Accent Red (`#D3361E`):** Serves as an interactive hover/pressed state for primary controls and alert-driven highlight ribbons.

### Neutrals & Surfaces
- **Pure White (`#FFFFFF`):** Base canvas for product card viewports, input interiors, modal bodies, and sticky headers.
- **Pearl Cream Base (`#FAF8F5`):** Default page background tone providing warmth and reducing optical glare.
- **Surface Muted Gray (`#F3F4F6`):** Secondary card backgrounds, table header bars, and disabled element fills.
- **Subtle Outline Gray (`#E5E7EB`):** Standard non-intrusive container borders, field separators, and social button borders.
- **Muted Text Gray (`#6B7280`):** Secondary information, metadata tags, breadcrumb paths, and helper captions.
- **Deep Text Slate (`#1F2937`):** Primary body typography, pricing integer figures, and standard titles.
- **Charcoal Black (`#111827`):** Heavy headlines, navigational anchors, and high-impact microcopy.

### Functional & Third-Party
- **Success (`#10B981`):** Inventory availability tags, checkout success receipts, discount voucher claims.
- **Error / Destructive (`#EF4444`):** Real-time field validation errors, out-of-stock badges, order cancellations.
- **Social Media Accent (`#1877F2`):** Direct third-party OAuth sign-in integration (Facebook).

## Typography

The typography scale utilizes **Be Vietnam Pro** across all operational tiers. Its precision geometric balance, open counterforms, and native diacritic accommodation provide exceptional rendering for Vietnamese and international product catalogues alike.

- **Numerics & Prices:** Pricing tags use `title-md` or `headline-md` at `fontWeight: 700` with tabular number rendering (`font-variant-numeric: tabular-nums`) to prevent horizontal jitter during cart updates.
- **Hierarchy Rules:** 
  - `display` and `headline-lg` are reserved for hero campaign titles and category department launches.
  - `title-md` is standard for product catalog naming, clamped to a maximum of 2 lines.
  - `helper` and `caption` maintain strict contrast compliance (`#6B7280` on `#FFFFFF` yields > 4.5:1), ensuring legal, promotional, and validation notices remain effortless to scan.

## Layout & Spacing

The layout is built upon a standard 8pt modular system using a responsive fluid grid structure with constrained maximum widths:
- **Max Content Width:** 1280px (`max-w-7xl`), centered within the viewport.
- **Desktop Grid (>= 1024px):** 12-column grid system with 24px (`1.5rem`) gutters and 32px (`2rem`) margins. Product grids default to 4 or 6 items per row.
- **Tablet Grid (768px - 1023px):** 8-column layout with 16px (`1rem`) gutters. Product grids collapse to 3 items per row.
- **Mobile Grid (< 768px):** 4-column layout with 12px (`0.75rem`) gutters and 16px (`1rem`) margins. Product grids reflow into an optimized 2-column card stream.

Spacing tokens (`space-xs` through `space-xl`) exclusively govern structural padding and spacing gaps between nested components to preserve horizontal visual cadence.

## Elevation & Depth

Visual hierarchy is conveyed through a combination of crisp tonal layering and diffused, ambient shadows that elevate cards off the pearl foundation without visual clutter.

- **Base Layer (Level 0):** Neutral ground (`#FAF8F5`). Flat, non-elevated surfaces.
- **Layer 1 - Low Surface (`shadow-sm`):** `0 1px 2px 0 rgba(17, 24, 39, 0.05)`. Applied to standard catalog item cards, list rows, and input states. Paired with a delicate border (`1px solid #E5E7EB`).
- **Layer 2 - Active Surface (`shadow-md`):** `0 4px 6px -1px rgba(17, 24, 39, 0.07), 0 2px 4px -2px rgba(17, 24, 39, 0.05)`. Used for hovering product cards, open filter popovers, and sticky navigation headers.
- **Layer 3 - Floating Brand Elements (`shadow-xl`):** `0 20px 25px -5px rgba(232, 71, 43, 0.12), 0 8px 10px -6px rgba(184, 47, 25, 0.08)`. Tinted ambient dispersion deployed strictly on floating checkout bars, quick-buy triggers, and promotional campaign modals to convey urgency.
- **Glassmorphism Rule:** Sticky mobile navigation bars and sub-category headers apply `rgba(255, 255, 255, 0.85)` with `backdrop-filter: blur(12px)` and a subtle bottom border (`#E5E7EB`) to let product colors bleed gracefully underneath.

## Shapes

The design system implements a refined, approachable geometry via `roundedness: 2`:
- **Default Elements (0.5rem / 8px):** Applied to form fields, secondary buttons, standard chip containers, dropdown panels, and rating badges.
- **Large Elements (`rounded-lg`, 1rem / 16px):** Standard product cards, filter drawers, cart line containers, and informational banners.
- **Extra Large Elements (`rounded-xl`, 1.5rem / 24px):** Hero showcase cards, floating promotion banners, flash sale modules, and dialog overlays.
- **Capsule / Pill Shapes (`rounded-full`):** Category pill filters, counter badges, notification dots, and promotional discount chips.

## Components

### Buttons
- **Primary Action:** Solid background with brand gradient `linear-gradient(135deg, #E8472B 0%, #D3361E 100%)`, text `#FFFFFF`, font weight `600`, radius `rounded-lg` (8px). 
  - *Interactions:* Hover switches to `linear-gradient(135deg, #D3361E 0%, #B82F19 100%)` with `shadow-md` and `transform: translateY(-1px)`. Active state triggers `transform: translateY(0px)`.
- **Secondary Action:** Pure white background (`#FFFFFF`), border `1.5px solid #E5E7EB`, text `#1F2937`.
  - *Interactions:* Hover initiates border color `#E8472B` and text `#E8472B` on a pearl backdrop (`#FAF8F5`).
- **Social Buttons:** Dedicated Facebook button (`#1877F2`, white text) and Google button (`#FFFFFF`, border `#E5E7EB`, text `#1F2937`).

### Input Fields
- **Container:** Height 44px (mobile 48px), background `#FFFFFF`, border `1px solid #E5E7EB`, rounded `rounded-lg`.
- **States:**
  - *Default:* Border `#E5E7EB`, placeholder `#6B7280`.
  - *Focus:* Border `#E8472B`, subtle glow `box-shadow: 0 0 0 3px rgba(232, 71, 43, 0.15)`, outline none.
  - *Error:* Border `#EF4444`, glow `box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.15)`.
- **Helper & Validation Text:** Positioned 4px below field using `helper` type style (`#6B7280` for standard cues, `#EF4444` for error strings).

### Product Cards
- **Structure:** Surface `#FFFFFF`, border `1px solid #E5E7EB`, border-radius `rounded-xl`, padding `space-md`.
- **Visuals:** Top image container features aspect ratio 1:1, overflow hidden, with soft zoom on hover (`scale-105` over 300ms ease).
- **Pricing:** Discount price rendered in `#E8472B` (`headline-sm`, 700 weight); original price strikethrough in `#6B7280` (`body-md`).
- **Elevation Behavior:** Shifts from `shadow-sm` at rest to `shadow-md` on cursor hover with smooth 200ms cubic-bezier transitions.

### Chips & Filter Tags
- **Default:** Background `#F3F4F6`, border `1px solid transparent`, text `#1F2937`, padding `6px 14px`, `rounded-full`.
- **Active / Selected:** Background `rgba(232, 71, 43, 0.08)`, border `1px solid #E8472B`, text `#E8472B`, font weight `600`.

### Checkboxes & Radio Controls
- **Geometry:** Checkboxes use 4px radius; radio controls use full circular tokens. Width/Height: 18px.
- **States:** Default border `#E5E7EB`, checked state filled with `#E8472B`, white micro-icon checkmark or bullet dot centered.

### Floating Cart & Toast Badges
- Floating summary containers feature `#FFFFFF` background with `shadow-xl` (tinted wine-coral ambient shadow), rounded-xl border, and high-visibility checkout button displaying real-time aggregated subtotal.