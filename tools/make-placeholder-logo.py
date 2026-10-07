#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
جانشین موقت نشانه و لوگوتایپ (Placeholder wordmark)
=====================================================
تا زمانی که فایل نهایی لوگوی خطاطی‌تان را در پوشه بگذارید، این ابزار یک نشانه‌ی
تمیز و هم‌خانواده با برند می‌سازد: مونوگرام «م» با دو لوزیِ مشخصه‌ی لوگوی شما،
و لوگوتایپ «میرعمو» با خط لاتین زیر آن — همه با گرادیان طلایی و پس‌زمینه‌ی شفاف.

⚠️ این دارایی‌ها *موقت* هستند. برای جایگزینی با لوگوی واقعی:

    python3 tools/make-logo.py --src /path/to/your-calligraphy-logo.png

که نشانه، لوگوتایپ، فاوآیکون‌ها و کاور شبکه‌های اجتماعی را از تصویر شما می‌سازد
و همین نام‌ها را بازنویسی می‌کند (هیچ تغییری در HTML لازم نیست).

پیش‌نیازها (یک‌بار):
    pip install --break-system-packages --user Pillow numpy fonttools brotli arabic-reshaper python-bidi

اجرا:
    python3 tools/make-placeholder-logo.py
"""

import os
import sys
import importlib.util

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "assets", "img")
CACHE = os.path.join(HERE, ".cache")

# ابزار اصلی (توابع مشترک: trim، on_background، brand_og، build_preview)
spec = importlib.util.spec_from_file_location("make_logo", os.path.join(HERE, "make-logo.py"))
ml = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ml)

GOLD_STOPS = [(0.00, (252, 235, 178)), (0.42, (214, 178, 62)), (1.00, (168, 130, 26))]
INK_STOPS = [(0.00, (44, 34, 9)), (1.00, (15, 11, 3))]


# ---------------------------------------------------------------- فونت
def woff2_to_ttf():
    """تبدیل فونت متغیر وزیرمتن از woff2 به ttf (برای رندر متن روی تصویر)."""
    os.makedirs(CACHE, exist_ok=True)
    target = os.path.join(CACHE, "Vazirmatn-Variable.ttf")
    if os.path.exists(target):
        return target
    try:
        from fontTools.ttLib import TTFont
    except ImportError:
        return None
    src = os.path.join(ROOT, "assets", "fonts", "vazirmatn-arabic-wght-normal.woff2")
    if not os.path.exists(src):
        return None
    try:
        font = TTFont(src)
        font.flavor = None
        font.save(target)
    except Exception as exc:  # noqa: BLE001
        print("  ⚠ تبدیل فونت ناموفق بود:", exc)
        return None
    return target


def load_font(path, size, weight=800):
    font = ImageFont.truetype(path, size)
    if weight and hasattr(font, "set_variation_by_axes"):
        try:
            font.set_variation_by_axes([weight])
        except Exception:  # noqa: BLE001
            pass
    return font


def shape_fa(text):
    """آماده‌سازی متن فارسی برای رندر: شکل‌دهی حروف + ترتیب راست‌به‌چپ."""
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display

        return get_display(arabic_reshaper.reshape(text))
    except ImportError:
        return text


def gradient(size, stops=GOLD_STOPS, sheen=0.07):
    """تصویر گرادیان عمودی طلایی با درخشش افقی ملایم."""
    w, h = size
    ys = np.linspace(0, 1, h, dtype=np.float32)
    stops = sorted(stops)
    out = np.zeros((h, 3), dtype=np.float32)
    for i in range(len(stops) - 1):
        p0, c0 = stops[i]
        p1, c1 = stops[i + 1]
        sel = (ys >= p0) & (ys <= p1)
        t = ((ys[sel] - p0) / max(1e-6, p1 - p0))[:, None]
        out[sel] = (1 - t) * np.array(c0, dtype=np.float32) + t * np.array(c1, dtype=np.float32)
    rgb = np.repeat(out[:, None, :], w, axis=1)
    if sheen:
        x = np.linspace(-1, 1, w, dtype=np.float32)[None, :, None]
        rgb = rgb * (1.0 + sheen * np.cos(x * 2.0))
    return Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), "RGB")


def fill_mask(mask, stops=GOLD_STOPS, deepen=True):
    """رنگ‌آمیزی یک ماسک با گرادیان + سایه‌ی داخلی برای حس فلزی/برجسته."""
    w, h = mask.size
    rgb = np.asarray(gradient((w, h), stops)).astype(np.float32)
    a = np.asarray(mask).astype(np.float32) / 255.0
    if deepen:
        blur = np.asarray(mask.filter(ImageFilter.GaussianBlur(max(1, w * 0.006)))).astype(np.float32) / 255.0
        inner = np.clip(blur - a, 0, 1) * a
        rgb = rgb * (1.0 - 0.5 * inner[..., None])
    return Image.merge("RGBA", (*Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), "RGB").split(),
                                mask))


def diamond(draw, cx, cy, r, fill=255):
    """لوزیِ مشخصه‌ی لوگو."""
    pts = [(cx, cy - r * 1.42), (cx + r * 1.42, cy), (cx, cy + r * 1.42), (cx - r * 1.42, cy)]
    draw.polygon(pts, fill=fill)


# ---------------------------------------------------------------- ساخت نشانه
def build_mark(font_path, stops=GOLD_STOPS, size=2048, mono="م", with_diamonds=True):
    """مونوگرام مربعی: حرف «م» + دو لوزی بالا."""
    mask = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(mask)
    big = load_font(font_path, int(size * 0.98), weight=800)
    text = shape_fa(mono) if len(mono) > 1 else mono
    box = d.textbbox((0, 0), text, font=big)
    # مقیاس تا حرف حدود ۶۲٪ بوم را پر کند (نسبت به عرض)، سپس مرکزچینی بینایی
    scale = (size * 0.62) / max(1, box[2] - box[0])
    fs = max(12, int(size * 0.98 * scale))
    big = load_font(font_path, fs, weight=800)
    box = d.textbbox((0, 0), text, font=big)
    x = (size - (box[2] - box[0])) / 2 - box[0]
    y = (size - (box[3] - box[1])) / 2 - box[1] + size * 0.05
    d.text((x, y), text, font=big, fill=255)
    if with_diamonds:
        dr = size * 0.028
        diamond(d, size * 0.295, size * 0.215, dr)
        diamond(d, size * 0.395, size * 0.185, dr * 0.78)
    mask = mask.filter(ImageFilter.GaussianBlur(size * 0.0012))
    mark = fill_mask(mask, stops)
    return mark


def build_lockup(font_path, stops=GOLD_STOPS, size=2048, latin=True):
    """لوگوتایپ: «میرعمو» + دو لوزی + خط لاتین زیر آن."""
    mask = Image.new("L", (size, int(size * 0.72)), 0)
    d = ImageDraw.Draw(mask)
    W, H = mask.size

    # متن فارسی
    big = load_font(font_path, int(H * 0.46), weight=800)
    fa = shape_fa("میرعمو")
    box = d.textbbox((0, 0), fa, font=big)
    scale = (W * 0.86) / max(1, box[2] - box[0])
    big = load_font(font_path, int(H * 0.46 * scale), weight=800)
    box = d.textbbox((0, 0), fa, font=big)
    tx = (W - (box[2] - box[0])) / 2 - box[0]
    ty = H * 0.30 - box[1]
    d.text((tx, ty), fa, font=big, fill=255)

    # دو لوزی بالای متن (مشخصه‌ی لوگو)
    dr = H * 0.035
    diamond(d, W * 0.395, H * 0.135, dr)
    diamond(d, W * 0.472, H * 0.115, dr * 0.78)

    # خط لاتین
    if latin:
        for cand, label in [("/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf", "Abolfazl Mir'amo"),
                            ("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf", "Abolfazl Mir'amo")]:
            if not os.path.exists(cand):
                continue
            lf = ImageFont.truetype(cand, int(H * 0.115))
            lbox = d.textbbox((0, 0), label, font=lf)
            lx = (W - (lbox[2] - lbox[0])) / 2 - lbox[0]
            ly = H * 0.66 - lbox[1]
            d.text((lx, ly), label, font=lf, fill=int(255 * 0.92))
            break

    mask = mask.filter(ImageFilter.GaussianBlur(size * 0.0011))
    lockup = fill_mask(mask, stops)
    return lockup


# ---------------------------------------------------------------- اصلی
def main():
    os.makedirs(OUT, exist_ok=True)
    print("• ساخت دارایی‌های موقت لوگو…")

    font_path = woff2_to_ttf()
    if not font_path:
        sys.exit("✗ فونت وزیرمتن برای رندر متن در دسترس نیست. "
                 "fonttools و brotli را نصب کنید: pip install --user fonttools brotli")
    print(f"  فونت: {font_path}")

    mark = build_mark(font_path, GOLD_STOPS)
    mark_light = build_mark(font_path, INK_STOPS)
    lockup = build_lockup(font_path, GOLD_STOPS)
    lockup_light = build_lockup(font_path, INK_STOPS)

    mark = ml.trim(mark, pad_ratio=0.08, square=True)
    mark_light = ml.trim(mark_light, pad_ratio=0.08, square=True)
    lockup = ml.trim(lockup, pad_ratio=0.04)
    lockup_light = ml.trim(lockup_light, pad_ratio=0.04)

    outs = {}
    for name, image, cap in [
        ("logo-mark.png", mark, 512),
        ("logo-mark-light.png", mark_light, 512),
        ("logo-lockup.png", lockup, 1024),
        ("logo-lockup-light.png", lockup_light, 1024),
    ]:
        p = os.path.join(OUT, name)
        ml.resize_max(image, cap).save(p, optimize=True)
        outs[name] = p

    # فاوآیکون و آیکون‌ها
    small = ml.resize_max(mark, 256)
    for name, size, bg, radius in [
        ("favicon-32.png", 32, None, None),
        ("favicon-180.png", 180, ml.BRAND_BLACK, int(180 * 0.22)),
        ("icon-512.png", 512, ml.BRAND_BLACK, int(512 * 0.22)),
    ]:
        if bg is None:
            canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
            art = small.resize((int(size * 0.92), int(size * 0.92)), Image.Resampling.LANCZOS)
            canvas.alpha_composite(art, ((size - art.width) // 2, (size - art.height) // 2))
            icon = canvas
        else:
            icon = ml.on_background(small, size, bg=bg, pad_ratio=0.18, radius=radius)
        p = os.path.join(OUT, name)
        icon.save(p, optimize=True)
        outs[name] = p

    ico = ml.on_background(small, 48, bg=ml.BRAND_BLACK, pad_ratio=0.12)
    p = os.path.join(OUT, "favicon.ico")
    ico.save(p, sizes=[(16, 16), (32, 32), (48, 48)])
    outs["favicon.ico"] = p

    # کاور شبکه‌های اجتماعی: لوگوتایپ روی هنر انتزاعی (تیره‌شده تا متن خوانا بماند)
    plain = os.path.join(OUT, "og-cover-abstract.jpg")
    cur = os.path.join(OUT, "og-cover.jpg")
    if not os.path.exists(plain) and os.path.exists(cur):
        Image.open(cur).convert("RGB").save(plain, quality=92, optimize=True)
    if os.path.exists(plain):
        base = Image.open(plain).convert("RGBA")
        base = Image.alpha_composite(base, Image.new("RGBA", base.size, (6, 6, 6, 132)))
        w, h = base.size
        art = lockup.copy()
        target = int(h * 0.62)
        art = art.resize((int(art.width * target / max(art.size)), int(art.height * target / max(art.size))),
                         Image.Resampling.LANCZOS)
        base.alpha_composite(art, ((w - art.width) // 2, int((h - art.height) / 2)))
        base.convert("RGB").save(cur, quality=88, optimize=True)
        outs["og-cover.jpg"] = cur

    p = ml.build_preview(ml.resize_max(mark, 512), ml.resize_max(lockup, 1024),
                         os.path.join(OUT, "logo-preview.png"))
    outs["logo-preview.png"] = p

    print("\n✓ ساخته شد:")
    for name, path in outs.items():
        print(f"   • {name:<24} {os.path.getsize(path)/1024.0:6.1f} کیلوبایت")
    print("\n⚠️  این نشانه موقت است. برای لوگوی واقعی:")
    print("    python3 tools/make-logo.py --src /path/to/your-logo.png")


if __name__ == "__main__":
    sys.exit(main())
