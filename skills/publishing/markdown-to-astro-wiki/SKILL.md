---
name: markdown-to-astro-wiki
description: Transform markdown documentation folders into beautiful Astro-based wikis with Apple iOS26-style glassmorphism design. Use when the user has a folder of .md files and wants to generate a polished wiki/documentation site with dark/light mode support, readable typography, and modern frosted-glass aesthetics. Triggers on requests involving markdown-to-wiki conversion, documentation site generation, Astro wiki creation, or glassmorphism documentation themes.
---

## Execution Context

> **This skill runs AFTER wiki-doc-generator, not as part of the bm launch pipeline.**
> It converts wiki markdown pages into a glassmorphism Astro site.
> Use `process-markdown.sh --images <generated-dir>` to include visual assets alongside markdown.
> Always run `init-astro-wiki.sh` first to scaffold the Astro project.

# Markdown to Astro Wiki Generator

Transform any folder of markdown documentation into a stunning glassmorphism-styled wiki powered by Astro and Bun.

## Workflow Overview

1. **Scan** - Analyze the markdown folder structure and content
2. **Structure** - Generate navigation hierarchy and content collections
3. **Style** - Apply iOS26 glassmorphism design system
4. **Build** - Create complete Astro project with Bun

## Step 1: Scan Documentation

Analyze the user's markdown folder to understand the structure:

```bash
# List all markdown files recursively
find /path/to/docs -name "*.md" -type f | head -50

# Check folder depth and organization
find /path/to/docs -type d | head -20
```

Extract from each markdown file:
- Title (first `# ` heading or filename)
- Description (first paragraph or frontmatter)
- Category (parent folder name)
- Order (numeric prefix if present, e.g., `01-introduction.md`)

## Step 2: Initialize Astro Project

Run the initialization script to scaffold the project:

```bash
cd /home/claude
./scripts/init-astro-wiki.sh <project-name>
```

The script creates:
- Astro project with Bun
- Content collections configuration
- Glassmorphism component library
- Theme toggle system
- Navigation components

## Step 3: Process Markdown Files

For each markdown file, create corresponding content:

```typescript
// Content collection schema (src/content/config.ts)
import { defineCollection, z } from 'astro:content';

const docs = defineCollection({
  type: 'content',
  schema: z.object({
    title: z.string(),
    description: z.string().optional(),
    category: z.string().optional(),
    order: z.number().optional(),
    icon: z.string().optional(),
  }),
});

export const collections = { docs };
```

Copy markdown files to `src/content/docs/` preserving folder structure. Add frontmatter if missing.

## Step 4: Apply Glassmorphism Design System

The design system follows iOS26 glassmorphism principles from `references/glassmorphism-system.md`:

### Core Visual Properties

```css
/* Glass Card Base */
.glass-card {
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 24px;
  box-shadow: 
    0 8px 32px rgba(0, 0, 0, 0.12),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
}

/* Dark Mode Glass */
[data-theme="dark"] .glass-card {
  background: rgba(30, 30, 35, 0.6);
  border-color: rgba(255, 255, 255, 0.08);
}

/* Light Mode Glass */
[data-theme="light"] .glass-card {
  background: rgba(255, 255, 255, 0.72);
  border-color: rgba(0, 0, 0, 0.06);
}
```

### Typography System

Use SF Pro Display characteristics with system font fallbacks:

```css
:root {
  /* Font Stack - Apple-inspired */
  --font-display: "SF Pro Display", -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif;
  --font-text: "SF Pro Text", -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif;
  --font-mono: "SF Mono", "Fira Code", "JetBrains Mono", monospace;
  
  /* Type Scale - Optimal Readability */
  --text-xs: 0.75rem;    /* 12px */
  --text-sm: 0.875rem;   /* 14px */
  --text-base: 1rem;     /* 16px - body */
  --text-lg: 1.125rem;   /* 18px */
  --text-xl: 1.25rem;    /* 20px */
  --text-2xl: 1.5rem;    /* 24px */
  --text-3xl: 1.875rem;  /* 30px */
  --text-4xl: 2.25rem;   /* 36px */
  
  /* Line Heights */
  --leading-tight: 1.25;
  --leading-normal: 1.5;
  --leading-relaxed: 1.75;
  
  /* Letter Spacing */
  --tracking-tight: -0.02em;
  --tracking-normal: 0;
  --tracking-wide: 0.02em;
}

/* Body Text - Optimized for Reading */
body {
  font-family: var(--font-text);
  font-size: var(--text-base);
  line-height: var(--leading-relaxed);
  letter-spacing: var(--tracking-normal);
  font-feature-settings: "kern" 1, "liga" 1;
  text-rendering: optimizeLegibility;
  -webkit-font-smoothing: antialiased;
}

/* Headings */
h1, h2, h3, h4 {
  font-family: var(--font-display);
  font-weight: 600;
  letter-spacing: var(--tracking-tight);
  line-height: var(--leading-tight);
}
```

