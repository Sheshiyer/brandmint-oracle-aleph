# Product Photography Prompt Templates

## Template 1: Product Design Journal / Catalog (Firat Bilal)
**Use for:** Dual-section layout — lifestyle hero top + technical drawings bottom

### JSON Prompt
{
  "reference_images": {
    "product_image": "UPLOADED_IMAGE",
    "usage_rule": "Use the uploaded image as the exact visual reference for the product's form, proportions, materials, and overall identity. Do not redesign or reinterpret the product."
  },
  "layout": {
    "canvas": {"orientation": "vertical", "aspect_ratio": "3:4", "background": "warm neutral paper-like surface"},
    "structure": {"top_section": "lifestyle_hero", "bottom_section": "technical_specification"}
  },
  "top_section": {
    "type": "lifestyle_product_image",
    "composition": {"placement": "top_center", "scale": "dominant", "margin": "generous whitespace around product"},
    "environment": {
      "setting": "minimal architectural interior",
      "lighting": {"type": "natural sunlight", "direction": "angled side light", "quality": "soft but high-contrast shadows"},
      "floor": "subtle concrete or stone surface",
      "background": "textured plaster wall"
    },
    "rendering": {"style": "editorial lifestyle photography", "detail": "high realism", "color_grading": "warm, muted, premium"}
  },
  "bottom_section": {
    "type": "technical_specification_panel",
    "layout": {"grid": "modular", "alignment": "clean, architectural"},
    "technical_drawings": {
      "placement": "bottom_left_and_center",
      "style": "architectural line drawings",
      "views": ["front view", "side view", "three-quarter cutaway or profile view"],
      "projection": "orthographic",
      "line_style": {"color": "muted red or sepia", "weight": "fine technical lines"},
      "annotations": {"type": "measurement and construction callouts", "language": "neutral technical labels", "density": "minimal, editorial"}
    },
    "materials_panel": {
      "placement": "bottom_right",
      "content": {"type": "material_swatches", "count": "3-4 depending on product", "format": "square or rectangular samples"},
      "textures": {"source": "derived from the product materials", "examples": ["fabric", "leather", "metal", "wood", "plastic"]},
      "labels": {"style": "small editorial captions", "tone": "technical but refined"}
    }
  },
  "typography": {"style": "minimal editorial", "usage": "subtle captions, no large headlines", "color": "soft black or dark brown"},
  "overall_style": {"mood": "design catalog / product design journal", "aesthetic": "architectural, premium, calm", "avoid": ["clutter", "bold colors", "heavy branding", "overly decorative graphics"]},
  "constraints": {"do_not": ["change product design", "invent new materials", "add logos unless present in reference", "use perspective distortion in drawings"]}
}

---

## Template 2: Commercial Beverage Hero Shot (Johnn)
**Use for:** 8K frozen-motion beverage photography with splash physics

### JSON Prompt
{
  "master_prompt": {
    "global_settings": {
      "resolution": "8K ultra-high-definition",
      "aspect_ratio": "3:4 vertical",
      "style": "hyper-realistic AI-edited commercial beverage photography",
      "sharpness": "extreme clarity, micro-detail visibility",
      "lighting_quality": "cinematic studio lighting with controlled highlights and shadows",
      "motion_freeze": "high-speed capture, frozen liquid splashes and particles",
      "noise": "none",
      "artifacts": "none"
    },
    "module_1_glass_beverage_style": {
      "subject": {
        "type": "transparent glass",
        "glass_style": "tall cylindrical glass with thick base",
        "surface_details": "cold condensation droplets on outer glass surface",
        "fill_level": "80 percent full"
      },
      "liquid_and_layers": {
        "beverage_type": "iced latte or chocolate protein shake",
        "liquid_color": "rich coffee brown or creamy cocoa",
        "layering": "soft milk-to-coffee gradient with subtle swirls",
        "texture": "smooth, thick, glossy, realistic viscosity"
      },
      "motion_and_splash": {
        "action": "liquid splash erupting from inside the glass",
        "splash_behavior": "curved arcs rising above rim with suspended droplets",
        "droplet_detail": "micro droplets frozen mid-air with sharp definition"
      },
      "floating_elements": {
        "ice_cubes": "large clear ice cubes rotating in mid-air",
        "coffee_beans_or_cocoa": "roasted coffee beans or cocoa powder particles floating",
        "cream_stream": "thin stream of milk or cream pouring into glass"
      },
      "pose_and_camera": {
        "position": "centered hero composition",
        "angle": "three-quarter close-up",
        "camera_feel": "slightly low angle for premium, powerful presence"
      },
      "background": {
        "color_palette": "deep espresso brown fading into warm beige highlights",
        "bokeh": "soft cinematic bokeh lights with warm glow",
        "atmosphere": "luxurious, indulgent, high-end cafe mood"
      },
      "surface_and_reflection": {
        "base": "wet reflective surface with subtle liquid pooling",
        "shadow_style": "clean, soft separated shadow beneath glass",
        "reflection_quality": "controlled highlights along glass edges"
      }
    }
  }
}

---

## Template 3: Beauty Product Flat-lay (Oogie - Laneige Style)
**Use for:** Skincare/cosmetic editorial with floral and dewy aesthetics

### Text Prompt
A hyper-realistic beauty product photograph of a [PRODUCT DESCRIPTION] placed at the center of a vibrant pastel-[COLOR] surface covered in fresh water droplets, the jar upright with a frosted [COLOR] lid and glossy translucent body, surrounded organically by delicate flowers including [FLOWER TYPES] arranged diagonally around the product, soft diffused studio lighting from above creating gentle highlights and natural shadows, moisture beads sparkling across the background for a fresh dewy feel, clean skincare editorial aesthetic, feminine and luxurious mood, balanced flat-lay composition, shallow depth of field, ultra-detailed textures, photorealistic, high-end cosmetic advertising style, 8K quality.

### Variables
- [PRODUCT DESCRIPTION]: e.g., "pink LANEIGE Lip Sleeping Mask jar"
- [COLOR]: product-matched pastel tone
- [FLOWER TYPES]: e.g., "purple blossoms, pale lilies, yellow sprigs, and green leaves"

---

## Photography Principles

1. **JSON > Prose**: JSON-structured prompts yield 2-3x higher adherence on Nano Banana Pro
2. **8K is baseline**: Always specify 8K UHD for commercial-grade output
3. **Frozen motion**: Use "high-speed capture" + "frozen liquid splashes" for beverage dynamics
4. **Orthographic for tech**: Technical drawings must use orthographic projection, never perspective
5. **Separated shadows**: Commercial photography uses clean, soft separated shadows beneath products
6. **Condensation = realism**: Adding "cold condensation droplets" to glass surfaces dramatically increases photorealism

---

## Visual Examples

### Firat Bilal - Product Design Catalog
![Ultraman Catalog Layout](images/ultraman_catalog.jpg)
![Mamma Mia Catalog Layout](images/mammamia_catalog.jpg)

### Johnn - Commercial Beverage
![Beverage Hero Shot 1](images/bev_1.jpg)
![Beverage Hero Shot 2](images/bev_2.jpg)
![Beverage Hero Shot 3](images/bev_3.jpg)
![Beverage Hero Shot 4](images/bev_4.jpg)

### Oogie - Beauty Product (Laneige)
![Laneige Flat-lay 1](images/laneige_1.jpg)
![Laneige Flat-lay 2](images/laneige_2.jpg)
![Laneige Flat-lay 3](images/laneige_3.jpg)
