"""
compositor.py — Logo and product image compositing engine.

Provides pixel-exact overlay of user-provided logos and product images onto
AI-generated scenes. This is the core answer to "why not use the real logo?"
— guarantees pixel fidelity instead of relying on AI reinterpretation.

Supports:
- Logo compositing with 9-grid positioning, scale, blend modes, padding, shadow
- Product image compositing with feathered edges
- Post-generation composite pass (generate scene → overlay real logo)
- Multi-layer stacking (background + product + logo + text)

Requires: pip install brandmint[vision]  (Pillow >= 10.0)
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

try:
    from PIL import Image, ImageFilter

    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False

from .image_utils import _require_pillow, analyze_logo, load_image, save_image


# ---------------------------------------------------------------------------
# Enums and config
# ---------------------------------------------------------------------------


class Position(str, Enum):
    """9-grid positioning for logo/overlay placement."""

    TOP_LEFT = "top-left"
    TOP_CENTER = "top-center"
    TOP_RIGHT = "top-right"
    CENTER_LEFT = "center-left"
    CENTER = "center"
    CENTER_RIGHT = "center-right"
    BOTTOM_LEFT = "bottom-left"
    BOTTOM_CENTER = "bottom-center"
    BOTTOM_RIGHT = "bottom-right"


class BlendMode(str, Enum):
    NORMAL = "normal"
    MULTIPLY = "multiply"
    SCREEN = "screen"


@dataclass
class CompositeConfig:
    """Configuration for a single composite operation."""

    position: Position = Position.BOTTOM_RIGHT
    scale: float = 0.15  # fraction of canvas width
    padding: int = 20  # pixels from edge
    blend_mode: BlendMode = BlendMode.NORMAL
    opacity: float = 1.0  # 0.0 to 1.0
    shadow: bool = False
    shadow_offset: tuple[int, int] = (3, 3)
    shadow_blur: int = 5
    shadow_color: tuple[int, int, int, int] = (0, 0, 0, 100)


@dataclass
class LayerDef:
    """Definition for one layer in a multi-layer composite."""

    image: "Image.Image"
    position: Position = Position.CENTER
    scale: float = 1.0
    opacity: float = 1.0
    blend_mode: BlendMode = BlendMode.NORMAL
    padding: int = 0


# ---------------------------------------------------------------------------
# AF-06: Logo Compositing Engine
# ---------------------------------------------------------------------------


class LogoCompositor:
    """Composite a logo onto a background with precise positioning and blending."""

    def composite(
        self,
        background: "Image.Image",
        logo: "Image.Image",
        config: Optional[CompositeConfig] = None,
    ) -> "Image.Image":
        """Overlay logo onto background at configured position/scale/blend."""
        _require_pillow()
        if config is None:
            config = CompositeConfig()

        result = background.copy().convert("RGBA")
        logo_rgba = logo.convert("RGBA")

        # Scale logo relative to canvas width
        target_w = int(result.width * config.scale)
        if target_w < 1:
            target_w = 1
        ratio = target_w / logo_rgba.width
        target_h = int(logo_rgba.height * ratio)
        if target_h < 1:
            target_h = 1
        logo_scaled = logo_rgba.resize((target_w, target_h), Image.LANCZOS)

        # Apply opacity
        if config.opacity < 1.0:
            logo_scaled = _apply_opacity(logo_scaled, config.opacity)

        # Add drop shadow
        if config.shadow:
            shadow_layer = _create_shadow(
                logo_scaled, config.shadow_offset, config.shadow_blur, config.shadow_color
            )
            sx, sy = _compute_position(
                result.size, shadow_layer.size, config.position, config.padding
            )
            result = Image.alpha_composite(result, _place_on_canvas(shadow_layer, result.size, sx, sy))

        # Compute position
        x, y = _compute_position(result.size, logo_scaled.size, config.position, config.padding)

        # Apply blend mode
        if config.blend_mode == BlendMode.NORMAL:
            result = Image.alpha_composite(result, _place_on_canvas(logo_scaled, result.size, x, y))
        elif config.blend_mode == BlendMode.MULTIPLY:
            result = _blend_multiply(result, logo_scaled, x, y)
        elif config.blend_mode == BlendMode.SCREEN:
            result = _blend_screen(result, logo_scaled, x, y)

        return result

    def composite_from_paths(
        self,
        background_path: str,
        logo_path: str,
        output_path: str,
        config: Optional[CompositeConfig] = None,
    ) -> str:
        """Convenience: load files, composite, save result."""
        bg = load_image(background_path)
        logo = load_image(logo_path)
        result = self.composite(bg, logo, config)
        return save_image(result, output_path)


# ---------------------------------------------------------------------------
# AF-07: Product Image Compositing
# ---------------------------------------------------------------------------


class ProductCompositor:
    """Composite real product photos into generated scene backgrounds."""

    def composite(
        self,
        background: "Image.Image",
        product_image: "Image.Image",
        position: Position = Position.CENTER,
        scale: float = 0.5,
        feather_radius: int = 5,
        padding: int = 20,
        opacity: float = 1.0,
    ) -> "Image.Image":
        """Place product image into background with feathered edges."""
        _require_pillow()

        result = background.copy().convert("RGBA")
        product = product_image.convert("RGBA")

        # Auto-remove white background if product doesn't have transparency
        product = _auto_remove_background(product)

        # Scale product
        target_w = int(result.width * scale)
        if target_w < 1:
            target_w = 1
        ratio = target_w / product.width
        target_h = int(product.height * ratio)
        if target_h < 1:
            target_h = 1
        product_scaled = product.resize((target_w, target_h), Image.LANCZOS)

        # Feather edges
        if feather_radius > 0:
            product_scaled = _feather_edges(product_scaled, feather_radius)

        # Apply opacity
        if opacity < 1.0:
            product_scaled = _apply_opacity(product_scaled, opacity)

        # Position and composite
        x, y = _compute_position(result.size, product_scaled.size, position, padding)
        result = Image.alpha_composite(result, _place_on_canvas(product_scaled, result.size, x, y))

        return result


# ---------------------------------------------------------------------------
# AF-08: Post-Generation Composite Pass
# ---------------------------------------------------------------------------


class PostGenCompositor:
    """Two-step pipeline: AI generates scene → overlay real logo at configured position."""

    def __init__(self, logo_compositor: Optional[LogoCompositor] = None):
        self.logo_compositor = logo_compositor or LogoCompositor()

    def composite_pass(
        self,
        generated_image_path: str,
        logo_path: str,
        output_path: str,
        config: Optional[CompositeConfig] = None,
    ) -> str:
        """Apply composite pass to an already-generated image."""
        return self.logo_compositor.composite_from_paths(
            generated_image_path, logo_path, output_path, config
        )

    def composite_pass_with_analysis(
        self,
        generated_image_path: str,
        logo_path: str,
        output_path: str,
        position: Optional[Position] = None,
        scale: Optional[float] = None,
    ) -> str:
        """Composite with auto-derived parameters from logo analysis."""
        analysis = analyze_logo(logo_path)

        # Auto-determine scale based on logo aspect ratio
        if scale is None:
            if analysis.aspect_ratio > 2.0:
                scale = 0.20  # wide logos need more space
            elif analysis.aspect_ratio < 0.5:
                scale = 0.10  # tall logos
            else:
                scale = 0.15  # square-ish logos

        config = CompositeConfig(
            position=position or Position.BOTTOM_RIGHT,
            scale=scale,
            shadow=analysis.has_transparency,
        )

        return self.logo_compositor.composite_from_paths(
            generated_image_path, logo_path, output_path, config
        )


# ---------------------------------------------------------------------------
# AF-09: Multi-Layer Compositor
# ---------------------------------------------------------------------------


class LayerStack:
    """Stack multiple layers: background + product + logo + optional text."""

    def __init__(self, canvas_size: tuple[int, int]):
        _require_pillow()
        self.canvas_size = canvas_size
        self.layers: list[LayerDef] = []

    def add_layer(
        self,
        image: "Image.Image",
        position: Position = Position.CENTER,
        scale: float = 1.0,
        opacity: float = 1.0,
        blend_mode: BlendMode = BlendMode.NORMAL,
        padding: int = 0,
    ) -> "LayerStack":
        """Add a layer to the stack. Returns self for chaining."""
        self.layers.append(
            LayerDef(
                image=image,
                position=position,
                scale=scale,
                opacity=opacity,
                blend_mode=blend_mode,
                padding=padding,
            )
        )
        return self

    def add_background(self, image: "Image.Image") -> "LayerStack":
        """Add a full-canvas background layer."""
        return self.add_layer(image, Position.CENTER, scale=1.0)

    def add_logo(
        self,
        image: "Image.Image",
        position: Position = Position.BOTTOM_RIGHT,
        scale: float = 0.15,
        padding: int = 20,
        opacity: float = 1.0,
    ) -> "LayerStack":
        """Add a logo overlay layer."""
        return self.add_layer(image, position, scale, opacity, padding=padding)

    def add_product(
        self,
        image: "Image.Image",
        position: Position = Position.CENTER,
        scale: float = 0.5,
        opacity: float = 1.0,
    ) -> "LayerStack":
        """Add a product image layer."""
        return self.add_layer(image, position, scale, opacity)

    def flatten(self) -> "Image.Image":
        """Composite all layers in order and return the flattened result."""
        _require_pillow()
        canvas = Image.new("RGBA", self.canvas_size, (0, 0, 0, 0))

        for layer_def in self.layers:
            layer_img = layer_def.image.convert("RGBA")

            # Scale
            if layer_def.scale >= 1.0:
                # Full canvas coverage — resize to fill
                layer_img = layer_img.resize(self.canvas_size, Image.LANCZOS)
            else:
                target_w = int(self.canvas_size[0] * layer_def.scale)
                if target_w < 1:
                    target_w = 1
                ratio = target_w / layer_img.width
                target_h = int(layer_img.height * ratio)
                if target_h < 1:
                    target_h = 1
                layer_img = layer_img.resize((target_w, target_h), Image.LANCZOS)

            # Opacity
            if layer_def.opacity < 1.0:
                layer_img = _apply_opacity(layer_img, layer_def.opacity)

            # Position
            x, y = _compute_position(
                self.canvas_size, layer_img.size, layer_def.position, layer_def.padding
            )

            # Composite
            placed = _place_on_canvas(layer_img, self.canvas_size, x, y)
            if layer_def.blend_mode == BlendMode.NORMAL:
                canvas = Image.alpha_composite(canvas, placed)
            elif layer_def.blend_mode == BlendMode.MULTIPLY:
                canvas = _blend_multiply(canvas, layer_img, x, y)
            elif layer_def.blend_mode == BlendMode.SCREEN:
                canvas = _blend_screen(canvas, layer_img, x, y)

        return canvas

    def flatten_and_save(self, output_path: str, quality: int = 95) -> str:
        """Flatten and save to disk."""
        result = self.flatten()
        return save_image(result, output_path)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _compute_position(
    canvas_size: tuple[int, int],
    overlay_size: tuple[int, int],
    position: Position,
    padding: int,
) -> tuple[int, int]:
    """Compute (x, y) for placing overlay on canvas."""
    cw, ch = canvas_size
    ow, oh = overlay_size

    positions = {
        Position.TOP_LEFT: (padding, padding),
        Position.TOP_CENTER: ((cw - ow) // 2, padding),
        Position.TOP_RIGHT: (cw - ow - padding, padding),
        Position.CENTER_LEFT: (padding, (ch - oh) // 2),
        Position.CENTER: ((cw - ow) // 2, (ch - oh) // 2),
        Position.CENTER_RIGHT: (cw - ow - padding, (ch - oh) // 2),
        Position.BOTTOM_LEFT: (padding, ch - oh - padding),
        Position.BOTTOM_CENTER: ((cw - ow) // 2, ch - oh - padding),
        Position.BOTTOM_RIGHT: (cw - ow - padding, ch - oh - padding),
    }
    return positions.get(position, ((cw - ow) // 2, (ch - oh) // 2))


def _place_on_canvas(
    overlay: "Image.Image", canvas_size: tuple[int, int], x: int, y: int
) -> "Image.Image":
    """Place an RGBA overlay onto a transparent canvas at (x, y)."""
    canvas = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
    canvas.paste(overlay, (x, y), overlay)
    return canvas


def _apply_opacity(img: "Image.Image", opacity: float) -> "Image.Image":
    """Reduce opacity of an RGBA image."""
    img = img.copy()
    alpha = img.split()[-1]
    alpha = alpha.point(lambda p: int(p * opacity))
    img.putalpha(alpha)
    return img


def _create_shadow(
    img: "Image.Image",
    offset: tuple[int, int],
    blur: int,
    color: tuple[int, int, int, int],
) -> "Image.Image":
    """Create a drop shadow from an image's alpha channel."""
    shadow = Image.new("RGBA", img.size, color)
    alpha = img.split()[-1]
    shadow.putalpha(alpha)
    shadow = shadow.filter(ImageFilter.GaussianBlur(blur))
    # Offset: create a larger canvas and paste with offset
    w, h = img.size
    canvas = Image.new("RGBA", (w + abs(offset[0]), h + abs(offset[1])), (0, 0, 0, 0))
    canvas.paste(shadow, (max(offset[0], 0), max(offset[1], 0)), shadow)
    return canvas.crop((0, 0, w, h))


