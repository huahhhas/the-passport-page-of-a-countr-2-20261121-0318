#!/usr/bin/env python3
"""Draw an invented passport spread for the Republic of Solmere.

Writes /output/entry.png (1024x1024, PNG, <= 1 MiB): an open passport
spread for a fictional North Atlantic island nation. Left page: visas and
stamps. Right page: data page with a drawn portrait, personal details and a
machine-readable zone with real ICAO 9303 check digits.

Everything is drawn with PIL from scratch; no external files, no network,
no randomness, so two runs are byte-identical.
"""
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W = H = 1024

# ---------------------------------------------------------------- fonts
SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
SERIF_B = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SERIF_I = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
SANS_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"

_FALLBACK = {
    SERIF: "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
    SERIF_B: "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
    SERIF_I: "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf",
    SANS: "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    SANS_B: "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    MONO: "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
}


def font(path, size):
    for p in (path, _FALLBACK.get(path)):
        if p and os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except OSError:
                pass
    return ImageFont.load_default()


# ---------------------------------------------------------------- colours
DESK = (122, 114, 102)
PAGE = (243, 237, 218)
PAGE_EDGE = (201, 191, 164)
INK = (30, 42, 68)          # dark navy ink
INK_SOFT = (74, 84, 104)
RULE = (150, 138, 108)
STAMP_BLUE = (43, 77, 143)
STAMP_PURPLE = (107, 63, 160)
STAMP_RED = (163, 51, 39)
PHOTO_BG = (183, 195, 201)
SKIN = (217, 169, 134)
SKIN_DARK = (198, 148, 112)
HAIR = (74, 56, 42)
SHAWL = (52, 68, 92)
GOLD = (146, 110, 52)


def tracked(d, xy, text, fnt, fill, spacing=2):
    """Draw text with letter spacing, returning the width used."""
    x, y = xy
    for ch in text:
        d.text((x, y), ch, font=fnt, fill=fill)
        x += d.textlength(ch, font=fnt) + spacing
    return x


def centre(d, cx, y, text, fnt, fill, spacing=0):
    w = sum(d.textlength(c, font=fnt) + spacing for c in text) - spacing
    tracked(d, (cx - w / 2, y), text, fnt, fill, spacing)
    return w


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
def coat_of_arms(d, cx, cy, r):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=GOLD, width=3)
    d.ellipse([cx - r + 6, cy - r + 6, cx + r - 6, cy + r - 6],
              outline=GOLD, width=1)
    # lighthouse
    d.polygon([(cx - 7, cy + r - 12), (cx - 4, cy - r + 22),
               (cx + 4, cy - r + 22), (cx + 7, cy + r - 12)],
              fill=INK)
    d.rectangle([cx - 8, cy - r + 14, cx + 8, cy - r + 22], fill=INK)
    d.line([cx - 16, cy - r + 18, cx - 26, cy - r + 12], fill=GOLD, width=2)
    d.line([cx + 16, cy - r + 18, cx + 26, cy - r + 12], fill=GOLD, width=2)
    # waves
    for k, yy in enumerate((cy + r - 26, cy + r - 18, cy + r - 10)):
        d.arc([cx - r + 12, yy - 6, cx + r - 12, yy + 10],
              start=200, end=340, fill=INK, width=2)
    # gull
    d.arc([cx - 24, cy - 6, cx - 12, cy + 6], start=200, end=340,
          fill=INK, width=2)
    d.arc([cx - 12, cy - 6, cx, cy + 6], start=200, end=340,
          fill=INK, width=2)


# ---------------------------------------------------------------- portrait
def portrait(d, box):
    x0, y0, x1, y1 = box
    d.rectangle(box, fill=PHOTO_BG)
    # faint backdrop lines
    for yy in range(y0 + 14, y1 - 10, 18):
        d.line([x0, yy, x1, yy], fill=(172, 184, 190), width=1)
    cx = (x0 + x1) // 2
    # shoulders / woollen shawl
    d.pieslice([cx - 78, y1 - 96, cx + 78, y1 + 40], start=180, end=360,
               fill=SHAWL)
    d.rectangle([cx - 78, y1 - 52, cx + 78, y1], fill=SHAWL)
    d.line([cx - 78, y1 - 52, cx + 78, y1 - 52], fill=(40, 54, 76), width=2)
    # shawl fold lines
    d.arc([cx - 60, y1 - 60, cx - 10, y1 + 10], start=90, end=200,
          fill=(40, 54, 76), width=2)
    d.arc([cx + 10, y1 - 60, cx + 60, y1 + 10], start=340, end=90,
          fill=(40, 54, 76), width=2)
    # neck
    d.rectangle([cx - 13, y1 - 118, cx + 13, y1 - 84], fill=SKIN_DARK)
    # head
    d.ellipse([cx - 34, y0 + 26, cx + 34, y0 + 118], fill=SKIN)
    # hair: cap + bun + side sweep
    d.pieslice([cx - 36, y0 + 22, cx + 36, y0 + 92], start=180, end=360,
               fill=HAIR)
    d.ellipse([cx + 8, y0 + 8, cx + 42, y0 + 42], fill=HAIR)  # bun
    d.pieslice([cx - 36, y0 + 30, cx - 8, y0 + 96], start=90, end=270,
               fill=HAIR)
    # brows, eyes, nose, mouth
    d.line([cx - 22, y0 + 74, cx - 8, y0 + 72], fill=HAIR, width=3)
    d.line([cx + 8, y0 + 72, cx + 22, y0 + 74], fill=HAIR, width=3)
    d.ellipse([cx - 19, y0 + 80, cx - 11, y0 + 86], fill=(38, 32, 28))
    d.ellipse([cx + 11, y0 + 80, cx + 19, y0 + 86], fill=(38, 32, 28))
    d.line([cx + 1, y0 + 86, cx - 2, y0 + 100], fill=SKIN_DARK, width=2)
    d.line([cx - 9, y0 + 110, cx + 9, y0 + 110], fill=(146, 84, 66), width=3)
    # cheek shading
    d.ellipse([cx - 30, y0 + 92, cx - 18, y0 + 102], fill=(206, 150, 116))
    d.ellipse([cx + 18, y0 + 92, cx + 30, y0 + 102], fill=(206, 150, 116))


