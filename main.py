#!/usr/bin/env python3
"""news-image-20261121 -- render a 1024x1024 world-news poster as PNG.

Fresh build for the make.fun news-image-20261121 bounty.
Python standard library ONLY (no third-party dependencies).

The program contains:
  * its own 5x7 bitmap font (uppercase, digits, punctuation),
  * its own PNG encoder (zlib + struct + binascii from the stdlib),
  * a fixed 2-column x 3-row layout for six verified news stories
    dated Saturday 21 November 2026.

Deterministic: running the program twice produces byte-identical PNG
output (no timestamps, no randomness, fixed zlib compression level).

Usage:
    python3 main.py
Output:
    entry.png  (1024 x 1024, RGB)
"""

import binascii
import hashlib
import struct
import zlib
from pathlib import Path

W, H = 1024, 1024
OUT = Path(__file__).resolve().parent / "entry.png"

# ---------------------------------------------------------------------------
# 5x7 bitmap font. Each glyph is 7 rows of 5 bits ("1" = pixel on).
# Uppercase letters, digits and the punctuation used by the poster text.
# ---------------------------------------------------------------------------
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ";": ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "\u2014": ("00000", "00000", "00000", "11111", "00000", "00000", "00000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    '"': ("01010", "01010", "01010", "00000", "00000", "00000", "00000"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
}

# ---------------------------------------------------------------------------
# Palette
# ---------------------------------------------------------------------------
BG = (10, 26, 51)        # dark navy page background
TITLE = (255, 255, 255)  # white title
GOLD = (255, 200, 50)    # gold subtitle / accents
CELL = (255, 255, 255)   # white story cards
INK = (10, 26, 51)       # navy headline text
BODY = (51, 51, 51)      # dark-grey body text
MUTED = (110, 120, 135)  # grey for the story number

# ---------------------------------------------------------------------------
# The six verified stories of Saturday 21 November 2026.
# (kicker, accent colour, headline, supporting text)
# ---------------------------------------------------------------------------
STORIES = [
    (
        "GEOPOLITICS",
        (215, 38, 61),
        "RUSSIA STRIKES, MISSILES LAND IN POLAND",
        "RUSSIA FIRED 400+ DRONES AND 110 MISSILES AT UKRAINE OVERNIGHT. "
        "TWO MISSILES AND A SUSPECTED DRONE CAME DOWN IN POLAND. "
        "NATO CALLS IT A GRAVE VIOLATION.",
    ),
    (
        "MARKETS",
        (27, 111, 208),
        "S&P 500 AND DOW ENTER CORRECTION",
        "US STOCKS FELL 3.7% ON FRIDAY AS AN AI SELL-OFF PUSHED THE S&P 500 "
        "AND DOW INTO CORRECTION. THE NASDAQ ERASED ITS 2026 GAINS. "
        "NVIDIA FELL ABOUT 14%.",
    ),
    (
        "DISASTER",
        (230, 126, 0),
        "MAGNITUDE 6.8 QUAKE SHAKES PERU",
        "A 6.8 EARTHQUAKE STRUCK THE JUNIN REGION OF CENTRAL PERU. "
        "TREMORS WERE FELT IN LIMA, 320 KM AWAY. "
        "NO CASUALTIES OR MAJOR DAMAGE REPORTED.",
    ),
    (
        "ECONOMY",
        (30, 142, 74),
        "RECORD FOREIGN CASH POURS INTO INDIA",
        "FOREIGN INVESTORS PUT A NET 1.22 LAKH CRORE RUPEES INTO INDIAN "
        "SHARES IN NOVEMBER, THE HIGHEST MONTHLY INFLOW ON RECORD, "
        "ENDING A 16-MONTH SELLING STREAK.",
    ),
    (
        "POLITICS",
        (123, 47, 190),
        "MAMDANI SETS 2032 TO CLOSE RIKERS",
        "MAYOR ZOHRAN MAMDANI PLANS TO CLOSE RIKERS ISLAND BY 2032, "
        "REPLACING IT WITH FOUR SMALLER BOROUGH JAILS. "
        "THE POPULATION WOULD FALL FROM 6,600 TO 4,100.",
    ),
    (
        "SPORT",
        (14, 124, 123),
        "KL RAHUL COMPLETES THE SENA SET",
        "KL RAHUL SCORED 100 IN WELLINGTON, BECOMING THE FIRST INDIAN "
        "OPENER WITH TEST CENTURIES IN ALL FOUR SENA COUNTRIES: "
        "SOUTH AFRICA, ENGLAND, NEW ZEALAND AND AUSTRALIA.",
    ),
]

TITLE_TEXT = "WORLD NEWS \u2014 SATURDAY 21 NOVEMBER 2026"
SUBTITLE_TEXT = "SIX STORIES FROM AROUND THE WORLD"


