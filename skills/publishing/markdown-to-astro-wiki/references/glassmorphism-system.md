# iOS26 Glassmorphism Design System

Complete design system reference for creating Apple-inspired glassmorphism interfaces.

## Core Principles

### The Glass Effect

Glassmorphism creates depth through translucent surfaces that reveal underlying content while maintaining visual hierarchy. Apple's iOS26 approach emphasizes:

- **Clarity** - Content remains readable despite transparency
- **Depth** - Layered surfaces create spatial relationships
- **Elegance** - Subtle effects that enhance rather than distract
- **Performance** - Optimized blur that runs smoothly on all devices

### Visual Hierarchy

```
┌─────────────────────────────────────┐
│  Background Layer (z: 0)            │
│  - Gradient mesh or solid color     │
│  - Optional subtle pattern/texture  │
├─────────────────────────────────────┤
│  Content Layer (z: 10)              │
│  - Main glass panels                │
│  - Primary navigation               │
├─────────────────────────────────────┤
│  Elevated Layer (z: 20)             │
│  - Modals, dropdowns, tooltips      │
│  - Higher blur, stronger border     │
├─────────────────────────────────────┤
│  Overlay Layer (z: 30)              │
│  - Full-screen overlays             │
│  - Search modal, command palette    │
└─────────────────────────────────────┘
```

## Glass Properties

### Base Glass Variables

```css
:root {
  /* Blur Intensities */
  --blur-xs: 8px;
  --blur-sm: 12px;
  --blur-md: 20px;
  --blur-lg: 32px;
  --blur-xl: 48px;
  
  /* Saturation - Enhances colors behind glass */
  --saturate-subtle: 120%;
  --saturate-normal: 180%;
  --saturate-vivid: 200%;
  
  /* Glass Opacity Scales */
  --glass-opacity-subtle: 0.04;
  --glass-opacity-light: 0.08;
  --glass-opacity-medium: 0.12;
  --glass-opacity-strong: 0.18;
  --glass-opacity-solid: 0.72;
  
  /* Border Opacity */
  --border-opacity-subtle: 0.06;
  --border-opacity-light: 0.1;
  --border-opacity-medium: 0.15;
  --border-opacity-strong: 0.2;
  
  /* Shadow Scales */
  --shadow-glass-sm: 0 2px 8px rgba(0, 0, 0, 0.08);
  --shadow-glass-md: 0 8px 32px rgba(0, 0, 0, 0.12);
  --shadow-glass-lg: 0 16px 48px rgba(0, 0, 0, 0.16);
  --shadow-glass-xl: 0 24px 64px rgba(0, 0, 0, 0.2);
  
  /* Inset Highlights */
  --highlight-top: inset 0 1px 0 rgba(255, 255, 255, 0.1);
  --highlight-subtle: inset 0 1px 0 rgba(255, 255, 255, 0.05);
}
```

### Glass Card Variants

```css
/* Subtle Glass - Minimal presence */
.glass-subtle {
  background: rgba(255, 255, 255, var(--glass-opacity-subtle));
  backdrop-filter: blur(var(--blur-sm)) saturate(var(--saturate-subtle));
  border: 1px solid rgba(255, 255, 255, var(--border-opacity-subtle));
}

/* Light Glass - Default cards */
.glass-light {
  background: rgba(255, 255, 255, var(--glass-opacity-light));
  backdrop-filter: blur(var(--blur-md)) saturate(var(--saturate-normal));
  border: 1px solid rgba(255, 255, 255, var(--border-opacity-light));
  box-shadow: var(--shadow-glass-sm), var(--highlight-top);
}

/* Medium Glass - Elevated elements */
.glass-medium {
  background: rgba(255, 255, 255, var(--glass-opacity-medium));
  backdrop-filter: blur(var(--blur-md)) saturate(var(--saturate-normal));
  border: 1px solid rgba(255, 255, 255, var(--border-opacity-medium));
  box-shadow: var(--shadow-glass-md), var(--highlight-top);
}

/* Strong Glass - Prominent panels */
.glass-strong {
  background: rgba(255, 255, 255, var(--glass-opacity-strong));
  backdrop-filter: blur(var(--blur-lg)) saturate(var(--saturate-vivid));
  border: 1px solid rgba(255, 255, 255, var(--border-opacity-strong));
  box-shadow: var(--shadow-glass-lg), var(--highlight-top);
}

/* Solid Glass - Maximum readability */
.glass-solid {
  background: rgba(255, 255, 255, var(--glass-opacity-solid));
  backdrop-filter: blur(var(--blur-xl)) saturate(var(--saturate-vivid));
  border: 1px solid rgba(255, 255, 255, var(--border-opacity-medium));
  box-shadow: var(--shadow-glass-md);
}
```

