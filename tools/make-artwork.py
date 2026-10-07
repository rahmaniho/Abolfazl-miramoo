#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ابزار تولید تصاویر برداری (SVG) سایت ابوالفضل میرعمو
------------------------------------------------------
همه‌ی کاورها، آواتارها و تصویر پرتره به صورت «هنر انتزاعی موسیقایی»
با خطوط طلایی روی پس‌زمینه‌ی مشکی ساخته می‌شوند تا هیچ عکس استوک عمومی
در صفحه استفاده نشود.

اجرا:
    python3 tools/make-artwork.py

خروجی‌ها در assets/img/ ساخته می‌شوند و می‌توانند با عکس‌های واقعی
(نسبت ۸:۵ برای کاورها، ۱:۱ برای پرتره و آواتارها) جایگزین شوند.
"""

import os

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "img")

GOLD = "#D4AF37"
GOLD_LIGHT = "#E8CB6A"
GOLD_DEEP = "#C9A227"
AMBER = "#F0A93B"

HEAD = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="{label}">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#141210"/>
      <stop offset="0.55" stop-color="#0C0B0A"/>
      <stop offset="1" stop-color="#060606"/>
    </linearGradient>
    <radialGradient id="glow" cx="0.5" cy="0.42" r="0.62">
      <stop offset="0" stop-color="{amber}" stop-opacity="0.30"/>
      <stop offset="0.45" stop-color="{gold}" stop-opacity="0.10"/>
      <stop offset="1" stop-color="{gold}" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="gold" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{gl}"/>
      <stop offset="0.55" stop-color="{g}"/>
      <stop offset="1" stop-color="{gd}"/>
    </linearGradient>
    <linearGradient id="line" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="{g}" stop-opacity="0"/>
      <stop offset="0.5" stop-color="{gl}" stop-opacity="0.9"/>
      <stop offset="1" stop-color="{g}" stop-opacity="0"/>
    </linearGradient>
    <linearGradient id="fade" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{gl}" stop-opacity="0.85"/>
      <stop offset="1" stop-color="{gd}" stop-opacity="0.05"/>
    </linearGradient>
    <filter id="soft" x="-30%" y="-30%" width="160%" height="160%">
      <feGaussianBlur stdDeviation="14"/>
    </filter>
    <filter id="softer" x="-40%" y="-40%" width="180%" height="180%">
      <feGaussianBlur stdDeviation="30"/>
    </filter>
  </defs>
"""

TAIL = "</svg>\n"


def grid(w, h, step=40, opacity="0.05"):
    """شبکه‌ی محو خطوط برای حس «پارتیتور»."""
    out = ['  <g stroke="%s" stroke-width="1" opacity="%s">' % (GOLD, opacity)]
    x = step
    while x < w:
        out.append('    <line x1="%d" y1="0" x2="%d" y2="%d"/>' % (x, x, h))
        x += step
    y = step
    while y < h:
        out.append('    <line x1="0" y1="%d" x2="%d" y2="%d"/>' % (y, w, y))
        y += step
    out.append("  </g>")
    return "\n".join(out)


def frame(w, h, inset=22):
    return (
        '  <rect x="%d" y="%d" width="%d" height="%d" fill="none" stroke="%s" '
        'stroke-opacity="0.22" stroke-width="1" rx="10"/>' % (inset, inset, w - 2 * inset, h - 2 * inset, GOLD)
    )


def cover_base(w, h, label):
    return HEAD.format(w=w, h=h, label=label, amber=AMBER, gold=GOLD, gl=GOLD_LIGHT, g=GOLD, gd=GOLD_DEEP)


