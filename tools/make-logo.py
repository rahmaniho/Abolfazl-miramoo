#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ساخت دارایی‌های لوگو از تصویرِ موکاپ (پس‌زمینه‌دار)
=====================================================
این ابزار تصویری که از لوگوی «میرعمو» دارید را می‌گیرد — چه طلایی روی پس‌زمینه‌ی
مشکی، چه طلایی روی زرشکی، چه سرمه‌ای روی روشن — پس‌زمینه را حذف می‌کند
(کانال آلفا با ماتینگ واقعی، بدون هاله‌ی رنگی) و همه‌ی فایل‌های لازم سایت را می‌سازد.

اجرا (ساده‌ترین حالت: فایل منبع را در assets/img/ بگذارید):

    pip install --break-system-packages --user Pillow numpy
    python3 tools/make-logo.py

یا با مسیر دلخواه:

    python3 tools/make-logo.py --src /path/to/logo.jpg --out assets/img

خروجی‌ها:
    assets/img/logo-mark.png          ← نشانه‌ی شفاف طلایی (ناوبری، فوتر، واترمارک، وینیل)
    assets/img/logo-mark-light.png    ← نشانه‌ی شفاف تیره (برای پس‌زمینه‌ی طلایی/روشن)
    assets/img/logo-lockup.png        ← نشانه + خط لاتین، شفاف
    assets/img/favicon-32.png         ← فاوآیکون
    assets/img/favicon-180.png        ← آیکون اپل (apple-touch-icon)
    assets/img/icon-512.png           ← آیکون اندروید/PWA (پس‌زمینه‌دار)
    assets/img/favicon.ico            ← فاوآیکون چندسایزی مرورگرهای قدیمی
    assets/img/og-cover.jpg           ← کاور شبکه‌های اجتماعی با نشانه‌ی طلایی
    assets/img/logo-preview.png       ← برگه‌ی بازبینی روی چهار پس‌زمینه

نکته: اگر خودتان نسخه‌ی PNG با پس‌زمینه‌ی شفاف دارید، فقط آن را با نام
      assets/img/logo-mark.png و logo-mark-light.png در پوشه بگذارید؛
      کلاس‌های سایت خودشان آن را برداشته و نمایش می‌دهند و به این ابزار نیازی نیست.
