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

---

## 15. Discovery from @@AmirMushich (via Twitter Sync)

**Source:** https://x.com/AmirMushich/status/2028115571724660920 by @@AmirMushich (2026-03-02)
**Signal:** 1131 likes, 91 RTs

**Learning:** Nano Banana smart prompt:

Modular typographic brand poster design 

Prompt 👇 https://t.co/zmUPOdHLzr

**Reference:** https://x.com/AmirMushich/status/2028115571724660920/photo/1


---

## 16. Discovery from @@AmirMushich (via Twitter Sync)

**Source:** https://x.com/AmirMushich/status/2027798913516761522 by @@AmirMushich (2026-03-02)
**Signal:** 1417 likes, 126 RTs

**Learning:** Nano Banana smart prompt:

Font masking poster design

Prompt 👇 https://t.co/4jFnNQ0Oaq

**Reference:** https://x.com/AmirMushich/status/2027798913516761522/photo/1


---

## 17. Discovery from @@_vmlops (via Twitter Sync)

**Source:** https://x.com/_vmlops/status/2027336259040133499 by @@_vmlops (2026-03-02)
**Signal:** 1284 likes, 193 RTs

**Learning:** Check out Antigravity Awesome Skills - a massive library with 900+ AI agent skills for Claude, Copilot, Gemini, Cursor, and more

Automate workflows, search faster, manage GitHub tasks &amp; unlock your AI’s full potential all in one place

https://t.co/rbNXLl9OU8 https://t.co/9sDGRBlS7x

**Reference:** https://github.com/sickn33/antigravity-awesome-skills, https://x.com/_vmlops/status/2027336259040133499/photo/1

**Web Content:** GitHub - sickn33/antigravity-awesome-skills: The Ultimate Collection of 900+ Agentic Skills for Claude Code/Antigravity/Cursor. Battle-tested, high-performance skills for AI agents including official skills from Anthropic and Vercel. — Skip to content Navigation Menu Toggle navigation Sign in Appearance settings Search or jump to... Search code, repositories, users, issues, pull requests... Search Clear Search syntax tips Provide feedback We read every piece of feedback, and take your input very seriously. Include my email address so I can be contacted Cancel Submit feedback Saved searches Use saved searches to filter your results more quickly Name Query To see all available qualifiers, see our documentation . Cancel Create sa


---

## 18. Discovery from @@azed_ai (via Twitter Sync)

**Source:** https://x.com/azed_ai/status/2027021107015143498 by @@azed_ai (2026-03-02)
**Signal:** 556 likes, 58 RTs

**Learning:** Nano Banana Pro prompt share

Create cool ads using this prompt 👇
created using @LeonardoAI https://t.co/QbYPszfM9q

**Reference:** https://x.com/azed_ai/status/2027021107015143498/photo/1


---

## 19. Discovery from @@OdinLovis (via Twitter Sync)

**Source:** https://x.com/OdinLovis/status/2027155305378074960 by @@OdinLovis (2026-03-02)
**Signal:** 1139 likes, 108 RTs

**Learning:** To celebrate nano-banana-2 launching on @fal , I built FalSprite, sprite sheet generator that turns a text prompt into game-ready animations.                                                                                       
                                                                                                                                                                                                                                                         
  One https://t.co/SpUceQWzbJ key powers the whole pipeline:                                                                                                                                                                                                              
  → nano-banana-2 for image generation                      
  → BRIA for background removal
  → OpenRouter LLM for prompt rewriting

  ~$0.20 per generation. Try it live or fork it:

  🔗 https://t.co/GAbZTKokVG
  🔗 https://t.co/jLQoHGg8Sq

  Thanks @BlendiByl  for the help on this 🙏

**Reference:** https://fal.ai/, https://falsprite.vercel.app/, https://github.com/lovisdotio/falsprite