### Dark Mode Adaptations

```css
[data-theme="dark"] {
  --glass-base-color: 30, 30, 35;
  
  .glass-subtle {
    background: rgba(var(--glass-base-color), 0.3);
    border-color: rgba(255, 255, 255, 0.04);
  }
  
  .glass-light {
    background: rgba(var(--glass-base-color), 0.4);
    border-color: rgba(255, 255, 255, 0.06);
  }
  
  .glass-medium {
    background: rgba(var(--glass-base-color), 0.5);
    border-color: rgba(255, 255, 255, 0.08);
  }
  
  .glass-strong {
    background: rgba(var(--glass-base-color), 0.6);
    border-color: rgba(255, 255, 255, 0.1);
  }
  
  .glass-solid {
    background: rgba(var(--glass-base-color), 0.85);
    border-color: rgba(255, 255, 255, 0.08);
  }
}
```

## Typography for Glass

### Readability on Translucent Surfaces

```css
/* Text needs higher contrast on glass */
.glass-card {
  /* Light mode - darker text */
  color: rgba(0, 0, 0, 0.85);
}

[data-theme="dark"] .glass-card {
  /* Dark mode - bright text */
  color: rgba(255, 255, 255, 0.92);
}

/* Secondary text */
.text-secondary {
  color: rgba(0, 0, 0, 0.6);
}

[data-theme="dark"] .text-secondary {
  color: rgba(255, 255, 255, 0.65);
}

/* Tertiary/muted text */
.text-muted {
  color: rgba(0, 0, 0, 0.45);
}

[data-theme="dark"] .text-muted {
  color: rgba(255, 255, 255, 0.45);
}
```

### Type Scale with Optical Adjustments

```css
/* Headings get tighter tracking at larger sizes */
h1 {
  font-size: 2.5rem;
  font-weight: 700;
  letter-spacing: -0.03em;
  line-height: 1.1;
}

h2 {
  font-size: 2rem;
  font-weight: 600;
  letter-spacing: -0.025em;
  line-height: 1.2;
}

h3 {
  font-size: 1.5rem;
  font-weight: 600;
  letter-spacing: -0.02em;
  line-height: 1.25;
}

h4 {
  font-size: 1.25rem;
  font-weight: 600;
  letter-spacing: -0.015em;
  line-height: 1.3;
}

/* Body text optimized for long-form reading */
.prose {
  font-size: 1.0625rem; /* 17px - Apple's preferred */
  line-height: 1.7;
  letter-spacing: 0.01em;
}

.prose p {
  margin-bottom: 1.5em;
}

/* Code blocks */
code, pre {
  font-family: var(--font-mono);
  font-size: 0.9375rem; /* 15px */
  line-height: 1.6;
}

pre {
  padding: 1.25rem 1.5rem;
  border-radius: 12px;
  overflow-x: auto;
}
```

## Color Palette

### Semantic Colors

```css
:root {
  /* Success */
  --color-success: #34c759;
  --color-success-bg: rgba(52, 199, 89, 0.12);
  --color-success-border: rgba(52, 199, 89, 0.3);
  
  /* Warning */
  --color-warning: #ff9f0a;
  --color-warning-bg: rgba(255, 159, 10, 0.12);
  --color-warning-border: rgba(255, 159, 10, 0.3);
  
  /* Error */
  --color-error: #ff3b30;
  --color-error-bg: rgba(255, 59, 48, 0.12);
  --color-error-border: rgba(255, 59, 48, 0.3);
  
  /* Info */
  --color-info: #5ac8fa;
  --color-info-bg: rgba(90, 200, 250, 0.12);
  --color-info-border: rgba(90, 200, 250, 0.3);
}

[data-theme="dark"] {
  --color-success: #30d158;
  --color-warning: #ffd60a;
  --color-error: #ff453a;
  --color-info: #64d2ff;
}
```

### Accent Color System

