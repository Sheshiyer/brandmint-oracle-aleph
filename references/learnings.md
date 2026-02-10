# Brandmint — Hard-Won Learnings

Critical gotchas and patterns from production use. Violating these causes broken assets, wasted API calls, or inconsistent brands.

---

## 1. Recraft V3 Format Mismatch

**Problem:** Recraft V3 returns different file formats depending on the style parameter. There is NO API parameter to override this.

| Style | Returns | What to do |
|-------|---------|-----------|
| `vector_illustration/*` | SVG | Save as `.svg`, convert to PNG with `rsvg-convert` |
| `digital_illustration` | WebP | Save as `.webp`, convert to PNG with `sips` (macOS) |

**Fix:** Always detect the format from the URL extension or style parameter. Save the native format AND convert to PNG. Never assume PNG output from Recraft.

---

## 2. Recraft 1000-Character Prompt Limit

**Problem:** Recraft V3 silently truncates prompts longer than ~1000 characters. Your carefully crafted details just vanish.

**Fix:** Always condense Recraft prompts to under 990 characters. Verify length before calling the API:
```python
if len(prompt) >= 1000:
    print(f"ERROR: Prompt is {len(prompt)} chars. Condense to <1000.")
    sys.exit(1)
```

**Condensation strategy:** Keep brand colors, key visual descriptors, and layout instructions. Remove adjective stacking, repeated descriptions, and verbose camera specs.

---

## 3. Style Anchor Cascade

**Problem:** Without a visual anchor, 50+ assets generated independently will look like they come from 50 different brands.

**Fix:** Generate the bento grid (2A) FIRST. Upload its output:
```python
anchor_url = fal_client.upload_file("path/to/2A-bento-v1.png")
```

Pass as `image_urls=[anchor_url]` to ALL subsequent Nano Banana Pro calls. This creates visual consistency across the entire brand.

**Rule:** Never run any other generation script before the anchor is complete.

---

## 4. SVG-to-PNG Conversion

**Tool:** `rsvg-convert` (from `librsvg`)

```bash
brew install librsvg  # macOS
rsvg-convert -w 2048 -h 2048 --keep-aspect-ratio file.svg -o file.png
```

**Gotcha:** Some SVGs from Recraft have viewBox issues. The `--keep-aspect-ratio` flag handles most cases. If conversion fails, the SVG is still usable.

---

## 5. WebP-to-PNG Conversion

**Tool:** `sips` (macOS built-in)

```bash
sips -s format png file.webp --out file.png
```

**Gotcha:** `sips` is macOS-only. On Linux, use `convert file.webp file.png` (ImageMagick) or `dwebp file.webp -o file.png` (libwebp).

---

## 6. API Key Management

**Rule:** NEVER hardcode API keys. Always load from environment:

```python
from dotenv import load_dotenv
load_dotenv(os.path.expanduser("~/.claude/.env"))
```

**The `.env` file:** Store `FAL_KEY=your-key` in `~/.claude/.env`. This path is standardized across all Brandmint scripts.

---

## 7. Seed Strategy

**Pattern:** seed 42 = v1 (primary), seed 137 = v2 (alternate). Two variations per prompt for selection.

**For poster series:** Use only seed 42 (one variation) to keep cost manageable when generating 13+ posters.

**For hero assets:** Add seed 256 = v3 for three variations of critical assets like the seeker poster.

---

## 8. Recraft Color Parameter Format

**Gotcha:** Colors must be wrapped in `{"rgb": "#hex"}` dictionaries:

```python
# CORRECT
args["colors"] = [{"rgb": "#0A1628"}, {"rgb": "#F0EDE3"}]

# WRONG — will fail silently
args["colors"] = ["#0A1628", "#F0EDE3"]
```

---

## 9. Template Poster Pattern

**Pattern:** For batch generation (e.g., 13 engine posters), define a `BASE_PROMPT` with `{placeholder}` fields and a dictionary per item:

```python
BASE_PROMPT = """... Single {object} on {bg_color} ({bg_hex}) ..."""

ENGINES = {
    "9A-01": {"name": "Dasha", "object": "copper orrery", "bg_color": "Void Teal", ...},
    "9A-02": {"name": "Nakshatra", "object": "crystal sphere", ...},
}

for eid, data in ENGINES.items():
    prompt = BASE_PROMPT.format(**data)
```

This keeps prompts DRY while allowing per-item customization.

---

## 10. Contact Sheet Composition Reference

**Pattern:** For contact sheets and grid layouts, pass TWO images to Nano Banana Pro:

