---
version: alpha
name: Trupeer Editorial Light
description: A warm, minimal SaaS system combining elegant serif headlines with pragmatic sans-serif UI.
colors:
  primary: "#1A1A1A"
  secondary: "#6B6B6B"
  tertiary: "#B8A98A"
  neutral: "#F7F1E6"
  surface: "#FFFFFF"
  on-surface: "#1A1A1A"
  muted-surface: "#FFF8ED"
  border: "#E5E7EB"
  accent: "#F7D27B"
  error: "#D64545"
  success: "#2E7D5B"
typography:
  headline-display:
    fontFamily: Kalice Regular
    fontSize: 51px
    fontWeight: 400
    lineHeight: 57.12px
    letterSpacing: -1.5px
  headline-lg:
    fontFamily: Stack Sans Headline
    fontSize: 38px
    fontWeight: 400
    lineHeight: 47.88px
    letterSpacing: -0.7px
  headline-md:
    fontFamily: Stack Sans Headline
    fontSize: 29px
    fontWeight: 400
    lineHeight: 35px
    letterSpacing: 0px
  headline-sm:
    fontFamily: Stack Sans Headline
    fontSize: 21px
    fontWeight: 400
    lineHeight: 31.2px
    letterSpacing: -0.5px
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: 400
    lineHeight: 28px
    letterSpacing: 0px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: 400
    lineHeight: 24px
    letterSpacing: 0px
  body-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: 400
    lineHeight: 20px
    letterSpacing: 0px
  label-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: 400
    lineHeight: 24px
    letterSpacing: 0px
  label-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: 400
    lineHeight: 20px
    letterSpacing: 0px
  label-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: 400
    lineHeight: 16px
    letterSpacing: 0.02em
  caption:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: 400
    lineHeight: 16px
    letterSpacing: 0.08em
rounded:
  none: 0px
  sm: 4px
  md: 8px
  lg: 12px
  xl: 16px
  full: 9999px
spacing:
  xs: 8px
  sm: 16px
  md: 24px
  lg: 48px
  xl: 64px
  2xl: 120px
components:
  button-primary:
    backgroundColor: "{colors.accent}"
    textColor: "{colors.on-surface}"
    typography: "{typography.label-md}"
    rounded: "{rounded.md}"
    padding: "8px 16px"
    height: "40px"
  button-primary-hover:
    backgroundColor: "#F2C85E"
    textColor: "{colors.on-surface}"
    rounded: "{rounded.md}"
  button-secondary:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    typography: "{typography.label-md}"
    rounded: "{rounded.md}"
    padding: "8px 16px"
    height: "40px"
  button-secondary-hover:
    backgroundColor: "{colors.muted-surface}"
    textColor: "{colors.on-surface}"
    rounded: "{rounded.md}"
  button-link:
    backgroundColor: "transparent"
    textColor: "{colors.on-surface}"
    typography: "{typography.label-sm}"
    rounded: "{rounded.none}"
    padding: "0px"
  card:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    rounded: "{rounded.lg}"
    padding: "16px"
  input:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    rounded: "{rounded.md}"
    padding: "8px 12px"
  chip:
    backgroundColor: "{colors.muted-surface}"
    textColor: "{colors.on-surface}"
    rounded: "{rounded.full}"
    padding: "4px 10px"
---

# Trupeer Editorial Light

## Overview
Trupeer feels calm, polished, and high-trust, with a subtle editorial tone lifted by a large serif hero and generous whitespace. The experience is aimed at professionals evaluating a modern productivity or knowledge-work tool, so the UI should stay crisp, simple, and highly legible. The emotional balance is warm rather than cold: light cream surfaces, soft gold accents, and restrained contrast create an inviting SaaS presence.