# ---------------------------------------------------------------- کاور ۱: موج صدا
def cover_waveform():
    w, h = 800, 500
    bars = []
    heights = [26, 54, 88, 40, 120, 170, 96, 210, 140, 64, 188, 232, 110, 74, 156, 198, 86, 132, 58, 96, 34]
    n = len(heights)
    bw = 14
    gap = (w - 160 - n * bw) / (n - 1)
    x = 80
    for i, hh in enumerate(heights):
        op = 0.35 + (hh / 232.0) * 0.55
        bars.append(
            '    <rect x="%.1f" y="%.1f" width="%d" height="%d" rx="7" fill="url(#fade)" opacity="%.2f"/>'
            % (x, (h - hh) / 2.0, bw, hh, op)
        )
        if hh == max(heights):
            bars.append(
                '    <rect x="%.1f" y="%.1f" width="%d" height="%d" rx="7" fill="%s" filter="url(#soft)" opacity="0.55"/>'
                % (x, (h - hh) / 2.0, bw, hh, GOLD_LIGHT)
            )
        x += bw + gap
    body = "\n".join(bars)
    return (
        cover_base(w, h, "کاور نمونه‌کار — موج صدا")
        + '  <rect width="%d" height="%d" fill="url(#bg)"/>\n' % (w, h)
        + grid(w, h)
        + '  <ellipse cx="%d" cy="%d" rx="330" ry="215" fill="url(#glow)"/>\n' % (w // 2, h // 2)
        + '  <line x1="60" y1="250" x2="740" y2="250" stroke="url(#line)" stroke-width="1.5" opacity="0.7"/>\n'
        + '  <circle cx="400" cy="250" r="196" fill="none" stroke="%s" stroke-opacity="0.16"/>\n' % GOLD
        + body
        + "\n"
        + frame(w, h)
        + TAIL
    )


# ---------------------------------------------------------------- کاور ۲: صفحه گرامافون
def cover_vinyl():
    w, h = 800, 500
    cx, cy, r = 400, 250, 186
    grooves = []
    rr = r
    while rr > 58:
        grooves.append('    <circle cx="%d" cy="%d" r="%.1f" fill="none" stroke="%s" stroke-opacity="0.16"/>' % (cx, cy, rr, GOLD))
        rr -= 13
    return (
        cover_base(w, h, "کاور نمونه‌کار — صفحه گرامافون")
        + '  <rect width="%d" height="%d" fill="url(#bg)"/>\n' % (w, h)
        + grid(w, h)
        + '  <ellipse cx="%d" cy="%d" rx="340" ry="220" fill="url(#glow)"/>\n' % (cx, cy)
        + '  <circle cx="%d" cy="%d" r="%d" fill="#0B0A09" stroke="%s" stroke-opacity="0.34"/>\n' % (cx, cy, r, GOLD)
        + "\n".join(grooves)
        + "\n"
        + '  <path d="M %d %d A %d %d 0 0 1 %d %d" fill="none" stroke="url(#line)" stroke-width="2.5" opacity="0.85"/>\n'
        % (cx - r + 26, cy - 30, r - 26, r - 26, cx + r - 26, cy - 30)
        + '  <circle cx="%d" cy="%d" r="54" fill="url(#gold)"/>\n' % (cx, cy)
        + '  <circle cx="%d" cy="%d" r="9" fill="#0A0A0A"/>\n' % (cx, cy)
        + '  <rect x="%d" y="%d" width="150" height="7" rx="4" fill="url(#gold)" opacity="0.9" transform="rotate(-28 %d %d)"/>\n'
        % (cx + 150, cy - 176, cx + 150, cy - 176)
        + '  <circle cx="%d" cy="%d" r="13" fill="%s" opacity="0.95"/>\n' % (cx + 214, cy - 210, GOLD_LIGHT)
        + '  <circle cx="%d" cy="%d" r="30" fill="%s" opacity="0.35" filter="url(#soft)"/>\n' % (cx + 214, cy - 210, AMBER)
        + frame(w, h)
        + TAIL
    )


# ---------------------------------------------------------------- کاور ۳: اجرای زنده
def cover_stage():
    w, h = 800, 500
    beams = []
    for i, (x0, x1) in enumerate([(150, 60), (400, 300), (650, 740)]):
        beams.append(
            '    <path d="M {a} 0 L {b} 0 L {c} {d} L {e} {d} Z" fill="url(#fade)" opacity="{o:.2f}"/>'.format(
                a=x0 - 46, b=x0 + 46, c=x1 + 120, d=h - 90, e=x1 - 120, o=0.30 - i * 0.04
            )
        )
    crowd = []
    for i in range(9):
        cxx = 100 + i * 75
        r = 20 + (i % 3) * 6
        crowd.append(
            '    <g opacity="0.92">'
            '<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="#15120E" stroke="{g}" stroke-opacity="0.35"/>'
            '<path d="M {cx:.1f} 470 q 0 -46 {cx:.1f} -46 q 34 0 34 46 z" fill="#15120E" stroke="{g}" stroke-opacity="0.30"/>'
            "</g>".format(cx=cxx, cy=408 - r * 0.2, r=r, g=GOLD)
        )
    return (
        cover_base(w, h, "کاور نمونه‌کار — اجرای زنده")
        + '  <rect width="%d" height="%d" fill="url(#bg)"/>\n' % (w, h)
        + '  <ellipse cx="400" cy="60" rx="360" ry="200" fill="url(#glow)"/>\n'
        + "\n".join(beams)
        + "\n"
        + '  <rect x="0" y="%d" width="%d" height="%d" fill="#070706"/>\n' % (h - 96, w, 96)
        + '  <line x1="0" y1="%d" x2="%d" y2="%d" stroke="url(#line)" stroke-width="1.6"/>\n' % (h - 96, w, h - 96)
        + "\n".join(crowd)
        + "\n"
        + frame(w, h)
        + TAIL
    )


# ---------------------------------------------------------------- کاور ۴: رویداد و صحنه
def cover_event():
    w, h = 800, 500
    dots = []
    import random

    random.seed(7)
    for _ in range(46):
        x = random.uniform(60, 740)
        y = random.uniform(60, 300)
        r = random.uniform(1.2, 3.4)
        o = random.uniform(0.18, 0.75)
        dots.append('    <circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s" opacity="%.2f"/>' % (x, y, r, GOLD_LIGHT, o))
    rays = []
    for i in range(7):
        ang = -80 + i * 26.7
        rays.append(
            '    <path d="M 400 470 L %.1f %.1f" stroke="%s" stroke-opacity="%.2f" stroke-width="2"/>'
            % (400 + 520 * math_cos(math_rad(ang)), 470 + 520 * math_sin(math_rad(ang)), GOLD, 0.30)
        )
    return (
        cover_base(w, h, "کاور نمونه‌کار — رویداد و صحنه")
        + '  <rect width="%d" height="%d" fill="url(#bg)"/>\n' % (w, h)
        + grid(w, h, 50, "0.04")
        + '  <ellipse cx="400" cy="470" rx="380" ry="260" fill="url(#glow)"/>\n'
        + "\n".join(rays)
        + "\n"
        + '  <circle cx="400" cy="470" r="150" fill="none" stroke="%s" stroke-opacity="0.32"/>\n' % GOLD
        + '  <circle cx="400" cy="470" r="230" fill="none" stroke="%s" stroke-opacity="0.14"/>\n' % GOLD
        + "\n".join(dots)
        + "\n"
        + frame(w, h)
        + TAIL
    )


def math_rad(d):
    import math

    return math.radians(d)


def math_cos(r):
    import math

    return math.cos(r)


def math_sin(r):
    import math

    return math.sin(r)


# ---------------------------------------------------------------- کاور ۵: آموزش و پیانو
def cover_teaching():
    w, h = 800, 500
    keys = []
    kw = 48
    x0 = (w - 10 * kw) / 2.0
    for i in range(10):
        x = x0 + i * kw
        keys.append(
            '    <rect x="%.1f" y="150" width="%.1f" height="200" rx="7" fill="#131110" stroke="%s" stroke-opacity="0.30"/>'
            % (x, kw - 5, GOLD)
        )
        pressed = i in (2, 6)
        if pressed:
            keys.append(
                '    <rect x="%.1f" y="150" width="%.1f" height="200" rx="7" fill="url(#gold)" opacity="0.16"/>'
                '    <rect x="%.1f" y="150" width="%.1f" height="200" rx="7" fill="none" stroke="%s" stroke-opacity="0.9"/>'
                % (x, kw - 5, x, kw - 5, GOLD_LIGHT)
            )
    blacks = []
    for i in [0, 1, 3, 4, 5, 7, 8]:
        x = x0 + i * kw + (kw - 5) - 8
        blacks.append(
            '    <rect x="%.1f" y="150" width="18" height="118" rx="5" fill="#080807" stroke="%s" stroke-opacity="0.45"/>' % (x, GOLD)
        )
    notes = []
    for i, (nx, ny) in enumerate([(150, 96), (300, 78), (520, 104), (660, 84)]):
        notes.append(
            '    <g opacity="0.9"><ellipse cx="%.1f" cy="%.1f" rx="11" ry="8" fill="%s" transform="rotate(-20 %.1f %.1f)"/>'
            '<rect x="%.1f" y="%.1f" width="3" height="46" fill="%s"/></g>' % (nx, ny, GOLD, nx, ny, nx + 9, ny - 44, GOLD)
        )
    return (
        cover_base(w, h, "کاور نمونه‌کار — آموزش و پیانو")
        + '  <rect width="%d" height="%d" fill="url(#bg)"/>\n' % (w, h)
        + grid(w, h)
        + '  <ellipse cx="400" cy="240" rx="330" ry="200" fill="url(#glow)"/>\n'
        + "\n".join(keys)
        + "\n"
        + '  <rect x="%.1f" y="%d" width="%.1f" height="52" rx="8" fill="#0B0A09" stroke="%s" stroke-opacity="0.35"/>\n'
        % (x0 - 14, 150, 10 * kw + 23, GOLD)
        + "\n".join(blacks)
        + "\n"
        + '  <line x1="80" y1="402" x2="720" y2="402" stroke="url(#line)" stroke-width="1.6"/>\n'
        + "\n".join(notes)
        + "\n"
        + frame(w, h)
        + TAIL
    )


# ---------------------------------------------------------------- کاور ۶: میکروفون و مراسم
def cover_mic():
    w, h = 800, 500
    cx, cy = 400, 250
    rings = []
    for i, r in enumerate([96, 138, 180, 224]):
        rings.append('    <circle cx="%d" cy="%d" r="%d" fill="none" stroke="%s" stroke-opacity="%.2f"/>' % (cx, cy, r, GOLD, 0.30 - i * 0.05))
    return (
        cover_base(w, h, "کاور نمونه‌کار — میکروفون و مراسم")
        + '  <rect width="%d" height="%d" fill="url(#bg)"/>\n' % (w, h)
        + grid(w, h, 44, "0.045")
        + '  <ellipse cx="%d" cy="%d" rx="320" ry="220" fill="url(#glow)"/>\n' % (cx, cy)
        + "\n".join(rings)
        + "\n"
        # بدنه میکروفون
        + '  <rect x="%d" y="%d" width="76" height="140" rx="38" fill="#100E0C" stroke="%s" stroke-opacity="0.85" stroke-width="2"/>\n'
        % (cx - 38, cy - 96, GOLD)
        + '  <g stroke="%s" stroke-opacity="0.5" stroke-width="1.4">\n' % GOLD_LIGHT
        + "".join('    <line x1="%d" y1="%d" x2="%d" y2="%d"/>\n' % (cx - 26, cy - 82 + i * 22, cx + 26, cy - 82 + i * 22) for i in range(6))
        + "  </g>\n"
        + '  <path d="M %d %d q 0 74 -74 74" fill="none" stroke="%s" stroke-opacity="0.6" stroke-width="2"/>\n' % (cx - 44, cy + 34, GOLD)
        + '  <path d="M %d %d q 0 74 74 74" fill="none" stroke="%s" stroke-opacity="0.6" stroke-width="2"/>\n' % (cx + 44, cy + 34, GOLD)
        + '  <rect x="%d" y="%d" width="8" height="86" rx="4" fill="url(#gold)"/>\n' % (cx - 4, cy + 44)
        + '  <rect x="%d" y="%d" width="96" height="8" rx="4" fill="url(#gold)"/>\n' % (cx - 48, cy + 126)
        + TAIL  # بدون کادر برای تنوع بصری
    )


# ---------------------------------------------------------------- پرتره (جای‌نگهدار عکس)
def portrait():
    w = h = 600
    return (
        HEAD.format(w=w, h=h, label="جای‌نگهدار تصویر پرتره — ابوالفضل میرعمو", amber=AMBER, gold=GOLD, gl=GOLD_LIGHT, g=GOLD, gd=GOLD_DEEP)
        + '  <rect width="600" height="600" fill="url(#bg)"/>\n'
        + grid(600, 600, 60, "0.045")
        + '  <circle cx="300" cy="292" r="232" fill="none" stroke="%s" stroke-opacity="0.20"/>\n' % GOLD
        + '  <circle cx="300" cy="292" r="196" fill="none" stroke="%s" stroke-opacity="0.30"/>\n' % GOLD
        + '  <ellipse cx="300" cy="300" rx="200" ry="200" fill="url(#glow)"/>\n'
        # شانه‌ها + سر (سیلوئت انتزاعی)
        + '  <path d="M 118 560 q 20 -190 182 -190 q 162 0 182 190 z" fill="#171310" stroke="%s" stroke-opacity="0.45" stroke-width="1.6"/>\n' % GOLD
        + '  <circle cx="300" cy="252" r="104" fill="#1A1613" stroke="%s" stroke-opacity="0.55" stroke-width="1.6"/>\n' % GOLD
        + '  <path d="M 196 252 q 0 -104 104 -104 q 104 0 104 104" fill="none" stroke="url(#gold)" stroke-opacity="0.55" stroke-width="2"/>\n'
        # رینگ نور طلایی
        + '  <path d="M 300 88 a 164 164 0 0 1 116 48" fill="none" stroke="url(#gold)" stroke-width="3" stroke-linecap="round"/>\n'
        # نُت‌های شناور
        + '  <g opacity="0.9" transform="translate(96 150) scale(1.5)"><ellipse cx="0" cy="48" rx="13" ry="9.5" fill="url(#gold)" transform="rotate(-20)"/><rect x="10" y="0" width="4" height="50" fill="url(#gold)"/><path d="M 14 0 q 24 8 22 30" fill="none" stroke="url(#gold)" stroke-width="4"/></g>\n'
        + '  <g opacity="0.75" transform="translate(486 466) scale(1.15)"><ellipse cx="0" cy="48" rx="13" ry="9.5" fill="%s" transform="rotate(-20)"/><rect x="10" y="0" width="4" height="50" fill="%s"/></g>\n' % (GOLD, GOLD)
        + '  <line x1="60" y1="300" x2="118" y2="300" stroke="url(#line)" stroke-width="2"/>\n'
        + '  <line x1="482" y1="300" x2="540" y2="300" stroke="url(#line)" stroke-width="2"/>\n'
        + TAIL
    )


# ---------------------------------------------------------------- آواتارها
def avatar(motif, seed):
    w = h = 200
    accents = {
        "note": '<g transform="translate(64 62) scale(1.05)"><ellipse cx="0" cy="62" rx="15" ry="11" fill="url(#gold)" transform="rotate(-20)"/><rect x="11" y="4" width="4.5" height="60" fill="url(#gold)"/><path d="M 15.5 4 q 26 9 24 33" fill="none" stroke="url(#gold)" stroke-width="4.5"/></g>',
        "wave": '<g stroke="url(#gold)" stroke-width="7" stroke-linecap="round">'
        + "".join('<line x1="%d" y1="%d" x2="%d" y2="%d"/>' % (62 + i * 14, 100 - hh / 2, 62 + i * 14, 100 + hh / 2) for i, hh in enumerate([24, 48, 74, 40, 88, 56, 30]))
        + "</g>",
        "star": '<path d="m100 52 13.6 27.6 30.4 4.4-22 21.4 5.2 30.3L100 122l-27.2 14.3 5.2-30.3-22-21.4 30.4-4.4z" fill="none" stroke="url(#gold)" stroke-width="6" stroke-linejoin="round"/>',
        "mic": '<g stroke="url(#gold)" stroke-width="6" stroke-linecap="round" fill="none"><rect x="86" y="46" width="28" height="58" rx="14" fill="url(#gold)"/><path d="M 70 96 a 30 30 0 0 0 60 0"/><line x1="100" y1="126" x2="100" y2="146"/><line x1="84" y1="146" x2="116" y2="146"/></g>',
        "sparkle": '<g stroke="url(#gold)" stroke-width="6" stroke-linecap="round"><path d="M 100 48 v 26 M 100 126 v 26 M 62 100 h 26 M 112 100 h 26"/><path d="M 78 78 l 14 14 M 122 122 l -14 -14 M 122 78 l -14 14 M 78 122 l 14 -14"/></g>',
    }
    return (
        HEAD.format(w=w, h=h, label="آواتار هنرجو", amber=AMBER, gold=GOLD, gl=GOLD_LIGHT, g=GOLD, gd=GOLD_DEEP)
        + '  <rect width="200" height="200" fill="url(#bg)"/>\n'
        + '  <circle cx="100" cy="100" r="96" fill="url(#glow)"/>\n'
        + '  <circle cx="100" cy="100" r="88" fill="#0D0C0B" stroke="%s" stroke-opacity="0.45"/>\n' % GOLD
        + '  <circle cx="100" cy="100" r="62" fill="none" stroke="%s" stroke-opacity="0.18"/>\n' % GOLD
        + '  <path d="M 100 14 a 86 86 0 0 1 60 24" fill="none" stroke="url(#gold)" stroke-width="3" stroke-linecap="round"/>\n'
        + "  " + accents[motif] + "\n"
        + TAIL
    )


def favicon():
    return (
        HEAD.format(w=64, h=64, label="نشانه سایت", amber=AMBER, gold=GOLD, gl=GOLD_LIGHT, g=GOLD, gd=GOLD_DEEP)
        + '  <rect width="64" height="64" rx="14" fill="#0A0A0A"/>\n'
        + '  <rect x="1.5" y="1.5" width="61" height="61" rx="13" fill="none" stroke="%s" stroke-opacity="0.45"/>\n' % GOLD
        + '  <g transform="translate(20 12) scale(0.62)"><ellipse cx="0" cy="62" rx="16" ry="11.5" fill="url(#gold)" transform="rotate(-20)"/><rect x="11" y="0" width="5" height="62" fill="url(#gold)"/><path d="M 16 0 q 28 10 25 36" fill="none" stroke="url(#gold)" stroke-width="5"/></g>\n'
        + TAIL
    )


FILES = {
    "cover-waveform.svg": cover_waveform,
    "cover-vinyl.svg": cover_vinyl,
    "cover-stage.svg": cover_stage,
    "cover-event.svg": cover_event,
    "cover-teaching.svg": cover_teaching,
    "cover-mic.svg": cover_mic,
    "portrait-placeholder.svg": portrait,
    "avatar-note.svg": lambda: avatar("note", 1),
    "avatar-wave.svg": lambda: avatar("wave", 2),
    "avatar-star.svg": lambda: avatar("star", 3),
    "avatar-mic.svg": lambda: avatar("mic", 4),
    "avatar-sparkle.svg": lambda: avatar("sparkle", 5),
    "favicon.svg": favicon,
}


def main():
    os.makedirs(OUT, exist_ok=True)
    from xml.dom.minidom import parseString

    for name, fn in FILES.items():
        svg = fn()
        parseString(svg)  # اعتبارسنجی XML
        with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
            f.write(svg)
        print("✓", name)


if __name__ == "__main__":
    main()
