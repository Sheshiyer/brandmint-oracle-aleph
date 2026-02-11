#!/bin/bash
# init-astro-wiki.sh - Initialize a glassmorphism-styled Astro wiki project
# Usage: ./init-astro-wiki.sh <project-name>
#
# Creates a complete Astro project with:
#   - iOS26 glassmorphism design system
#   - Dark/light theme toggle
#   - Content collections for markdown docs
#   - Navigation sidebar with collapsible categories
#   - Table of contents with scroll spy
#   - Command-K search modal
#   - Responsive layout

set -e

PROJECT_NAME="${1:?Usage: ./init-astro-wiki.sh <project-name>}"

echo "🚀 Initializing Astro Wiki: $PROJECT_NAME"
echo ""

# Create project directory structure
mkdir -p "$PROJECT_NAME"
cd "$PROJECT_NAME"

mkdir -p src/components
mkdir -p src/content/docs
mkdir -p src/layouts
mkdir -p src/pages/docs
mkdir -p src/styles
mkdir -p public/fonts

echo "📁 Created project structure"

# Create package.json
cat > package.json << 'EOF'
{
  "name": "astro-wiki",
  "type": "module",
  "version": "1.0.0",
  "scripts": {
    "dev": "astro dev",
    "start": "astro dev",
    "build": "astro build",
    "preview": "astro preview",
    "astro": "astro"
  },
  "dependencies": {
    "astro": "^4.0.0",
    "@astrojs/mdx": "^3.0.0"
  }
}
EOF

echo "📦 Created package.json"

# Create astro.config.mjs
cat > astro.config.mjs << 'EOF'
import { defineConfig } from 'astro/config';
import mdx from '@astrojs/mdx';

export default defineConfig({
  integrations: [mdx()],
  markdown: {
    shikiConfig: {
      theme: 'github-dark-dimmed',
      wrap: true,
    },
  },
});
EOF

echo "⚙️  Created astro.config.mjs"

# Create tsconfig.json
cat > tsconfig.json << 'EOF'
{
  "extends": "astro/tsconfigs/strict"
}
EOF

# Create content collections config
cat > src/content/config.ts << 'EOF'
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
EOF

echo "📚 Created content collections config"

# Create global.css with full design system
cat > src/styles/global.css << 'EOF'
/* global.css - iOS26 Glassmorphism Design System */

/* ===========================================
   CSS Custom Properties
   =========================================== */

:root {
  /* Font Stack - Apple-inspired */
  --font-display: "SF Pro Display", -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif;
  --font-text: "SF Pro Text", -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif;
  --font-mono: "SF Mono", "Fira Code", "JetBrains Mono", monospace;

  /* Type Scale */
  --text-xs: 0.75rem;
  --text-sm: 0.875rem;
  --text-base: 1rem;
  --text-lg: 1.125rem;
  --text-xl: 1.25rem;
  --text-2xl: 1.5rem;
  --text-3xl: 1.875rem;
  --text-4xl: 2.25rem;

  /* Line Heights */
  --leading-tight: 1.25;
  --leading-normal: 1.5;
  --leading-relaxed: 1.75;

  /* Letter Spacing */
  --tracking-tight: -0.02em;
  --tracking-normal: 0;
  --tracking-wide: 0.02em;

  /* Spacing */
  --space-1: 0.25rem;
  --space-2: 0.5rem;
  --space-3: 0.75rem;
  --space-4: 1rem;
  --space-5: 1.25rem;
  --space-6: 1.5rem;
  --space-8: 2rem;
  --space-10: 2.5rem;
  --space-12: 3rem;
  --space-16: 4rem;
  --space-20: 5rem;
  --space-24: 6rem;

  /* Border Radius */
  --radius-xs: 4px;
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 16px;
  --radius-xl: 20px;
  --radius-2xl: 24px;
  --radius-3xl: 32px;
  --radius-full: 9999px;

  /* Blur Intensities */
  --blur-xs: 8px;
  --blur-sm: 12px;
  --blur-md: 20px;
  --blur-lg: 32px;
  --blur-xl: 48px;

  /* Shadows */
  --shadow-glass-sm: 0 2px 8px rgba(0, 0, 0, 0.08);
  --shadow-glass-md: 0 8px 32px rgba(0, 0, 0, 0.12);
  --shadow-glass-lg: 0 16px 48px rgba(0, 0, 0, 0.16);
  --shadow-glass-xl: 0 24px 64px rgba(0, 0, 0, 0.2);

  /* Transitions */
  --ease-out-expo: cubic-bezier(0.16, 1, 0.3, 1);
  --ease-out-quart: cubic-bezier(0.25, 1, 0.5, 1);
  --ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);
  --duration-fast: 150ms;
  --duration-normal: 200ms;
  --duration-slow: 300ms;
  --duration-slower: 400ms;

  /* Light Theme Colors */
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

  /* Semantic Colors */
  --color-success: #34c759;
  --color-warning: #ff9f0a;
  --color-error: #ff3b30;
  --color-info: #5ac8fa;
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

  --color-success: #30d158;
  --color-warning: #ffd60a;
  --color-error: #ff453a;
  --color-info: #64d2ff;
}