### Color System

```css
:root {
  /* Light Theme */
  --color-bg-primary: #f5f5f7;
  --color-bg-secondary: #ffffff;
  --color-bg-tertiary: rgba(0, 0, 0, 0.03);
  
  --color-text-primary: #1d1d1f;
  --color-text-secondary: #6e6e73;
  --color-text-tertiary: #86868b;
  
  --color-accent: #0071e3;
  --color-accent-hover: #0077ed;
  
  --color-border: rgba(0, 0, 0, 0.08);
  --color-divider: rgba(0, 0, 0, 0.05);
}

[data-theme="dark"] {
  --color-bg-primary: #000000;
  --color-bg-secondary: #1c1c1e;
  --color-bg-tertiary: rgba(255, 255, 255, 0.05);
  
  --color-text-primary: #f5f5f7;
  --color-text-secondary: #a1a1a6;
  --color-text-tertiary: #6e6e73;
  
  --color-accent: #2997ff;
  --color-accent-hover: #4bb3ff;
  
  --color-border: rgba(255, 255, 255, 0.1);
  --color-divider: rgba(255, 255, 255, 0.06);
}
```

## Step 5: Generate Components

Create these core components in `src/components/`:

1. **GlassCard.astro** - Container with frosted glass effect
2. **Navigation.astro** - Sidebar with collapsible categories
3. **ThemeToggle.astro** - Dark/light mode switcher with smooth transition
4. **SearchModal.astro** - Command-K search with glass overlay
5. **TableOfContents.astro** - Article TOC with scroll spy
6. **CodeBlock.astro** - Syntax-highlighted code with copy button
7. **Breadcrumb.astro** - Navigation breadcrumb trail

See `scripts/init-astro-wiki.sh` for complete component implementations (inline via heredocs).

## Step 6: Create Layouts

### Base Layout (`src/layouts/BaseLayout.astro`)

```astro
---
import ThemeToggle from '../components/ThemeToggle.astro';
import Navigation from '../components/Navigation.astro';
import '../styles/global.css';

interface Props {
  title: string;
  description?: string;
}

const { title, description } = Astro.props;
---
<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title}</title>
  <meta name="description" content={description} />
  <script is:inline>
    const theme = localStorage.getItem('theme') || 
      (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    document.documentElement.setAttribute('data-theme', theme);
  </script>
</head>
<body>
  <div class="layout">
    <aside class="sidebar glass-panel">
      <Navigation />
    </aside>
    <main class="content">
      <slot />
    </main>
  </div>
  <ThemeToggle />
</body>
</html>
```

### Doc Layout (`src/layouts/DocLayout.astro`)

Extends BaseLayout with:
- Table of contents
- Breadcrumbs
- Previous/next navigation
- Reading time estimate

## Step 7: Build and Output

```bash
cd <project-name>
bun run build
```

Final structure:
```
project-name/
├── astro.config.mjs
├── bun.lockb
├── package.json
├── public/
│   └── fonts/
├── src/
│   ├── components/
│   │   ├── GlassCard.astro
│   │   ├── Navigation.astro
│   │   ├── ThemeToggle.astro
│   │   ├── SearchModal.astro
│   │   ├── TableOfContents.astro
│   │   ├── CodeBlock.astro
│   │   └── Breadcrumb.astro
│   ├── content/
│   │   ├── config.ts
│   │   └── docs/
│   │       └── [processed markdown files]
│   ├── layouts/
│   │   ├── BaseLayout.astro
│   │   └── DocLayout.astro
│   ├── pages/
│   │   ├── index.astro
│   │   └── docs/
│   │       └── [...slug].astro
│   └── styles/
│       ├── global.css
│       └── glassmorphism.css
└── dist/
    └── [static output]
```

## Quick Start Example

```bash
# User has docs in ~/my-project/docs/
# Run the full conversion:

# 1. Initialize
./scripts/init-astro-wiki.sh my-wiki

# 2. Process markdown
./scripts/process-markdown.sh ~/my-project/docs ./my-wiki/src/content/docs

# 3. Build
cd my-wiki && bun run build
```

## Design Principles

1. **Depth through Layers** - Use z-index, shadows, and blur to create visual hierarchy
2. **Subtle Motion** - Smooth transitions (200-300ms) on hover and state changes
3. **Readable Contrast** - WCAG AA minimum, prefer AAA for body text
4. **Responsive Glass** - Adjust blur and transparency for performance on mobile
5. **System Integration** - Respect prefers-color-scheme and prefers-reduced-motion

## Resources

- `scripts/init-astro-wiki.sh` - Project scaffolding
- `scripts/process-markdown.sh` - Markdown processing and frontmatter injection
- `references/glassmorphism-system.md` - Complete design system documentation
- `assets/components/` - Ready-to-use Astro components
- `assets/styles/` - CSS design tokens and utilities