```css
:root {
  /* Primary accent - Blue */
  --accent-h: 211;
  --accent-s: 100%;
  --accent-l: 45%;
  
  --color-accent: hsl(var(--accent-h), var(--accent-s), var(--accent-l));
  --color-accent-hover: hsl(var(--accent-h), var(--accent-s), calc(var(--accent-l) + 5%));
  --color-accent-active: hsl(var(--accent-h), var(--accent-s), calc(var(--accent-l) - 5%));
  --color-accent-subtle: hsla(var(--accent-h), var(--accent-s), var(--accent-l), 0.12);
}

[data-theme="dark"] {
  --accent-l: 55%;
}
```

## Border Radius Scale

```css
:root {
  --radius-xs: 4px;
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 16px;
  --radius-xl: 20px;
  --radius-2xl: 24px;
  --radius-3xl: 32px;
  --radius-full: 9999px;
}

/* Contextual usage */
.button { border-radius: var(--radius-md); }
.card { border-radius: var(--radius-xl); }
.modal { border-radius: var(--radius-2xl); }
.avatar { border-radius: var(--radius-full); }
.code-block { border-radius: var(--radius-lg); }
.input { border-radius: var(--radius-md); }
.pill { border-radius: var(--radius-full); }
```

## Spacing System

```css
:root {
  --space-1: 0.25rem;  /* 4px */
  --space-2: 0.5rem;   /* 8px */
  --space-3: 0.75rem;  /* 12px */
  --space-4: 1rem;     /* 16px */
  --space-5: 1.25rem;  /* 20px */
  --space-6: 1.5rem;   /* 24px */
  --space-8: 2rem;     /* 32px */
  --space-10: 2.5rem;  /* 40px */
  --space-12: 3rem;    /* 48px */
  --space-16: 4rem;    /* 64px */
  --space-20: 5rem;    /* 80px */
  --space-24: 6rem;    /* 96px */
}
```

## Animation & Transitions

### Timing Functions

```css
:root {
  /* Apple-style easings */
  --ease-out-expo: cubic-bezier(0.16, 1, 0.3, 1);
  --ease-out-quart: cubic-bezier(0.25, 1, 0.5, 1);
  --ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);
  --ease-bounce: cubic-bezier(0.34, 1.56, 0.64, 1);
  
  /* Duration scale */
  --duration-fast: 150ms;
  --duration-normal: 200ms;
  --duration-slow: 300ms;
  --duration-slower: 400ms;
}
```

### Standard Transitions

```css
/* Interactive elements */
.interactive {
  transition: 
    background-color var(--duration-fast) var(--ease-out-quart),
    border-color var(--duration-fast) var(--ease-out-quart),
    transform var(--duration-normal) var(--ease-out-expo),
    box-shadow var(--duration-normal) var(--ease-out-quart);
}

/* Glass panels */
.glass-panel {
  transition:
    background-color var(--duration-slow) var(--ease-in-out),
    backdrop-filter var(--duration-slow) var(--ease-in-out);
}

/* Theme transitions */
html {
  transition:
    background-color var(--duration-slower) var(--ease-in-out),
    color var(--duration-slow) var(--ease-in-out);
}
```

### Reduced Motion

```css
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

## Component Patterns

### Glass Navigation Sidebar

```css
.sidebar {
  position: fixed;
  left: 0;
  top: 0;
  bottom: 0;
  width: 280px;
  background: rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(24px) saturate(180%);
  border-right: 1px solid rgba(255, 255, 255, 0.08);
  padding: var(--space-6);
  overflow-y: auto;
}

[data-theme="dark"] .sidebar {
  background: rgba(20, 20, 22, 0.7);
  border-color: rgba(255, 255, 255, 0.06);
}

.nav-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  color: var(--color-text-secondary);
  transition: all var(--duration-fast) var(--ease-out-quart);
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.08);
  color: var(--color-text-primary);
}

.nav-item.active {
  background: rgba(255, 255, 255, 0.12);
  color: var(--color-accent);
}
```

### Theme Toggle Button

```css
.theme-toggle {
  position: fixed;
  bottom: var(--space-6);
  right: var(--space-6);
  width: 48px;
  height: 48px;
  border-radius: var(--radius-full);
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.15);
  box-shadow: var(--shadow-glass-md);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--duration-normal) var(--ease-out-expo);
}

.theme-toggle:hover {
  transform: scale(1.05);
  background: rgba(255, 255, 255, 0.15);
}

.theme-toggle:active {
  transform: scale(0.95);
}

/* Icon rotation on theme change */
.theme-toggle svg {
  transition: transform var(--duration-slow) var(--ease-out-expo);
}

