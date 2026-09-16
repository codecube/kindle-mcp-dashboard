from __future__ import annotations

import io
import textwrap
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont, ImageOps

from .sources import resolve, snapshot

FONT_PATHS = (
    Path("/usr/share/fonts/TTF/DejaVuSans.ttf"),
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
)
BOLD_PATHS = (
    Path("/usr/share/fonts/TTF/DejaVuSans-Bold.ttf"),
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
)


def render_dashboard(data: dict[str, Any], values: dict[str, Any] | None = None) -> Image.Image:
    width, height = data["device"]["width"], data["device"]["height"]
    image = Image.new("L", (width, height), 255)
    draw = ImageDraw.Draw(image)
    screen = next(item for item in data["screens"] if item["id"] == data["active_screen"])
    live = values or snapshot()
    for region in screen["regions"]:
        if region["kind"] == "image":
            _draw_image(image, region, width, height)
        else:
            _draw_region(draw, region, live, width, height)
    # Quantize to the EY21 panel's 16 grayscale levels.
    return image.quantize(colors=16).convert("L")


def render_png(data: dict[str, Any], values: dict[str, Any] | None = None) -> bytes:
    buffer = io.BytesIO()
    render_dashboard(data, values).save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()


def _box(region: dict[str, Any], width: int, height: int) -> tuple[int, int, int, int]:
    return tuple(round(region[key] * scale / 1000) for key, scale in (("x", width), ("y", height), ("w", width), ("h", height)))


