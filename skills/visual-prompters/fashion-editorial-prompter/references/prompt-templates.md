# Fashion & Editorial Prompt Templates

## Template 1: Multi-Angle Contact Sheet (Aleena Amir)
**Use for:** 3x3 grid of consistent character poses for editorial lookbooks

### JSON Prompt
{
  "subject": {
    "identity_reference": "uploaded face and body reference",
    "identity_accuracy": "100% same facial structure, hair, skin tone, body shape, outfit, accessories; do not alter identity",
    "pose_variations": [
      {"name": "front-facing medium shot", "description": "upper to mid-body, facing camera directly, elegant and confident posture"},
      {"name": "front-facing extreme close-up", "description": "focus on face and eyes, capturing expression and makeup details"},
      {"name": "low-angle full-body shot", "description": "camera slightly below, looking upward, powerful stance emphasizing outfit and height"},
      {"name": "high-angle shot", "description": "slightly above, looking down, soft editorial perspective"},
      {"name": "side profile portrait", "description": "exact profile of face and hair, elegant posture, studio lighting highlights contours"},
      {"name": "34 profile (three-quarter turn)", "description": "torso and face turned three-quarters, emphasizing silhouette and outfit details"},
      {"name": "over-the-shoulder view", "description": "subject looks slightly away from camera, shoulder closest to camera in foreground"},
      {"name": "Dutch tilt", "description": "slightly rotated camera angle for dynamic editorial feel, maintaining consistent pose"},
      {"name": "mid-walk candid", "description": "natural motion captured, subtle step forward, relaxed arms, editorial energy"}
    ]
  },
  "wardrobe": {"description": "maintain exact outfit, fabric, and accessories as in identity reference", "consistency": "all panels must match perfectly"},
  "environment": {"setting": "studio environment", "background": "clean, minimal, neutral or light-grey cyclorama", "lighting": "soft professional studio lighting, subtle fill, flattering highlights"},
  "camera": {"shot_type": "varies per panel as specified", "angle": "specified per panel", "depth_of_field": "shallow, subject in sharp focus, blurred background"},
  "composition": {"grid": "3x3 contact sheet", "spacing": "consistent, balanced layout", "framing": "each panel fully showcases pose and outfit while keeping identity clear"},
  "aesthetic": {"style": "editorial fashion photography", "mood": "cinematic, professional, high-end", "color_palette": "maintain wardrobe and skin tones as reference, neutral background"},
  "render_quality": {"realism": "ultra-photorealistic", "resolution": "high (8K recommended)", "detail_focus": "fabric texture, skin, hair, accessories, lighting consistency across panels"},
  "negative_prompts": ["identity change", "distorted anatomy", "extra limbs", "blurred face", "motion artifacts", "low resolution", "inconsistent outfit or hair", "harsh shadows", "plastic skin", "busy background"]
}

---

## Template 2: High-Fashion Editorial Portrait (Aleena Amir - "Crimson Confidence")
**Use for:** Single fierce editorial shot with detailed wardrobe and pose spec

### JSON Prompt
{
  "subject": {
    "identity_reference": "uploaded face reference",
    "identity_accuracy": "100% match in facial structure, eyes, lips, nose, jawline, hairline, natural skin texture",
    "pose": {
      "body_orientation": "standing, torso twisted, body turned at sharp angle",
      "shoulders": {"front_shoulder": "thrust forward prominently toward camera", "rear_shoulder": "pulled back"},
      "head": {"tilt": "chin down, head slightly lowered", "gaze": "eyes looking up from under brows, predatory intense gaze"},
      "arms": "hanging naturally or one hand in pocket",
      "hands": "bare, realistic fingers"
    },
    "expression": "fierce, predatory, intense, theatrical, smoldering gaze",
    "hair": "tight sleek bun"
  },
  "wardrobe": {
    "suit": {
      "blazer": {"color": "deep cherry red / burgundy", "fit": "oversized, exaggerated dropped-shoulder, structured broad shoulders, sharp shoulder pads, mid-thigh length", "front": "double-breasted, wide peak lapels, slightly boxy silhouette"},
      "trousers": {"style": "high-waisted, ultra-wide-leg, deep front pleats, long hem pooling over heels"},
      "fabric": {"material": "premium heavy wool gabardine / wool twill", "texture": "dense, matte, slightly dry, visible diagonal twill weave, subtle creases, realistic drape"}
    },
    "accessories": {"earrings": "large gold hoop", "bracelet": "chunky gold on bare wrist"},
    "shoes": {"color": "burgundy", "style": "stiletto heels with ornate gold buckles"}
  },
  "camera": {"equipment": "Phase One XF, Schneider Kreuznach 80mm f/2.8 LS", "settings": {"aperture": "f/8", "ISO": 100, "shutter_speed": "1/160s"}, "perspective": "vertical 3:4 full-body medium-to-long shot"},
  "lighting": {"type": "soft diffused butterfly lighting", "fill": "subtle studio fill", "effect": "high-fashion clean illumination, emphasizes texture and drape"},
  "negative_prompts": ["glasses", "gloves", "motion blur", "low resolution", "extra limbs", "text or watermark", "plastic skin", "fabric shine", "incorrect anatomy", "cropped extremities"]
}

