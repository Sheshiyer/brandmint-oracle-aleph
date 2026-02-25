# Brand Config Mapping Specification

## Mapping contract
Product MD extraction maps into canonical `brand-config.yaml` sections.

## Core mappings
- `product_name` -> `brand.name`
- `category` -> `brand.domain`
- `audience.persona` -> `audience.persona_name`
- `audience.pain_points[]` -> `audience.pain_points[]`
- `value_proposition` -> `positioning.statement`
- `differentiators[]` -> `positioning.pillars[]`
- `voice_clues[]` -> `brand.voice`
- `tone_clues[]` -> `brand.tone`
- `launch_goal` -> `campaign.primary_objective`

## Mapping rules
- Preserve source snippet references for each mapped field.
- When confidence < 0.75, mark field as `needs_review`.
- Do not drop unknown input; attach under `notes.unmapped_inputs`.

## Output requirements
- YAML export must be valid and round-trip parsable.
- Include generation metadata:
  - source document hash
  - extraction timestamp
  - prompt version identifiers
