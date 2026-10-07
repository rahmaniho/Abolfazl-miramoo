#!/usr/bin/env node
/**
 * سازنده‌ی اسپرایت آیکون‌ها (icons sprite)
 * ----------------------------------------
 * آیکون‌ها از سه بسته‌ی متن‌باز و معتبر خوانده می‌شوند و به یک اسپرایت
 * SVG درون‌خطی (inline) تبدیل می‌شوند تا صفحه هیچ وابستگی به CDN نداشته باشد:
 *
 *   • lucide-static  (ISC)        → آیکون‌های خطی رابط کاربری
 *   • @mdi/svg       (Apache-2.0) → نت، کلید سل، پیانو، مترونوم
 *   • simple-icons   (CC0-1.0)    → لوگوهای اینستاگرام، یوتیوب، اسپاتیفای، تلگرام، واتساپ
 *
 * اجرا:
 *   npm i -D lucide-static @mdi/svg simple-icons
 *   node tools/make-icons.mjs            # می‌نویسد: assets/icons/sprite.svg
 *   node tools/make-icons.mjs --inject   # همان + تزریق داخل index.html
 */

import { readFileSync, writeFileSync, mkdirSync, existsSync } from "node:fs";
import { resolve, dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const PACKS = process.env.ICON_PACKS_DIR || join(ROOT, "node_modules");

/* ------------------------------------------------ آیکون‌های درخواستی */
// آیکون‌های خطی Lucide:  نام فایل → شناسه در اسپرایت
const LUCIDE = {
  menu: "i-menu",
  x: "i-close",
  phone: "i-phone",
  "phone-call": "i-phone-call",
  mic: "i-mic",
  "mic-vocal": "i-mic-vocal",
  "graduation-cap": "i-cap",
  music: "i-music",
  "music-2": "i-music-2",
  "music-4": "i-music-4",
  "audio-waveform": "i-waveform",
  headphones: "i-headphones",
  feather: "i-feather",
  megaphone: "i-megaphone",
  "calendar-check": "i-calendar",
  "map-pin": "i-map-pin",
  star: "i-star",
  check: "i-check",
  "arrow-down": "i-arrow-down",
  "arrow-up": "i-arrow-up",
  "chevron-left": "i-chevron-left",
  "chevron-right": "i-chevron-right",
  sparkles: "i-sparkles",
  "disc-3": "i-disc",
  piano: "i-piano",
  clock: "i-clock",
  "message-circle": "i-message",
  users: "i-users",
  "badge-check": "i-badge-check",
  radio: "i-radio",
  quote: "i-quote",
  waves: "i-waves",
  "sliders-horizontal": "i-sliders",
  award: "i-award",
  guitar: "i-guitar",
  "external-link": "i-external",
  "circle-check-big": "i-check-circle",
  send: "i-send",
  user: "i-user",
  "shield-check": "i-shield",
  "trending-up": "i-trending",
  "play-square": "i-play-square",
};

// آیکون‌های پُر (filled) MDI
const MDI = {
  "music-clef-treble": "i-clef",
  "music-note-eighth": "i-note",
  "music-note-quarter": "i-note-quarter",
  "music-note-half": "i-note-half",
  piano: "i-piano-keys",
  metronome: "i-metronome",
  "waveform": "i-waveform-fill",
};

// لوگوهای برند
const BRAND = {
  instagram: "i-instagram",
  youtube: "i-youtube",
  spotify: "i-spotify",
  telegram: "i-telegram",
  whatsapp: "i-whatsapp",
};

/* ------------------------------------------------ خواندن بسته‌ها */
function readSvg(file) {
  if (!existsSync(file)) throw new Error("فایل آیکون پیدا نشد: " + file);
  return readFileSync(file, "utf8");
}

function inner(file) {
  const raw = readSvg(file);
  const vb = (raw.match(/viewBox="([^"]+)"/) || [, "0 0 24 24"])[1];
  const body = raw
    .replace(/^[\s\S]*?<svg[^>]*>/, "")
    .replace(/<\/svg>[\s\S]*$/, "")
    .replace(/<!--[\s\S]*?-->/g, "")
    .replace(/\s*\n\s*/g, " ")
    .replace(/\s{2,}/g, " ")
    .trim();
  return { vb, body };
}

const strokeWrap = (id, file) => {
  const { vb, body } = inner(file);
  return `<symbol id="${id}" viewBox="${vb}" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">${body}</symbol>`;
};

const fillWrap = (id, file) => {
  const { vb, body } = inner(file);
  const filled = body.replace(/<path /g, '<path fill="currentColor" ');
  return `<symbol id="${id}" viewBox="${vb}">${filled}</symbol>`;
};

/* ------------------------------------------------ آیکون‌های دست‌ساز */
const CUSTOM = {
  // دکمه‌ی پخش: مثلث نرم و گرد
  "i-play": `<symbol id="i-play" viewBox="0 0 24 24"><path d="M8 5.6a1 1 0 0 1 1.52-.85l10.1 6.4a1 1 0 0 1 0 1.7l-10.1 6.4A1 1 0 0 1 8 18.4z" fill="currentColor" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/></symbol>`,
  // کلید سل کوچک تزئینی (خطی) برای جداکننده‌ها
  "i-treble-line": `<symbol id="i-treble-line" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M13.6 21.2c-1.9 0-3.4-1.4-3.4-3.3 0-1.6 1.1-2.9 2.6-2.9 1.4 0 2.5 1 2.5 2.4 0 1.3-1 2.3-2.3 2.3"/><path d="M13.9 15V4.6c0-.9.7-1.6 1.6-1.6.8 0 1.5.6 1.5 1.4 0 1-.9 1.6-2.2 2.2-1.9.9-3.6 2.4-3.6 4.9 0 2.6 1.9 4.3 4.4 4.3"/></symbol>`,
};

/* ------------------------------------------------ ساخت اسپرایت */
function build() {
  const out = [];
  const missing = [];

  for (const [name, id] of Object.entries(LUCIDE)) {
    const f = join(PACKS, "lucide-static", "icons", `${name}.svg`);
    if (!existsSync(f)) {
      missing.push(`lucide:${name}`);
      continue;
    }
    out.push("    " + strokeWrap(id, f));
  }
  for (const [name, id] of Object.entries(MDI)) {
    const f = join(PACKS, "@mdi/svg", "svg", `${name}.svg`);
    if (!existsSync(f)) {
      missing.push(`mdi:${name}`);
      continue;
    }
    out.push("    " + fillWrap(id, f));
  }
  for (const [name, id] of Object.entries(BRAND)) {
    const f = join(PACKS, "simple-icons", "icons", `${name}.svg`);
    if (!existsSync(f)) {
      missing.push(`simple-icons:${name}`);
      continue;
    }
    out.push("    " + fillWrap(id, f));
  }
  for (const [id, markup] of Object.entries(CUSTOM)) {
    out.push("    " + markup);
  }

  if (missing.length) console.warn("⚠ آیکون‌های یافت‌نشده:", missing.join(", "));

  const sprite = `<svg class="svg-sprite" aria-hidden="true" focusable="false" width="0" height="0" style="position:absolute;overflow:hidden">
  <defs>
${out.join("\n")}
  </defs>
</svg>`;

  mkdirSync(join(ROOT, "assets", "icons"), { recursive: true });
  writeFileSync(join(ROOT, "assets", "icons", "sprite.svg"), sprite + "\n", "utf8");
  console.log(`✓ assets/icons/sprite.svg  (${out.length} آیکون${missing.length ? "، " + missing.length + " ناموفق" : ""})`);

  if (process.argv.includes("--inject")) {
    const idxPath = join(ROOT, "index.html");
    if (!existsSync(idxPath)) {
      console.warn("⚠ index.html موجود نیست؛ فقط اسپرایت ساخته شد.");
      return;
    }
    const html = readFileSync(idxPath, "utf8");
    const START = "<!-- ICON-SPRITE:START -->";
    const END = "<!-- ICON-SPRITE:END -->";
    if (!html.includes(START) || !html.includes(END)) {
      console.warn("⚠ نشانه‌های ICON-SPRITE در index.html پیدا نشد.");
      return;
    }
    const next = html.replace(
      new RegExp(`${START}[\\s\\S]*?${END}`),
      `${START}\n${sprite}\n  ${END}`
    );
    writeFileSync(idxPath, next, "utf8");
    console.log("✓ اسپرایت داخل index.html تزریق شد.");
  }
}

build();