/* ===========================================
   Base Styles
   =========================================== */

*, *::before, *::after {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

html {
  scroll-behavior: smooth;
  transition:
    background-color var(--duration-slower) var(--ease-in-out),
    color var(--duration-slow) var(--ease-in-out);
}

body {
  font-family: var(--font-text);
  font-size: var(--text-base);
  line-height: var(--leading-relaxed);
  letter-spacing: var(--tracking-normal);
  font-feature-settings: "kern" 1, "liga" 1;
  text-rendering: optimizeLegibility;
  -webkit-font-smoothing: antialiased;
  color: var(--color-text-primary);
  background-color: var(--color-bg-primary);
  background-image:
    radial-gradient(ellipse 80% 50% at 20% 40%, rgba(120, 119, 198, 0.15), transparent),
    radial-gradient(ellipse 60% 50% at 80% 60%, rgba(255, 119, 198, 0.1), transparent),
    radial-gradient(ellipse 50% 80% at 50% 100%, rgba(120, 200, 255, 0.12), transparent);
  min-height: 100vh;
}

[data-theme="dark"] body {
  background-image:
    radial-gradient(ellipse 80% 50% at 20% 40%, rgba(100, 80, 180, 0.2), transparent),
    radial-gradient(ellipse 60% 50% at 80% 60%, rgba(180, 80, 140, 0.15), transparent),
    radial-gradient(ellipse 50% 80% at 50% 100%, rgba(60, 120, 200, 0.18), transparent);
}

/* Noise texture overlay */
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

/* ===========================================
   Typography
   =========================================== */

h1, h2, h3, h4 {
  font-family: var(--font-display);
  font-weight: 600;
  letter-spacing: var(--tracking-tight);
  line-height: var(--leading-tight);
}

h1 { font-size: 2.5rem; font-weight: 700; letter-spacing: -0.03em; line-height: 1.1; }
h2 { font-size: 2rem; letter-spacing: -0.025em; line-height: 1.2; }
h3 { font-size: 1.5rem; letter-spacing: -0.02em; line-height: 1.25; }
h4 { font-size: 1.25rem; letter-spacing: -0.015em; line-height: 1.3; }

a {
  color: var(--color-accent);
  text-decoration: none;
  transition: color var(--duration-fast) var(--ease-out-quart);
}

a:hover {
  color: var(--color-accent-hover);
}

code, pre {
  font-family: var(--font-mono);
  font-size: 0.9375rem;
  line-height: 1.6;
}

pre {
  padding: 1.25rem 1.5rem;
  border-radius: var(--radius-lg);
  overflow-x: auto;
}

/* ===========================================
   Layout
   =========================================== */

.layout {
  display: flex;
  min-height: 100vh;
}

.sidebar {
  position: fixed;
  left: 0;
  top: 0;
  bottom: 0;
  width: 280px;
  padding: var(--space-6);
  overflow-y: auto;
  z-index: 10;
}

.content {
  margin-left: 280px;
  flex: 1;
  padding: var(--space-8) var(--space-10);
  max-width: 900px;
}

/* Glass panel for sidebar */
.glass-panel {
  background: rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(24px) saturate(180%);
  -webkit-backdrop-filter: blur(24px) saturate(180%);
  border-right: 1px solid rgba(255, 255, 255, 0.08);
}

[data-theme="dark"] .glass-panel {
  background: rgba(20, 20, 22, 0.7);
  border-color: rgba(255, 255, 255, 0.06);
}

[data-theme="light"] .glass-panel {
  background: rgba(255, 255, 255, 0.8);
  border-color: rgba(0, 0, 0, 0.06);
}

/* ===========================================
   Prose Styles (Article Content)
   =========================================== */

.prose {
  font-size: 1.0625rem;
  line-height: 1.7;
  letter-spacing: 0.01em;
}

.prose p { margin-bottom: 1.5em; }
.prose h1 { margin: 2em 0 0.75em; }
.prose h2 { margin: 1.75em 0 0.5em; }
.prose h3 { margin: 1.5em 0 0.5em; }
.prose h4 { margin: 1.25em 0 0.5em; }

.prose ul, .prose ol {
  padding-left: 1.5em;
  margin-bottom: 1.5em;
}

.prose li {
  margin-bottom: 0.5em;
}

.prose blockquote {
  border-left: 3px solid var(--color-accent);
  padding-left: var(--space-4);
  color: var(--color-text-secondary);
  font-style: italic;
  margin: 1.5em 0;
}

.prose img {
  max-width: 100%;
  border-radius: var(--radius-lg);
  margin: 1.5em 0;
}

.prose table {
  width: 100%;
  border-collapse: collapse;
  margin: 1.5em 0;
}

.prose th, .prose td {
  padding: var(--space-3) var(--space-4);
  text-align: left;
  border-bottom: 1px solid var(--color-divider);
}

.prose th {
  font-weight: 600;
  color: var(--color-text-primary);
}

/* ===========================================
   Responsive
   =========================================== */

@media (max-width: 768px) {
  .sidebar {
    display: none;
  }

  .content {
    margin-left: 0;
    padding: var(--space-4);
  }
}

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
EOF

echo "🎨 Created global.css with design system"

# Copy glassmorphism utility classes
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"

if [ -f "$SKILL_DIR/assets/styles/glassmorphism.css" ]; then
  cp "$SKILL_DIR/assets/styles/glassmorphism.css" src/styles/glassmorphism.css
  echo "✨ Copied glassmorphism.css utilities"
else
  echo "⚠️  glassmorphism.css not found at $SKILL_DIR/assets/styles/ — skipping"
fi

# Create GlassCard component
cat > src/components/GlassCard.astro << 'EOF'
---
interface Props {
  variant?: 'subtle' | 'light' | 'medium' | 'strong' | 'solid';
  interactive?: boolean;
  class?: string;
}

const { variant = 'medium', interactive = false, class: className = '' } = Astro.props;
const classes = [
  'glass-card',
  `glass-${variant}`,
  interactive ? 'glass-interactive' : '',
  className,
].filter(Boolean).join(' ');
---

<div class={classes}>
  <slot />
</div>

<style>
  .glass-card {
    border-radius: var(--radius-xl);
    padding: var(--space-6);
  }
</style>
EOF

# Create Navigation component
cat > src/components/Navigation.astro << 'EOF'
---
import { getCollection } from 'astro:content';

const docs = await getCollection('docs');

// Group docs by category
const categories: Record<string, typeof docs> = {};
for (const doc of docs) {
  const category = doc.data.category || 'General';
  if (!categories[category]) categories[category] = [];
  categories[category].push(doc);
}

// Sort each category by order
for (const cat of Object.keys(categories)) {
  categories[cat].sort((a, b) => (a.data.order ?? 999) - (b.data.order ?? 999));
}

const sortedCategories = Object.entries(categories).sort(([a], [b]) => a.localeCompare(b));
---

<nav class="wiki-nav">
  <div class="nav-header">
    <a href="/" class="nav-logo">
      <span class="nav-logo-icon">📖</span>
      <span class="nav-logo-text">Wiki</span>
    </a>
  </div>

  {sortedCategories.map(([category, categoryDocs]) => (
    <div class="nav-category">
      <h3 class="nav-category-title">{category}</h3>
      <ul class="nav-list">
        {categoryDocs.map(doc => (
          <li>
            <a href={`/docs/${doc.slug}`} class="nav-glass-item">
              {doc.data.icon && <span class="nav-icon">{doc.data.icon}</span>}
              {doc.data.title}
            </a>
          </li>
        ))}
      </ul>
    </div>
  ))}
</nav>

<style>
  .wiki-nav {
    display: flex;
    flex-direction: column;
    gap: var(--space-6);
  }

  .nav-header {
    margin-bottom: var(--space-4);
  }

  .nav-logo {
    display: flex;
    align-items: center;
    gap: var(--space-3);
    font-size: var(--text-xl);
    font-weight: 700;
    color: var(--color-text-primary);
    text-decoration: none;
  }

  .nav-logo-icon {
    font-size: 1.5rem;
  }

  .nav-category-title {
    font-size: var(--text-xs);
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--color-text-tertiary);
    margin-bottom: var(--space-2);
    padding: 0 var(--space-3);
  }

  .nav-list {
    list-style: none;
    padding: 0;
    margin: 0;
  }

  .nav-list li {
    margin-bottom: 2px;
  }

  .nav-icon {
    font-size: var(--text-sm);
  }
