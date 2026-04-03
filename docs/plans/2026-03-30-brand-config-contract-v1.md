# Canonical `brand-config.yaml` Contract v1

## Status

- Date: `2026-03-30`
- Task: `P1-W3-SA-T09`
- Contract version: `v1`
- Scope: define the single source-of-truth contract that later Phase 2-6 work must implement

## Decision

`brand-config.yaml` is the only persisted artifact that Brandmint may treat as authoritative for a run.

Everything else is a working input or transient mirror:

- GitHub URL
- cloned repo path
- `product.md`
- extraction JSON
- browser localStorage drafts
- bridge request payloads
- Tauri in-memory wizard state
- run reports
- sidecar health/status state

Those artifacts may help produce or review a config, but none of them are launch authority.

## Why this contract exists

Wave 1.2 established four drifts:

1. source-of-truth drift: the UI exports a download, but downstream launch behavior is not tied to an approved saved config
2. runtime-path drift: the bridge can resolve relative paths against the wrong repo root
3. visual-domain drift: app/SaaS runs can still inherit physical-product prompt families
4. docs/backlog drift: the written operator story does not match the live desktop path

This contract fixes the first drift and gives the later phases a stable boundary to build against.

## Canonical Boundary

The canonical semantic payload is:

- every top-level key in `brand-config.yaml` except the reserved `_brandmint` block

That means the approved business and generation input is the full YAML document minus `_brandmint`.

This is deliberate:

- existing loaders mostly read named sections through `config.get(...)`
- adding one reserved top-level namespace is low-impact
- the current config structure stays intact
- Phase 2 can extend validation and serialization without a schema rewrite

## Reserved Namespace

The config must reserve one top-level system block:

```yaml
_brandmint:
  document:
    kind: brand-config
    contract_version: "1"
    state: draft
  lineage:
    source_type: product-md
    source_uri: ""
    source_hash: "sha256:..."
    extractor_version: ""
    mapping_spec_version: "2026-03-30"
    created_at: "2026-03-30T12:00:00Z"
    updated_at: "2026-03-30T12:15:00Z"
  review:
    pending_fields:
      - "brand.name"
      - "positioning.statement"
    edited_fields:
      - "brand.voice"
    fields:
      "brand.name":
        source_keys: ["product_name"]
        confidence: 0.93
        review_state: confirmed
        source_snippets:
          - snippet_id: "snippet-001"
            text: "Brandmint helps teams..."
            start_offset: 0
            end_offset: 24
      "positioning.statement":
        source_keys: ["value_proposition"]
        confidence: 0.61
        review_state: needs_review
        source_snippets:
          - snippet_id: "snippet-014"
            text: "..."
            start_offset: 220
            end_offset: 275
  approval:
    approved_by: ""
    approved_at: ""
    approval_note: ""
    fingerprint_algorithm: "sha256"
    fingerprint_scope: "semantic-config-v1"
    fingerprint_value: ""
```

## Required Meaning of `_brandmint`

### `_brandmint.document`

- `kind` is always `brand-config`
- `contract_version` versions the contract, not the brand
- `state` is one of:
  - `draft`
  - `approved`
  - `superseded`

### `_brandmint.lineage`

Tracks how this config draft was produced.

Required fields:

- `source_type`: `github-url|product-md|manual|imported-config`
- `source_uri`: repo URL, local file path, or import origin
- `source_hash`: deterministic hash of the intake source that fed extraction
- `extractor_version`: extraction/mapping implementation identifier
- `mapping_spec_version`: mapping spec or prompt version identifier
- `created_at`
- `updated_at`

### `_brandmint.review`

Tracks why a draft should or should not be trusted yet.

Required behavior:

- `pending_fields` contains every field path whose `review_state` is `needs_review`
- `edited_fields` contains every field path whose current value differs from raw extraction output
- `fields` is keyed by canonical dot-path, for example `brand.name`
- every tracked field entry records:
  - upstream source keys
  - confidence
  - `review_state`
  - supporting source snippets

Allowed `review_state` values:

- `needs_review`
- `confirmed`
- `edited`

### `_brandmint.approval`

Tracks who approved the exact saved document.

Required behavior:

- `approved_by`, `approved_at`, and `fingerprint_value` must all be empty in `draft`
- they must all be populated in `approved`
- `approval_note` is optional but recommended

## User-Visible Notes Section

The front-end mapping spec already calls for `notes.unmapped_inputs`.

