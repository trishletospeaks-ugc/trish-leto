/* Trish Leto: the only script on the site. Everything works without it;
   it adds the mobile menu, click-to-load TikTok players, copy buttons and the
   "past event" label. No third-party code loads until someone presses Play. */
(function () {
  "use strict";
  var d = document;

  // Mobile menu
  var toggle = d.querySelector(".nav-toggle");
  var nav = d.getElementById("site-nav");
  if (toggle && nav) {
    var setOpen = function (open) {
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
      nav.classList.toggle("is-open", open);
    };
    toggle.addEventListener("click", function () {
      setOpen(toggle.getAttribute("aria-expanded") !== "true");
    });
    d.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && nav.classList.contains("is-open")) {
        setOpen(false);
        toggle.focus();
      }
    });
  }

  // TikTok: swap the cover for TikTok's official player only when asked.
  Array.prototype.forEach.call(d.querySelectorAll("[data-tiktok]"), function (btn) {
    btn.addEventListener("click", function () {
      var id = btn.getAttribute("data-tiktok");
      if (!/^\d+$/.test(id)) return;
      var box = btn.closest(".vid-media");
      var frame = d.createElement("iframe");
      frame.src = "https://www.tiktok.com/player/v1/" + id + "?autoplay=1&rel=0&music_info=0&description=0";
      frame.title = btn.getAttribute("data-title") || "TikTok video";
      frame.setAttribute("allow", "autoplay; fullscreen; encrypted-media; picture-in-picture");
      frame.setAttribute("allowfullscreen", "");
      box.textContent = "";
      box.appendChild(frame);
      frame.focus();
    });
  });

  // Copy buttons (email address, inquiry template)
  Array.prototype.forEach.call(d.querySelectorAll("[data-copy]"), function (btn) {
    if (!navigator.clipboard) return;
    btn.hidden = false;
    btn.addEventListener("click", function () {
      var src = btn.getAttribute("data-copy-from");
      var text = src ? (d.getElementById(src) || {}).textContent : btn.getAttribute("data-copy");
      var status = d.getElementById(btn.getAttribute("data-status"));
      navigator.clipboard.writeText(text || "").then(function () {
        if (status) {
          status.textContent = btn.getAttribute("data-done") || "Copied.";
          setTimeout(function () { status.textContent = ""; }, 2500);
        }
      });
    });
  });

  // Events flip to "Past event" once they are over.
  Array.prototype.forEach.call(d.querySelectorAll("[data-event-end]"), function (el) {
    var end = Date.parse(el.getAttribute("data-event-end"));
    if (!isNaN(end) && Date.now() > end) {
      el.textContent = el.getAttribute("data-past-label") || "Past event";
      el.classList.add("is-past");
    }
  });
})();