</style>
EOF

# Create ThemeToggle component
cat > src/components/ThemeToggle.astro << 'EOF'
---
---

<button class="theme-toggle" id="theme-toggle" aria-label="Toggle theme">
  <svg class="sun-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
    <circle cx="12" cy="12" r="5"/>
    <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/>
  </svg>
  <svg class="moon-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
    <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
  </svg>
</button>

<style>
  .theme-toggle {
    position: fixed;
    bottom: var(--space-6);
    right: var(--space-6);
    width: 48px;
    height: 48px;
    border-radius: var(--radius-full);
    background: rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.15);
    box-shadow: var(--shadow-glass-md);
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all var(--duration-normal) var(--ease-out-expo);
    z-index: 50;
    color: var(--color-text-primary);
  }

  .theme-toggle:hover {
    transform: scale(1.05);
    background: rgba(255, 255, 255, 0.15);
  }

  .theme-toggle:active {
    transform: scale(0.95);
  }

  [data-theme="light"] .theme-toggle {
    background: rgba(0, 0, 0, 0.05);
    border-color: rgba(0, 0, 0, 0.1);
  }

  [data-theme="light"] .theme-toggle:hover {
    background: rgba(0, 0, 0, 0.08);
  }

  .sun-icon { display: none; }
  .moon-icon { display: block; }

  [data-theme="light"] .sun-icon { display: block; }
  [data-theme="light"] .moon-icon { display: none; }
