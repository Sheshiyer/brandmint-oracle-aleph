# Document Schemas

Detailed content schemas for each wiki page type. Agents use these to extract and structure content consistently.

## Product Documentation

### product/overview.md

Extract from: MDS, Product Positioning

```yaml
sections:
  - name: Product Vision
    source_field: mds.product_pitch
    guidance: One compelling paragraph, what this product enables
    
  - name: Core Value Proposition
    source_field: positioning.value_props
    guidance: 3-5 bullet points, what makes this unique
    
  - name: Target Audience Summary
    source_field: mds.target_audiences
    guidance: Brief overview, link to full persona docs
    
  - name: Key Differentiators
    source_field: positioning.usp, competitor.gaps
    guidance: How this stands apart from alternatives
```

### product/features.md

Extract from: MDS, Detailed Product Description

```yaml
sections:
  - name: Feature Overview
    source_field: mds.features_benefits
    guidance: Organized by category/priority
    
  - name: Feature Details
    format: |
      ### {Feature Name}
      **What it does:** {description}
      **Who benefits:** {persona reference}
      **How it works:** {mechanism if relevant}
    
  - name: Use Cases
    source_field: mds.use_cases
    guidance: Real-world scenarios, link to persona needs
```

### product/specifications.md

Extract from: Detailed Product Description, Proposal (architecture section)

```yaml
sections:
  - name: Technical Specifications
    format: table
    columns: [Specification, Value, Notes]
    
  - name: System Requirements
    source_field: proposal.tech_stack
    guidance: Environment, dependencies, integrations
    
  - name: Compatibility
    guidance: Platforms, browsers, devices supported
```

## Brand Documentation

### brand/voice-tone.md

Extract from: Voice & Tone skill output

```yaml
sections:
  - name: Brand Persona
    source_field: voice.persona_definition
    guidance: Who the brand "is" as a character
    
  - name: Voice Principles
    source_field: voice.voice_principles
    format: |
      ### {Principle}
      **Do:** {examples}
      **Don't:** {anti-examples}
    
  - name: Tone Calibration
    source_field: voice.tone_spectrum
    guidance: How tone shifts by context (serious ↔ playful)
    
  - name: Writing Examples
    guidance: Before/after rewrites demonstrating voice
```

### brand/visual-guidelines.md

Extract from: Visual Identity Core (if available)

```yaml
sections:
  - name: Color Palette
    format: |
      | Color | Hex | Usage |
      |-------|-----|-------|
      | Primary | {hex} | {when to use} |
    
  - name: Typography
    guidance: Font families, sizes, hierarchy
    
  - name: Logo Usage
    guidance: Clear space, minimum sizes, don'ts
    
  - name: Imagery Style
    guidance: Photo style, illustration approach
```

## Audience Documentation

### audience/primary-persona.md

Extract from: Buyer Persona Generator

```yaml
sections:
  - name: Persona Overview
    format: |
      **Name:** {persona_name}
      **Role:** {professional role}
      **Age Range:** {demographics}
      **Tech Comfort:** {level}
    
  - name: Goals & Motivations
    source_field: persona.goals
    guidance: What drives them, what success looks like
    
  - name: Pain Points
    source_field: persona.frustrations
    guidance: Current struggles, failed solutions
    
  - name: Decision Factors
    source_field: persona.buying_triggers
    guidance: What convinces them to act
    
  - name: Objections
    source_field: persona.objections
    guidance: Common hesitations, how to address
    
  - name: Channels
    source_field: persona.media_consumption
    guidance: Where they spend time, how to reach them
```

### market/competitive-landscape.md

Extract from: Competitor Analysis

```yaml
sections:
  - name: Market Overview
    guidance: Category definition, market size if known
    
  - name: Competitor Matrix
    format: |
      | Competitor | Strengths | Weaknesses | Price Point |
      |------------|-----------|------------|-------------|
    
  - name: Competitive Positioning
    source_field: competitor.positioning_map
    guidance: Where we fit vs alternatives
    
  - name: Differentiation Strategy
    guidance: Our unique advantages, why customers choose us
```

## Marketing Documentation

### marketing/campaign-copy.md

Extract from: Campaign Page Copy

```yaml
sections:
  - name: Headline Bank
    source_field: campaign.headlines
    guidance: Primary, secondary, social headlines
    
  - name: Value Proposition Copy
    source_field: campaign.value_props
    guidance: Short-form value statements
    
  - name: Feature Copy
    source_field: campaign.feature_sections
    guidance: Benefit-focused feature descriptions
    
  - name: Social Proof
    guidance: Testimonial frameworks, trust signals
    
  - name: CTA Copy
    source_field: campaign.ctas
    guidance: Call-to-action variations by context
```

### marketing/email-templates.md

Extract from: Welcome, Pre-launch, Launch Email Sequences

```yaml
sections:
  - name: Sequence Overview
    format: |
      | Sequence | Emails | Purpose |
      |----------|--------|---------|
      | Welcome | 2 | Onboard new subscribers |
      | Pre-launch | 4 | Build anticipation |
      | Launch | 5 | Drive conversions |
    
  - name: Email Templates
    format: |
      ### {Sequence Name} - Email {N}
      **Subject:** {subject_line}
      **Preview:** {preview_text}
      **Goal:** {email objective}
      **Body:** {full email content}
```

## Project Documentation

### project/architecture.md

Extract from: Proposal (technical architecture section)

```yaml
sections:
  - name: System Overview
    guidance: High-level architecture diagram description
    
  - name: Technology Stack
    format: |
      | Layer | Technology | Purpose |
      |-------|------------|---------|
      | Frontend | {tech} | {why chosen} |
    
  - name: Integrations
    guidance: Third-party services, APIs, data flows
    
  - name: Security
    guidance: Auth approach, data protection, compliance
```

### project/timeline.md

Extract from: Proposal (timeline), Contract (milestones)

```yaml
sections:
  - name: Project Phases
    format: |
      ### Phase {N}: {Name}
      **Duration:** {weeks}
      **Deliverables:**
      - {deliverable 1}
      - {deliverable 2}
      **Dependencies:** {what must complete first}
    
  - name: Milestone Schedule
    format: |
      | Milestone | Target Date | Payment (if applicable) |
      |-----------|-------------|-------------------------|
    
  - name: Risk Factors
    guidance: Known risks, mitigation strategies
```

### project/team-roles.md

Extract from: Proposal (team composition)

```yaml
sections:
  - name: Team Structure
    format: |
      ### {Role Title}
      **Responsibilities:**
      - {responsibility 1}
      **Allocation:** {hours/week or % time}
    
  - name: Communication Cadence
    guidance: Standup frequency, reporting structure
    
  - name: Escalation Path
    guidance: How issues get raised and resolved
```

## Index Page (index.md)

Synthesize from: All sources

```yaml
sections:
  - name: Project Overview
    guidance: 2-3 paragraphs, what this project is
    
  - name: Quick Links
    format: |
      - [Product Overview](product/overview.md)
      - [Brand Guidelines](brand/voice-tone.md)
      - [Our Audience](audience/primary-persona.md)
    
  - name: Getting Started
    guidance: Where to begin reading
    
  - name: Recent Updates
    guidance: Changelog or latest additions
```
