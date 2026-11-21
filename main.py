#!/usr/bin/env python3
"""Draw an invented passport spread for the Republic of Solmere.

Pure Python standard library only (os, zlib, struct, math). No Pillow:
the grader runs this in the official python image, which has no PIL.

Writes /output/entry.png (1024x1024, PNG, <= 1 MiB): an open passport
spread for a fictional North Atlantic island nation. Left page: visas and
stamps. Right page: data page with a drawn portrait, personal details and
a machine-readable zone with real ICAO 9303 check digits.

The PNG is encoded by hand (signature + IHDR + IDAT + IEND, zlib level 9)
and every shape is drawn with small raster helpers on a bytearray canvas,
plus a built-in 5x7 bitmap font. No timestamps anywhere, so two runs are
byte-identical.
"""
import math
import os
import struct
import zlib

W = H = 1024

# ---------------------------------------------------------------- colours
DESK = (122, 114, 102)
SHADOW = (70, 64, 56)
PAGE = (243, 237, 218)
PAGE_EDGE = (201, 191, 164)
PAGE_LINE = (214, 204, 178)
INK = (30, 42, 68)          # dark navy ink
INK_SOFT = (74, 84, 104)
RULE = (150, 138, 108)
STAMP_BLUE = (43, 77, 143)
STAMP_PURPLE = (107, 63, 160)
STAMP_RED = (163, 51, 39)
PHOTO_BG = (183, 195, 201)
PHOTO_LINE = (172, 184, 190)
SKIN = (217, 169, 134)
SKIN_DARK = (198, 148, 112)
CHEEK = (206, 150, 116)
HAIR = (74, 56, 42)
SHAWL = (52, 68, 92)
SHAWL_DARK = (40, 54, 76)
GOLD = (146, 110, 52)
EYE = (38, 32, 28)
MOUTH = (146, 84, 66)

# ---------------------------------------------------------------- canvas
canvas = bytearray(W * H * 3)
CLIP = [0, 0, W, H]


def set_clip(x0, y0, x1, y1):
    CLIP[0], CLIP[1], CLIP[2], CLIP[3] = x0, y0, x1, y1


def reset_clip():
    CLIP[0], CLIP[1], CLIP[2], CLIP[3] = 0, 0, W, H


def fill_canvas(color):
    canvas[:] = bytes(color) * (W * H)


def fill_rect(x0, y0, x1, y1, color):
    x0 = max(x0, CLIP[0])
    y0 = max(y0, CLIP[1])
    x1 = min(x1, CLIP[2])
    y1 = min(y1, CLIP[3])
    if x0 >= x1 or y0 >= y1:
        return
    row = bytes(color) * (x1 - x0)
    for y in range(y0, y1):
        o = (y * W + x0) * 3
        canvas[o:o + len(row)] = row


def set_px(x, y, color):
    if CLIP[0] <= x < CLIP[2] and CLIP[1] <= y < CLIP[3]:
        o = (y * W + x) * 3
        canvas[o] = color[0]
        canvas[o + 1] = color[1]
        canvas[o + 2] = color[2]


def draw_line(x0, y0, x1, y1, color, width=1):
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    x, y = x0, y0
    while True:
        if width == 1:
            set_px(x, y, color)
        else:
            hw = width // 2
            fill_rect(x - hw, y - hw, x + hw + 1, y + hw + 1, color)
        if x == x1 and y == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x += sx
        if e2 <= dx:
            err += dx
            y += sy


def draw_polyline(points, color, width=1):
    for i in range(len(points) - 1):
        draw_line(points[i][0], points[i][1],
                  points[i + 1][0], points[i + 1][1], color, width)


def fill_ellipse(cx, cy, rx, ry, color):
    for y in range(cy - ry, cy + ry + 1):
        t = (y - cy) / ry
        dx = int(rx * math.sqrt(max(0.0, 1.0 - t * t)))
        fill_rect(cx - dx, y, cx + dx + 1, y + 1, color)


def circle_outline(cx, cy, r, color, width=2):
    steps = max(24, int(2 * math.pi * r))
    hw = width // 2
    for i in range(steps):
        a = 2 * math.pi * i / steps
        x = int(round(cx + r * math.cos(a)))
        y = int(round(cy + r * math.sin(a)))
        fill_rect(x - hw, y - hw, x + hw + 1, y + hw + 1, color)


