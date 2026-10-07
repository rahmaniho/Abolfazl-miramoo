/* ==========================================================================
   آزمون خودکار صفحهٔ لندینگ (بدون مرورگر، با jsdom)
   --------------------------------------------------------------------------
   رفتاری که آزمایش می‌شود: ناوبری و منوی موبایل، تایپ نقش‌ها، شمارنده‌ها،
   فیلتر نمونه‌کارها، اعتبارسنجی فرم (شمارهٔ فارسی و +۹۸)، امنیت پیام فرم،
   پیانوی تعاملی، و کامل‌بودن اسپرایت آیکون‌ها.

   اجرا:
     npm i -D jsdom
     node tools/test-dom.mjs        # یا: npm test
   ========================================================================== */
import { JSDOM, VirtualConsole } from "jsdom";
import { readFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const html = readFileSync(`${ROOT}/index.html`, "utf8");
const mainJs = readFileSync(`${ROOT}/assets/js/main.js`, "utf8");

const errors = [];
const vc = new VirtualConsole();
vc.on("jsdomError", (e) => {
  // خطای «بوم پشتیبانی نمی‌شود» در jsdom طبیعی است
  if (/getContext|Not implemented/.test(e.message)) return;
  errors.push("jsdomError: " + e.message);
});
vc.on("error", (m) => errors.push("console.error: " + m));

const dom = new JSDOM(html, {
  url: "http://localhost:8080/",
  runScripts: "outside-only",
  pretendToBeVisual: true,
  virtualConsole: vc,
});
const { window } = dom;
const { document } = window;

// پشتیبانی‌های غایب jsdom را شبیه‌سازی می‌کنیم تا مسیرهای واقعی کد اجرا شوند
const observed = [];
window.IntersectionObserver = class {
  constructor(cb, opts) {
    this.cb = cb;
    this.opts = opts;
  }
  observe(el) {
    observed.push(el);
  }
  unobserve() {}
  disconnect() {}
};

// AudioContext ساختگی برای آزمون پیانو
class FakeParam {
  setValueAtTime() { return this; }
  exponentialRampToValueAtTime() { return this; }
}
class FakeNode {
  constructor() {
    this.gain = new FakeParam();
    this.frequency = new FakeParam();
    this.type = "";
    this.state = "running";
    this.destination = {};
  }
  connect() { return this; }
  start() {}
  stop() {}
  resume() {}
  createOscillator() { return new FakeNode(); }
  createGain() { return new FakeNode(); }
  createBiquadFilter() { return new FakeNode(); }
}
window.AudioContext = class {
  constructor() { this.currentTime = 0; this.state = "running"; }
  createOscillator() { return new FakeNode(); }
  createGain() { return new FakeNode(); }
  createBiquadFilter() { return new FakeNode(); }
  resume() {}
};

// اجرای main.js
try {
  window.eval(mainJs);
} catch (e) {
  errors.push("EXECUTION ERROR: " + e.stack);
}

// jsdom رویداد DOMContentLoaded را غیرهم‌زمان اجرا می‌کند (مثل مرورگر واقعی با script defer)
await new Promise((resolve) => setTimeout(resolve, 250));

const results = [];
const check = (name, cond, extra = "") =>
  results.push(`${cond ? "PASS" : "FAIL"}  ${name}${extra ? "  → " + extra : ""}`);

// ---------- ۱) کلاس js روی ریشه
check("کلاس js به <html> اضافه شد", document.documentElement.classList.contains("js"));

// ---------- ۲) تگ‌های اصلی
check("h1 یکتا", document.querySelectorAll("h1").length === 1, document.querySelectorAll("h1").length + " عدد");
check("بخش‌ها موجودند", ["hero", "about", "services", "portfolio", "testimonials", "book", "contact"].every((id) => document.getElementById(id)));
check("عناصر reveal زیر نظر گرفته شدند", observed.length > 10, observed.length + " عنصر");

// ---------- ۳) پیانو
const whites = document.querySelectorAll(".piano__key").length;
const blacks = document.querySelectorAll(".piano__black").length;
check("۱۴ کلید سفید", whites === 14, whites + " عدد");
check("۱۰ کلید سیاه", blacks === 10, blacks + " عدد");
const afterVals = [...document.querySelectorAll(".piano__black")].map((b) => +b.dataset.after);
check("data-after در بازه‌ی درست", afterVals.every((v) => v >= 0 && v < 14), afterVals.join(","));
// نواختن یک کلید با AudioContext ساختگی
let pianoOk = true;
try {
  document.querySelector(".piano__key").dispatchEvent(new window.Event("pointerdown", { bubbles: true }));
} catch (e) {
  pianoOk = false;
  errors.push("piano trigger: " + e.message);
}
check("نواختن کلید پیانو بدون خطا", pianoOk);

// ---------- ۴) فیلتر نمونه‌کارها
const filterBtns = document.querySelectorAll("[data-filter]");
const workItems = document.querySelectorAll("[data-cat]");
check("۵ دکمه‌ی فیلتر", filterBtns.length === 5, filterBtns.length + " عدد");
check("۶ نمونه‌کار", workItems.length === 6, workItems.length + " عدد");
filterBtns[2].dispatchEvent(new window.Event("click", { bubbles: true })); // «اجرا»
const visible = [...workItems].filter((i) => !i.classList.contains("is-filtered-out"));
const activePressed = [...filterBtns].filter((b) => b.getAttribute("aria-pressed") === "true").length;
check("فیلتر «اجرا» فقط کارت‌های اجرا را نشان می‌دهد", visible.length === 1 && visible[0].dataset.cat === "live", visible.map((v) => v.dataset.cat).join(","));
check("فقط یک دکمه aria-pressed=true دارد", activePressed === 1, activePressed + " عدد");
check("پیام زنده‌ی نتیجه‌ی فیلتر پر شد", /نمونه‌کار/.test(document.getElementById("filter-status").textContent));
filterBtns[0].dispatchEvent(new window.Event("click", { bubbles: true })); // «همه»
check("فیلتر «همه» همه را برمی‌گرداند", [...workItems].every((i) => !i.classList.contains("is-filtered-out")));

// ---------- ۵) شمارنده‌ها (بدون IntersectionObserver واقعی، مقدار نهایی فوری)
const counters = [...document.querySelectorAll("[data-count]")];
check("چهار شمارنده", counters.length === 4, counters.length + " عدد");

// ---------- ۶) اعتبارسنجی فرم
const form = document.getElementById("contact-form");
const nameField = document.getElementById("field-name");
const phoneField = document.getElementById("field-phone");
const msgField = document.getElementById("field-message");

const fire = (el, type) => el.dispatchEvent(new window.Event(type, { bubbles: true }));

// الف) ارسال خالی → همه‌ی خطاها
fire(form, "submit");
const errCount = document.querySelectorAll(".field.has-error").length;
check("ارسال خالی ۳ خطا می‌دهد", errCount === 3, errCount + " عدد");
check("aria-invalid روی فیلد نام", nameField.getAttribute("aria-invalid") === "true");

// ب) شماره‌ی نامعتبر
nameField.value = "علی رضایی";
phoneField.value = "12345";
msgField.value = "سلام، برای کلاس آواز خصوصی وقت می‌خواستم.";
fire(form, "submit");
check("شماره‌ی نامعتبر رد می‌شود", phoneField.closest(".field").classList.contains("has-error"));
check("خطای شماره فارسی است", /موبایل معتبر نیست/.test(document.querySelector("#error-phone").textContent));

// ج) شماره با ارقام فارسی و پیش‌شماره‌ی ‎+۹۸
for (const variant of ["۰۹۱۹۲۵۸۶۵۵۹", "+989192586559", "۰۹۱۹ ۲۵۸ ۶۵۵۹"]) {
  phoneField.value = variant;
  fire(form, "submit");
  check(`پذیرش شماره‌ی «${variant}»`, !phoneField.closest(".field").classList.contains("has-error"));
}

// د) ارسال معتبر → پیام موفقیت + لینک واتساپ
fire(form, "submit");
const status = document.getElementById("form-status");
check("پیام موفقیت نمایش داده شد", status.classList.contains("is-visible"));
check("لینک واتساپ با متن پیام ساخته شد", /wa\.me\/989192586559\?text=/.test(status.innerHTML));
check("نام کاربر در پیام هست", /علی رضایی/.test(status.textContent));

// ه) تزریق HTML در نام نباید اجرا شود
nameField.value = "<img src=x onerror=alert(1)>پویا";
fire(form, "submit");
check(
  "ورودی خطرناک بی‌اثر می‌شود (بدون تگ اجراشدنی)",
  !status.querySelector("img, script, iframe") && /&lt;img/.test(status.innerHTML),
  status.innerHTML.slice(0, 60)
);

// ---------- ۷) تایپ نقش‌ها
const typed = document.getElementById("typed");
check("عنصر تایپ با data-roles", typed && typed.dataset.roles.split("|").length === 4, typed ? typed.dataset.roles : "-");

// ---------- ۸) منوی موبایل
const toggle = document.querySelector(".nav-toggle");
const menu = document.getElementById("nav-menu");
toggle.dispatchEvent(new window.Event("click", { bubbles: true }));
check("منوی موبایل باز می‌شود", toggle.getAttribute("aria-expanded") === "true" && menu.classList.contains("is-open"));
document.dispatchEvent(new window.KeyboardEvent("keydown", { key: "Escape" }));
check("کلید Escape منو را می‌بندد", toggle.getAttribute("aria-expanded") === "false");

// ---------- ۹) ناوبری چسبان با اسکرول
Object.defineProperty(window, "scrollY", { value: 700, configurable: true });
window.dispatchEvent(new window.Event("scroll"));
check("کلاس is-scrolled روی ناوبری", document.querySelector(".site-nav").classList.contains("is-scrolled"));
check("دکمه‌ی بازگشت به بالا نمایان شد", document.querySelector(".back-to-top").classList.contains("is-visible"));

// ---------- ۱۰) شمارش استفاده‌ی آیکون‌ها
const spriteIds = new Set([...document.querySelectorAll("symbol")].map((s) => s.id));
const usedIds = new Set([...document.querySelectorAll("use")].map((u) => u.getAttribute("href").slice(1)));
const missing = [...usedIds].filter((id) => !spriteIds.has(id));
check("همه‌ی آیکون‌های استفاده‌شده در اسپرایت موجودند", missing.length === 0, missing.join(","));
check("بیش از ۴۰ آیکون در اسپرایت", spriteIds.size > 40, spriteIds.size + " عدد");

// ---------- ۱۱) پیوندهای تماس
const telLinks = [...document.querySelectorAll('a[href^="tel:"]')];
const norm = (s) => s.replace(/[۰-۹]/g, (d) => "۰۱۲۳۴۵۶۷۸۹".indexOf(d));
check("همه‌ی پیوندهای tel: شماره یکی دارند", telLinks.every((a) => norm(a.getAttribute("href")) === "tel:09192586559" || a.getAttribute("href") === "tel:09192586559"), telLinks.map((a) => a.getAttribute("href")).join(" | "));

console.log("\n" + results.join("\n"));
const failed = results.filter((r) => r.startsWith("FAIL"));
console.log(`\nنتیجه: ${results.length - failed.length}/${results.length} موفق`);
if (errors.length) console.log("\n⚠ خطاهای اجرا:\n" + errors.join("\n"));

// بستن پنجره تا تایمرهای باقی‌مانده (تایپ و اسلایدر) پروسه را زنده نگه ندارند
dom.window.close();
process.exit(errors.length || failed.length ? 1 : 0);