```python
image_urls = [anchor_url, composition_ref_url]
```

The first image (anchor) provides brand consistency. The second (composition ref) guides the grid layout structure. This dramatically improves layout quality.

---

## 11. Parallel Execution After Anchor

**Pattern:** After the anchor (2A) completes, all other batches are independent. Run them in parallel:

```
Anchor (2A) → BLOCKING, must complete first
Then parallel:
  Agent 1: Identity (2B, 2C)
  Agent 2: Products (3A, 3B, 3C)
  Agent 3: Photography (4A, 4B)
  Agent 4: Illustrations (5A-5D)
  Agent 5: Narrative (7A)
  Agent 6: Posters (8A, 9A, 10A-C)
```

No shared state between batches. Each agent uploads its own copy of the anchor.

---

## 12. File Naming Convention

**Pattern:** `{ID}-{slug}-{model}-{variant}.{ext}`

| Component | Format | Example |
|-----------|--------|---------|
| ID | Section + letter/number | `2A`, `5D-1`, `9A-01` |
| Slug | Lowercase, hyphenated | `brand-kit-bento`, `vedic-engine-icons` |
| Model | Short model name | `nanobananapro`, `flux2pro`, `recraft` |
| Variant | Version from seed | `v1`, `v2`, `v3` |
| Ext | File format | `.png`, `.svg`, `.webp` |

Examples:
- `2A-brand-kit-bento-nanobananapro-v1.png`
- `5D-1-vedic-engine-icons-recraft-v1.svg`
- `5D-1-vedic-engine-icons-recraft-v1.png` (converted)
- `9A-01-vimshottari-dasha-poster-v1.png`

---

## 13. Composition Reference Images

**Problem:** Without a composition reference, Nano Banana Pro generates layouts that may not match the desired structure (e.g., a 3x3 grid, a catalog layout, or a bento grid).

**Fix:** Store composition reference images in `references/images/` with standardized naming. The `REF_IMAGES` dict in generated scripts maps each prompt ID to its reference file. Reference images are passed alongside the style anchor via `image_urls`:

```python
image_urls = [anchor_url]  # style anchor first
ref_path = get_ref_image("4A")  # composition reference
if ref_path:
    image_urls.append(fal_client.upload_file(ref_path))
```

**Key points:**
- Only **Nano Banana Pro** accepts `image_urls` — Flux 2 Pro and Recraft V3 do NOT
- First image = style anchor (brand consistency), second image = composition reference (layout guide)
- Reference images are optional — scripts degrade gracefully if not found
- The same ref can be reused (e.g., 10A-C sequences reuse the 7A contact sheet ref for grid layout)
- Stored at `~/.claude/skills/brandmint/references/images/` for all brands to share

---

## 14. Reference Image Library & Naming Convention

**The full library has 49 images** organized in 4 tiers by naming prefix:

| Prefix | Pattern | Count | Purpose |
|--------|---------|-------|---------|
| `ref-{ID}-` | `ref-2A-bento-grid.jpg` | 14 | **Primary** composition reference for a prompt template ID. Wired into `REF_IMAGES` dict. |
| `ref-alt-` | `ref-alt-chrome-logos.jpg` | 19 | **Supplementary** style references. Alternative compositions for existing templates. |
| `ref-style-` | `ref-style-bold-portrait-grid.jpg` | 11 | **Portrait/character** style references. Useful for brands without "hands not faces" constraint. |
| `ref-demo-` | `ref-demo-aerial-logo.jpg` | 5 | **Demo/inspiration** gallery. Nano Banana Pro creative concept examples. |

**Primary refs** (14) are the ones that matter for script generation. Each maps to a prompt ID:
- `2A` bento grid, `2B` brand seal, `2C` logo emboss, `3A` capsule collection, `3B` hero product, `3C` essence vial, `4A` catalog layout, `4B` flatlay, `5A` heritage engraving, `5B` campaign grid, `5D` engine icons, `7A` contact sheet, `8A` seeker poster, `9A` engine poster
- `10A-C` reuses the `7A` contact sheet ref for grid layout

**Supplementary refs** (19) are available for swapping — e.g., if a brand wants chrome logos instead of wax seals for 2B, use `ref-alt-chrome-logos.jpg` by updating the `REF_IMAGES` dict.

**Rule:** All 49 images are sourced from Amir Mushich's Nano Banana Pro / FAL.AI portfolio. Each was visually inspected and mapped to a specific template based on composition similarity. No hallucinated mappings.