That stays in the semantic payload, not in `_brandmint`, so operators can review it directly:

```yaml
notes:
  unmapped_inputs:
    - raw_key: "pricing"
      excerpt: "Annual discount available for early teams"
      status: "pending"
```

Rules:

- unknown or unplaced intake content must not be dropped
- `notes.unmapped_inputs` persists through export/import round trips
- approval is allowed with unmapped inputs still present, but the UI must surface them explicitly before approval

## Semantic Fingerprint Rule

The approval fingerprint is computed over the normalized semantic payload:

- include: every top-level key except `_brandmint`
- exclude: all of `_brandmint`

Implications:

- provenance timestamps do not cause fingerprint churn
- real config edits do change the fingerprint
- the fingerprint represents the exact launchable brand payload

The normalization rule should be deterministic:

1. parse YAML to a dictionary
2. remove `_brandmint`
3. sort keys recursively
4. serialize deterministically
5. hash with `sha256`

## Launchability Rules

A config is launchable only when all of the following are true:

1. `_brandmint.document.state == "approved"`
2. `_brandmint.approval.approved_by` is populated
3. `_brandmint.approval.approved_at` is populated
4. `_brandmint.approval.fingerprint_value` is populated
5. `_brandmint.review.pending_fields` is empty
6. the file exists on disk at the configured path

Browser downloads, localStorage copies, and bridge payload echoes do not satisfy this contract by themselves.

## Mutation Rules

### Draft mutation

Allowed:

- extraction can write or rewrite a `draft`
- the operator can edit semantic fields
- the operator can resolve or mark review fields
- unmapped inputs can be acknowledged or mapped

### Approval transition

When a draft becomes approved, the system must:

1. recompute `pending_fields`
2. fail approval if `pending_fields` is non-empty
3. compute the semantic fingerprint
4. populate approval metadata
5. persist the approved file to disk

### Approved mutation

Approved configs are immutable for execution purposes.

If anything changes after approval, including:

- any semantic field outside `_brandmint`
- any provenance or review entry inside `_brandmint.lineage` or `_brandmint.review`
- `notes.unmapped_inputs`

then the document must return to `draft`, approval metadata must be cleared, and a new approval must be recorded before launch.

### Runtime mutation ban

Downstream execution paths must not silently rewrite approved config files.

Runtime state belongs elsewhere:

- `.brandmint/state.json`
- sidecar process state
- run reports
- logs

If a command needs different brand semantics, it must create or request a new draft, not mutate the approved file in place.

## Entry-Point Rules

### UI

- extraction creates a draft config representation
- export must save the exact YAML to the configured file path
- launch must use the saved approved file, not only the in-memory wizard state
- `exportedAt` alone is not a valid launch gate

### Bridge

- accepts file paths, not implicit authority from request bodies
- must reject launch of a `draft`
- must resolve relative paths from the actual workspace root, not a hardcoded alternate root

### CLI

- `bm launch` must treat the saved config file as the authority
- CLI flags may add runtime options, but must not override approved semantic fields already present in the config

### Pipeline / generators

- read-only with respect to approved config
- may read `_brandmint` for gating, provenance, and audit surfaces
- must not assume missing `_brandmint` means approved; legacy configs should be treated as unapproved until migrated

## Backward-Compatibility Rule

Legacy configs without `_brandmint` remain parseable, but they are not considered approved by this contract.

Migration rule for Phase 2:

- if `_brandmint` is absent, initialize a `draft` contract block on first controlled export/import
- do not infer approval from file existence alone

## Phase 2 Implementation Consequences

This contract implies the next implementation wave must do all of the following:

- extend schema/examples with `_brandmint`
- serialize provenance and `needs_review` data
- persist explicit approval metadata and fingerprint
- reject unapproved launch across CLI, bridge, and Tauri
- round-trip `notes.unmapped_inputs`
- make the UI diff between extracted draft and approved payload explicit

## Acceptance Check For This Contract

This contract is correct if later implementation can answer these questions unambiguously:

1. Which file is authoritative for a run?
2. How do we know whether that file was approved?
3. What evidence supports each extracted field?
4. What happens when an approved config is edited?
5. Can any entry point launch without a saved approved config?

Under this contract the answers are:

1. the saved `brand-config.yaml`
2. `_brandmint.document.state` plus approval metadata
3. `_brandmint.review.fields[...]`
4. it becomes a new `draft`
5. no