---

## Template 3: Premium Sport Jersey (Amir Mushich 7.1)
**Use for:** Floating branded football/sport jersey editorial

### Text Prompt
[BRAND NAME]. Act as a fashion photographer and creative director shooting a high-end editorial lookbook for a bespoke football jersey designed by this brand.

THE SUBJECT & COMPOSITION (FLOATING & ANGLED):
A single, premium custom football jersey is floating suspended in mid-air, centered in the frame. There is no hanger visible. The jersey is rotated slightly (approximately 15 degrees angled view) to show depth. The fabric must show realistic weight, deep gravity-defying folds, creases, and natural wrinkles.

BRANDED DESIGN & AESTHETICS:
The official [BRAND NAME] logo is authentically applied as the main club crest on the chest.

MATERIALITY & TEXTURE: Heavyweight, retro-inspired athletic cotton-blend or technical knit with visible, coarse weave structure.

ENVIRONMENT: Abstract, infinite white photo studio cyclorama space.

LIGHTING: Sophisticated studio lighting. Soft, diffused light that sculpts the folds of the fabric. Hyper-realistic editorial fashion photography.

---

## Template 4: Photo Campaign Triptych (Amir Mushich 7.2)
**Use for:** 3-panel editorial fashion campaign with close-up focus

### Text Prompt
[BRAND NAME]. A high-end, hyper-realistic editorial fashion photography triptych campaign.

Act as a world-class fashion photographer shooting a defining image campaign. Create a cohesive 3-panel editorial layout, stacked horizontally (top, middle, bottom panels).

THE MUSE (AI AUTONOMY): Analyze the brand's archetype and audience. Autonomously generate the ultimate human muse.

THE TRIPTYCH:
- Top Panel (The Intense Portrait): Cinematic, tight headshot focusing on eyes and face.
- Middle Panel (The Gesture/Action): Tight crop focusing on a specific body part in motion or repose.
- Bottom Panel (The Ultimate Texture/Symbol): Extreme macro close-up of garment fabric, jewelry, or symbolic prop.

STYLING: Push boundaries. Avant-garde high fashion. Raw, expensive, and tactile.

TECHNICAL: Strong film grain, highly detailed textures, bold cinematic lighting, chiaroscuro.

---

## Template 5: Hypebeast Showroom (Amir Mushich 7.3)
**Use for:** Limited merchandise drop announcement still life

### Text Prompt
[BRAND NAME]. Act as a Creative Director and Still Life Photographer for a hypebeast fashion publication.

Create a high-end "Showroom Still Life" photograph announcing a limited merchandise drop.

PHASE 1: AUTONOMOUS CURATION: Analyze brand, determine palette, select merch item.
PHASE 2: SET DESIGN: White powder-coated metal rack, hanging jacket, stacked core products, hand-painted canvas backdrop.
PHASE 3: PHYSICAL BRANDING: Chenille patches, embroidery on merch. Correct logo visibility on products.
PHASE 4: PHOTOGRAPHY: Soft directional window light. 50mm or 85mm lens.
PHASE 5: UI OVERLAY: Large white logo left side, small slogan text.

---

## Template 6: Cross-branded Winter Outerwear (Amir Mushich 7.4)
**Use for:** Technical outerwear collaboration campaign

### Text Prompt
[BRAND NAME]. Act as a Creative Director for a technical outerwear brand.