# ---------------------------------------------------------------- stamps
def stamp(base, cx, cy, lines, colour, angle, w=200, h=112):
    """A rotated rubber-stamp layer pasted onto the spread."""
    layer = Image.new("RGBA", (w + 60, h + 60), (0, 0, 0, 0))
    sd = ImageDraw.Draw(layer)
    ox, oy = 30, 30
    sd.rounded_rectangle([ox, oy, ox + w, oy + h], radius=10,
                         outline=colour + (215,), width=3)
    sd.rounded_rectangle([ox + 6, oy + 6, ox + w - 6, oy + h - 6], radius=7,
                         outline=colour + (215,), width=1)
    f_big = font(SANS_B, 26)
    f_mid = font(SANS_B, 17)
    f_sml = font(SANS, 14)
    ys = [oy + 12, oy + 42, oy + 68]
    fonts = [f_big, f_mid, f_sml]
    for (txt, fnt), yy in zip(zip(lines, fonts), ys):
        tw = sd.textlength(txt, font=fnt)
        sd.text((ox + (w - tw) / 2, yy), txt, font=fnt, fill=colour + (225,))
    layer = layer.rotate(angle, resample=Image.BICUBIC, expand=False)
    base.alpha_composite(layer, (int(cx - layer.width / 2),
                                int(cy - layer.height / 2)))


def round_seal(base, cx, cy, r, colour, angle, top, bottom):
    """A small circular seal, rotated, stamped over a photo corner."""
    size = r * 2 + 24
    layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    sd = ImageDraw.Draw(layer)
    c = size // 2
    sd.ellipse([8, 8, size - 8, size - 8], outline=colour + (200,), width=3)
    sd.ellipse([16, 16, size - 16, size - 16], outline=colour + (200,),
               width=1)
    sd.text((c, c - 4), "*", font=font(SERIF_B, 30),
            fill=colour + (210,), anchor="mm")
    f = font(SANS_B, 11)
    for txt, yy in ((top, c - r + 12), (bottom, c + r - 24)):
        tw = sd.textlength(txt, font=f)
        sd.text((c - tw / 2, yy), txt, font=f, fill=colour + (210,))
    layer = layer.rotate(angle, resample=Image.BICUBIC, expand=False)
    base.alpha_composite(layer, (int(cx - size / 2), int(cy - size / 2)))


# ---------------------------------------------------------------- pages
def guilloche(d, x0, y0, x1, y1):
    for r in range(120, 900, 90):
        d.ellipse([x1 - r, y1 - r, x1 + r, y1 + r],
                  outline=(214, 204, 178), width=1)


def field(d, x, y, label, value, vfont=None, vsize=20):
    d.text((x, y), label, font=font(SANS, 12), fill=INK_SOFT)
    d.text((x, y + 15), value, font=vfont or font(SERIF_B, vsize), fill=INK)