## Colors
- **Primary (#1A1A1A):** A deep ink used for headlines, navigation, primary text, and dark utility icons. It gives the brand its strongest contrast and keeps the interface feeling premium and grounded.
- **Secondary (#6B6B6B):** A mid-gray for supporting copy, secondary nav items, and less prominent metadata. It softens the hierarchy without losing clarity.
- **Tertiary (#B8A98A):** A muted tan used as a warm neutral accent in borders, illustration-adjacent moments, or secondary emphasis. It should stay understated.
- **Neutral (#F7F1E6):** The signature warm cream background that defines the overall atmosphere. It replaces stark white with a softer, more editorial surface.
- **Surface (#FFFFFF):** Clean white panels used for cards, dialogs, and embedded content. It preserves contrast against the warm page background.
- **On-surface (#1A1A1A):** The default readable color on white and pale surfaces. It should be used for labels, buttons, and body copy on cards.
- **Muted-surface (#FFF8ED):** A barely tinted ivory for subtle chips, hover states, and quiet sections that need separation without heavy borders.
- **Border (#E5E7EB):** A light neutral line for pills, cards, and framing the top navigation. Borders are more important than shadows in this system.
- **Accent (#F7D27B):** The soft yellow-gold used for the strongest calls to action. It is bright enough to draw the eye, but intentionally not saturated.
- **Error (#D64545):** Reserved for destructive states, validation, and alerts. It should remain rare and highly legible.
- **Success (#2E7D5B):** A restrained green for confirmation states, status dots, and positive feedback.

## Typography
The type system combines a distinctive serif display face with a clean sans-serif interface stack. `headline-display` uses Kalice Regular for the largest hero messaging, creating the brand’s editorial personality; the long, airy letterforms and negative tracking make the main headline feel refined. Supporting headings use Stack Sans Headline in regular weight, while body and labels use Inter for consistency, readability, and a modern SaaS feel.

Headlines are intentionally light in weight, not heavy or shouting. Use the serif display only where the page needs emotional pull, then switch to sans-serif for subheads, navigation, controls, and explanatory copy. Labels and small UI text should stay compact, with slightly increased letter spacing only for caption-like content such as trust notes or all-caps microcopy.

## Layout
The page uses a centered, fixed-max-width structure with large outer margins and substantial vertical breathing room. Sections are separated by generous gaps rather than hard dividers, which reinforces the premium, uncluttered feel. The rhythm is spacious: `xs` for tight internal alignment, `sm` and `md` for standard UI groupings, and `lg` to `2xl` for hero-to-content transitions and section breaks.

Navigation, hero, and embedded media are all horizontally centered and visually balanced. Cards and media containers should favor wide aspect ratios and large internal padding, with content aligned in a simple column. Avoid dense multi-column layouts unless there is a strong functional reason; the brand prefers clear focal areas over information-heavy grids.

## Elevation & Depth
The system is intentionally flat. Depth comes from contrast, whitespace, borders, and layered content rather than shadows. Cards and embedded frames rely on subtle outlines and tonal separation, while the bright accent button and dark text establish hierarchy more effectively than elevation effects.

Use `border` for quiet framing and `surface` blocks for content containment. If a floating feel is needed, prefer a slightly tinted background or a stacked panel arrangement instead of box shadows. Shadows should remain absent unless a product-specific interaction truly requires them.

## Shapes
The shape language is soft but disciplined. Interactive controls use small radii around `4px` to `8px`, which keeps the interface crisp and businesslike. Larger containers may expand to `12px` or `16px`, especially for feature cards and media frames, but the overall impression should still be lightly rounded rather than bubbly.

Pills and status chips can use `full` radius for a refined capsule shape. Avoid exaggerated corner rounding on buttons or cards; the design should feel controlled, not playful.

## Components
**Buttons:** Primary buttons use the `button-primary` token: a warm gold fill, dark text, `rounded.md`, and compact `8px 16px` padding. They should feel prominent but not loud. Hover states can deepen or slightly warm the gold via `button-primary-hover`. Secondary buttons use `button-secondary` with a white surface and a thin neutral border; they are quieter actions like “Book a Demo.” Link buttons should remain minimal, with no border or fill, and are best for tertiary actions such as inline navigation.

**Cards:** Cards use `card` with white backgrounds, `border`-like separation, `rounded.lg`, and `16px` padding. They should frame content cleanly without heavy shadowing. Embedded media containers may add an outer cream or warm neutral surround, but the inner content area should still feel crisp and well bounded.

**Inputs:** Inputs should be simple and high-contrast, with white backgrounds, subtle borders, `rounded.md`, and moderate padding. Focus states should be visible through border or ring treatment, not through dramatic color changes. Keep placeholder text subdued and maintain strong readability for user-entered values.

**Chips:** Chips and small tags should use a muted warm surface, dark text, and `rounded.full`. They are best for status, counts, or language/metadata labels. Keep them compact and avoid bright fills unless they represent a primary status.

**Navigation:** The top nav should be lightweight and enclosed by a soft border with a rounded container. Links are neutral by default, with subtle emphasis for the active or primary destination. Dropdown indicators should be understated and monochrome.

**Media frames:** Large feature media should sit inside a wide, softly rounded container with a light border and a warm background surround. The frame should feel curated and editorial, not heavily engineered.

## Do's and Don'ts
- Do keep layouts centered, airy, and easy to scan.
- Do use the serif headline face for the main hero only, then rely on Inter for interface text.
- Do keep button padding compact and corner radii subtle.
- Do prefer borders and whitespace over shadows for separation.
- Do reserve the gold accent for the most important CTA.
- Don't introduce vivid saturated colors that break the warm neutral palette.
- Don't use heavy shadows, glassmorphism, or aggressive gradients.
- Don't make corners overly pill-shaped except for chips and small status badges.