</style>

<script is:inline>
  const toggle = document.getElementById('theme-toggle');
  toggle.addEventListener('click', () => {
    const current = document.documentElement.getAttribute('data-theme');
    const next = current === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem('theme', next);
  });
</script>
EOF

# Create SearchModal component
cat > src/components/SearchModal.astro << 'EOF'
---
---

<div class="search-overlay" id="search-overlay">
  <div class="search-modal">
    <div class="search-input-wrapper">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="11" cy="11" r="8"/>
        <path d="M21 21l-4.35-4.35"/>
      </svg>
      <input type="text" class="search-input" id="search-input" placeholder="Search documentation..." autocomplete="off" />
      <kbd class="search-kbd">ESC</kbd>
    </div>
    <div class="search-results" id="search-results"></div>
  </div>
</div>

<style>
  .search-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.4);
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
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
    -webkit-backdrop-filter: blur(32px) saturate(200%);
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

  .search-input-wrapper {
    display: flex;
    align-items: center;
    gap: var(--space-3);
    padding: var(--space-4) var(--space-5);
    border-bottom: 1px solid var(--color-divider);
    color: var(--color-text-tertiary);
  }

  .search-input {
    flex: 1;
    background: none;
    border: none;
    outline: none;
    font-family: var(--font-text);
    font-size: var(--text-lg);
    color: var(--color-text-primary);
  }

  .search-input::placeholder {
    color: var(--color-text-tertiary);
  }

  .search-kbd {
    padding: 2px 8px;
    font-family: var(--font-mono);
    font-size: var(--text-xs);
    background: var(--color-bg-tertiary);
    border-radius: var(--radius-xs);
    color: var(--color-text-tertiary);
  }

  .search-results {
    max-height: 400px;
    overflow-y: auto;
    padding: var(--space-2);
  }
</style>