def build():
    img = Image.new("RGB", (W, H), DESK).convert("RGBA")
    d = ImageDraw.Draw(img, "RGBA")

    # soft shadow under the spread
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle([78, 84, 962, 966], radius=6,
                                             fill=(0, 0, 0, 110))
    shadow = shadow.filter(ImageFilter.GaussianBlur(10))
    img.paste(Image.alpha_composite(img.convert("RGBA"), shadow), (0, 0))
    d = ImageDraw.Draw(img, "RGBA")

    # the two pages
    for (px0, px1) in ((70, 508), (516, 954)):
        d.rectangle([px0, 70, px1, 954], fill=PAGE, outline=PAGE_EDGE,
                    width=2)
        guilloche(d, px0, 70, px1, 954)
    # centre gutter
    d.line([512, 70, 512, 954], fill=(120, 108, 84), width=3)
    d.line([508, 70, 508, 954], fill=(255, 255, 255, 90), width=1)

    # ================= left page: visas =================
    lx0, lx1 = 96, 482
    centre(d, (lx0 + lx1) // 2, 104, "VISAS", font(SERIF_B, 24), INK, 6)
    d.line([lx0 + 60, 140, lx1 - 60, 140], fill=RULE, width=2)

    stamp(img, 205, 225, ["TARN", "ARRIVAL", "02 APR 2024"],
          STAMP_BLUE, -8)
    stamp(img, 380, 235, ["TARN", "DEPARTURE", "19 APR 2024"],
          STAMP_BLUE, 6)
    stamp(img, 200, 380, ["TARN", "VISITOR VISA", "30 DAYS · No. T-2214"],
          STAMP_PURPLE, 4)
    stamp(img, 385, 395, ["MIRELLE", "ARRIVAL", "07 SEP 2025"],
          STAMP_PURPLE, -6)
    stamp(img, 200, 540, ["MIRELLE", "DEPARTURE", "21 SEP 2025"],
          STAMP_PURPLE, 8)
    stamp(img, 385, 550, ["SOLMERE", "ENTRY", "22 SEP 2025"],
          STAMP_RED, -3)

    # conditions box — the telling paperwork detail
    bx0, bx1, by0, by1 = lx0, lx1, 650, 800
    d.rectangle([bx0, by0, bx1, by1], outline=STAMP_RED + (220,), width=3)
    d.rectangle([bx0 + 5, by0 + 5, bx1 - 5, by1 - 5],
                outline=STAMP_RED + (220,), width=1)
    centre(d, (bx0 + bx1) // 2, by0 + 16, "CONDITIONS OF ENTRY",
           font(SANS_B, 16), STAMP_RED + (235,), 2)
    cond = ["HOLDER MAY LAND BY SEA ONLY.",
            "SOLMERE HAS NO AIRPORT.",
            "HARBOUR TAX 12 KR PAID",
            "AT PORT SOLMERE."]
    yy = by0 + 44
    for line in cond:
        centre(d, (bx0 + bx1) // 2, yy, line, font(SANS_B, 15),
               STAMP_RED + (235,), 1)
        yy += 24
    d.text((lx0, 850), "OBSERVATIONS:  NONE", font=font(SANS, 14),
           fill=INK_SOFT)
    d.text((lx0, 880), "Page 3 of 32", font=font(SANS, 13), fill=INK_SOFT)

    # ================= right page: data page =================
    rx0, rx1 = 542, 928
    coat_of_arms(d, 735, 158, 40)
    centre(d, 735, 214, "REPUBLIC OF SOLMERE", font(SERIF_B, 29), INK, 1)
    centre(d, 735, 250, "PASSPORT · VEGABRÉF", font(SANS, 14), INK_SOFT, 3)
    d.line([rx0 + 40, 282, rx1 - 40, 282], fill=RULE, width=2)

    # portrait
    portrait(d, (rx0, 300, rx0 + 168, 510))
    d.rectangle([rx0, 300, rx0 + 168, 510], outline=INK, width=2)
    round_seal(img, rx0 + 140, 468, 24, STAMP_RED, -14,
               "PORT", "SOLMERE")

    # fields beside the portrait
    fx = rx0 + 186
    field(d, fx, 300, "SURNAME", "AULDER")
    field(d, fx, 352, "GIVEN NAMES", "MARA INGRID")
    field(d, fx, 404, "NATIONALITY", "SOLMERI")
    field(d, fx, 456, "DATE OF BIRTH", "14 JUN 1988")

    # second row of fields
    field(d, rx0, 540, "PLACE OF BIRTH", "PORT SOLMERE")
    field(d, rx0 + 200, 540, "SEX", "F")
    field(d, rx0, 592, "TYPE", "P")
    field(d, rx0 + 66, 592, "CODE", "SLM")
    field(d, rx0 + 150, 592, "PASSPORT No.", "SLM 041 882")
    field(d, rx0, 644, "DATE OF ISSUE", "12 MAR 2024")
    field(d, rx0 + 200, 644, "DATE OF EXPIRY", "11 MAR 2034")
    field(d, rx0, 696, "AUTHORITY", "PORT SOLMERE")

    # signature
    d.text((rx0, 742), "Mara Ingrid Aulder", font=font(SERIF_I, 26),
           fill=INK)
    d.line([rx0, 778, rx0 + 210, 778], fill=INK, width=1)
    d.text((rx0, 782), "Signature of holder", font=font(SANS, 12),
           fill=INK_SOFT)

    # machine-readable zone
    l1, l2 = mrz_lines()
    mf = font(MONO, 14)
    d.text((rx0, 824), l1, font=mf, fill=INK)
    d.text((rx0, 844), l2, font=mf, fill=INK)
    d.line([rx0, 812, rx1, 812], fill=RULE, width=1)
    d.text((rx0, 878), "Language: SOLMERI · ENGLISH",
           font=font(SANS, 13), fill=INK_SOFT)
    d.text((rx1 - 60, 878), "P. 2", font=font(SANS, 13), fill=INK_SOFT)
    return img


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    img = build()
    path = os.path.join(out_dir, "entry.png")
    img.convert("RGB").save(path, format="PNG")
    print("wrote", path, img.size, os.path.getsize(path), "bytes")


if __name__ == "__main__":
    main()
