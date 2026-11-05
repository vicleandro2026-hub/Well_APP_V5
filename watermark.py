"""Orientação, composição e exportação das fotos com os logos incorporados."""

from dataclasses import dataclass
from functools import lru_cache
import json
from pathlib import Path

from PIL import Image, ImageOps
from theme import COLORS

ASSETS = Path(__file__).resolve().parent / "assets"
SUPPORTED = {".jpg", ".jpeg", ".png", ".webp"}

POSITIONS = (
    ("top_left", "Topo esq."), ("top", "Topo"), ("top_right", "Topo dir."),
    ("left", "Meio esq."), ("center", "Centro"), ("right", "Meio dir."),
    ("bottom_left", "Base esq."), ("bottom", "Base"), ("bottom_right", "Base dir."),
)
POSITION_NAMES = dict(POSITIONS, original="Padrão Well")


@dataclass(frozen=True)
class Settings:
    position: str = "original"
    scale: int = 100
    opacity: int = 100
    margin: int = 4


@dataclass(frozen=True)
class Photo:
    path: str
    width: int
    height: int

    @property
    def logo(self):
        return "vertical" if self.height > self.width else "horizontal"

    @property
    def format_label(self):
        if self.height == self.width:
            return "Quadrada"
        return "Vertical" if self.height > self.width else "Horizontal"


def inspect_photo(path):
    path = Path(path).resolve()
    if path.suffix.lower() not in SUPPORTED:
        raise ValueError("Formato não suportado. Use JPG, PNG ou WebP.")
    with Image.open(path) as image:
        width, height = image.size
        if image.getexif().get(274) in (5, 6, 7, 8):
            width, height = height, width
    return Photo(str(path), width, height)


@lru_cache(maxsize=1)
def layouts():
    return json.loads((ASSETS / "layouts.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=2)
def load_logo(key):
    with Image.open(ASSETS / f"logo_{key}.png") as image:
        return image.convert("RGBA")


def compose(image, settings, logo_key):
    """A mesma geometria é usada na prévia e na exportação em resolução original."""
    result = image.convert("RGBA")
    width, height = result.size
    layout = layouts()[logo_key]
    canvas_w, canvas_h = layout["canvas"]
    left, top, right, bottom = layout["bbox"]
    template_scale = min(width / canvas_w, height / canvas_h)
    factor = max(0.25, min(3.0, settings.scale / 100))
    mark_w = (right - left) * template_scale * factor
    mark_h = (bottom - top) * template_scale * factor
    margin = min(width, height) * max(0, min(12, settings.margin)) / 100
    padding = 0 if settings.position == "original" else margin
    fit = min(1.0, max(1, width - padding * 2) / mark_w,
              max(1, height - padding * 2) / mark_h)
    mark_w, mark_h = max(1, round(mark_w * fit)), max(1, round(mark_h * fit))
    logo = load_logo(logo_key).resize((mark_w, mark_h), Image.Resampling.LANCZOS)
    if settings.opacity < 100:
        opacity = max(0, settings.opacity) / 100
        logo.putalpha(logo.getchannel("A").point(lambda value: round(value * opacity)))

    if settings.position == "original":
        center_x = (width - canvas_w * template_scale) / 2 + (left + right) / 2 * template_scale
        center_y = (height - canvas_h * template_scale) / 2 + (top + bottom) / 2 * template_scale
        x, y = center_x - mark_w / 2, center_y - mark_h / 2
    else:
        x = (width - mark_w) / 2
        y = (height - mark_h) / 2
        if settings.position in {"top_left", "left", "bottom_left"}:
            x = margin
        elif settings.position in {"top_right", "right", "bottom_right"}:
            x = width - mark_w - margin
        if settings.position in {"top_left", "top", "top_right"}:
            y = margin
        elif settings.position in {"bottom_left", "bottom", "bottom_right"}:
            y = height - mark_h - margin
    x = round(max(0, min(width - mark_w, x)))
    y = round(max(0, min(height - mark_h, y)))
    result.alpha_composite(logo, (x, y))
    return result


def render_preview(photo, settings, size, original=False):
    width, height = max(100, int(size[0])), max(100, int(size[1]))
    with Image.open(photo.path) as source:
        source.draft("RGB", (width * 2, height * 2))
        image = ImageOps.exif_transpose(source)
        image.thumbnail((width, height), Image.Resampling.LANCZOS)
        rendered = image.convert("RGBA") if original else compose(image, settings, photo.logo)
    matte = Image.new("RGBA", rendered.size, COLORS["matte"])
    matte.alpha_composite(rendered)
    return matte.convert("RGB")


def export_photo(photo, destination, settings):
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    original = Path(photo.path)
    output = destination / f"marcadagua_{original.name}"
    counter = 2
    while output.exists():
        output = destination / f"marcadagua_{original.stem}_{counter}{original.suffix}"
        counter += 1

    with Image.open(original) as source:
        icc_profile = source.info.get("icc_profile")
        corrected = ImageOps.exif_transpose(source)
        result = compose(corrected, settings, photo.logo)
        options = {}
        if icc_profile:
            options["icc_profile"] = icc_profile
        exif = corrected.getexif()
        if exif:
            options["exif"] = exif.tobytes()
        if output.suffix.lower() in {".jpg", ".jpeg"}:
            flattened = Image.new("RGB", result.size, "white")
            flattened.paste(result, mask=result.getchannel("A"))
            result = flattened
            options.update(quality=95, subsampling=0)
        elif output.suffix.lower() == ".webp":
            options.update(quality=95, method=4)
        else:
            options["compress_level"] = 6
        created = False
        try:
            with output.open("xb") as stream:
                created = True
                result.save(stream, format={".jpg": "JPEG", ".jpeg": "JPEG", ".png": "PNG",
                                          ".webp": "WEBP"}[output.suffix.lower()], **options)
        except Exception:
            # Somente remove um arquivo parcial criado por esta exportação.
            # Um arquivo que já existia nunca é substituído.
            if created:
                output.unlink(missing_ok=True)
            raise
    return output