<script is:inline>
  const overlay = document.getElementById('search-overlay');
  const input = document.getElementById('search-input');

  document.addEventListener('keydown', (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
      e.preventDefault();
      overlay.classList.toggle('open');
      if (overlay.classList.contains('open')) {
        input.focus();
      }
    }
    if (e.key === 'Escape') {
      overlay.classList.remove('open');
    }
  });

  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) {
      overlay.classList.remove('open');
    }
  });
</script>
EOF

# Create TableOfContents component
cat > src/components/TableOfContents.astro << 'EOF'
---
interface Props {
  headings: { depth: number; slug: string; text: string }[];
}

const { headings } = Astro.props;
const toc = headings.filter(h => h.depth >= 2 && h.depth <= 3);
---

{toc.length > 0 && (
  <nav class="toc">
    <h4 class="toc-title">On this page</h4>
    <ul class="toc-list">
      {toc.map(heading => (
        <li class={`toc-item toc-depth-${heading.depth}`}>
          <a href={`#${heading.slug}`} class="toc-link">{heading.text}</a>
        </li>
      ))}
    </ul>
  </nav>
)}

<style>
  .toc {
    position: sticky;
    top: var(--space-8);
  }

  .toc-title {
    font-size: var(--text-xs);
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--color-text-tertiary);
    margin-bottom: var(--space-3);
  }

  .toc-list {
    list-style: none;
    padding: 0;
    margin: 0;
    border-left: 1px solid var(--color-divider);
  }

  .toc-item {
    margin: 0;
  }

  .toc-depth-3 {
    padding-left: var(--space-4);
  }

  .toc-link {
    display: block;
    padding: var(--space-1) var(--space-4);
    font-size: var(--text-sm);
    color: var(--color-text-tertiary);
    text-decoration: none;
    border-left: 2px solid transparent;
    margin-left: -1px;
    transition: all var(--duration-fast) var(--ease-out-quart);
  }

  .toc-link:hover {
    color: var(--color-text-primary);
  }

  .toc-link.active {
    color: var(--color-accent);
    border-left-color: var(--color-accent);
  }
</style>

<script is:inline>
  const tocLinks = document.querySelectorAll('.toc-link');
  const headings = document.querySelectorAll('h2[id], h3[id]');

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        tocLinks.forEach(link => link.classList.remove('active'));
        const activeLink = document.querySelector(`.toc-link[href="#${entry.target.id}"]`);
        if (activeLink) activeLink.classList.add('active');
      }
    });
  }, { rootMargin: '-80px 0px -80% 0px' });

  headings.forEach(heading => observer.observe(heading));
</script>
EOF

# Create CodeBlock component
cat > src/components/CodeBlock.astro << 'EOF'
---
interface Props {
  language?: string;
  filename?: string;
}

const { language = '', filename = '' } = Astro.props;
---

<div class="code-block">
  {(language || filename) && (
    <div class="code-block-header">
      <span class="code-lang">{filename || language}</span>
      <button class="copy-button" data-copy>Copy</button>
    </div>
  )}
  <div class="code-block-content">
    <slot />
  </div>
</div>

<style>
  .code-block {
    position: relative;
    background: rgba(0, 0, 0, 0.04);
    border: 1px solid rgba(0, 0, 0, 0.06);
    border-radius: var(--radius-lg);
    overflow: hidden;
    margin: 1.5em 0;
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
    font-size: var(--text-xs);
    color: var(--color-text-tertiary);
  }

  [data-theme="dark"] .code-block-header {
    background: rgba(255, 255, 255, 0.02);
    border-color: rgba(255, 255, 255, 0.04);
  }

  .copy-button {
    padding: var(--space-1) var(--space-2);
    border-radius: var(--radius-sm);
    background: transparent;
    border: none;
    color: var(--color-text-tertiary);
    font-size: var(--text-xs);
    font-family: var(--font-text);
    cursor: pointer;
    transition: all var(--duration-fast) var(--ease-out-quart);
  }

  .copy-button:hover {
    background: rgba(0, 0, 0, 0.05);
    color: var(--color-text-secondary);
  }

  [data-theme="dark"] .copy-button:hover {
    background: rgba(255, 255, 255, 0.08);
  }

  .code-block-content :global(pre) {
    margin: 0;
    border: none;
    border-radius: 0;
    background: transparent;
  }
