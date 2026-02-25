# Product MD Intake Requirements

## Supported input modes
- File upload (`.md`, `.txt`)
- Paste text
- Continue from saved draft

## Required extraction sections
- Product name / category
- Target audience
- Core problem and value proposition
- Differentiators and proof points
- Voice and tone clues
- Launch objective / CTA direction

## Validation rules
- Minimum input length: 250 characters
- Warn (not block) when audience or offer is missing
- Flag ambiguous sections for user confirmation
- Preserve original text snippets for traceability

## Recovery behavior
- Autosave every 5 seconds during edits
- Draft restore prompt on returning users
- If parsing fails, provide:
  - reason in plain language
  - suggested fix
  - fallback manual mapping mode

## Exit criteria for intake phase
- User confirms extracted summary
- Required fields are complete or explicitly deferred
- Payload is ready for brand-config synthesis
