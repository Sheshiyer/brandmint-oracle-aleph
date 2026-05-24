# NotebookLM Source Quality Baseline

- **Sources dir:** `/Volumes/madara/2026/twc-vault/01-Projects/thoughtseed/thoughtseed-labs/60-client-ecosystem/newsense/deliverables/notebooklm/sources`
- **Files scanned:** 18
- **Average score:** 56.91
- **Classification counts:** pass=3, warn=7, fail=8
- **Total forbidden hits:** 40
- **Total placeholder markers:** 25

## Worst Files First

### kickstarter-campaign-messaging.md — score 0.0 (fail)
- words=91, bullets=4, forbidden_hits=6, placeholders=5
- forbidden patterns:
  - `source_skill_label` x2 (severity 2): Pipeline-internal labels leak into published prose.
  - `missing_artifact_stub` x2 (severity 3): Placeholder stubs should never ship to NotebookLM.
  - `waiting_on_stub` x2 (severity 3): Dependency placeholders indicate incomplete source material.

### kickstarter-crafting-compelling-copy.md — score 0.0 (fail)
- words=89, bullets=4, forbidden_hits=6, placeholders=5
- forbidden patterns:
  - `source_skill_label` x2 (severity 2): Pipeline-internal labels leak into published prose.
  - `missing_artifact_stub` x2 (severity 3): Placeholder stubs should never ship to NotebookLM.
  - `waiting_on_stub` x2 (severity 3): Dependency placeholders indicate incomplete source material.

### kickstarter-driving-continual-interest.md — score 0.0 (fail)
- words=91, bullets=4, forbidden_hits=6, placeholders=5
- forbidden patterns:
  - `source_skill_label` x2 (severity 2): Pipeline-internal labels leak into published prose.
  - `missing_artifact_stub` x2 (severity 3): Placeholder stubs should never ship to NotebookLM.
  - `waiting_on_stub` x2 (severity 3): Dependency placeholders indicate incomplete source material.

### kickstarter-email-strategy.md — score 0.0 (fail)
- words=111, bullets=5, forbidden_hits=9, placeholders=7
- forbidden patterns:
  - `source_skill_label` x3 (severity 2): Pipeline-internal labels leak into published prose.
  - `missing_artifact_stub` x3 (severity 3): Placeholder stubs should never ship to NotebookLM.
  - `waiting_on_stub` x3 (severity 3): Dependency placeholders indicate incomplete source material.

### kickstarter-product-detailing.md — score 7.0 (fail)
- words=220, bullets=19, forbidden_hits=6, placeholders=3
- forbidden patterns:
  - `source_skill_label` x4 (severity 2): Pipeline-internal labels leak into published prose.
  - `missing_artifact_stub` x1 (severity 3): Placeholder stubs should never ship to NotebookLM.
  - `waiting_on_stub` x1 (severity 3): Dependency placeholders indicate incomplete source material.

### artifact-voice-and-tone.md — score 60.71 (fail)
- words=103, bullets=19, forbidden_hits=1, placeholders=0
- forbidden patterns:
  - `source_skill_label` x1 (severity 2): Pipeline-internal labels leak into published prose.

### artifact-competitor-summary.md — score 61.67 (fail)
- words=62, bullets=12, forbidden_hits=1, placeholders=0
- forbidden patterns:
  - `source_skill_label` x1 (severity 2): Pipeline-internal labels leak into published prose.

### kickstarter-market-understanding.md — score 66.0 (fail)
- words=109, bullets=14, forbidden_hits=2, placeholders=0
- forbidden patterns:
  - `source_skill_label` x2 (severity 2): Pipeline-internal labels leak into published prose.

### artifact-market-buyer-persona.md — score 75.0 (warn)
- words=37, bullets=6, forbidden_hits=1, placeholders=0
- forbidden patterns:
  - `source_skill_label` x1 (severity 2): Pipeline-internal labels leak into published prose.

### artifact-mds.md — score 79.0 (warn)
- words=36, bullets=3, forbidden_hits=1, placeholders=0
- forbidden patterns:
  - `source_skill_label` x1 (severity 2): Pipeline-internal labels leak into published prose.

### artifact-product-positioning-summary.md — score 79.0 (warn)
- words=42, bullets=3, forbidden_hits=1, placeholders=0
- forbidden patterns:
  - `source_skill_label` x1 (severity 2): Pipeline-internal labels leak into published prose.

### brand-config-source.md — score 80.0 (warn)
- words=391, bullets=52, forbidden_hits=0, placeholders=0

### brand-foundation.md — score 80.0 (warn)
- words=388, bullets=88, forbidden_hits=0, placeholders=0

### kickstarter-readiness.md — score 80.0 (warn)
- words=201, bullets=28, forbidden_hits=0, placeholders=0

### visual-asset-catalog.md — score 80.0 (warn)
- words=134, bullets=31, forbidden_hits=0, placeholders=0

### campaign-content.md — score 88.0 (pass)
- words=9, bullets=0, forbidden_hits=0, placeholders=0

### communications-social.md — score 88.0 (pass)
- words=13, bullets=0, forbidden_hits=0, placeholders=0

### brand-strategy.md — score 100.0 (pass)
- words=135, bullets=16, forbidden_hits=0, placeholders=0