</style>
EOF

# Create Breadcrumb component
cat > src/components/Breadcrumb.astro << 'EOF'
---
interface Props {
  category?: string;
  title: string;
}

const { category, title } = Astro.props;
---

<nav class="breadcrumb" aria-label="Breadcrumb">
  <ol class="breadcrumb-list">
    <li class="breadcrumb-item">
      <a href="/">Home</a>
    </li>
    {category && (
      <li class="breadcrumb-item">
        <span class="breadcrumb-sep">/</span>
        <span>{category}</span>
      </li>
    )}
    <li class="breadcrumb-item breadcrumb-current">
      <span class="breadcrumb-sep">/</span>
      <span>{title}</span>
    </li>
  </ol>
</nav>

<style>
  .breadcrumb {
    margin-bottom: var(--space-6);
  }

  .breadcrumb-list {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    list-style: none;
    padding: 0;
    margin: 0;
  }

  .breadcrumb-item {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    font-size: var(--text-sm);
    color: var(--color-text-tertiary);
  }

  .breadcrumb-item a {
    color: var(--color-text-secondary);
    text-decoration: none;
  }

  .breadcrumb-item a:hover {
    color: var(--color-accent);
  }

  .breadcrumb-sep {
    color: var(--color-text-tertiary);
    opacity: 0.5;
  }

  .breadcrumb-current {
    color: var(--color-text-primary);
  }
</style>
EOF

echo "🧩 Created 7 Astro components"

# Create BaseLayout
cat > src/layouts/BaseLayout.astro << 'EOF'
---
import ThemeToggle from '../components/ThemeToggle.astro';
import Navigation from '../components/Navigation.astro';
import SearchModal from '../components/SearchModal.astro';
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
  {description && <meta name="description" content={description} />}
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
  <SearchModal />
</body>
</html>
EOF

# Create DocLayout
cat > src/layouts/DocLayout.astro << 'EOF'
---
import BaseLayout from './BaseLayout.astro';
import Breadcrumb from '../components/Breadcrumb.astro';
import TableOfContents from '../components/TableOfContents.astro';

interface Props {
  title: string;
  description?: string;
  category?: string;
  headings?: { depth: number; slug: string; text: string }[];
}

const { title, description, category, headings = [] } = Astro.props;

// Estimate reading time
const content = await Astro.slots.render('default');
const wordCount = content.split(/\s+/).length;
const readingTime = Math.max(1, Math.ceil(wordCount / 200));
---
<BaseLayout title={title} description={description}>
  <article class="doc-article">
    <Breadcrumb title={title} category={category} />

    <header class="doc-header">
      <h1 class="doc-title">{title}</h1>
      {description && <p class="doc-description">{description}</p>}
      <div class="doc-meta">
        <span class="reading-time">{readingTime} min read</span>
      </div>
    </header>

    <div class="doc-layout">
      <div class="doc-content prose">
        <slot />
      </div>
      {headings.length > 0 && (
        <aside class="doc-sidebar">
          <TableOfContents headings={headings} />
        </aside>
      )}
    </div>
  </article>
</BaseLayout>

<style>
  .doc-article {
    max-width: 100%;
  }

  .doc-header {
    margin-bottom: var(--space-8);
    padding-bottom: var(--space-6);
    border-bottom: 1px solid var(--color-divider);
  }

  .doc-title {
    font-size: var(--text-4xl);
    margin-bottom: var(--space-3);
  }

  .doc-description {
    font-size: var(--text-lg);
    color: var(--color-text-secondary);
    margin-bottom: var(--space-4);
  }

  .doc-meta {
    display: flex;
    gap: var(--space-4);
    font-size: var(--text-sm);
    color: var(--color-text-tertiary);
  }

  .doc-layout {
    display: flex;
    gap: var(--space-12);
  }

  .doc-content {
    flex: 1;
    min-width: 0;
  }

  .doc-sidebar {
    width: 220px;
    flex-shrink: 0;
  }

  @media (max-width: 1100px) {
    .doc-sidebar {
      display: none;
    }
  }
</style>
EOF

echo "📐 Created layouts"

# Create index page
cat > src/pages/index.astro << 'EOF'
---
import { getCollection } from 'astro:content';
import BaseLayout from '../layouts/BaseLayout.astro';
import GlassCard from '../components/GlassCard.astro';