"""

import argparse
import glob
import os
import re
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

# ---------------------------------------------------------------- پالت برند
BRAND_BLACK = (10, 10, 10)
GOLD_TOP = np.array([244, 226, 164], dtype=np.float32)   # #F4E2A4
GOLD_MID = np.array([212, 175, 55], dtype=np.float32)    # #D4AF37
GOLD_BOT = np.array([176, 138, 30], dtype=np.float32)    # #B08A1E
INK_TOP = np.array([58, 44, 10], dtype=np.float32)       # قهوه‌ای تیره برای پس‌زمینه‌ی طلایی
INK_BOT = np.array([20, 15, 4], dtype=np.float32)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DEFAULT_OUT = os.path.join(ROOT, "assets", "img")

CANDIDATE_GLOBS = [
    "logo-source.*", "logo.*", "miramoo-logo.*", "logo-final.*", "MirAmo.*",
]
SEARCH_DIRS = [
    DEFAULT_OUT,
    os.path.join(ROOT, "assets"),
    ROOT,
    "/home/user/uploads",
    os.path.join(os.path.expanduser("~"), "uploads"),
]
EXTS = (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff")


# ---------------------------------------------------------------- کمکی‌ها
def log(msg):
    print(msg, flush=True)


def find_source(explicit=None):
    """پیدا کردن خودکار تصویر لوگو."""
    if explicit:
        if not os.path.exists(explicit):
            sys.exit(f"✗ فایل پیدا نشد: {explicit}")
        return explicit

    hits = []
    for d in SEARCH_DIRS:
        if not os.path.isdir(d):
            continue
        for pattern in CANDIDATE_GLOBS:
            hits += sorted(glob.glob(os.path.join(d, pattern)))
        # فایل‌های ارسالی پلتفرم (uploads/file_*.png)
        if "uploads" in d:
            hits += sorted(glob.glob(os.path.join(d, "file_*")))
    hits = [h for h in hits if h.lower().endswith(EXTS)]
    # حذف دارایی‌های تولیدی خودمان
    hits = [h for h in hits if not re.search(r"(logo-mark|logo-lockup|favicon|icon-\d+|logo-preview|og-cover)", os.path.basename(h))]
    if not hits:
        return None
    # بزرگ‌ترین فایل، محتمل‌ترین منبع است
    hits.sort(key=lambda p: os.path.getsize(p), reverse=True)
    return hits[0]


def smoothstep(edge0, edge1, x):
    t = np.clip((x - edge0) / max(1e-6, (edge1 - edge0)), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def border_color(rgb):
    """رنگ پس‌زمینه از حاشیه‌ی تصویر (میانه‌ی نواری)."""
    h, w, _ = rgb.shape
    band = max(2, int(min(h, w) * 0.02))
    strips = np.concatenate([
        rgb[:band].reshape(-1, 3),
        rgb[-band:].reshape(-1, 3),
        rgb[:, :band].reshape(-1, 3),
        rgb[:, -band:].reshape(-1, 3),
    ])
    return np.median(strips, axis=0)


def luminance(rgb):
    return rgb[..., 0] * 0.299 + rgb[..., 1] * 0.587 + rgb[..., 2] * 0.114


def unpremultiply(rgb, alpha, bg):
    """
    بازیابی رنگ واقعیِ پیش‌زمینه از تصویرِ آمیخته با پس‌زمینه:
        مشاهده = α·F + (۱−α)·B   ⇒   F = (مشاهده − (۱−α)·B) / α
    بدون این کار، لبه‌ها هاله‌ی رنگ پس‌زمینه (مشکی/زرشکی) می‌گیرند.
    """
    a = np.clip(alpha, 0.0, 1.0)[..., None]
    safe = np.maximum(a, 0.06)
    f = (rgb.astype(np.float32) - (1.0 - a) * bg.astype(np.float32)) / safe
    return np.clip(f, 0, 255)


def alpha_to_image(alpha, rgb=None, size=None):
    a = np.clip(alpha * 255.0, 0, 255).astype(np.uint8)
    if rgb is None:
        rgb = np.zeros((*a.shape, 3), dtype=np.float32)
    out = Image.fromarray(rgb.astype(np.uint8), "RGB").convert("RGBA")
    out.putalpha(Image.fromarray(a, "L").resize(out.size, Image.Resampling.LANCZOS) if size else Image.fromarray(a, "L"))
    return out


def trim(img, pad_ratio=0.06, square=False):
    """برش ناحیه‌ی شفاف‌نشده + حاشیه‌ی دلخواه."""
    alpha = np.array(img.getchannel("A"))
    ys, xs = np.where(alpha > 8)
    if len(xs) == 0:
        return img
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    pad = int(max(x1 - x0, y1 - y0) * pad_ratio)
    x0, y0 = max(0, x0 - pad), max(0, y0 - pad)
    x1, y1 = min(img.width, x1 + pad), min(img.height, y1 + pad)
    cropped = img.crop((x0, y0, x1, y1))
    if square:
        side = max(cropped.width, cropped.height)
        canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
        canvas.paste(cropped, ((side - cropped.width) // 2, (side - cropped.height) // 2), cropped)
        cropped = canvas
    return cropped


def resize_max(img, max_side):
    if max(img.width, img.height) <= max_side:
        return img
    scale = max_side / float(max(img.width, img.height))
    return img.resize((max(1, int(img.width * scale)), max(1, int(img.height * scale))), Image.Resampling.LANCZOS)


def gold_fill(alpha, seed=0):
    """رنگ‌آمیزی طلایی متالیک بر اساس کانال آلفا."""
    h, w = alpha.shape
    t = np.linspace(0, 1, h, dtype=np.float32)[:, None]
    grad = (1 - t) * GOLD_TOP + t * GOLD_MID
    # درخشش ملایم افقی برای حس فلزی
    x = np.linspace(-1, 1, w, dtype=np.float32)[None, :]
    sheen = 1.0 + 0.10 * np.sin((x + seed) * np.pi) * (1 - t)
    grad = np.clip(grad[..., None, :] * 1.0, 0, 255)
    wide = np.repeat(grad, w, axis=1) if grad.shape[1] == 3 else grad
    wide = wide * np.clip(sheen, 0.85, 1.15)[..., None]
    # تیره‌شدن ملایم در پایین برای عمق
    wide = wide * (1.0 - 0.12 * (t ** 2))[..., None]
    return np.clip(wide, 0, 255)


def ink_fill(alpha):
    h, w = alpha.shape
    t = np.linspace(0, 1, h, dtype=np.float32)[:, None, None]
    base = (1 - t) * INK_TOP.reshape(1, 1, 3) + t * INK_BOT.reshape(1, 1, 3)
    return np.repeat(base, w, axis=1)


# ---------------------------------------------------------------- استخراج نشانه
def extract(path, mode_hint="auto"):
    """
    خواندن تصویر موکاپ و برگرداندن (mark_rgba, lockup_rgba, kind)
    kind: 'dark' یا 'light' — نوع پس‌زمینه‌ی منبع
    """
    img = Image.open(path).convert("RGB")
    scale_down = 1600 / max(img.size)
    if scale_down < 1:
        img = img.resize((int(img.width * scale_down), int(img.height * scale_down)), Image.Resampling.LANCZOS)
    rgb = np.asarray(img).astype(np.float32)
    bg = border_color(rgb)
    bg_lum = float(luminance(bg.reshape(1, 1, 3))[0, 0])
    kind = mode_hint
    if kind == "auto":
        kind = "light" if bg_lum > 140 else "dark"
    lum = luminance(rgb)

    if kind == "dark":
        # طلایی روی مشکی/زرشکی:  α از روشنایی
        hi = float(np.percentile(lum, 99.5))
        lo = bg_lum + (hi - bg_lum) * 0.16
        hii = bg_lum + (hi - bg_lum) * 0.45
        alpha = smoothstep(lo, hii, lum)
        fg = unpremultiply(rgb, alpha, bg)
        # اشباع ملایم برای بازگرداندن درخشش طلا
        fg = np.clip(fg * 1.03, 0, 255)
    else:
        # سرمه‌ای روی روشن:  α از تیرگی، سپس رنگ‌آمیزی طلایی
        lo = float(np.percentile(lum, 0.5))
        dark = bg_lum - lum
        alpha = smoothstep((bg_lum - lo) * 0.16, (bg_lum - lo) * 0.48, dark)
        fg = gold_fill(alpha)

    # پاک‌سازی نویز JPEG در نواحی خالی
    alpha = np.where(alpha < 0.06, 0.0, alpha)
    mark_rgba = Image.merge("RGBA", (*Image.fromarray(np.clip(fg, 0, 255).astype(np.uint8), "RGB").split(),
                                     Image.fromarray((np.clip(alpha, 0, 1) * 255).astype(np.uint8), "L")))

    # جدا کردن خط لاتین از نشانه (تحلیل نمایه‌ی سطری)
    mask = np.array(mark_rgba.getchannel("A")) > 12
    rows = mask.sum(axis=1)
    thresh = max(2, int(mask.shape[1] * 0.005))
    active = rows > thresh
    segments, start = [], None
    for i, on in enumerate(active):
        if on and start is None:
            start = i
        elif not on and start is not None:
            segments.append((start, i))
            start = None
    if start is not None:
        segments.append((start, len(active)))
    segments = [s for s in segments if s[1] - s[0] > mask.shape[0] * 0.012]

    mark = mark_rgba
    lockup = mark_rgba
    if len(segments) >= 2:
        # بزرگ‌ترین فاصله = مرز بین نشانه و متن لاتین
        gaps = [(segments[i + 1][0] - segments[i][1], i) for i in range(len(segments) - 1)]
        gap, idx = max(gaps)
        if gap > mask.shape[0] * 0.03:
            cut = (segments[idx][1] + segments[idx + 1][0]) // 2
            mark = mark_rgba.crop((0, 0, mark_rgba.width, cut))
            lockup = mark_rgba
    return mark, lockup, kind


# ---------------------------------------------------------------- خروجی‌ها
def on_background(img, size, bg=BRAND_BLACK, pad_ratio=0.16, radius=None):
    canvas = Image.new("RGBA", (size, size), (*bg, 255))
    inner = int(size * (1 - 2 * pad_ratio))
    art = img.copy()
    if max(art.size) > inner:
        art = art.resize((int(art.width * inner / max(art.size)), int(art.height * inner / max(art.size))),
                         Image.Resampling.LANCZOS)
    canvas.alpha_composite(art, ((size - art.width) // 2, (size - art.height) // 2))
    if radius:
        mask = Image.new("L", (size, size), 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=255)
        canvas.putalpha(mask)
    return canvas


def build_preview(mark, lockup, out_path):
    """برگه‌ی بازبینی: لوگو روی چهار پس‌زمینه‌ی مختلف."""
    tile = 340
    bgs = [("مشکی سایت #0A0A0A", (10, 10, 10)), ("زرشکی", (90, 20, 24)),
           ("طلایی #D4AF37", (212, 175, 55)), ("کرم #F5F1E8", (245, 241, 232))]
    sheet = Image.new("RGB", (tile * 2, tile * 2), (0, 0, 0))
    for i, (_, bg) in enumerate(bgs):
        art = mark if i != 2 else mark_light_for_preview(mark)
        cell = on_background(art, tile, bg=bg, pad_ratio=0.18)
        sheet.paste(cell.convert("RGB"), ((i % 2) * tile, (i // 2) * tile))
    sheet.save(out_path)
    return out_path


def mark_light_for_preview(mark):
    """نسخه‌ی تیره برای پیش‌نمایش روی طلایی."""
    a = np.array(mark.getchannel("A")).astype(np.float32) / 255.0
    fg = ink_fill(a)
    return Image.merge("RGBA", (*Image.fromarray(fg.astype(np.uint8), "RGB").split(),
                                Image.fromarray((a * 255).astype(np.uint8), "L")))


def brand_og(mark, out_path, plain_path=None):
    """کاور شبکه‌های اجتماعی: نشانه‌ی طلایی روی کاور انتزاعی."""
    src = plain_path if plain_path and os.path.exists(plain_path) else out_path
    if not os.path.exists(src):
        return None
    base = Image.open(src).convert("RGB")
    w, h = base.size
    target = int(h * 0.62)
    art = mark.copy()
    art = art.resize((int(art.width * target / max(art.size)), int(art.height * target / max(art.size))),
                     Image.Resampling.LANCZOS)
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    layer.alpha_composite(art, ((w - art.width) // 2, (h - art.height) // 2))
    # هاله‌ی ملایم پشت نشانه برای جدا شدن از پس‌زمینه
    halo = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(halo).ellipse(
        [(w - art.width) // 2 - int(w * 0.06), (h - art.height) // 2 - int(h * 0.05),
         (w + art.width) // 2 + int(w * 0.06), (h + art.height) // 2 + int(h * 0.05)],
        fill=(0, 0, 0, 130))
    halo = halo.filter(ImageFilter.GaussianBlur(int(w * 0.035)))
    base = Image.alpha_composite(base.convert("RGBA"), halo)
    base = Image.alpha_composite(base, layer)
    base.convert("RGB").save(out_path, quality=88, optimize=True)
    return out_path


def main():
    ap = argparse.ArgumentParser(description="ساخت دارایی‌های لوگو از تصویر موکاپ")
    ap.add_argument("--src", help="مسیر تصویر منبع (پیش‌فرض: جست‌وجوی خودکار در assets/img و uploads)")
    ap.add_argument("--out", default=DEFAULT_OUT, help="پوشه‌ی خروجی")
    ap.add_argument("--mode", choices=["auto", "dark", "light"], default="auto",
                    help="نوع پس‌زمینه‌ی منبع: dark=طلایی روی تیره، light=سرمه‌ای روی روشن")
    ap.add_argument("--keep-latin", action="store_true", default=True,
                    help="ساخت لوگوتایپ کامل (نشانه + خط لاتین)")
    args = ap.parse_args()

    src = find_source(args.src)
    if not src:
        log("✗ تصویر لوگو پیدا نشد.")
        log("  یکی از این کارها را انجام دهید:")
        log("   ۱) فایل لوگو را با نام assets/img/logo-source.png بگذارید، یا")
        log("   ۲) مسیر فایل را بدهید:  python3 tools/make-logo.py --src /path/logo.jpg")
        sys.exit(2)

    os.makedirs(args.out, exist_ok=True)
    log(f"• منبع: {src}")
    mark, lockup, kind = extract(src, args.mode)
    log(f"• پس‌زمینه‌ی تشخیص‌داده‌شده: {'تیره (طلایی)' if kind == 'dark' else 'روشن (سرمه‌ای → طلایی)'}")

    mark_sq = trim(mark, pad_ratio=0.07, square=True)
    lockup_trim = trim(lockup, pad_ratio=0.05, square=False)

    outputs = {}

    # نشانه‌ی طلایی شفاف
    mark_out = resize_max(mark_sq, 512)
    p = os.path.join(args.out, "logo-mark.png")
    mark_out.save(p, optimize=True)
    outputs["logo-mark.png"] = p

    # نشانه‌ی تیره شفاف (برای پس‌زمینه‌ی طلایی/روشن)
    light = mark_light_for_preview(mark_sq)
    light = resize_max(light, 512)
    p = os.path.join(args.out, "logo-mark-light.png")
    light.save(p, optimize=True)
    outputs["logo-mark-light.png"] = p

    # لوگوتایپ کامل
    if args.keep_latin:
        lk = resize_max(lockup_trim, 1024)
        p = os.path.join(args.out, "logo-lockup.png")
        lk.save(p, optimize=True)
        outputs["logo-lockup.png"] = p
        # نسخه‌ی تیره‌ی لوگوتایپ برای پس‌زمینه‌های روشن/طلایی
        la = lk.getchannel("A")
        lf = ink_fill(np.array(la).astype(np.float32) / 255.0)
        lk_light = Image.merge("RGBA", (*Image.fromarray(lf.astype(np.uint8), "RGB").split(), la))
        p2 = os.path.join(args.out, "logo-lockup-light.png")
        lk_light.save(p2, optimize=True)
        outputs["logo-lockup-light.png"] = p2

    # فاوآیکون‌ها و آیکون‌ها
    for name, size, bg in [("favicon-32.png", 32, None), ("favicon-180.png", 180, BRAND_BLACK),
                           ("icon-512.png", 512, BRAND_BLACK)]:
        if bg is None:
            art = resize_max(mark_sq, 64)
            canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
            art2 = art.resize((int(art.width * size * 0.94 / max(art.size)),
                               int(art.height * size * 0.94 / max(art.size))), Image.Resampling.LANCZOS)
            canvas.alpha_composite(art2, ((size - art2.width) // 2, (size - art2.height) // 2))
            icon = canvas
        else:
            icon = on_background(mark_sq, size, bg=bg, pad_ratio=0.18, radius=int(size * 0.22))
        p = os.path.join(args.out, name)
        icon.save(p, optimize=True)
        outputs[name] = p

    # favicon.ico چندسایزی
    ico_sizes = [(16, 16), (32, 32), (48, 48)]
    ico = on_background(mark_sq, 48, bg=BRAND_BLACK, pad_ratio=0.12)
    p = os.path.join(args.out, "favicon.ico")
    ico.save(p, sizes=ico_sizes)
    outputs["favicon.ico"] = p

    # کاور شبکه‌های اجتماعی
    plain = os.path.join(args.out, "og-cover-abstract.jpg")
    cur_og = os.path.join(args.out, "og-cover.jpg")
    if os.path.exists(cur_og) and not os.path.exists(plain):
        Image.open(cur_og).convert("RGB").save(plain, quality=90, optimize=True)
    p = brand_og(mark_sq, cur_og, plain_path=plain)
    if p:
        outputs["og-cover.jpg"] = p

    # برگه‌ی بازبینی
    p = build_preview(mark_sq, lockup_trim, os.path.join(args.out, "logo-preview.png"))
    outputs["logo-preview.png"] = p

    log("\n✓ ساخته شد:")
    for name, path in outputs.items():
        size = os.path.getsize(path) / 1024.0
        log(f"   • {name:<22} {size:6.1f} کیلوبایت")
    log("\nبرای بازبینی کیفیت، فایل logo-preview.png را ببینید.")
    log("اگر نسخه‌ی PNG شفافِ اختصاصی دارید، همین نام‌ها را جایگزین کنید و این ابزار را لازم نیست اجرا کنید.")


if __name__ == "__main__":
    main()
