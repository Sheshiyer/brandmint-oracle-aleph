# Frontmatter Templates

Copy-paste templates for each wiki page category. Ensure consistent metadata across all generated documentation.

## Core Schema

Every page requires these fields:

```yaml
---
title: ""           # Page title (appears in nav and H1)
description: ""     # SEO meta description, 150-160 chars max
category: ""        # product|brand|audience|marketing|project|general
tags: []            # Array of relevant keywords
sources: []         # Array of source document filenames
lastUpdated: ""     # ISO date: YYYY-MM-DD
---
```

## Product Pages

### product/overview.md
```yaml
---
title: "Product Overview"
description: "Complete overview of {ProductName}, including vision, value proposition, and key features."
category: "product"
tags: ["overview", "introduction", "product", "value-proposition"]
sources: ["mds.md", "positioning.md"]
lastUpdated: "2025-01-24"
---
```

### product/features.md
```yaml
---
title: "Features & Capabilities"
description: "Detailed breakdown of {ProductName} features, use cases, and benefits for each user type."
category: "product"
tags: ["features", "capabilities", "benefits", "use-cases"]
sources: ["mds.md", "detailed-product.md"]
lastUpdated: "2025-01-24"
---
```

### product/specifications.md
```yaml
---
title: "Technical Specifications"
description: "System requirements, technical specs, and compatibility information for {ProductName}."
category: "product"
tags: ["specifications", "technical", "requirements", "compatibility"]
sources: ["detailed-product.md", "proposal.md"]
lastUpdated: "2025-01-24"
---
```

## Brand Pages

### brand/voice-tone.md
```yaml
---
title: "Voice & Tone Guidelines"
description: "Brand voice definition, tone calibration, and writing principles for {BrandName} communications."
category: "brand"
tags: ["voice", "tone", "writing", "brand-guidelines", "copywriting"]
sources: ["voice-tone.md"]
lastUpdated: "2025-01-24"
---
```

### brand/visual-guidelines.md
```yaml
---
title: "Visual Identity Guidelines"
description: "Color palette, typography, logo usage, and imagery guidelines for {BrandName}."
category: "brand"
tags: ["visual", "design", "colors", "typography", "logo", "brand-guidelines"]
sources: ["visual-identity.md"]
lastUpdated: "2025-01-24"
---
```

### brand/writing-principles.md
```yaml
---
title: "Writing Principles"
description: "Content guidelines, style rules, and writing examples for consistent {BrandName} messaging."
category: "brand"
tags: ["writing", "content", "style-guide", "messaging"]
sources: ["voice-tone.md", "mds.md"]
lastUpdated: "2025-01-24"
---
```

## Audience Pages

### audience/primary-persona.md
```yaml
---
title: "{PersonaName} - Primary Persona"
description: "Detailed profile of our primary target customer: demographics, goals, pain points, and decision factors."
category: "audience"
tags: ["persona", "customer", "target-audience", "user-research"]
sources: ["buyer-persona.md"]
lastUpdated: "2025-01-24"
---
```

### audience/secondary-personas.md
```yaml
---
title: "Secondary Personas"
description: "Profiles of additional customer segments and their unique needs."
category: "audience"
tags: ["persona", "segments", "audience", "user-types"]
sources: ["buyer-persona.md"]
lastUpdated: "2025-01-24"
---
```

### market/competitive-landscape.md
```yaml
---
title: "Competitive Landscape"
description: "Market analysis, competitor comparison, and differentiation strategy for {ProductName}."
category: "audience"
tags: ["competition", "market-analysis", "competitors", "positioning"]
sources: ["competitor-analysis.md", "positioning.md"]
lastUpdated: "2025-01-24"
---
```

## Marketing Pages

### marketing/campaign-copy.md
```yaml
---
title: "Campaign Copy Library"
description: "Headlines, value propositions, feature copy, and CTAs for {ProductName} marketing campaigns."
category: "marketing"
tags: ["copy", "headlines", "messaging", "campaign", "advertising"]
sources: ["campaign-page.md", "mds.md"]
lastUpdated: "2025-01-24"
---
```

### marketing/email-templates.md
```yaml
---
title: "Email Templates"
description: "Welcome, pre-launch, and launch email sequences with full templates and subject lines."
category: "marketing"
tags: ["email", "sequences", "templates", "automation", "nurture"]
sources: ["welcome-email.md", "prelaunch-email.md", "launch-email.md"]
lastUpdated: "2025-01-24"
---
```

### marketing/ad-creative.md
```yaml
---
title: "Advertising Creative"
description: "Pre-launch and live campaign ad copy variations across awareness, urgency, and social proof themes."
category: "marketing"
tags: ["ads", "advertising", "creative", "facebook", "paid-media"]
sources: ["prelaunch-ads.md", "live-ads.md"]
lastUpdated: "2025-01-24"
---
```

## Project Pages

### project/architecture.md
```yaml
---
title: "Technical Architecture"
description: "System architecture, technology stack, integrations, and security approach for {ProjectName}."
category: "project"
tags: ["architecture", "technical", "stack", "infrastructure"]
sources: ["proposal.md"]
lastUpdated: "2025-01-24"
---
```

### project/timeline.md
```yaml
---
title: "Project Timeline"
description: "Development phases, milestones, deliverables, and target dates for {ProjectName}."
category: "project"
tags: ["timeline", "milestones", "schedule", "phases", "planning"]
sources: ["proposal.md", "contract.md"]
lastUpdated: "2025-01-24"
---
```

### project/team-roles.md
```yaml
---
title: "Team & Roles"
description: "Team structure, responsibilities, communication cadence, and escalation paths."
category: "project"
tags: ["team", "roles", "responsibilities", "communication"]
sources: ["proposal.md"]
lastUpdated: "2025-01-24"
---
```

### project/scope.md
```yaml
---
title: "Project Scope"
description: "Deliverables, inclusions, exclusions, and success criteria for {ProjectName}."
category: "project"
tags: ["scope", "deliverables", "requirements", "boundaries"]
sources: ["proposal.md", "contract.md"]
lastUpdated: "2025-01-24"
---
```

## General Pages

### index.md
```yaml
---
title: "{ProjectName} Wiki"
description: "Central documentation hub for {ProjectName}: product info, brand guidelines, marketing assets, and project details."
category: "general"
tags: ["home", "index", "overview", "documentation"]
sources: ["all"]
lastUpdated: "2025-01-24"
---
```

### getting-started/quickstart.md
```yaml
---
title: "Quick Start Guide"
description: "Get oriented with the {ProjectName} documentation. Where to start and how to navigate."
category: "general"
tags: ["quickstart", "getting-started", "guide", "navigation"]
sources: []
lastUpdated: "2025-01-24"
---
```

## Variable Substitution

Replace these placeholders in all templates:

| Placeholder | Source |
|-------------|--------|
| `{ProductName}` | MDS product name or proposal project name |
| `{BrandName}` | Voice & Tone brand name or company name |
| `{PersonaName}` | Buyer Persona primary persona name |
| `{ProjectName}` | Proposal project name or client + project |
| `2025-01-24` | Current date in ISO format |
