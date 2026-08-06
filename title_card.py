"""
Har bir post uchun mavzu nomi yozilgan chiroyli "sarlavha kartasi" (title
card) rasmini generatsiya qiladi. Tashqi API yoki internet ulanishi shart
emas - hammasi mahalliy ravishda Pillow bilan chiziladi, shuning uchun
qo'shimcha API kalit yoki kvota kerak emas va har doim ishlaydi.

generate_title_card(...) PNG bytes qaytaradi, u to'g'ridan-to'g'ri
Telegram'ning sendPhoto endpointiga yuboriladi.
"""

import os
import textwrap
from io import BytesIO

from PIL import Image, ImageDraw, ImageFont

_ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "fonts")
_BOLD_FONT_PATH = os.path.join(_ASSETS_DIR, "DejaVuSans-Bold.ttf")
_REGULAR_FONT_PATH = os.path.join(_ASSETS_DIR, "DejaVuSans.ttf")

CARD_WIDTH = 1200
CARD_HEIGHT = 630

# Turkumga qarab rang sxemasi (yuqori-pastki gradient).
_COLOR_SCHEMES = {
    "listening_tips": {
        "top": (2, 132, 199),      # sky blue
        "bottom": (14, 165, 233),  # lighter sky
        "accent": (250, 204, 21),
        "label": "LISTENING TIPS",
    },
    "reading_tips": {
        "top": (67, 56, 202),      # indigo
        "bottom": (99, 102, 241),  # lighter indigo
        "accent": (250, 204, 21),
        "label": "READING TIPS",
    },
    "speaking_tips": {
        "top": (219, 39, 119),     # rose
        "bottom": (147, 51, 234),  # purple
        "accent": (250, 204, 21),
        "label": "SPEAKING TIPS",
    },
    "fun_fact": {
        "top": (217, 119, 6),      # amber
        "bottom": (194, 65, 12),   # burnt orange
        "accent": (255, 255, 255),
        "label": "BILASIZMI?",
    },
    "speaking_part1": {
        "top": (5, 150, 105),      # emerald
        "bottom": (13, 148, 136),  # teal
        "accent": (250, 204, 21),
        "label": "SPEAKING PART 1",
    },
}


def _font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size)


def _draw_vertical_gradient(draw: ImageDraw.ImageDraw, size, top_color, bottom_color) -> None:
    width, height = size
    for y in range(height):
        ratio = y / max(height - 1, 1)
        r = int(top_color[0] + (bottom_color[0] - top_color[0]) * ratio)
        g = int(top_color[1] + (bottom_color[1] - top_color[1]) * ratio)
        b = int(top_color[2] + (bottom_color[2] - top_color[2]) * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))


def _draw_decorative_circles(base_img: Image.Image) -> None:
    """Fonga yengil, xiralashgan doiralar qo'shadi - zerikarli tekis fon
    o'rniga biroz chuqurlik va zamonaviylik beradi."""
    overlay_specs = [
        (CARD_WIDTH - 120, -80, 320, (255, 255, 255, 22)),
        (-100, CARD_HEIGHT - 150, 260, (255, 255, 255, 18)),
        (CARD_WIDTH - 260, CARD_HEIGHT - 60, 180, (255, 255, 255, 14)),
    ]
    for cx, cy, r, color in overlay_specs:
        circle_layer = Image.new("RGBA", (CARD_WIDTH, CARD_HEIGHT), (0, 0, 0, 0))
        circle_draw = ImageDraw.Draw(circle_layer)
        circle_draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)
        base_img.alpha_composite(circle_layer)


def _wrap_to_width(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list:
    """Berilgan piksel kengligiga sig'adigan qilib matnni qatorlarga bo'ladi."""
    words = text.split()
    lines = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        bbox = draw.textbbox((0, 0), candidate, font=font)
        if bbox[2] - bbox[0] <= max_width or not current:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _clean_topic_title(topic: str) -> str:
    """Mavzu nomidagi qavs ichidagi o'zbekcha izohni olib tashlaydi (kartada
    faqat asosiy inglizcha/qisqa nom ko'rinishi uchun)."""
    return topic.split("(")[0].strip()


def generate_title_card(topic: str, category: str, part: int | None = None) -> bytes:
    """category: 'listening_tips' / 'reading_tips' / 'speaking_tips' /
    'fun_fact' / 'speaking_part1'. part hozircha ishlatilmaydi (kelajakda
    ko'p qismli seriya qo'shilsa deb qoldirilgan). PNG rasm bytes qaytaradi."""
    scheme = _COLOR_SCHEMES.get(category, _COLOR_SCHEMES["grammar"])
    title = _clean_topic_title(topic)

    img = Image.new("RGBA", (CARD_WIDTH, CARD_HEIGHT), (0, 0, 0, 255))
    draw = ImageDraw.Draw(img)
    _draw_vertical_gradient(draw, (CARD_WIDTH, CARD_HEIGHT), scheme["top"], scheme["bottom"])
    _draw_decorative_circles(img)

    label_font = _font(_BOLD_FONT_PATH, 30)
    title_font = _font(_BOLD_FONT_PATH, 68)
    footer_font = _font(_REGULAR_FONT_PATH, 28)
    badge_font = _font(_BOLD_FONT_PATH, 32)

    margin_x = 90

    # Yuqori yorliq (masalan "DAILY GRAMMAR")
    draw.text((margin_x, 70), scheme["label"], font=label_font, fill=(255, 255, 255, 235))

    # O'ng yuqori burchakda qism ko'rsatkichi (grammar uchun, masalan "2 / 5")
    if part is not None:
        badge_text = f"{part} / 5"
        bbox = draw.textbbox((0, 0), badge_text, font=badge_font)
        badge_w = bbox[2] - bbox[0] + 46
        badge_h = 56
        badge_x0 = CARD_WIDTH - margin_x - badge_w
        badge_y0 = 60
        draw.rounded_rectangle(
            [badge_x0, badge_y0, badge_x0 + badge_w, badge_y0 + badge_h],
            radius=28,
            fill=(*scheme["accent"], 255),
        )
        draw.text(
            (badge_x0 + 23, badge_y0 + 10),
            badge_text,
            font=badge_font,
            fill=(30, 30, 30, 255),
        )

    # Asosiy sarlavha - avtomatik qatorlarga bo'linadi va vertikal markazga
    # joylashtiriladi.
    max_text_width = CARD_WIDTH - margin_x * 2
    lines = _wrap_to_width(draw, title, title_font, max_text_width)
    line_height = title_font.size + 14
    total_text_height = line_height * len(lines)
    start_y = (CARD_HEIGHT - total_text_height) // 2 + 10

    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=title_font)
        line_w = bbox[2] - bbox[0]
        x = (CARD_WIDTH - line_w) // 2
        y = start_y + i * line_height
        # Yengil soya - matnni fon ustida yaxshiroq ajratib turadi.
        draw.text((x + 3, y + 3), line, font=title_font, fill=(0, 0, 0, 90))
        draw.text((x, y), line, font=title_font, fill=(255, 255, 255, 255))

    # Pastki chiziq va kanal nomi
    draw.line(
        [(margin_x, CARD_HEIGHT - 90), (CARD_WIDTH - margin_x, CARD_HEIGHT - 90)],
        fill=(255, 255, 255, 90),
        width=2,
    )
    draw.text(
        (margin_x, CARD_HEIGHT - 68),
        "@djami_teacher",
        font=footer_font,
        fill=(255, 255, 255, 220),
    )

    buf = BytesIO()
    img.convert("RGB").save(buf, format="PNG", optimize=True)
    return buf.getvalue()