[data-theme="dark"] .theme-toggle svg {
  transform: rotate(180deg);
}
```

### Search Modal Overlay

```css
.search-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding-top: 15vh;
  z-index: 100;
  opacity: 0;
  visibility: hidden;
  transition: all var(--duration-normal) var(--ease-out-quart);
}

.search-overlay.open {
  opacity: 1;
  visibility: visible;
}

.search-modal {
  width: 100%;
  max-width: 640px;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(32px) saturate(200%);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: var(--radius-2xl);
  box-shadow: var(--shadow-glass-xl);
  overflow: hidden;
  transform: scale(0.96) translateY(-10px);
  transition: transform var(--duration-normal) var(--ease-out-expo);
}

.search-overlay.open .search-modal {
  transform: scale(1) translateY(0);
}

[data-theme="dark"] .search-modal {
  background: rgba(40, 40, 44, 0.9);
  border-color: rgba(255, 255, 255, 0.1);
}
```

### Code Block with Glass

```css
.code-block {
  position: relative;
  background: rgba(0, 0, 0, 0.04);
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

[data-theme="dark"] .code-block {
  background: rgba(0, 0, 0, 0.3);
  border-color: rgba(255, 255, 255, 0.06);
}

.code-block-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-3) var(--space-4);
  background: rgba(0, 0, 0, 0.02);
  border-bottom: 1px solid rgba(0, 0, 0, 0.04);
}

[data-theme="dark"] .code-block-header {
  background: rgba(255, 255, 255, 0.02);
  border-color: rgba(255, 255, 255, 0.04);
}

.copy-button {
  padding: var(--space-1) var(--space-2);
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--color-text-tertiary);
  font-size: var(--text-xs);
  transition: all var(--duration-fast) var(--ease-out-quart);
}

.copy-button:hover {
  background: rgba(0, 0, 0, 0.05);
  color: var(--color-text-secondary);
}

[data-theme="dark"] .copy-button:hover {
  background: rgba(255, 255, 255, 0.08);
}
```

## Background Treatments

### Gradient Mesh Background

```css
body {
  background-color: var(--color-bg-primary);
  background-image:
    radial-gradient(
      ellipse 80% 50% at 20% 40%,
      rgba(120, 119, 198, 0.15),
      transparent
    ),
    radial-gradient(
      ellipse 60% 50% at 80% 60%,
      rgba(255, 119, 198, 0.1),
      transparent
    ),
    radial-gradient(
      ellipse 50% 80% at 50% 100%,
      rgba(120, 200, 255, 0.12),
      transparent
    );
}

[data-theme="dark"] body {
  background-image:
    radial-gradient(
      ellipse 80% 50% at 20% 40%,
      rgba(100, 80, 180, 0.2),
      transparent
    ),
    radial-gradient(
      ellipse 60% 50% at 80% 60%,
      rgba(180, 80, 140, 0.15),
      transparent
    ),
    radial-gradient(
      ellipse 50% 80% at 50% 100%,
      rgba(60, 120, 200, 0.18),
      transparent
    );
}
```

### Noise Texture Overlay

```css
body::before {
  content: "";
  position: fixed;
  inset: 0;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E");
  opacity: 0.03;
  pointer-events: none;
  z-index: 1000;
}

[data-theme="dark"] body::before {
  opacity: 0.04;
}
```

## Responsive Considerations

### Reduce Blur on Mobile

```css
@media (max-width: 768px) {
  .glass-card {
    /* Reduce blur for performance */
    backdrop-filter: blur(12px) saturate(150%);
  }
  
  .sidebar {
    backdrop-filter: blur(16px) saturate(160%);
  }
}

/* Further reduce for low-end devices */
@media (max-width: 768px) and (prefers-reduced-motion: reduce) {
  .glass-card,
  .sidebar {
    backdrop-filter: none;
    background: var(--color-bg-secondary);
  }
}
```

## Accessibility Checklist

1. **Contrast Ratios**
   - Body text: minimum 4.5:1 (WCAG AA)
   - Large text (18px+): minimum 3:1
   - Interactive elements: minimum 3:1 against adjacent colors

2. **Focus States**
   - Visible focus ring on all interactive elements
   - Focus ring must have 3:1 contrast against background

3. **Motion**
   - Respect `prefers-reduced-motion`
   - Provide alternative static states

4. **Color Independence**
   - Information conveyed by color also conveyed by text/icon
   - Links distinguishable without relying on color alone
