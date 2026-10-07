/* ==========================================================================
   ابو‌لفضل میرعمو — افکت‌های تصویری روی بوم (Canvas)
   --------------------------------------------------------------------------
   ۱) صورت فلکی نُت‌ها  → پس‌زمینه‌ی کل صفحه + تعامل با ماوس
   ۲) موج Siri-like     → پس‌زمینه‌ی بخش هیرو
   بدون هیچ کتابخانه‌ی بیرونی. هر دو افکت در حالت «کاهش حرکت» غیرفعال می‌شوند
   و هنگام خارج‌شدن از دید، حلقه‌ی رندر متوقف می‌شود (صرفه‌جویی در باتری).
   ========================================================================== */
(function () {
  "use strict";

  function mediaQuery(query) {
    if (typeof window.matchMedia === "function") return window.matchMedia(query);
    return { matches: false, addEventListener: function () {}, addListener: function () {} };
  }
  var reduceMotion = mediaQuery("(prefers-reduced-motion: reduce)").matches;

  var hasCanvas = false;
  try {
    hasCanvas = !!document.createElement("canvas").getContext("2d");
  } catch (error) {
    hasCanvas = false; // محیط‌هایی که از بوم پشتیبانی نمی‌کنند
  }

  /* ---------------------------------------------------------------- ابزارها */
  function dpr(max) {
    return Math.min(window.devicePixelRatio || 1, max || 2);
  }

  function fit(canvas, capDpr) {
    var rect = canvas.getBoundingClientRect();
    var ratio = dpr(capDpr);
    var w = Math.max(1, Math.round(rect.width));
    var h = Math.max(1, Math.round(rect.height));
    canvas.width = Math.round(w * ratio);
    canvas.height = Math.round(h * ratio);
    var ctx = canvas.getContext("2d");
    ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
    return { w: w, h: h, ctx: ctx };
  }

  /* ---------------------------------------------------------------- ۱) صورت فلکی نُت‌ها */
  var NOTES = {
    gold: "rgba(212, 175, 55, 1)",
    light: "rgba(232, 203, 106, 1)",
    amber: "rgba(240, 169, 59, 1)",
  };

  function drawNote(ctx, x, y, size, rotation, alpha, color) {
    ctx.save();
    ctx.translate(x, y);
    ctx.rotate(rotation);
    ctx.globalAlpha = alpha;
    ctx.fillStyle = color;
    // سرِ نت
    ctx.beginPath();
    ctx.ellipse(0, 0, size * 0.44, size * 0.32, -0.34, 0, Math.PI * 2);
    ctx.fill();
    // ساقه
    ctx.fillRect(size * 0.3, -size * 2.05, size * 0.12, size * 2.1);
    // پرچم نت
    ctx.beginPath();
    ctx.moveTo(size * 0.42, -size * 2.05);
    ctx.quadraticCurveTo(size * 1.08, -size * 1.7, size * 0.74, -size * 0.9);
    ctx.quadraticCurveTo(size * 0.88, -size * 1.58, size * 0.42, -size * 1.6);
    ctx.closePath();
    ctx.fill();
    ctx.restore();
  }

  function initStarfield() {
    var canvas = document.getElementById("starfield");
    if (!canvas || reduceMotion) return;

    var view, ctx;
    var parts = [];
    var pointer = { x: -9999, y: -9999, active: false };
    var raf = null;
    var last = 0;

    function build() {
      var area = view.w * view.h;
      var count = Math.max(26, Math.min(78, Math.round(area / 24000)));
      parts = [];
      for (var i = 0; i < count; i++) {
        parts.push({
          x: Math.random() * view.w,
          y: Math.random() * view.h,
          vx: (Math.random() - 0.5) * 0.24,
          vy: (Math.random() - 0.5) * 0.24,
          size: 2.4 + Math.random() * 5.2,
          rot: Math.random() * Math.PI * 2,
          spin: (Math.random() - 0.5) * 0.006,
          note: Math.random() < 0.42, // بخشی از ذرات «نت» هستند
          alpha: 0.2 + Math.random() * 0.42,
          twinkle: Math.random() * Math.PI * 2,
        });
      }
    }

    function resize() {
      view = fit(canvas, 2);
      ctx = view.ctx;
      build();
    }

    function draw(dt, time) {
      ctx.clearRect(0, 0, view.w, view.h);
      ctx.globalCompositeOperation = "lighter";

      // خطوط صورت فلکی
      ctx.lineWidth = 1;
      for (var i = 0; i < parts.length; i++) {
        var a = parts[i];
        for (var j = i + 1; j < parts.length; j++) {
          var b = parts[j];
          var dx = a.x - b.x;
          var dy = a.y - b.y;
          var dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < 132) {
            var alpha = (1 - dist / 132) * 0.16;
            ctx.strokeStyle = "rgba(212, 175, 55," + alpha.toFixed(3) + ")";
            ctx.beginPath();
            ctx.moveTo(a.x, a.y);
            ctx.lineTo(b.x, b.y);
            ctx.stroke();
          }
        }
      }

      // پیوند نور با نشانگر ماوس
      if (pointer.active) {
        for (var k = 0; k < parts.length; k++) {
          var p = parts[k];
          var mx = p.x - pointer.x;
          var my = p.y - pointer.y;
          var md = Math.sqrt(mx * mx + my * my);
          if (md < 210) {
            ctx.strokeStyle = "rgba(240, 169, 59," + ((1 - md / 210) * 0.4).toFixed(3) + ")";
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.moveTo(pointer.x, pointer.y);
            ctx.lineTo(p.x, p.y);
            ctx.stroke();
            // جذب ملایم ذرات به سمت نشانگر
            p.x -= (mx / md) * 0.42;
            p.y -= (my / md) * 0.42;
          }
        }
      }

      // ذرات و نُت‌ها
      for (var n = 0; n < parts.length; n++) {
        var q = parts[n];
        q.x += q.vx * dt * 60;
        q.y += q.vy * dt * 60;
        q.rot += q.spin * dt * 60;
        q.twinkle += 0.02 * dt * 60;

        if (q.x < -30) q.x = view.w + 20;
        if (q.x > view.w + 30) q.x = -20;
        if (q.y < -30) q.y = view.h + 20;
        if (q.y > view.h + 30) q.y = -20;

        var glow = 0.72 + Math.sin(q.twinkle) * 0.28;
        var color = q.note ? NOTES.gold : n % 3 === 0 ? NOTES.light : NOTES.gold;

        if (q.note) {
          drawNote(ctx, q.x, q.y, q.size * 1.5, q.rot, q.alpha * glow * 0.85, color);
        } else {
          ctx.globalAlpha = q.alpha * glow;
          ctx.fillStyle = color;
          ctx.beginPath();
          ctx.arc(q.x, q.y, q.size * 0.42, 0, Math.PI * 2);
          ctx.fill();
          ctx.globalAlpha = q.alpha * glow * 0.24;
          ctx.beginPath();
          ctx.arc(q.x, q.y, q.size * 1.5, 0, Math.PI * 2);
          ctx.fill();
        }
      }
      ctx.globalAlpha = 1;
      ctx.globalCompositeOperation = "source-over";
      void time;
    }

    function loop(now) {
      if (!last) last = now;
      var dt = Math.min(0.05, (now - last) / 1000);
      last = now;
      draw(dt, now / 1000);
      raf = window.requestAnimationFrame(loop);
    }

    function start() {
      if (raf === null) {
        last = 0;
        raf = window.requestAnimationFrame(loop);
      }
    }
    function stop() {
      if (raf !== null) {
        window.cancelAnimationFrame(raf);
        raf = null;
      }
    }

    resize();

    var resizeTimer = null;
    window.addEventListener(
      "resize",
      function () {
        window.clearTimeout(resizeTimer);
        resizeTimer = window.setTimeout(resize, 180);
      },
      { passive: true }
    );

    // تعامل با ماوس/لمس
    window.addEventListener(
      "pointermove",
      function (e) {
        pointer.x = e.clientX;
        pointer.y = e.clientY;
        pointer.active = true;
      },
      { passive: true }
    );
    window.addEventListener(
      "pointerleave",
      function () {
        pointer.active = false;
      },
      { passive: true }
    );

    document.addEventListener("visibilitychange", function () {
      if (document.hidden) stop();
      else start();
    });

    start();
  }

  /* ---------------------------------------------------------------- ۲) موج Siri-like */
  function initSiriWave() {
    var canvas = document.getElementById("siri-wave");
    if (!canvas || reduceMotion) return;
    var hero = document.querySelector(".hero");
    var view, ctx;
    var running = false;
    var raf = null;
    var boost = 0; // با هاور روی هیرو، موج قوی‌تر می‌شود
    var targetBoost = 0;

    var waves = [
      { freq: 1.15, amp: 0.3, speed: 0.55, width: 2.6, color: "rgba(240, 169, 59, 0.55)", blur: 22 },
      { freq: 1.55, amp: 0.42, speed: 0.42, width: 2.2, color: "rgba(232, 203, 106, 0.45)", blur: 18 },
      { freq: 0.85, amp: 0.2, speed: 0.72, width: 3.4, color: "rgba(212, 175, 55, 0.32)", blur: 26 },
      { freq: 2.1, amp: 0.5, speed: 0.95, width: 1.5, color: "rgba(245, 241, 232, 0.22)", blur: 12 },
      { freq: 1.32, amp: 0.34, speed: 0.6, width: 1.9, color: "rgba(240, 169, 59, 0.34)", blur: 16 },
    ];

    function resize() {
      view = fit(canvas, 1.75);
      ctx = view.ctx;
    }

    function render(time) {
      var W = view.w;
      var H = view.h;
      var mid = H * 0.52;
      var maxAmp = H * 0.34 * (1 + boost);

      ctx.clearRect(0, 0, W, H);
      ctx.globalCompositeOperation = "lighter";
      ctx.lineCap = "round";

      for (var i = 0; i < waves.length; i++) {
        var w = waves[i];
        ctx.beginPath();
        for (var x = 0; x <= W; x += 3) {
          var nx = x / W;
          var envelope = Math.pow(Math.sin(Math.PI * nx), 1.5);
          var phase = nx * Math.PI * 2 * w.freq * 2.4 + time * w.speed + i * 0.7;
          var y = mid + Math.sin(phase) * maxAmp * envelope * w.amp;
          // لایه‌ی هارمونیک نرم برای حس «موج زنده»
          y += Math.sin(phase * 2.3 + 1.2) * maxAmp * envelope * w.amp * 0.22;
          if (x === 0) ctx.moveTo(x, y);
          else ctx.lineTo(x, y);
        }
        ctx.strokeStyle = w.color;
        ctx.lineWidth = w.width;
        ctx.shadowBlur = w.blur;
        ctx.shadowColor = "rgba(240, 169, 59, 0.55)";
        ctx.stroke();
      }
      ctx.shadowBlur = 0;
      ctx.globalCompositeOperation = "source-over";
    }

    function loop(now) {
      var t = now / 1000;
      boost += (targetBoost - boost) * 0.05;
      render(t);
      raf = window.requestAnimationFrame(loop);
    }

    function start() {
      if (!running) {
        running = true;
        raf = window.requestAnimationFrame(loop);
      }
    }
    function stop() {
      running = false;
      if (raf !== null) window.cancelAnimationFrame(raf);
      raf = null;
    }

    resize();
    var resizeTimer = null;
    window.addEventListener(
      "resize",
      function () {
        window.clearTimeout(resizeTimer);
        resizeTimer = window.setTimeout(resize, 180);
      },
      { passive: true }
    );

    if (hero && "IntersectionObserver" in window) {
      new IntersectionObserver(
        function (entries) {
          entries.forEach(function (entry) {
            if (entry.isIntersecting) start();
            else stop();
          });
        },
        { threshold: 0.05 }
      ).observe(hero);
      hero.addEventListener("pointerenter", function () {
        targetBoost = 0.55;
      });
      hero.addEventListener("pointerleave", function () {
        targetBoost = 0;
      });
    } else {
      start();
    }

    document.addEventListener("visibilitychange", function () {
      if (document.hidden) stop();
      else if (!hero || hero.getBoundingClientRect().bottom > 0) start();
    });
  }

  /* ---------------------------------------------------------------- اجرا */
  function boot() {
    if (!hasCanvas) return;
    try {
      initStarfield();
    } catch (error) {
      if (window.console && window.console.error) window.console.error("[starfield]", error);
    }
    try {
      initSiriWave();
    } catch (error) {
      if (window.console && window.console.error) window.console.error("[siri-wave]", error);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
