"""
image_utils.py — Image processing utilities for the asset fidelity pipeline.

Provides:
- Image I/O: load, save, convert between formats
- Metadata extraction: dimensions, color profile, transparency, DPI
- Logo analysis: bounding box, dominant colors, transparency mask, aspect ratio

Requires: pip install brandmint[vision]  (Pillow >= 10.0)
"""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional

try:
    from PIL import Image

    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False

try:
    import colorgram as colorgram_mod

    HAS_COLORGRAM = True
except ImportError:
    HAS_COLORGRAM = False


def _require_pillow():
    if not HAS_PILLOW:
        raise ImportError(
            "Pillow is required for image processing. "
            "Install with: pip install 'brandmint[vision]'"
        )


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


class ImageFormat(str, Enum):
    PNG = "png"
    JPEG = "jpeg"
    WEBP = "webp"
    SVG = "svg"
    GIF = "gif"
    UNKNOWN = "unknown"


class ColorMode(str, Enum):
    RGB = "RGB"
    RGBA = "RGBA"
    CMYK = "CMYK"
    L = "L"  # grayscale
    LA = "LA"  # grayscale + alpha
    P = "P"  # palette
    UNKNOWN = "unknown"


@dataclass
class AssetMetadata:
    """Structured metadata extracted from an image file."""

    width: int = 0
    height: int = 0
    format: ImageFormat = ImageFormat.UNKNOWN
    color_mode: ColorMode = ColorMode.UNKNOWN
    has_transparency: bool = False
    dpi: tuple[int, int] = (72, 72)
    file_size_kb: float = 0.0
    file_path: str = ""

    @property
    def aspect_ratio(self) -> float:
        if self.height == 0:
            return 0.0
        return self.width / self.height

    @property
    def is_landscape(self) -> bool:
        return self.width > self.height

    @property
    def is_portrait(self) -> bool:
        return self.height > self.width

    @property
    def is_square(self) -> bool:
        return self.width == self.height


@dataclass
class DominantColor:
    """A dominant color extracted from an image."""

    r: int
    g: int
    b: int
    proportion: float = 0.0

    @property
    def hex(self) -> str:
        return f"#{self.r:02x}{self.g:02x}{self.b:02x}"

    @property
    def rgb(self) -> tuple[int, int, int]:
        return (self.r, self.g, self.b)


