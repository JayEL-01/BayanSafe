"""Reusable text-layout helpers for BayanSafe.

All measurements are in **canvas pixels** (320×180 internal resolution).
Every helper works with the theme.TextFont objects returned by theme.get_font().
"""

from typing import List, Tuple, Optional

import pygame

from src.core import settings
from src.ui import theme


# ── measuring ────────────────────────────────────────────────────────

def measure_text(text: str, size: str = "tiny") -> Tuple[int, int]:
    """Return (width, height) in canvas pixels for *text* at the named size."""
    font = theme.get_font(size)
    return font.size(text)


def line_height(size: str = "tiny") -> int:
    """The height of one line of text in canvas pixels."""
    return theme.get_font(size).get_height()


# ── wrapping / ellipsis ──────────────────────────────────────────────

def wrap_text(text: str, size: str, max_width: int) -> List[str]:
    """Word-wrap *text* so every line fits inside *max_width* canvas-px.

    Very long words that cannot fit even alone are hard-broken with a
    hyphen.  Empty input returns ``[""]``.
    """
    font = theme.get_font(size)
    words = text.split()
    if not words:
        return [""]
    lines: List[str] = []
    current = ""
    for word in words:
        test = f"{current} {word}".strip()
        tw, _ = font.size(test)
        if tw <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            # If a single word overflows, hard-break it
            ww, _ = font.size(word)
            if ww > max_width and max_width > 0:
                word = _hard_break(font, word, max_width, lines)
            current = word
    if current:
        lines.append(current)
    return lines or [""]


def _hard_break(font, word: str, max_width: int, lines: List[str]) -> str:
    """Break *word* into chunks that fit, appending complete chunks to *lines*.
    Returns the remaining tail."""
    buf = ""
    for ch in word:
        test = buf + ch + "-"
        if font.size(test)[0] > max_width and buf:
            lines.append(buf + "-")
            buf = ch
        else:
            buf += ch
    return buf


def ellipsize(text: str, size: str, max_width: int) -> str:
    """Shorten *text* with '…' so it fits inside *max_width* canvas-px."""
    font = theme.get_font(size)
    tw, _ = font.size(text)
    if tw <= max_width:
        return text
    ellip = "..."
    ew = font.size(ellip)[0]
    for i in range(len(text), 0, -1):
        if font.size(text[:i])[0] + ew <= max_width:
            return text[:i].rstrip() + ellip
    return ellip


# ── drawing ──────────────────────────────────────────────────────────

def draw_wrapped(
    surface: pygame.Surface,
    text: str,
    x: int,
    y: int,
    size: str,
    max_width: int,
    color=None,
    shadow: bool = False,
    anchor: str = "topleft",
    line_gap: int = 1,
    max_lines: int = 0,
    ellipsis_overflow: bool = True,
) -> int:
    """Word-wrap *text* and draw it.  Returns the total height used (px).

    *max_lines*: 0 = unlimited.  When the text would exceed *max_lines*
    and *ellipsis_overflow* is True, the last visible line is ellipsized.
    """
    if color is None:
        color = theme.CREAM
    lines = wrap_text(text, size, max_width)
    if max_lines and len(lines) > max_lines:
        lines = lines[:max_lines]
        if ellipsis_overflow and lines:
            lines[-1] = ellipsize(lines[-1] + "...", size, max_width)

    lh = line_height(size)
    gap = lh + line_gap
    for i, line in enumerate(lines):
        theme.draw_text(surface, line, (x, y + i * gap), size=size,
                        color=color, shadow=shadow, anchor=anchor)
    return gap * max(1, len(lines))


def get_wrapped_size(text: str, size: str, max_width: int, line_gap: int = 1) -> Tuple[int, int]:
    """Calculate the (width, height) required to draw wrapped text."""
    lines = wrap_text(text, size, max_width)
    if not lines or lines == [""]:
        return (0, 0)

    font = theme.get_font(size)
    max_w = 0
    for line in lines:
        w, _ = font.size(line)
        max_w = max(max_w, w)

    lh = font.get_height()
    total_h = len(lines) * lh + max(0, len(lines) - 1) * line_gap
    return (max_w, total_h)


def draw_panel(surface, rect, title=None, accent=None, alpha=235, border_color=None):
    """Draw a themed panel (delegates to theme.draw_panel but returns the rect)."""
    from src.config.palette import COLOR_UI_ACCENT
    if accent is None:
        accent = COLOR_UI_ACCENT
    return theme.draw_panel(surface, rect, title=title, accent=accent, alpha=alpha)


def clamp_rect(rect: pygame.Rect, bounds: pygame.Rect) -> pygame.Rect:
    """Return a copy of *rect* clamped fully inside *bounds*."""
    r = rect.copy()
    r.clamp_ip(bounds)
    return r