const docs = await getCollection('docs');

// Group by category
const categories: Record<string, typeof docs> = {};
for (const doc of docs) {
  const category = doc.data.category || 'General';
  if (!categories[category]) categories[category] = [];
  categories[category].push(doc);
}

// Sort
for (const cat of Object.keys(categories)) {
  categories[cat].sort((a, b) => (a.data.order ?? 999) - (b.data.order ?? 999));
}
---
<BaseLayout title="Documentation Wiki">
  <div class="hero">
    <h1>Documentation</h1>
    <p class="hero-subtitle">Browse the knowledge base</p>
  </div>

  <div class="category-grid">
    {Object.entries(categories).map(([category, categoryDocs]) => {
      return (
        <GlassCard variant="light" interactive>
          <h2 class="category-title">{category}</h2>
          <ul class="category-links">
            {categoryDocs.slice(0, 5).map(doc => (
              <li>
                <a href={`/docs/${doc.slug}`}>
                  {doc.data.icon && <span>{doc.data.icon} </span>}
                  {doc.data.title}
                </a>
              </li>
            ))}
          </ul>
          {categoryDocs.length > 5 && (
              <p class="category-more">+{categoryDocs.length - 5} more</p>
            )}
        </GlassCard>
      );
    })}
  </div>
</BaseLayout>

<style>
  .hero {
    text-align: center;
    padding: var(--space-16) 0 var(--space-12);
  }

  .hero h1 {
    font-size: 3rem;
    margin-bottom: var(--space-4);
    background: linear-gradient(135deg, var(--color-text-primary) 0%, var(--color-accent) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }

  .hero-subtitle {
    font-size: var(--text-xl);
    color: var(--color-text-secondary);
  }

  .category-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: var(--space-6);
  }

  .category-title {
    font-size: var(--text-xl);
    margin: 0 0 var(--space-4);
  }

  .category-links {
    list-style: none;
    padding: 0;
    margin: 0;
  }

  .category-links li {
    margin-bottom: var(--space-2);
  }

  .category-links a {
    color: var(--color-text-secondary);
    font-size: var(--text-sm);
  }

  .category-links a:hover {
    color: var(--color-accent);
  }

  .category-more {
    font-size: var(--text-sm);
    color: var(--color-text-tertiary);
    margin-top: var(--space-3);
  }
</style>
EOF

# Create dynamic doc page
cat > src/pages/docs/[...slug].astro << 'EOF'
---
import { getCollection } from 'astro:content';
import DocLayout from '../../layouts/DocLayout.astro';

export async function getStaticPaths() {
  const docs = await getCollection('docs');
  return docs.map(doc => ({
    params: { slug: doc.slug },
    props: { doc },
  }));
}

const { doc } = Astro.props;
const { Content, headings } = await doc.render();
---
<DocLayout
  title={doc.data.title}
  description={doc.data.description}
  headings={headings}
>
  <Content />
</DocLayout>
EOF

# Create sample doc
mkdir -p src/content/docs
cat > src/content/docs/getting-started.md << 'EOF'
---
title: Getting Started
description: Learn how to get started with this documentation wiki
category: Introduction
order: 1
icon: 🚀
---

# Getting Started

Welcome to your new documentation wiki! This guide will help you understand how to use and customize this wiki.

## Installation

The wiki is built with Astro and uses Bun as the package manager. To get started:

```bash
bun install
bun run dev
```

## Adding Content

Create new markdown files in the `src/content/docs/` directory. Each file should have frontmatter:

```yaml
---
title: Your Page Title
description: A brief description
category: Category Name
order: 1
icon: 📄
---
```

## Customization

### Theme

The wiki supports both light and dark modes. Users can toggle between them using the button in the bottom right corner.

### Styling

All styles use CSS custom properties defined in `src/styles/global.css`. You can customize:

- Colors
- Typography
- Spacing
- Glass effects

## Next Steps

- Add your markdown documentation files
- Customize the branding
- Deploy your wiki
EOF

echo ""
echo "✅ Astro Wiki initialized successfully!"
echo ""
echo "Next steps:"
echo "  cd $PROJECT_NAME"
echo "  bun run dev"
echo ""
echo "Add your markdown files to src/content/docs/"