@dataclass
class BoundingBox:
    """Bounding box of non-transparent content."""

    left: int = 0
    top: int = 0
    right: int = 0
    bottom: int = 0

    @property
    def width(self) -> int:
        return self.right - self.left

    @property
    def height(self) -> int:
        return self.bottom - self.top

    @property
    def center(self) -> tuple[int, int]:
        return ((self.left + self.right) // 2, (self.top + self.bottom) // 2)


@dataclass
class LogoAnalysis:
    """Comprehensive analysis of a logo image."""

    bounding_box: BoundingBox = field(default_factory=BoundingBox)
    dominant_colors: list[DominantColor] = field(default_factory=list)
    has_transparency: bool = False
    is_svg: bool = False
    aspect_ratio: float = 1.0
    trimmed_width: int = 0
    trimmed_height: int = 0
    original_width: int = 0
    original_height: int = 0
    color_count: int = 0
    file_path: str = ""


# ---------------------------------------------------------------------------
# Image I/O
# ---------------------------------------------------------------------------


def load_image(path: str | Path) -> "Image.Image":
    """Load an image from disk. Handles SVG via rsvg-convert fallback."""
    _require_pillow()
    path = str(path)

    if _detect_format_from_path(path) == ImageFormat.SVG:
        return _load_svg(path)

    img = Image.open(path)
    img.load()  # force full read
    return img


def save_image(
    img: "Image.Image",
    path: str | Path,
    quality: int = 95,
    optimize: bool = True,
) -> str:
    """Save an image, auto-detecting format from extension."""
    _require_pillow()
    path = str(path)
    fmt = _detect_format_from_path(path)

    kwargs: dict = {}
    if fmt == ImageFormat.JPEG:
        if img.mode == "RGBA":
            img = img.convert("RGB")
        kwargs = {"quality": quality, "optimize": optimize}
    elif fmt == ImageFormat.PNG:
        kwargs = {"optimize": optimize}
    elif fmt == ImageFormat.WEBP:
        kwargs = {"quality": quality}

    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    img.save(path, **kwargs)
    return path


def convert_format(
    src_path: str | Path,
    dst_path: str | Path,
    quality: int = 95,
) -> str:
    """Convert an image from one format to another."""
    img = load_image(src_path)
    return save_image(img, dst_path, quality=quality)


def get_format(path: str | Path) -> ImageFormat:
    """Detect image format from magic bytes, falling back to extension."""
    path = str(path)

    # Check magic bytes first
    try:
        with open(path, "rb") as f:
            header = f.read(16)
        if header[:8] == b"\x89PNG\r\n\x1a\n":
            return ImageFormat.PNG
        if header[:2] == b"\xff\xd8":
            return ImageFormat.JPEG
        if header[:4] == b"RIFF" and header[8:12] == b"WEBP":
            return ImageFormat.WEBP
        if header[:4] == b"GIF8":
            return ImageFormat.GIF
        # SVG detection (text-based)
        if b"<svg" in header or b"<?xml" in header:
            return ImageFormat.SVG
    except (OSError, IOError):
        pass

    return _detect_format_from_path(path)


def get_dimensions(path: str | Path) -> tuple[int, int]:
    """Get image dimensions (width, height) without loading full image."""
    _require_pillow()
    path = str(path)

    if get_format(path) == ImageFormat.SVG:
        # SVG dimensions require parsing or rasterization
        img = _load_svg(path)
        return img.size

    with Image.open(path) as img:
        return img.size


# ---------------------------------------------------------------------------
# Metadata extraction (AF-02)
# ---------------------------------------------------------------------------


def extract_metadata(path: str | Path) -> AssetMetadata:
    """Extract comprehensive metadata from an image file."""
    _require_pillow()
    path = str(path)

    fmt = get_format(path)
    file_size_kb = os.path.getsize(path) / 1024.0

    if fmt == ImageFormat.SVG:
        img = _load_svg(path)
        return AssetMetadata(
            width=img.width,
            height=img.height,
            format=ImageFormat.SVG,
            color_mode=ColorMode(img.mode) if img.mode in ColorMode.__members__ else ColorMode.UNKNOWN,
            has_transparency=img.mode in ("RGBA", "LA"),
            dpi=(72, 72),
            file_size_kb=file_size_kb,
            file_path=path,
        )

    with Image.open(path) as img:
        width, height = img.size
        mode = img.mode
        dpi = img.info.get("dpi", (72, 72))
        # Ensure DPI is a tuple of ints
        dpi = (int(dpi[0]), int(dpi[1]))

        has_transparency = _detect_transparency(img)
        color_mode = ColorMode(mode) if mode in ColorMode.__members__ else ColorMode.UNKNOWN

    return AssetMetadata(
        width=width,
        height=height,
        format=fmt,
        color_mode=color_mode,
        has_transparency=has_transparency,
        dpi=dpi,
        file_size_kb=file_size_kb,
        file_path=path,
    )


# ---------------------------------------------------------------------------
# Logo analysis (AF-03)
# ---------------------------------------------------------------------------


def analyze_logo(path: str | Path, max_colors: int = 5) -> LogoAnalysis:
    """Analyze a logo image: bounding box, colors, transparency, aspect ratio."""
    _require_pillow()
    path = str(path)

    is_svg = get_format(path) == ImageFormat.SVG
    img = load_image(path)

    original_w, original_h = img.size
    has_transparency = _detect_transparency(img)

    # Compute bounding box of non-transparent/non-white content
    bbox = _compute_content_bbox(img)

    # Extract dominant colors
    dominant_colors = _extract_dominant_colors(img, max_colors)

    # Trimmed dimensions
    trimmed_w = bbox.width if bbox.width > 0 else original_w
    trimmed_h = bbox.height if bbox.height > 0 else original_h
    aspect = trimmed_w / trimmed_h if trimmed_h > 0 else 1.0

    # Approximate unique color count
    color_count = _count_unique_colors(img)

    return LogoAnalysis(
        bounding_box=bbox,
        dominant_colors=dominant_colors,
        has_transparency=has_transparency,
        is_svg=is_svg,
        aspect_ratio=round(aspect, 3),
        trimmed_width=trimmed_w,
        trimmed_height=trimmed_h,
        original_width=original_w,
        original_height=original_h,
        color_count=color_count,
        file_path=path,
    )


def generate_transparency_mask(path: str | Path) -> Optional["Image.Image"]:
    """Generate a binary transparency mask from a logo (white=opaque, black=transparent)."""
    _require_pillow()
    img = load_image(str(path))

    if img.mode != "RGBA":
        # No alpha channel — return all-white mask (fully opaque)
        return Image.new("L", img.size, 255)

    alpha = img.split()[-1]  # extract alpha channel
    # Threshold: alpha > 128 → white (opaque), else black (transparent)
    return alpha.point(lambda p: 255 if p > 128 else 0)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _detect_format_from_path(path: str) -> ImageFormat:
    ext = os.path.splitext(path)[1].lower()
    mapping = {
        ".png": ImageFormat.PNG,
        ".jpg": ImageFormat.JPEG,
        ".jpeg": ImageFormat.JPEG,
        ".webp": ImageFormat.WEBP,
        ".svg": ImageFormat.SVG,
        ".gif": ImageFormat.GIF,
    }
    return mapping.get(ext, ImageFormat.UNKNOWN)


def _load_svg(path: str) -> "Image.Image":
    """Load SVG by rasterizing with rsvg-convert or cairosvg."""
    _require_pillow()

    # Try cairosvg first (pure Python)
    try:
        import cairosvg
        import io

        png_data = cairosvg.svg2png(url=path, output_width=2048)
        return Image.open(io.BytesIO(png_data))
    except ImportError:
        pass

    # Fall back to rsvg-convert (command line)
    try:
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp_path = tmp.name
        subprocess.run(
            ["rsvg-convert", "-w", "2048", "--keep-aspect-ratio", path, "-o", tmp_path],
            check=True,
            capture_output=True,
        )
        img = Image.open(tmp_path)
        img.load()
        os.unlink(tmp_path)
        return img
    except (FileNotFoundError, subprocess.CalledProcessError):
        pass

    # Last resort: try macOS sips
    try:
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp_path = tmp.name
        subprocess.run(
            ["sips", "-s", "format", "png", path, "--out", tmp_path],
            check=True,
            capture_output=True,
        )
        img = Image.open(tmp_path)
        img.load()
        os.unlink(tmp_path)
        return img
    except (FileNotFoundError, subprocess.CalledProcessError):
        pass

    raise RuntimeError(
        f"Cannot load SVG: {path}. Install cairosvg (pip install cairosvg) "
        "or rsvg-convert (brew install librsvg)"
    )


def _detect_transparency(img: "Image.Image") -> bool:
    """Detect if an image actually uses transparency (not just has an alpha channel)."""
    if img.mode == "RGBA":
        alpha = img.split()[-1]
        extrema = alpha.getextrema()
        # If minimum alpha < 255, some pixels are transparent
        return extrema[0] < 255
    if img.mode == "LA":
        alpha = img.split()[-1]
        return alpha.getextrema()[0] < 255
    if img.mode == "P":
        # Palette mode can have transparency
        return "transparency" in img.info
    return False


def _imgdata(im: "Image.Image"):
    """Get pixel data, preferring non-deprecated API."""
    return im.get_flattened_data() if hasattr(im, "get_flattened_data") else im.getdata()


def _compute_content_bbox(img: "Image.Image") -> BoundingBox:
    """Find the bounding box of non-transparent/non-white content."""
    if img.mode == "RGBA":
        # Use alpha channel for bounding box
        alpha = img.split()[-1]
        bbox = alpha.getbbox()
    else:
        # For images without alpha, find non-white content
        if img.mode != "RGB":
            img_rgb = img.convert("RGB")
        else:
            img_rgb = img
        # Create a diff against white background
        bg = Image.new("RGB", img_rgb.size, (255, 255, 255))
        diff = Image.new("L", img_rgb.size)
        for i, (p, b) in enumerate(zip(_imgdata(img_rgb), _imgdata(bg))):
            delta = abs(p[0] - b[0]) + abs(p[1] - b[1]) + abs(p[2] - b[2])
            diff.putpixel((i % img_rgb.width, i // img_rgb.width), min(delta, 255))
        bbox = diff.getbbox()

    if bbox is None:
        return BoundingBox(0, 0, img.width, img.height)
    return BoundingBox(left=bbox[0], top=bbox[1], right=bbox[2], bottom=bbox[3])


def _extract_dominant_colors(
    img: "Image.Image", max_colors: int = 5
) -> list[DominantColor]:
    """Extract dominant colors from an image."""
    # Prefer colorgram if available (better quality)
    if HAS_COLORGRAM:
        try:
            if img.mode == "RGBA":
                # Remove transparent pixels for color analysis
                bg = Image.new("RGB", img.size, (255, 255, 255))
                bg.paste(img, mask=img.split()[-1])
                target = bg
            elif img.mode != "RGB":
                target = img.convert("RGB")
            else:
                target = img

            # colorgram expects a file path or PIL image
            colors = colorgram_mod.extract(target, max_colors)
            total_pixels = sum(c.proportion for c in colors) or 1.0
            return [
                DominantColor(
                    r=c.rgb.r,
                    g=c.rgb.g,
                    b=c.rgb.b,
                    proportion=round(c.proportion / total_pixels, 3),
                )
                for c in colors
            ]
        except Exception:
            pass

    # Fallback: quantize with Pillow
    if img.mode == "RGBA":
        bg = Image.new("RGB", img.size, (255, 255, 255))
        bg.paste(img, mask=img.split()[-1])
        img_rgb = bg
    elif img.mode != "RGB":
        img_rgb = img.convert("RGB")
    else:
        img_rgb = img

    # Resize for speed
    small = img_rgb.copy()
    small.thumbnail((150, 150))

    quantized = small.quantize(colors=max_colors, method=Image.Quantize.MEDIANCUT)
    palette = quantized.getpalette()
    if not palette:
        return []

    # Count pixels per palette index
    pixel_counts: dict[int, int] = {}
    for pixel in _imgdata(quantized):
        pixel_counts[pixel] = pixel_counts.get(pixel, 0) + 1

    total = sum(pixel_counts.values()) or 1
    result = []
    for idx in sorted(pixel_counts, key=pixel_counts.get, reverse=True)[:max_colors]:
        r, g, b = palette[idx * 3], palette[idx * 3 + 1], palette[idx * 3 + 2]
        result.append(
            DominantColor(r=r, g=g, b=b, proportion=round(pixel_counts[idx] / total, 3))
        )

    return result


def _count_unique_colors(img: "Image.Image", sample_size: int = 10000) -> int:
    """Approximate unique color count (sample-based for large images)."""
    if img.mode == "RGBA":
        # Only count opaque pixels
        pixels = [
            (r, g, b)
            for r, g, b, a in _imgdata(img)
            if a > 128
        ]
    elif img.mode != "RGB":
        pixels = list(img.convert("RGB").getdata())
    else:
        pixels = list(_imgdata(img.convert("RGB")))

    if len(pixels) > sample_size:
        import random
        pixels = random.sample(pixels, sample_size)

    # Quantize to 6-bit per channel to reduce noise
    unique = set((r >> 2, g >> 2, b >> 2) for r, g, b in pixels)
    return len(unique)
