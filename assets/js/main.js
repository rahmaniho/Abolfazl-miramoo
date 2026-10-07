/* ==========================================================================
   ابو‌لفضل میرعمو — تعامل‌های صفحه (بدون هیچ کتابخانه‌ی بیرونی، جز Swiper)
   --------------------------------------------------------------------------
   ۱) ناوبری چسبان + منوی موبایل + فعال‌سازی پیوند بخش جاری
   ۲) ورود نرم عناصر با اسکرول (IntersectionObserver)
   ۳) شمارنده‌های آماری با اعداد فارسی
   ۴) تایپ نقش‌ها در هیرو (مدرس موسیقی، آهنگساز، خواننده، مجری)
   ۵) فیلتر نمونه‌کارها
   ۶) اسلایدر نظرات (Swiper — RTL)
   ۷) اعتبارسنجی فرم تماس + مسیر پشتیبان واتساپ/تلگرام
   ۸) پیانوی تعاملی (صدای واقعی با Web Audio)
   ۹) دکمه‌ی بازگشت به بالا و نمایش/پنهان‌کردن دکمه‌ی تماس
   ========================================================================== */
(function () {
  "use strict";

  var $ = function (sel, root) {
    return (root || document).querySelector(sel);
  };
  var $$ = function (sel, root) {
    return Array.prototype.slice.call((root || document).querySelectorAll(sel));
  };
  /* مرورگرهای قدیمی ممکن است matchMedia نداشته باشند؛ نبودِ آن نباید کل اسکریپت را از کار بیندازد. */
  function mediaQuery(query) {
    if (typeof window.matchMedia === "function") return window.matchMedia(query);
    return { matches: false, addEventListener: function () {}, addListener: function () {}, removeListener: function () {} };
  }
  var reduceMotion = mediaQuery("(prefers-reduced-motion: reduce)").matches;

  /* ---------------------------------------------------------------- اعداد فارسی */
  var FA_DIGITS = "۰۱۲۳۴۵۶۷۸۹";
  var AR_DIGITS = "٠١٢٣٤٥٦٧٨٩";

  function toFa(value) {
    return String(value).replace(/\d/g, function (d) {
      return FA_DIGITS.charAt(+d);
    });
  }
  function toEn(value) {
    return String(value).replace(/[۰-۹٠-٩]/g, function (d) {
      var i = FA_DIGITS.indexOf(d);
      if (i === -1) i = AR_DIGITS.indexOf(d);
      return String(i);
    });
  }
  /** متن کاربر را برای درج امن داخل HTML کدگذاری می‌کند (جلوگیری از تزریق) */
  function escapeText(value) {
    return String(value).replace(/[&<>"']/g, function (ch) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch];
    });
  }

  /** شماره‌ی موبایل ایران را یکدست می‌کند: +۹۸… و ۰۹… و فاصله/خط تیره */
  function normalizePhone(raw) {
    var v = toEn(raw).replace(/[\s()\-.]/g, "");
    if (v.indexOf("+98") === 0) v = "0" + v.slice(3);
    else if (v.indexOf("0098") === 0) v = "0" + v.slice(4);
    else if (/^98\d{10}$/.test(v)) v = "0" + v.slice(2);
    return v;
  }

  /* ---------------------------------------------------------------- ۱) ناوبری */
  function initNav() {
    var nav = $(".site-nav");
    var toggle = $(".nav-toggle");
    var menu = $("#nav-menu");

    function onScroll() {
      if (!nav) return;
      nav.classList.toggle("is-scrolled", window.scrollY > 24);
    }
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });

    if (toggle && menu) {
      var setOpen = function (open) {
        toggle.setAttribute("aria-expanded", open ? "true" : "false");
        menu.classList.toggle("is-open", open);
      };
      toggle.addEventListener("click", function () {
        setOpen(toggle.getAttribute("aria-expanded") !== "true");
      });
      $$("a", menu).forEach(function (a) {
        a.addEventListener("click", function () {
          setOpen(false);
        });
      });
      document.addEventListener("keydown", function (e) {
        if (e.key === "Escape" && toggle.getAttribute("aria-expanded") === "true") {
          setOpen(false);
          toggle.focus();
        }
      });
      document.addEventListener("click", function (e) {
        if (
          toggle.getAttribute("aria-expanded") === "true" &&
          !menu.contains(e.target) &&
          !toggle.contains(e.target)
        ) {
          setOpen(false);
        }
      });
    }

    // فعال‌سازی پیوند بخش جاری
    var links = $$(".nav-links a[href^='#']");
    var sections = links
      .map(function (a) {
        return document.getElementById(a.getAttribute("href").slice(1));
      })
      .filter(Boolean);

    if ("IntersectionObserver" in window && sections.length) {
      var io = new IntersectionObserver(
        function (entries) {
          entries.forEach(function (entry) {
            if (!entry.isIntersecting) return;
            links.forEach(function (a) {
              var current = a.getAttribute("href") === "#" + entry.target.id;
              if (current) a.setAttribute("aria-current", "true");
              else a.removeAttribute("aria-current");
            });
          });
        },
        { rootMargin: "-45% 0px -50% 0px", threshold: 0 }
      );
      sections.forEach(function (s) {
        io.observe(s);
      });
    }
  }

  /* ---------------------------------------------------------------- ۲) ورود با اسکرول */
  function initReveal() {
    // هم عناصر .reveal و هم بخش‌های دارای «موج اسکرول» زیر نظر گرفته می‌شوند
    var items = $$(".reveal, .section.ripple, .glow-on-scroll");
    if (!items.length) return;

    if (!("IntersectionObserver" in window) || reduceMotion) {
      items.forEach(function (el) {
        el.classList.add("is-visible");
      });
      return;
    }

    var io = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          entry.target.classList.add("is-visible");
          io.unobserve(entry.target);
        });
      },
      { threshold: 0.16, rootMargin: "0px 0px -8% 0px" }
    );
    items.forEach(function (el) {
      io.observe(el);
    });
  }

  /* ---------------------------------------------------------------- ۳) شمارنده‌ها */
  function initCounters() {
    var nodes = $$("[data-count]");
    if (!nodes.length) return;

    function run(el) {
      var target = parseFloat(el.getAttribute("data-count")) || 0;
      var duration = 1700;
      var start = null;

      function frame(now) {
        if (start === null) start = now;
        var p = Math.min(1, (now - start) / duration);
        var eased = 1 - Math.pow(1 - p, 3);
        var value = Math.round(target * eased);
        el.textContent = toFa(value);
        if (p < 1) window.requestAnimationFrame(frame);
      }
      window.requestAnimationFrame(frame);
    }

    if (!("IntersectionObserver" in window) || reduceMotion) {
      nodes.forEach(function (el) {
        el.textContent = toFa(el.getAttribute("data-count"));
        var stat = el.closest(".stat");
        if (stat) stat.classList.add("is-counted");
      });
      return;
    }

    var io = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          var el = entry.target;
          el.textContent = toFa(0);
          run(el);
          var stat = el.closest(".stat");
          if (stat) stat.classList.add("is-counted");
          io.unobserve(el);
        });
      },
      { threshold: 0.5 }
    );
    nodes.forEach(function (el) {
      io.observe(el);
    });
  }

  /* ---------------------------------------------------------------- ۴) تایپ نقش‌ها */
  function initTyping() {
    var el = $("#typed");
    if (!el) return;
    var roles = (el.getAttribute("data-roles") || "مدرس موسیقی|آهنگساز|خواننده|مجری").split("|");
    if (reduceMotion) {
      el.textContent = roles[0];
      return;
    }

    var roleIndex = 0;
    var charIndex = 0;
    var deleting = false;

    function tick() {
      var role = roles[roleIndex];
      if (!deleting) {
        charIndex++;
        el.textContent = role.slice(0, charIndex);
        if (charIndex === role.length) {
          deleting = true;
          window.setTimeout(tick, 1700);
          return;
        }
        window.setTimeout(tick, 95 + Math.random() * 60);
      } else {
        charIndex--;
        el.textContent = role.slice(0, Math.max(0, charIndex));
        if (charIndex <= 0) {
          deleting = false;
          roleIndex = (roleIndex + 1) % roles.length;
          window.setTimeout(tick, 380);
          return;
        }
        window.setTimeout(tick, 45);
      }
    }
    window.setTimeout(tick, 900);
  }

  /* ---------------------------------------------------------------- ۵) فیلتر نمونه‌کارها */
  function initFilters() {
    var buttons = $$("[data-filter]");
    var items = $$("[data-cat]");
    if (!buttons.length || !items.length) return;
    var live = $("#filter-status");

    buttons.forEach(function (btn) {
      btn.addEventListener("click", function () {
        var filter = btn.getAttribute("data-filter");
        buttons.forEach(function (b) {
          b.setAttribute("aria-pressed", b === btn ? "true" : "false");
        });

        var shown = 0;
        items.forEach(function (item) {
          var match = filter === "all" || item.getAttribute("data-cat") === filter;
          item.classList.toggle("is-filtered-out", !match);
          if (match) {
            shown++;
            item.style.setProperty("--d", shown * 0.06 + "s");
            if (!reduceMotion) {
              item.classList.remove("is-visible");
              // اجازه بده مرورگر بازنشانی را ببیند، سپس انیمیشن ورود
              void item.offsetWidth;
              window.requestAnimationFrame(function () {
                item.classList.add("is-visible");
              });
            }
          }
        });

        if (live) {
          live.textContent = shown + " نمونه‌کار نمایش داده شد.";
        }
      });
    });
  }

  /* ---------------------------------------------------------------- ۶) اسلایدر نظرات */
  function initTestimonials() {
    var el = $(".tst-swiper");
    if (!el || typeof window.Swiper !== "function") return;

    new window.Swiper(el, {
      slidesPerView: 1,
      spaceBetween: 18,
      speed: 750,
      loop: true,
      grabCursor: true,
      watchOverflow: true,
      autoplay: { delay: 5200, disableOnInteraction: false, pauseOnMouseEnter: true },
      pagination: {
        el: ".tst-pagination",
        clickable: true,
        bulletClass: "swiper-pagination-bullet",
        bulletActiveClass: "swiper-pagination-bullet-active",
      },
      navigation: { nextEl: ".tst-next", prevEl: ".tst-prev" },
      keyboard: { enabled: true, onlyInViewport: true },
      a11y: {
        containerMessage: "نظرات هنرجویان و کارفرمایان",
        containerRoleDescriptionMessage: "اسلایدر",
        itemRoleDescriptionMessage: "نظر",
        prevSlideMessage: "نظر قبلی",
        nextSlideMessage: "نظر بعدی",
        paginationBulletMessage: "رفتن به نظر {{index}}",
      },
      breakpoints: {
        0: { slidesPerView: 1, spaceBetween: 16 },
        720: { slidesPerView: 2, spaceBetween: 20 },
        1080: { slidesPerView: 3, spaceBetween: 24 },
      },
    });
  }

  /* ---------------------------------------------------------------- ۷) فرم تماس */
  function initForm() {
    var form = $("#contact-form");
    if (!form) return;
    var status = $("#form-status");
    var submitBtn = $("button[type='submit']", form);
    var endpoint = form.getAttribute("data-endpoint") || "";
    var whatsappBase = "https://wa.me/989192586559";

    var rules = {
      name: function (v) {
        if (!v.trim()) return "لطفاً نام و نام خانوادگی خود را وارد کنید.";
        if (v.trim().length < 3) return "نام باید حداقل ۳ حرف باشد.";
        return "";
      },
      phone: function (v) {
        if (!v.trim()) return "شماره‌ی تماس الزامی است.";
        if (!/^09\d{9}$/.test(normalizePhone(v))) return "شماره‌ی موبایل معتبر نیست (مثال: ۰۹۱۲۳۴۵۶۷۸۹).";
        return "";
      },
      message: function (v) {
        if (!v.trim()) return "متن پیام را بنویسید.";
        if (v.trim().length < 10) return "پیام باید حداقل ۱۰ حرف باشد.";
        return "";
      },
    };

    function validateField(field) {
      var name = field.getAttribute("data-field");
      var rule = rules[name];
      if (!rule) return true;
      var wrap = field.closest(".field");
      var errorBox = $(".error", wrap);
      var message = rule(field.value);
      wrap.classList.toggle("has-error", !!message);
      wrap.classList.toggle("is-valid", !message && !!field.value.trim());
      field.setAttribute("aria-invalid", message ? "true" : "false");
      if (errorBox) errorBox.textContent = message;
      return !message;
    }

    $$("[data-field]", form).forEach(function (field) {
      field.addEventListener("blur", function () {
        validateField(field);
      });
      field.addEventListener("input", function () {
        var wrap = field.closest(".field");
        if (wrap && wrap.classList.contains("has-error")) validateField(field);
      });
    });

    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var fields = $$("[data-field]", form);
      var firstInvalid = null;
      var ok = true;

      fields.forEach(function (field) {
        var valid = validateField(field);
        if (!valid) {
          ok = false;
          if (!firstInvalid) firstInvalid = field;
        }
      });

      if (!ok) {
        if (firstInvalid) firstInvalid.focus();
        if (status) status.classList.remove("is-visible");
        return;
      }

      var name = $("#field-name").value.trim();
      var phone = normalizePhone($("#field-phone").value);
      var topic = $("#field-topic") ? $("#field-topic").value : "";
      var message = $("#field-message").value.trim();
      var payload = { name: name, phone: phone, topic: topic, message: message };

      function showSuccess(extraHtml) {
        if (!status) return;
        status.innerHTML =
          '<svg class="icon" aria-hidden="true"><use href="#i-check-circle"></use></svg><div>' +
          "<strong>ممنون " +
          escapeText(name) +
          "! پیام شما ثبت شد.</strong><br>" +
          "برای پیگیری سریع‌تر، همین پیام را در واتساپ یا تلگرام هم برای من بفرستید — معمولاً کمتر از ۲ ساعت پاسخ می‌دهم." +
          (extraHtml || "") +
          '<div class="contact-actions"><a class="chip-link" href="' +
          whatsappBase +
          "?text=" +
          encodeURIComponent("سلام، " + name + " هستم.\n" + message + "\nشماره تماس من: " + phone) +
          '" target="_blank" rel="noopener"><svg class="icon" aria-hidden="true"><use href="#i-whatsapp"></use></svg>ارسال در واتساپ</a>' +
          '<a class="chip-link" href="https://t.me/AbolfazlMiramoo" target="_blank" rel="noopener"><svg class="icon" aria-hidden="true"><use href="#i-telegram"></use></svg>ارسال در تلگرام</a></div>' +
          "</div>";
        status.classList.add("is-visible");
      }

      if (endpoint) {
        // اگر آدرس سرور را در data-endpoint بگذارید، فرم به همان‌جا ارسال می‌شود.
        if (submitBtn) submitBtn.disabled = true;
        window
          .fetch(endpoint, {
            method: "POST",
            headers: { "Content-Type": "application/json", Accept: "application/json" },
            body: JSON.stringify(payload),
          })
          .then(function (res) {
            if (!res.ok) throw new Error("network");
            form.reset();
            $$(".field", form).forEach(function (f) {
              f.classList.remove("has-error", "is-valid");
            });
            showSuccess();
          })
          .catch(function () {
            if (status) {
              status.innerHTML =
                '<svg class="icon" aria-hidden="true"><use href="#i-message"></use></svg><div><strong>ارسال خودکار انجام نشد.</strong><br>لطفاً پیام را در واتساپ یا تلگرام بفرستید یا مستقیم تماس بگیرید: <a href="tel:09192586559">۰۹۱۹۲۵۸۶۵۵۹</a></div>';
              status.classList.add("is-visible");
            }
          })
          .then(function () {
            if (submitBtn) submitBtn.disabled = false;
          });
      } else {
        showSuccess();
      }
    });
  }

  /* ---------------------------------------------------------------- ۸) پیانوی تعاملی */
  function initPiano() {
    var piano = $(".piano");
    if (!piano) return;

    var FREQ = {
      C4: 261.63, Cs4: 277.18, D4: 293.66, Ds4: 311.13, E4: 329.63, F4: 349.23, Fs4: 369.99,
      G4: 392.0, Gs4: 415.3, A4: 440.0, As4: 466.16, B4: 493.88,
      C5: 523.25, Cs5: 554.37, D5: 587.33, Ds5: 622.25, E5: 659.25, F5: 698.46, Fs5: 739.99,
      G5: 783.99, Gs5: 830.61, A5: 880.0, As5: 932.33, B5: 987.77,
    };

    var ctxAudio = null;
    function audio() {
      if (ctxAudio) return ctxAudio;
      var Ctx = window.AudioContext || window.webkitAudioContext;
      if (!Ctx) return null;
      ctxAudio = new Ctx();
      return ctxAudio;
    }

    function play(note) {
      var freq = FREQ[note];
      var actx = audio();
      if (!freq || !actx) return;
      if (actx.state === "suspended") actx.resume();
      var now = actx.currentTime;
      var osc = actx.createOscillator();
      var gain = actx.createGain();
      var filter = actx.createBiquadFilter();
      filter.type = "lowpass";
      filter.frequency.value = 2400;
      osc.type = "triangle";
      osc.frequency.value = freq;
      gain.gain.setValueAtTime(0.0001, now);
      gain.gain.exponentialRampToValueAtTime(0.16, now + 0.02);
      gain.gain.exponentialRampToValueAtTime(0.0001, now + 1.5);
      osc.connect(filter);
      filter.connect(gain);
      gain.connect(actx.destination);
      osc.start(now);
      osc.stop(now + 1.6);
      // لایه‌ی هارمونیک ملایم
      var osc2 = actx.createOscillator();
      var gain2 = actx.createGain();
      osc2.type = "sine";
      osc2.frequency.value = freq * 2;
      gain2.gain.setValueAtTime(0.0001, now);
      gain2.gain.exponentialRampToValueAtTime(0.05, now + 0.03);
      gain2.gain.exponentialRampToValueAtTime(0.0001, now + 0.9);
      osc2.connect(gain2);
      gain2.connect(actx.destination);
      osc2.start(now);
      osc2.stop(now + 1);
    }

    var first = true;
    function trigger(key) {
      var note = key.getAttribute("data-note");
      play(note);
      key.classList.add("is-down");
      window.setTimeout(function () {
        key.classList.remove("is-down");
      }, 190);
      if (first) {
        first = false;
        piano.classList.remove("piano--auto"); // پایان نواختن خودکار
      }
    }

    $$(".piano__key, .piano__black", piano).forEach(function (key) {
      key.addEventListener("pointerdown", function () {
        trigger(key);
      });
      key.addEventListener("keydown", function (e) {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          trigger(key);
        }
      });
    });

    // جای‌گذاری دقیق کلیدهای سیاه روی مرز کلیدهای سفید
    function layoutBlacks() {
      var whites = $$(".piano__key", piano);
      var blacks = $$(".piano__black", piano);
      var blacksBox = $(".piano__blacks", piano);
      if (!whites.length || !blacks.length || !blacksBox) return;
      // مختصات هر دو نسبت به .piano محاسبه می‌شود، پس اختلاف مبنا حذف می‌شود
      var origin = blacksBox.offsetLeft;
      blacks.forEach(function (black) {
        var after = parseInt(black.getAttribute("data-after"), 10);
        var white = whites[after];
        if (!white) return;
        var width = Math.round(white.offsetWidth * 0.62);
        var left = Math.round(white.offsetLeft - origin + white.offsetWidth - width / 2);
        black.style.width = width + "px";
        black.style.left = left + "px";
      });
    }
    layoutBlacks();
    window.addEventListener("resize", layoutBlacks);
    if ("ResizeObserver" in window) new ResizeObserver(layoutBlacks).observe(piano);
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(layoutBlacks);
  }

  /* ---------------------------------------------------------------- ۹) دکمه‌های شناور */
  function initFloatingButtons() {
    var top = $(".back-to-top");
    var fab = $(".call-fab");
    var contact = $("#contact");

    function onScroll() {
      if (top) top.classList.toggle("is-visible", window.scrollY > 600);
      if (fab && contact) {
        var rect = contact.getBoundingClientRect();
        var inContact = rect.top < window.innerHeight * 0.82 && rect.bottom > 0;
        fab.style.opacity = inContact ? "0" : "1";
        fab.style.pointerEvents = inContact ? "none" : "auto";
      }
    }
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll, { passive: true });

    if (top) {
      top.addEventListener("click", function () {
        window.scrollTo({ top: 0, behavior: reduceMotion ? "auto" : "smooth" });
      });
    }
  }

  /* ---------------------------------------------------------------- اجرا */
  /**
   * هر قابلیت جداگانه اجرا می‌شود؛ اگر یک بخش به دلیلی شکست بخورد
   * (مثلاً مرورگر قدیمی)، بقیه‌ی صفحه سالم می‌ماند.
   */
  function safe(name, fn) {
    try {
      fn();
    } catch (error) {
      // خطا در کنسول دیده می‌شود اما صفحه از کار نمی‌افتد
      if (window.console && window.console.error) window.console.error("[" + name + "]", error);
    }
  }

  function boot() {
    document.documentElement.classList.add("js");
    safe("nav", initNav);
    safe("reveal", initReveal);
    safe("counters", initCounters);
    safe("typing", initTyping);
    safe("filters", initFilters);
    safe("testimonials", initTestimonials);
    safe("form", initForm);
    safe("piano", initPiano);
    safe("floating", initFloatingButtons);
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();