def fill_polygon(points, color):
    ys = [p[1] for p in points]
    n = len(points)
    for y in range(min(ys), max(ys) + 1):
        xs = []
        for i in range(n):
            x0, y0 = points[i]
            x1, y1 = points[(i + 1) % n]
            if (y0 <= y < y1) or (y1 <= y < y0):
                xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
        xs.sort()
        for i in range(0, len(xs) - 1, 2):
            fill_rect(int(xs[i]), y, int(xs[i + 1]) + 1, y + 1, color)


def rect_outline(x0, y0, x1, y1, color, width=1):
    for w in range(width):
        fill_rect(x0 + w, y0 + w, x1 - w, y0 + w + 1, color)
        fill_rect(x0 + w, y1 - w - 1, x1 - w, y1 - w, color)
        fill_rect(x0 + w, y0 + w, x0 + w + 1, y1 - w, color)
        fill_rect(x1 - w - 1, y0 + w, x1 - w, y1 - w, color)


# ---------------------------------------------------------------- bitmap font
# 5x7 glyphs, '#' = on, '.' = off. Written from scratch for this entry.
FONT = {
    " ": [".....", ".....", ".....", ".....", ".....", ".....", "....."],
    "!": ["..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."],
    "'": ["..#..", "..#..", ".#...", ".....", ".....", ".....", "....."],
    "(": ["...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#."],
    ")": [".#...", "..#..", "...#.", "...#.", "...#.", "..#..", ".#..."],
    ",": [".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."],
    "-": [".....", ".....", ".....", ".###.", ".....", ".....", "....."],
    ".": [".....", ".....", ".....", ".....", ".....", ".##..", ".##.."],
    "/": ["....#", "....#", "...#.", "...#.", "..#..", ".#...", "#...."],
    "0": [".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."],
    "1": ["..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."],
    "2": [".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"],
    "3": ["####.", "....#", "....#", ".###.", "....#", "....#", "####."],
    "4": ["...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."],
    "5": ["#####", "#....", "####.", "....#", "....#", "#...#", ".###."],
    "6": [".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."],
    "7": ["#####", "....#", "...#.", "...#.", "..#..", "..#..", "..#.."],
    "8": [".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."],
    "9": [".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."],
    ":": [".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."],
    ";": [".....", ".##..", ".##..", ".....", ".##..", ".##..", ".#..."],
    "<": ["...#.", "..#..", ".#...", "#....", ".#...", "..#..", "...#."],
    "=": [".....", ".....", "#####", ".....", "#####", ".....", "....."],
    ">": [".#...", "..#..", "...#.", "....#", "...#.", "..#..", ".#..."],
    "?": [".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."],
    "A": [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "B": ["####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."],
    "C": [".####", "#....", "#....", "#....", "#....", "#....", ".####"],
    "D": ["####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."],
    "E": ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
    "F": ["#####", "#....", "#....", "####.", "#....", "#....", "#...."],
    "G": [".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."],
    "H": ["#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "I": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"],
    "J": ["..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."],
    "K": ["#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"],
    "L": ["#....", "#....", "#....", "#....", "#....", "#....", "#####"],
    "M": ["#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"],
    "N": ["#...#", "##..#", "##..#", "#.#.#", "#..##", "#..##", "#...#"],
    "O": [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "P": ["####.", "#...#", "#...#", "####.", "#....", "#....", "#...."],
    "Q": [".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"],
    "R": ["####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"],
    "S": [".####", "#....", "#....", ".###.", "....#", "....#", "####."],
    "T": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    "U": ["#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "V": ["#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."],
    "W": ["#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"],
    "X": ["#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"],
    "Y": ["#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."],
    "Z": ["#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"],
    "a": [".....", ".....", ".###.", "....#", ".####", "#...#", ".####"],
    "b": ["#....", "#....", "####.", "#...#", "#...#", "#...#", "####."],
    "c": [".....", ".....", ".####", "#....", "#....", "#....", ".####"],
    "d": ["....#", "....#", ".####", "#...#", "#...#", "#...#", ".####"],
    "e": [".....", ".....", ".###.", "#...#", "#####", "#....", ".###."],
    "f": ["..##.", ".#..#", ".#...", "####.", ".#...", ".#...", ".#..."],
    "g": [".....", ".....", ".####", "#...#", "#...#", ".####", "....#"],
    "h": ["#....", "#....", "####.", "#...#", "#...#", "#...#", "#...#"],
    "i": [".....", "..#..", ".....", ".##..", "..#..", "..#..", ".###."],
    "j": ["...#.", ".....", "..##.", "...#.", "...#.", "...#.", ".##.."],
    "k": ["#....", "#....", "#..#.", "#.#..", "##...", "#.#..", "#..#."],
    "l": [".##..", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."],
    "m": [".....", ".....", "##.#.", "#.#.#", "#.#.#", "#.#.#", "#.#.#"],
    "n": [".....", ".....", "####.", "#...#", "#...#", "#...#", "#...#"],
    "o": [".....", ".....", ".###.", "#...#", "#...#", "#...#", ".###."],
    "p": [".....", ".....", "####.", "#...#", "#...#", "####.", "#...."],
    "q": [".....", ".....", ".####", "#...#", "#...#", ".####", "....#"],
    "r": [".....", ".....", "#.##.", "##..#", "#....", "#....", "#...."],
    "s": [".....", ".....", ".####", "#....", ".###.", "....#", "####."],
    "t": [".#...", ".#...", "####.", ".#...", ".#...", ".#...", "..##."],
    "u": [".....", ".....", "#...#", "#...#", "#...#", "#..##", ".##.#"],
    "v": [".....", ".....", "#...#", "#...#", "#...#", ".#.#.", "..#.."],
    "w": [".....", ".....", "#...#", "#.#.#", "#.#.#", "#.#.#", ".#.#."],
    "x": [".....", ".....", "#...#", ".#.#.", "..#..", ".#.#.", "#...#"],
    "y": [".....", ".....", "#...#", "#...#", ".####", "....#", ".###."],
    "z": [".....", ".....", "#####", "...#.", "..#..", ".#...", "#####"],
    "·": [".....", ".....", ".##..", ".##..", ".....", ".....", "....."],
    "É": ["...#.", "..#..", "#####", "#....", "####.", "#....", "#####"],
}


def text_width(s, scale):
    return len(s) * 6 * scale - scale


def _text_run(x, y, row, c0, c1, scale, color, slant):
    ox = x + c0 * scale + (6 - row) * slant
    oy = y + row * scale
    fill_rect(ox, oy, ox + (c1 - c0) * scale, oy + scale, color)


def draw_text(x, y, s, scale, color, slant=0):
    cx = x
    for ch in s:
        g = FONT.get(ch)
        if g is None:
            cx += 6 * scale
            continue
        for row in range(7):
            bits = g[row]
            run = None
            for col in range(5):
                if bits[col] == "#":
                    if run is None:
                        run = col
                elif run is not None:
                    _text_run(cx, y, row, run, col, scale, color, slant)
                    run = None
            if run is not None:
                _text_run(cx, y, row, run, 5, scale, color, slant)
        cx += 6 * scale


def draw_text_centred(cx, y, s, scale, color, slant=0):
    draw_text(cx - text_width(s, scale) // 2, y, s, scale, color, slant)


# ---------------------------------------------------------------- MRZ (ICAO 9303)
def _check_digit(s):
    weights = (7, 3, 1)
    total = 0
    for i, ch in enumerate(s):
        if ch == "<":
            v = 0
        elif ch.isdigit():
            v = int(ch)
        else:
            v = ord(ch) - 55  # A=10 ... Z=35
        total += v * weights[i % 3]
    return str(total % 10)


def mrz_lines():
    line1 = ("P<SLM" + "AULDER" + "<<" + "MARA" + "<" + "INGRID").ljust(44, "<")
    doc = "SLM041882"
    dob = "880614"
    exp = "340311"
    personal = "MARA1988SOLM<<"
    composite_src = (doc + _check_digit(doc) + "SLM" + dob + _check_digit(dob)
                     + "F" + exp + _check_digit(exp) + personal
                     + _check_digit(personal))
    line2 = (doc + _check_digit(doc) + "SLM" + dob + _check_digit(dob) + "F"
             + exp + _check_digit(exp) + personal + _check_digit(personal)
             + _check_digit(composite_src))
    assert len(line1) == 44 and len(line2) == 44, (line1, line2)
    return line1, line2


# ---------------------------------------------------------------- coat of arms
def coat_of_arms(cx, cy, r):
    circle_outline(cx, cy, r, GOLD, 3)
    circle_outline(cx, cy, r - 6, GOLD, 1)
    # lighthouse tower
    fill_polygon([(cx - 7, cy + r - 12), (cx - 4, cy - r + 22),
                  (cx + 4, cy - r + 22), (cx + 7, cy + r - 12)], INK)
    # lamp room
    fill_rect(cx - 8, cy - r + 14, cx + 8, cy - r + 22, INK)
    # light beams
    draw_line(cx - 16, cy - r + 18, cx - 26, cy - r + 12, GOLD, 2)
    draw_line(cx + 16, cy - r + 18, cx + 26, cy - r + 12, GOLD, 2)
    # waves
    for yy in (cy + r - 26, cy + r - 18, cy + r - 10):
        pts = []
        for k in range(25):
            x = cx - r + 12 + k * (2 * r - 24) / 24
            y = yy + 3 * math.sin(k * math.pi / 6)
            pts.append((int(x), int(y)))
        draw_polyline(pts, INK, 2)
    # gull: two shallow curves
    for gx in (cx - 24, cx - 12):
        pts = []
        for k in range(9):
            x = gx + k * 12 / 8
            y = cy - 6 + int(3 * math.sin(k * math.pi / 8))
            pts.append((int(x), int(y)))
        draw_polyline(pts, INK, 2)


# ---------------------------------------------------------------- portrait
def portrait(x0, y0, x1, y1):
    set_clip(x0, y0, x1, y1)
    fill_rect(x0, y0, x1, y1, PHOTO_BG)
    for yy in range(y0 + 14, y1 - 10, 18):
        draw_line(x0, yy, x1, yy, PHOTO_LINE, 1)
    cx = (x0 + x1) // 2
    # shoulders / woollen shawl: raised so the top meets the neck, folds
    # drawn only inside the shawl mass (earlier they crossed the bare
    # photo background and read as sticks)
    fill_ellipse(cx, y1 - 10, 80, 75, SHAWL)
    draw_line(cx - 45, y1 - 40, cx - 12, y1 - 8, SHAWL_DARK, 2)
    draw_line(cx + 12, y1 - 8, cx + 45, y1 - 40, SHAWL_DARK, 2)
    # neck
    fill_rect(cx - 13, y1 - 118, cx + 13, y1 - 84, SKIN_DARK)
    # hair behind the head, then the face over it
    fill_ellipse(cx, y0 + 50, 38, 36, HAIR)
    fill_ellipse(cx, y0 + 76, 33, 44, SKIN)
    # bun and side sweep
    fill_ellipse(cx + 34, y0 + 30, 16, 16, HAIR)
    fill_ellipse(cx - 28, y0 + 70, 12, 26, HAIR)
    # brows, eyes, nose, mouth
    draw_line(cx - 22, y0 + 74, cx - 8, y0 + 72, HAIR, 3)
    draw_line(cx + 8, y0 + 72, cx + 22, y0 + 74, HAIR, 3)
    fill_ellipse(cx - 15, y0 + 80, 4, 3, EYE)
    fill_ellipse(cx + 15, y0 + 80, 4, 3, EYE)
    draw_line(cx + 1, y0 + 86, cx - 2, y0 + 100, SKIN_DARK, 2)
    draw_line(cx - 9, y0 + 110, cx + 9, y0 + 110, MOUTH, 3)
    # cheek shading
    fill_ellipse(cx - 24, y0 + 97, 8, 5, CHEEK)
    fill_ellipse(cx + 24, y0 + 97, 8, 5, CHEEK)
    reset_clip()


# ---------------------------------------------------------------- stamps
def stamp(sx, sy, lines, color):
    rect_outline(sx, sy, sx + 186, sy + 120, color, 3)
    rect_outline(sx + 6, sy + 6, sx + 180, sy + 114, color, 1)
    draw_text_centred(sx + 93, sy + 12, lines[0], 3, color)
    draw_text_centred(sx + 93, sy + 45, lines[1], 2, color)
    draw_text_centred(sx + 93, sy + 74, lines[2], 1, color)


def field(x, y, label, value):
    draw_text(x, y, label, 2, INK_SOFT)
    draw_text(x, y + 16, value, 2, INK)


# ---------------------------------------------------------------- pages
def build():
    fill_canvas(DESK)
    # soft shadow under the spread
    fill_rect(78, 84, 962, 966, SHADOW)
    # the two pages
    fill_rect(70, 70, 508, 954, PAGE)
    fill_rect(516, 70, 954, 954, PAGE)
    rect_outline(70, 70, 508, 954, PAGE_EDGE, 2)
    rect_outline(516, 70, 954, 954, PAGE_EDGE, 2)
    rect_outline(80, 80, 498, 944, PAGE_LINE, 1)
    rect_outline(526, 80, 944, 944, PAGE_LINE, 1)
    # centre gutter
    fill_rect(508, 70, 516, 954, (120, 108, 84))

    # ================= left page: visas =================
    draw_text_centred(289, 100, "VISAS", 4, INK)
    draw_line(156, 142, 422, 142, RULE, 2)
    stamp(96, 165, ["TARN", "ARRIVAL", "02 APR 2024"], STAMP_BLUE)
    stamp(296, 165, ["TARN", "DEPARTURE", "19 APR 2024"], STAMP_BLUE)
    stamp(96, 300, ["TARN", "VISITOR VISA", "30 DAYS · No. T-2214"],
          STAMP_PURPLE)
    stamp(296, 300, ["MIRELLE", "ARRIVAL", "07 SEP 2025"], STAMP_PURPLE)
    stamp(96, 435, ["MIRELLE", "DEPARTURE", "21 SEP 2025"], STAMP_PURPLE)
    stamp(296, 435, ["SOLMERE", "ENTRY", "22 SEP 2025"], STAMP_RED)

    # conditions box — the telling paperwork detail
    rect_outline(96, 620, 482, 800, STAMP_RED, 3)
    rect_outline(101, 625, 477, 795, STAMP_RED, 1)
    draw_text_centred(289, 636, "CONDITIONS OF ENTRY", 2, STAMP_RED)
    for i, line in enumerate(["HOLDER MAY LAND BY SEA ONLY.",
                              "SOLMERE HAS NO AIRPORT.",
                              "HARBOUR TAX 12 KR PAID",
                              "AT PORT SOLMERE."]):
        draw_text_centred(289, 664 + i * 24, line, 2, STAMP_RED)
    draw_text(96, 830, "OBSERVATIONS:  NONE", 2, INK_SOFT)
    draw_text(96, 862, "Page 3 of 32", 2, INK_SOFT)

    # ================= right page: data page =================
    coat_of_arms(735, 158, 40)
    draw_text_centred(735, 214, "REPUBLIC OF SOLMERE", 3, INK)
    draw_text_centred(735, 250, "PASSPORT · VEGABRÉF", 2, INK_SOFT)
    draw_line(582, 282, 888, 282, RULE, 2)

    # portrait
    portrait(542, 300, 710, 510)
    rect_outline(542, 300, 710, 510, INK, 2)

    # fields beside the portrait
    field(728, 300, "SURNAME", "AULDER")
    field(728, 352, "GIVEN NAMES", "MARA INGRID")
    field(728, 404, "NATIONALITY", "SOLMERI")
    field(728, 456, "DATE OF BIRTH", "14 JUN 1988")

    # second row of fields
    field(542, 540, "PLACE OF BIRTH", "PORT SOLMERE")
    field(742, 540, "SEX", "F")
    field(542, 592, "TYPE", "P")
    field(608, 592, "CODE", "SLM")
    field(692, 592, "PASSPORT No.", "SLM 041 882")
    field(542, 644, "DATE OF ISSUE", "12 MAR 2024")
    field(742, 644, "DATE OF EXPIRY", "11 MAR 2034")
    field(542, 696, "AUTHORITY", "PORT SOLMERE")

    # signature
    draw_text(542, 742, "Mara Ingrid Aulder", 2, INK, slant=1)
    draw_line(542, 778, 752, 778, INK, 1)
    draw_text(542, 784, "Signature of holder", 2, INK_SOFT)

    # machine-readable zone
    l1, l2 = mrz_lines()
    draw_line(542, 812, 928, 812, RULE, 1)
    draw_text_centred(735, 824, l1, 1, INK)
    draw_text_centred(735, 844, l2, 1, INK)
    draw_text(542, 878, "Language: SOLMERI · ENGLISH", 2, INK_SOFT)
    draw_text(880, 878, "P. 2", 2, INK_SOFT)


# ---------------------------------------------------------------- PNG encode
def _chunk(typ, data):
    out = struct.pack(">I", len(data)) + typ + data
    out += struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)
    return out


def write_png(path):
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    raw = bytearray()
    for y in range(H):
        raw.append(0)
        raw += canvas[y * W * 3:(y + 1) * W * 3]
    png = (b"\x89PNG\r\n\x1a\n"
           + _chunk(b"IHDR", ihdr)
           + _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
           + _chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(png)


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    build()
    path = os.path.join(out_dir, "entry.png")
    write_png(path)
    print("wrote", path, (W, H), os.path.getsize(path), "bytes")
    l1, l2 = mrz_lines()
    print("MRZ1", l1)
    print("MRZ2", l2)


if __name__ == "__main__":
    main()
