---
name: Kinetic Dark
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
  on-surface-variant: '#c2c6d6'
  inverse-surface: '#e5e2e1'
  inverse-on-surface: '#313030'
  outline: '#8c909f'
  outline-variant: '#424754'
  surface-tint: '#adc6ff'
  primary: '#adc6ff'
  on-primary: '#002e6a'
  primary-container: '#4d8eff'
  on-primary-container: '#00285d'
  inverse-primary: '#005ac2'
  secondary: '#4edea3'
  on-secondary: '#003824'
  secondary-container: '#00a572'
  on-secondary-container: '#00311f'
  tertiary: '#ffb786'
  on-tertiary: '#502400'
  tertiary-container: '#df7412'
  on-tertiary-container: '#461f00'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#d8e2ff'
  primary-fixed-dim: '#adc6ff'
  on-primary-fixed: '#001a42'
  on-primary-fixed-variant: '#004395'
  secondary-fixed: '#6ffbbe'
  secondary-fixed-dim: '#4edea3'
  on-secondary-fixed: '#002113'
  on-secondary-fixed-variant: '#005236'
  tertiary-fixed: '#ffdcc6'
  tertiary-fixed-dim: '#ffb786'
  on-tertiary-fixed: '#311400'
  on-tertiary-fixed-variant: '#723600'
  background: '#131313'
  on-background: '#e5e2e1'
  surface-variant: '#353534'
typography:
  display-time:
    fontFamily: Space Grotesk
    fontSize: 48px
    fontWeight: '700'
    lineHeight: '1.1'
    letterSpacing: -0.02em
  headline-panel:
    fontFamily: Space Grotesk
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 24px
    letterSpacing: 0.01em
  body-main:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  body-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
  label-caps:
    fontFamily: Space Grotesk
    fontSize: 10px
    fontWeight: '700'
    lineHeight: 12px
    letterSpacing: 0.08em
  data-tabular:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: -0.01em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  unit: 4px
  container-padding: 24px
  element-gap: 12px
  panel-width-fixed: 360px
  floating-margin: 16px
---

## Brand & Style

The design system is engineered for high-performance geospatial analysis and transit visualization. It prioritizes the "Map as the Interface" philosophy, where the background serves as the primary canvas and UI components function as unobtrusive, high-utility overlays. 

The aesthetic is a fusion of **Minimalism** and **Glassmorphism**. By using deep blacks and charcoals for the base layers, the system creates a high-contrast environment where vibrant data visualizations—isochrones, heatmaps, and transit lines—become the focal point. The emotional response is one of precision, technological sophistication, and clarity amidst complex data. All interface elements are designed to feel lightweight and ethereal, using translucency to maintain the user's spatial awareness of the map beneath.

## Colors

The palette is anchored by a true black `#0a0a0a` background to eliminate bezel-to-screen friction and maximize the luminosity of data layers. The primary accent is a precision blue, used for interactive states and primary call-to-actions. 

The core of the system is the **Heatmap Spectrum**, a 5-step semantic scale ranging from Success Green to Danger Red. These colors are specifically tuned for high-vibrancy against dark backgrounds, ensuring that isochrone polygons remain legible even when layered or set to low opacities. Neutral tones are strictly cool-greys to maintain a technical, "radar-screen" atmosphere.

## Typography

This design system utilizes a dual-font approach to balance technical character with utilitarian readability. **Space Grotesk** is used for headlines, legends, and data labels to provide a geometric, futuristic feel that aligns with transit engineering. **Inter** is used for all body copy and dense data overlays to ensure maximum legibility at small sizes, particularly when rendered over complex map textures.

Numerical data should always utilize tabular figures to prevent "jitter" when travel times or coordinates update in real-time. For labels on the map itself, a subtle 1px black text-shadow or halo is required to ensure contrast against fluctuating heatmap colors.

## Layout & Spacing

The layout follows a **Floating Overlay** model. There is no traditional "sidebar" that pushes map content; instead, all UI elements float above the map container with consistent margins from the viewport edges. 

The primary control panel is fixed to a 360px width, typically positioned on the left, while secondary legends and map controls float in the corners. Spacing follows a tight 4px grid to maintain a dense, information-rich environment. Elements are grouped using generous internal padding (24px) but separated by smaller external gaps (12px) to create a cohesive "instrument cluster" feel.

## Elevation & Depth

Depth is achieved through **Glassmorphism** rather than traditional shadows. This allows the user to see the "flow" of the map underneath the interface.

1.  **Base Layer:** The map tiles (Dark Mode).
2.  **Mid Layer:** Semi-transparent isochrones and data visualizations.
3.  **Top Layer:** UI Panels. These use a `backdrop-filter: blur(12px)` and a background color of `rgba(23, 23, 23, 0.7)`. 
4.  **Interaction Layer:** Hover states and active selections use a subtle white inner-stroke (0.5px) to simulate a "lit" edge, increasing the perception of physical presence without adding bulk.

Shadows, if used, are extremely diffused (30px blur) and utilize the primary blue accent color at 5% opacity to create a subtle "glow" around active panels.

## Shapes

The design system employs a **Rounded** (Level 2) shape language. This softens the technical aesthetic, making the interface feel more like a modern consumer tool than a legacy GIS application. 

Standard components (buttons, input fields) use a 0.5rem (8px) radius. Larger floating panels use a more pronounced 1.5rem (24px) radius to emphasize their "floating" nature. Data-heavy items, like legend color swatches, remain sharp or slightly rounded (2px) to maintain a precise, scientific appearance.

## Components

-   **Floating Search Bar:** A prominent pill-shaped input centered at the top or top-left. It features a heavy backdrop blur and a high-contrast white text input.
-   **Glassmorphic Side Panels:** These house the primary filters and data controls. They should have a subtle 1px border (`rgba(255, 255, 255, 0.1)`) to define their boundaries against the map.
-   **Travel-Time Legends:** Vertical or horizontal strips using the Heatmap Spectrum. Labels are in `label-caps` typography, placed strictly outside the color bar or as minimal overlays.
-   **Action Buttons:** Primary buttons are solid `#3b82f6` with white text. Secondary buttons are transparent with a 1px white border and blur background.
-   **Data Chips:** Small, semi-transparent capsules used to show active filters (e.g., "Walking", "15 min"). These include a "close" icon for quick removal.
-   **Time Sliders:** Custom-styled range inputs with a blue glowing thumb and a translucent track. The current value is displayed in `display-time` typography as the user drags.