def _auto_remove_background(img: "Image.Image", threshold: int = 240) -> "Image.Image":
    """Remove near-white background from a product image."""
    if img.mode == "RGBA":
        # Already has alpha — check if it's actually used
        alpha = img.split()[-1]
        if alpha.getextrema()[0] < 250:
            return img  # Already has meaningful transparency

    rgb = img.convert("RGB")
    rgba = img.convert("RGBA")
    pixels = rgba.load()
    rgb_pixels = rgb.load()
    w, h = rgba.size

    for y in range(h):
        for x in range(w):
            r, g, b = rgb_pixels[x, y]
            if r > threshold and g > threshold and b > threshold:
                pixels[x, y] = (r, g, b, 0)  # Make transparent

    return rgba


def _feather_edges(img: "Image.Image", radius: int) -> "Image.Image":
    """Feather (soften) edges of an RGBA image's alpha channel."""
    alpha = img.split()[-1]
    # Blur the alpha channel to create soft edges
    feathered_alpha = alpha.filter(ImageFilter.GaussianBlur(radius))
    img = img.copy()
    img.putalpha(feathered_alpha)
    return img


def _blend_multiply(
    base: "Image.Image", overlay: "Image.Image", x: int, y: int
) -> "Image.Image":
    """Multiply blend mode at specific position."""
    result = base.copy()
    region = result.crop((x, y, x + overlay.width, y + overlay.height))
    # Multiply: pixel = base * overlay / 255
    from PIL import ImageChops

    multiplied = ImageChops.multiply(region.convert("RGB"), overlay.convert("RGB"))
    alpha = overlay.split()[-1] if overlay.mode == "RGBA" else None
    result.paste(multiplied.convert("RGBA"), (x, y), alpha)
    return result


def _blend_screen(
    base: "Image.Image", overlay: "Image.Image", x: int, y: int
) -> "Image.Image":
    """Screen blend mode at specific position."""
    result = base.copy()
    region = result.crop((x, y, x + overlay.width, y + overlay.height))
    from PIL import ImageChops

    screened = ImageChops.screen(region.convert("RGB"), overlay.convert("RGB"))
    alpha = overlay.split()[-1] if overlay.mode == "RGBA" else None
    result.paste(screened.convert("RGBA"), (x, y), alpha)
    return result