def _draw_region(draw: ImageDraw.ImageDraw, region: dict[str, Any], values: dict[str, Any], width: int, height: int) -> None:
    x, y, w, h = _box(region, width, height)
    # Give labels and content comfortable breathing room on the e-ink panel.
    pad = max(10, round(min(width, height) * 0.018))
    if region.get("border", True):
        draw.rounded_rectangle((x, y, x + w, y + h), radius=7, outline=30, width=2)
    if region.get("invert"):
        draw.rectangle((x, y, x + w, y + h), fill=20)
        fg, muted = 255, 205
    else:
        fg, muted = 15, 85
    label = str(region.get("label", ""))
    cursor_y = y + pad
    if label:
        font = _font(max(14, round(height * 0.018)), bold=True)
        # Region titles should remain high-contrast and readable after the
        # Kindle's grayscale quantization; muted gray is too faint here.
        draw.text((x + pad, cursor_y), label, font=font, fill=fg)
        cursor_y += _line_height(font) + 5
    icon = region.get("icon")
    icon_space = 0
    if icon:
        icon_size = min(54, max(30, h // 3))
        _draw_icon(draw, str(icon), x + pad, cursor_y + 3, icon_size, fg)
        icon_space = icon_size + pad
    kind = region["kind"]
    value = resolve(region, values)
    content_x = x + pad + icon_space
    content_w = max(10, w - pad * 2 - icon_space)
    if kind in {"text", "metric", "status"}:
        size = int(region.get("size", 40 if kind == "metric" else 26))
        if kind == "status":
            status = str(region.get("status", value)).lower()
            dot = 18
            fill = 20 if status in {"ok", "online", "healthy", "running"} else 120
            draw.ellipse((content_x, cursor_y + 7, content_x + dot, cursor_y + 7 + dot), fill=fill)
            content_x += dot + pad
            content_w -= dot + pad
        _draw_wrapped(draw, str(value), content_x, cursor_y, content_w, y + h - pad, size, fg,
                      region.get("align", "left"), bold=kind == "metric")
        unit = str(region.get("unit", ""))
        if unit and kind == "metric":
            draw.text((x + w - pad, y + h - pad), unit, font=_font(18), fill=muted, anchor="rs")
    elif kind == "progress":
        percent = max(0, min(100, float(value or 0)))
        value_font = _font(int(region.get("size", 36)), bold=True)
        draw.text((content_x, cursor_y), f"{percent:.0f}%", font=value_font, fill=fg)
        bar_y = y + h - pad - 24
        draw.rectangle((x + pad, bar_y, x + w - pad, bar_y + 20), outline=fg, width=2)
        fill_w = round((w - pad * 2 - 6) * percent / 100)
        draw.rectangle((x + pad + 3, bar_y + 3, x + pad + 3 + fill_w, bar_y + 17), fill=fg)
    elif kind == "list":
        items = region.get("items", value if isinstance(value, list) else [value])
        item_font = _font(int(region.get("size", 23)))
        line_h = _line_height(item_font) + 7
        for index, item in enumerate(items):
            row_y = cursor_y + index * line_h
            if row_y + line_h > y + h - pad:
                break
            text = item.get("text", item.get("label", "")) if isinstance(item, dict) else str(item)
            status = item.get("status", "") if isinstance(item, dict) else ""
            marker_y = row_y + max(2, line_h // 2 - 6)
            marker_box = (x + pad, marker_y, x + pad + 12, marker_y + 12)
            if status in {"ok", "online", "healthy", "running"}:
                draw.ellipse(marker_box, fill=fg)
            else:
                draw.ellipse(marker_box, outline=fg, width=2)
            draw.text((x + pad + 24, row_y), text, font=item_font, fill=fg)


def _draw_image(image: Image.Image, region: dict[str, Any], width: int, height: int) -> None:
    """Draw a local image asset, scaled to fit its normalized region."""
    path = region.get("image") or region.get("path")
    if not isinstance(path, str) or not path:
        return
    try:
        source = Image.open(Path(path).expanduser()).convert("L")
    except (OSError, ValueError):
        return
    if region.get("trim"):
        bbox = ImageOps.invert(source).getbbox()
        if bbox:
            source = source.crop(bbox)
    x, y, w, h = _box(region, width, height)
    pad = max(6, round(min(width, height) * 0.012))
    target_w, target_h = max(1, w - pad * 2), max(1, h - pad * 2)
    fitted = ImageOps.contain(source, (target_w, target_h))
    if region.get("invert"):
        fitted = ImageOps.invert(fitted)
    paste_x = x + (w - fitted.width) // 2
    paste_y = y + (h - fitted.height) // 2
    image.paste(fitted, (paste_x, paste_y))


def _draw_wrapped(draw: ImageDraw.ImageDraw, value: str, x: int, y: int, width: int, bottom: int,
                  size: int, fill: int, align: str, bold: bool = False) -> None:
    font = _font(size, bold)
    average = max(1, draw.textlength("ABCDEFGHIJKLMNOPQRSTUVWXYZ", font=font) / 26)
    chars = max(1, int(width / average))
    lines: list[str] = []
    for raw in value.splitlines() or [""]:
        lines.extend(textwrap.wrap(raw, width=chars) or [""])
    line_h = _line_height(font) + 3
    for line in lines:
        if y + line_h > bottom:
            break
        anchor = "ra" if align == "right" else "ma" if align == "center" else "la"
        draw_x = x + width if align == "right" else x + width // 2 if align == "center" else x
        draw.text((draw_x, y), line, font=font, fill=fill, anchor=anchor)
        y += line_h


def _font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    paths = BOLD_PATHS if bold else FONT_PATHS
    for path in paths:
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default(size=size)


def _line_height(font: ImageFont.ImageFont) -> int:
    box = font.getbbox("Ag")
    return box[3] - box[1]


def _draw_icon(draw: ImageDraw.ImageDraw, name: str, x: int, y: int, size: int, fill: int) -> None:
    cx, cy = x + size // 2, y + size // 2
    if name in {"cloud", "weather"}:
        draw.ellipse((x + 3, y + size // 3, x + size * 2 // 3, y + size - 5), outline=fill, width=3)
        draw.ellipse((x + size // 3, y + 5, x + size - 3, y + size - 5), outline=fill, width=3)
        draw.line((x + 9, y + size - 5, x + size - 4, y + size - 5), fill=fill, width=3)
    elif name in {"cpu", "memory"}:
        inset = size // 5
        draw.rectangle((x + inset, y + inset, x + size - inset, y + size - inset), outline=fill, width=3)
        for offset in range(inset, size - inset + 1, max(5, size // 5)):
            draw.line((x + offset, y, x + offset, y + inset), fill=fill, width=2)
            draw.line((x + offset, y + size - inset, x + offset, y + size), fill=fill, width=2)
    elif name == "disk":
        draw.rectangle((x + 4, y + 5, x + size - 4, y + size - 5), outline=fill, width=3)
        draw.ellipse((cx - 5, cy - 5, cx + 5, cy + 5), outline=fill, width=2)
    elif name == "agent":
        draw.ellipse((cx - 7, y + 2, cx + 7, y + 16), outline=fill, width=3)
        draw.line((cx, y + 16, cx, y + size - 4), fill=fill, width=3)
        draw.line((x + 5, cy, x + size - 5, cy), fill=fill, width=3)
        draw.line((cx, y + size - 4, x + 7, y + size), fill=fill, width=3)
        draw.line((cx, y + size - 4, x + size - 7, y + size), fill=fill, width=3)
    else:
        draw.ellipse((x + 4, y + 4, x + size - 4, y + size - 4), outline=fill, width=3)