**Web Content:** Generative AI APIs | Run Img, 3D, Video AI Models 4x Faster | fal.ai — Nano Banana 2 is here 🍌 4x faster, lower cost, better quality fal logo Explore Documentation Pricing Enterprise Research Grants Contact Sales Login Model Gallery Documentation Pricing Enterprise Research Grants Get started Contact Sales Generative media platform for developers. The world's best generative image, video, and audio models, all in one place. Develop and fine-tune models with serverless GPUs and on-demand clusters. Get started Contact Sales Trusted by over 1,500,000 developers and le


---

## 20. Discovery from @@Hesamation (via Twitter Sync)

**Source:** https://x.com/Hesamation/status/2026801420872093708 by @@Hesamation (2026-03-02)
**Signal:** 3111 likes, 213 RTs

**Learning:** this Obsidian + AI is the new hot combo.
few people know that the CEO of Obsidian @kepano has made multiples skills for Claude Code and Codex that you can use right now both for your codebase and your personal vault. https://t.co/pshaSsfcj6

**Reference:** https://x.com/Hesamation/status/2026801420872093708/photo/1


---

## 21. Discovery from @@internetvin (via Twitter Sync)

**Source:** https://x.com/internetvin/status/2026461256677245131 by @@internetvin (2026-03-02)
**Signal:** 1307 likes, 77 RTs

**Learning:** Here's 22 of the commands I am using with Obsidian and Claude Code with descriptions. 

I will turn this into something interactive soon so you can click the commands and then see the full prompts. https://t.co/C0y6kN9mNF

**Reference:** https://x.com/internetvin/status/2026461256677245131/photo/1


---

## 22. Discovery from @@MengTo (via Twitter Sync)

**Source:** https://x.com/MengTo/status/2026189291085607181 by @@MengTo (2026-03-02)
**Signal:** 5259 likes, 235 RTs

**Learning:** Can we talk about how insane Gemini 3.1 Pro is at webgl https://t.co/brXhfd9Wy7

**Reference:** https://x.com/MengTo/status/2026189291085607181/video/1


---

## 23. Discovery from @@DataChaz (via Twitter Sync)

**Source:** https://x.com/DataChaz/status/2026335537888702627 by @@DataChaz (2026-03-02)
**Signal:** 462 likes, 53 RTs

**Learning:** PowerPoint is officially dead.

With Gemini Pro 3.1, anyone can now design breathtaking slide decks in seconds 🤯

Steal the prompt below 🧵↓ https://t.co/3Q9G7kykus

**Reference:** https://x.com/DataChaz/status/2026335537888702627/video/1


---

## 24. Discovery from @@godofprompt (via Twitter Sync)

**Source:** https://x.com/godofprompt/status/2027787837639410110 by @@godofprompt (2026-03-02)
**Signal:** 880 likes, 126 RTs

**Learning:** Richard Feynman had one superpower: making the complex feel obvious.

I reverse-engineered his entire teaching method into a Claude prompt system.

Use it to understand anything in under 10 minutes (Save this for later): https://t.co/3pEwBFX2QQ

**Reference:** https://x.com/godofprompt/status/2027787837639410110/photo/1


---

## 25. Discovery from @@AmirMushich (via Twitter Sync)

**Source:** https://x.com/AmirMushich/status/2027393294469128313 by @@AmirMushich (2026-03-02)
**Signal:** 442 likes, 39 RTs

**Learning:** Nano Banana smart prompt:

Luxury merch concept

Works with: 
fashion, sports, lifestyle

One brand variable → autonomous fabric pattern + logo treatment + material + color

Prompt 👇 https://t.co/epFrtU9qL3

**Reference:** https://x.com/AmirMushich/status/2027393294469128313/photo/1


---

## 26. Discovery from @@AmirMushich (via Twitter Sync)

**Source:** https://x.com/AmirMushich/status/2027393296603992332 by @@AmirMushich (2026-03-02)
**Signal:** 52 likes, 4 RTs