PHASE 1: PARTNER SELECTION: Analyze brand DNA. Select partner (Moncler/Arc'teryx/Nike ACG). Design heavy technical outerwear with structured HOOD/HIGH COLLAR in brand's signature color.
PHASE 2: PHOTOGRAPHY: Tight head-and-shoulders side profile shot. Model faces left. Chiaroscuro tech lighting.
PHASE 3: UI OVERLAY: "Technical Blueprint" interface (thin white lines, grid, tech specs, partner logos).
PHASE 4: 100mm Macro Lens, f/8, High Contrast, Unreal Engine 5 render quality.

---

## Template 7: Crocs Collaboration (Amir Mushich 7.5)
**Use for:** Brand x Crocs collaboration campaign

### Text Prompt
[BRAND NAME]. Act as a World-Class Footwear Designer creating a "Crocs Collaboration" campaign image.

THE SUBJECT: Photorealistic Crocs Classic Clog in side profile view.
- Color Blocking: Body (primary color), Sole/Strap (secondary colors)
- Custom Jibbitz: 3-4 high-quality 3D charms associated with [BRAND NAME]

BACKGROUND: Pure White Studio Space (#FFFFFF)
LIGHTING: Ultra-realistic High-Key Studio Lighting, matte Croslite foam resin texture
BRANDING: Monochrome grey logos for [BRAND NAME] and "Crocs" in corners
TECH: Macro product photography, Phase One camera, 100mm lens, 8k resolution

---

## Template 8: Style Factory (Amir Mushich 7.6)
**Use for:** Fashion styling with face-accurate model

### Text Prompt
Main model (use image input with the face 100% accurate).
Wearing: [detailed clothing description - pieces, color scheme, style, layers, fabrics].
Paired with footwear: [type and details of shoes; include accessories].
Setting: studio backdrop in soft [describe color/tone/texture].
Lighting: soft cinematic studio lighting.
Style: [define style - editorial, streetwear, etc.].
Composition: model [describe pose] on [describe object], with [accessories/pose details].

---

## Template 9: Branded Boxing Gloves (Amir Mushich 7.7)
**Use for:** Luxury brand reinterpretation as premium boxing gloves

### Text Prompt
[BRAND NAME], conceptualized as a pair of premium, professional-grade leather boxing gloves. The design is a complete luxury reinterpretation using the signature color palette and iconic patterns of the brand. The primary brand logo is prominent across the main dorsal striking area and repeated on the wrist cuffs. Crafted from high-quality, supple full-grain leather with precise reinforced stitching. Hanging against a clean, seamless studio white background. Professional studio lighting with subtle cinematic bloom. Rendered with a 50mm prime lens aesthetic and shallow depth of field. 3D product render.

---

## Template 10: Brands as Sport Clubs (Amir Mushich 7.8)
**Use for:** Viral "Football Club Concept Kit" presentation

### Text Prompt
[BRAND NAME]. Act as a professional sports brand identity designer creating a viral "Football Club Concept Kit" presentation board.

COMPOSITION: Symmetrical 2x2 bento grid of white, rounded-rectangular "cards" on a deep brand-colored background.

THE 4 GRID CONTAINERS:
1. TOP LEFT (The Crest): Brand logo redesigned into a Football Club Badge
2. TOP RIGHT (The Icon): Clean, minimalist initials or icon in sporty typography
3. BOTTOM LEFT (The Kit): Photorealistic 3D render of the official Team Jersey
4. BOTTOM RIGHT (The Flag): 3D simulation of a waving team silk flag

CENTERPIECE: Discreet monochrome original logo in the center gap.
AESTHETICS: Bento Box UI design, soft shadows.

---

## Identity Anchoring Principles

JSON-structured prompts achieve higher adherence rates than prose prompts for fashion/editorial:

1. **Lock identity first**: `"identity_accuracy": "100% match"` prevents face drift
2. **Negative prompts are critical**: Explicitly exclude common failures (extra limbs, plastic skin, identity change)
3. **Camera spec = consistency**: Phase One XF with specific aperture/ISO creates reproducible lighting
4. **Wardrobe as constraint**: Specify fabric material AND texture (wool gabardine ≠ polyester) to prevent AI default to shiny fabrics
5. **Pose decomposition**: Break pose into body_orientation + shoulders + head + arms + hands for precise control

---

## Visual Examples

### Aleena Amir Editorial
![Multi-Angle Contact Sheet](images/grid_contact_sheet.jpg)
![Crimson Confidence Editorial](images/crimson_suit.jpg)

### Amir Mushich Apparel (Section 7)
![7.1 Premium Sport Jersey](images/2010426555843871121.jpg)
![7.2 Photo Campaign Triptych](images/2007890867626057901.jpg)
![7.3 Hypebeast Showroom](images/2015862641311219772.jpg)
![7.4 Cross-branded Winter Outerwear](images/2016245336948244946.jpg)
![7.5 Crocs Collaboration](images/2013325907843219831.jpg)
![7.6 Style Factory](images/1978207029232898373.jpg)
![7.7 Branded Boxing Gloves](images/2001186860115153355.jpg)
![7.8 Brands as Sport Clubs](images/2010789281300701307.jpg)