# ---------------------------------------------------------------------------
# Canvas helpers (RGB bytearray, row-major)
# ---------------------------------------------------------------------------
def fill_rect(canvas, x, y, w, h, color):
    """Fill an axis-aligned rectangle, clipped to the canvas."""
    x0 = max(0, x)
    y0 = max(0, y)
    x1 = min(W, x + w)
    y1 = min(H, y + h)
    if x1 <= x0 or y1 <= y0:
        return
    r, g, b = color
    for yy in range(y0, y1):
        base = (yy * W + x0) * 3
        for xx in range(x0, x1):
            i = base + (xx - x0) * 3
            canvas[i] = r
            canvas[i + 1] = g
            canvas[i + 2] = b


def text_width(text, scale):
    """Pixel width of a string at the given font scale."""
    return len(text) * 6 * scale


def draw_text(canvas, x, y, text, scale, color):
    """Draw one line of text; returns the x position after the last char."""
    cx = x
    for ch in text:
        glyph = FONT.get(ch, FONT["?"])
        for row_i, row in enumerate(glyph):
            for col_i, bit in enumerate(row):
                if bit == "1":
                    fill_rect(canvas, cx + col_i * scale, y + row_i * scale,
                              scale, scale, color)
        cx += 6 * scale
    return cx


def draw_text_centered(canvas, y, text, scale, color):
    draw_text(canvas, (W - text_width(text, scale)) // 2, y, text, scale, color)


def wrap_text(text, max_width, scale):
    """Greedy word wrap; returns a list of lines that fit max_width."""
    char_w = 6 * scale
    max_chars = max(1, max_width // char_w)
    lines = []
    current = ""
    for word in text.split(" "):
        trial = word if not current else current + " " + word
        if len(trial) <= max_chars:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


# ---------------------------------------------------------------------------
# PNG encoder (stdlib only)
# ---------------------------------------------------------------------------
def _chunk(chunk_type, data):
    out = struct.pack(">I", len(data)) + chunk_type + data
    out += struct.pack(">I", binascii.crc32(chunk_type + data) & 0xFFFFFFFF)
    return out


def encode_png(canvas):
    """Encode the RGB canvas as a PNG byte string (colour type 2, 8-bit)."""
    raw = bytearray()
    stride = W * 3
    for y in range(H):
        raw.append(0)  # filter type 0 (None) for every scanline
        raw += canvas[y * stride:(y + 1) * stride]
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += _chunk(b"IHDR", ihdr)
    png += _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += _chunk(b"IEND", b"")
    return png


# ---------------------------------------------------------------------------
# Layout and rendering
# ---------------------------------------------------------------------------
def render():
    canvas = bytearray(W * H * 3)
    fill_rect(canvas, 0, 0, W, H, BG)

    # --- Header ------------------------------------------------------------
    draw_text_centered(canvas, 18, TITLE_TEXT, 4, TITLE)
    draw_text_centered(canvas, 58, SUBTITLE_TEXT, 2, GOLD)

    # --- Story grid: 2 columns x 3 rows ------------------------------------
    margin = 16
    gap = 12
    top = 96
    row_h = (H - top - margin - 2 * gap) // 3   # 296
    col_w = (W - 2 * margin - gap) // 2         # 490
    pad = 22
    inner_w = col_w - 2 * pad                   # 446

    for idx, (kicker, accent, headline, body) in enumerate(STORIES):
        col = idx % 2
        row = idx // 2
        x = margin + col * (col_w + gap)
        y = top + row * (row_h + gap)

        # Card background + accent bar on top.
        fill_rect(canvas, x, y, col_w, row_h, CELL)
        fill_rect(canvas, x, y, col_w, 6, accent)

        cy = y + pad + 6  # content starts below the accent bar

        # Kicker (left) + story number (right).
        draw_text(canvas, x + pad, cy, kicker, 2, accent)
        number = "%02d" % (idx + 1)
        draw_text(canvas, x + col_w - pad - text_width(number, 2),
                  cy, number, 2, MUTED)
        cy += 14 + 12

        # Headline, scale 4 (28 px tall), line gap 6.
        head_lines = wrap_text(headline, inner_w, 4)
        for line in head_lines:
            draw_text(canvas, x + pad, cy, line, 4, INK)
            cy += 28 + 6
        cy += 4

        # Short accent rule under the headline.
        fill_rect(canvas, x + pad, cy, 64, 4, accent)
        cy += 4 + 12

        # Supporting text, scale 2 (14 px tall), line gap 5.
        body_lines = wrap_text(body, inner_w, 2)
        for line in body_lines:
            draw_text(canvas, x + pad, cy, line, 2, BODY)
            cy += 14 + 5

        # Safety: content must stay inside the card.
        if cy > y + row_h - pad:
            raise SystemExit(
                "layout overflow in story %d: content ends at y=%d, "
                "card bottom is %d" % (idx + 1, cy, y + row_h - pad)
            )

    return encode_png(canvas)


def main():
    png = render()
    OUT.write_bytes(png)
    digest = hashlib.sha256(png).hexdigest()
    print("wrote %s (%d bytes)" % (OUT, len(png)))
    print("sha256: %s" % digest)


if __name__ == "__main__":
    main()