**Learning:** Prompt: 
(access Nano Banana here: https://t.co/EY9xacrmOP) 

[BRAND NAME]. Act as a fashion photographer and creative director shooting a high-end editorial lookbook for a bespoke football jersey designed by this brand.
THE SUBJECT & COMPOSITION (FLOATING & ANGLED):
A single, premium custom football jersey is floating suspended in mid-air, centered in the frame. There is no hanger visible.
Crucial Angle: The jersey is NOT presented flatly frontal. It is rotated slightly (approximately 15 degrees angled view) to show depth, form, and a dynamic profile. Despite floating, the fabric must show realistic weight, deep gravity-defying folds, creases, and natural wrinkles. It must feel like a real, heavy garment frozen in time, not a stiff 3D model.
BRANDED DESIGN & AESTHETICS:
The jersey's design is a sophisticated interpretation of [BRAND NAME]'s visual identity.
Branding Placement: The official [BRAND NAME] logo is authentically applied as the main club crest on the chest (e.g., embroidered patch or high-quality heat transfer).
MATERIALITY & TEXTURE (CRITICAL):
The focus remains on luxurious, tactile textures.
Fabric: A heavyweight, retro-inspired athletic cotton-blend or technical knit with a visible, coarse weave structure.
ENVIRONMENT & BACKGROUND (WHITE STUDIO):
The jersey floats within an abstract, infinite white photo studio cyclorama space. The background is completely seamless, pure, clean white, and minimalist, with absolutely zero distractions, placing total focus on the suspended garment.
LIGHTING & PHOTOGRAPHY STYLE:
Style: Hyper-realistic editorial fashion photography. Clean, high-key aesthetic.
Lighting: sophisticated studio lighting. Soft, diffused light that sculpts the folds of the fabric and highlights the texture against the pure white background. Subtle soft shadows might be cast on the jersey itself to define its form in the white space.

**Reference:** https://ltx.studio/


---

## 27. Discovery from @@AmirMushich (via Twitter Sync)

**Source:** https://x.com/AmirMushich/status/2027798919044853902 by @@AmirMushich (2026-03-02)
**Signal:** 132 likes, 7 RTs

**Learning:** Prompt:  
(access Nano Banana 2 here: https://t.co/EY9xacrmOP)

[BRAND NAME]. Act as a Senior Editorial Designer and Typographer.

PHASE 1: TYPOGRAPHIC MASK (THE "WINDOW" EFFECT).

- Core Element: Use the most iconic slogan or the name of [BRAND NAME] as a massive, ultra-bold, heavy sans-serif typographic mask.

- Layout: The letters must be giant, filling the entire vertical frame from edge to edge with tight kerning.

- Concept: The text acts as a "cut-out" window. The background is solid white, and the photographic subject is visible ONLY through the letterforms.

PHASE 2: DYNAMIC SUBJECT LOGIC.

- Subject Selection:

- Detail: Ensure a high-contrast element (like a red shoe or a glowing headlight) is visible through one of the letters as a focal point.

PHASE 3: SOPHISTICATED MUTED PALETTE.

- Atmosphere: Use a "Refined Muted" color scheme.

- Tones: Soft slate blues, charcoal greys, and creamy off-whites for the photography inside the mask.

- Accent: Identify one sharp, saturated accent color belonging to [BRAND NAME] and apply it to a single key object visible through the text.

PHASE 4: PHOTOGRAPHY & LIGHTING.

- Lighting: Soft-box studio lighting. Diffused shadows and gentle highlights to create a cinematic, high-end editorial feel.

- Finish: Clean, matte texture with zero visual noise. High-definition photographic quality.

PHASE 5: MINIMALIST BRANDING.

- Accents: Add a tiny minimalist logo and a small vertical tagline in a clean, microscopic sans-serif font near the corners.

- Year: Include the year "2026" in a subtle, elegant font to mimic a limited-edition look.

**Reference:** https://ltx.studio/


---

## 28. Discovery from @@AmirMushich (via Twitter Sync)

**Source:** https://x.com/AmirMushich/status/2027824897431392456 by @@AmirMushich (2026-03-02)
**Signal:** 126 likes, 8 RTs

**Learning:** 3 steps to create such vids:

1. Midjourney -&gt; image generation
2. Nano Banana on LTX -&gt; font design
3. Editing &amp; SFX -&gt; any editing program

Prompts &amp; font settings 👇 https://t.co/HdztZJl4uf

**Reference:** https://x.com/AmirMushich/status/2027824897431392456/video/1


---

## 29. Discovery from @@AmirMushich (via Twitter Sync)

**Source:** https://x.com/AmirMushich/status/2028068337427603741 by @@AmirMushich (2026-03-02)
**Signal:** 110 likes, 6 RTs

**Learning:** Easy text-masking workflow w AI

Nano Banana prompt 👇 https://t.co/lGz7fENYO4

**Reference:** https://x.com/AmirMushich/status/2028068337427603741/photo/1


---

## 30. Discovery from @@AmirMushich (via Twitter Sync)

**Source:** https://x.com/AmirMushich/status/2027798922731647122 by @@AmirMushich (2026-03-02)
**Signal:** 42 likes, 3 RTs

**Learning:** My design skills now will work for you

I prepared my best tips for you in this article 👇

Open it -&gt; find your favorite settings -&gt; steal them
Make your brand look elite:

https://t.co/vEcsUKGzmj

**Reference:** https://x.com/AmirMushich/status/2026693633794076892?s=20


---

## 31. Discovery from @@AmirMushich (via Twitter Sync)

**Source:** https://x.com/AmirMushich/status/2027393298164252901 by @@AmirMushich (2026-03-02)
**Signal:** 18 likes, 2 RTs

**Learning:** Want my design skills to work on you? 

I prepared my best tips for you in this article 👇

Open it -&gt; find your favorite settings -&gt; steal them

Make your brand shine: 
https://t.co/8d3byheiMS

**Reference:** https://x.com/amirmushich/status/2026693633794076892?s=46


---

## 32. Discovery from @@AmirMushich (via Twitter Sync)

**Source:** https://x.com/AmirMushich/status/2028115575604396083 by @@AmirMushich (2026-03-02)
**Signal:** 16 likes, 0 RTs

**Learning:** Steal more of my design workflows: https://t.co/IQmmpLXrud

**Reference:** https://x.com/AmirMushich/status/2027798913516761522?s=20


---

## 33. Discovery from @@AmirMushich (via Twitter Sync)

**Source:** https://x.com/AmirMushich/status/2028115576690749775 by @@AmirMushich (2026-03-02)
**Signal:** 16 likes, 0 RTs

**Learning:** My design skills now will work for you

I prepared my best tips for you in this article 👇

Open it -&gt; find your favorite settings -&gt; steal them
Make your brand look elite:

https://t.co/vEcsUKGzmj

**Reference:** https://x.com/AmirMushich/status/2026693633794076892?s=20


---

## 34. Discovery from @@AmirMushich (via Twitter Sync)

**Source:** https://x.com/AmirMushich/status/2027824898408648880 by @@AmirMushich (2026-03-02)
**Signal:** 12 likes, 1 RTs

**Learning:** Steal my midjourney prompts here:

https://t.co/v0qecUqFrm

**Reference:** https://docs.google.com/document/d/1c89Hl_5WzLQkrM0VgYFqUUCY_C8EXpz5jVjyuB_rh3U/edit?usp=sharing


---

## 35. Discovery from @@AmirMushich (via Twitter Sync)

**Source:** https://x.com/AmirMushich/status/2027472643629215819 by @@AmirMushich (2026-03-02)
**Signal:** 13 likes, 0 RTs

**Learning:** 3 weeks of prompting &amp; chatting with voice keyboard - crazy

Genuinely enjoying the efficiency of my workflows now 🤌 https://t.co/muwkGwtjkD

**Reference:** https://x.com/AmirMushich/status/2027472643629215819/photo/1
