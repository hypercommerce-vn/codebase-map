// HC-AI | ticket: FDD-TOOL-CODEMAP
(function () {
  "use strict";

  var header = document.querySelector("[data-header]");
  if (header) {
    var onScroll = function () {
      if (window.scrollY > 8) header.setAttribute("data-scrolled", "");
      else header.removeAttribute("data-scrolled");
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
  }

  var menuBtn = document.querySelector("[data-menu]");
  var nav = document.querySelector("[data-nav]");
  if (menuBtn && nav) {
    var setMenu = function (open) {
      menuBtn.setAttribute("aria-expanded", open ? "true" : "false");
      menuBtn.setAttribute(
        "aria-label",
        menuBtn.getAttribute(open ? "data-label-close" : "data-label-open")
      );
      if (open) nav.setAttribute("data-open", "");
      else nav.removeAttribute("data-open");
    };
    menuBtn.addEventListener("click", function () {
      var open = menuBtn.getAttribute("aria-expanded") !== "true";
      setMenu(open);
      // The nav comes before the button in the page, so move focus into it;
      // otherwise Tab would skip past the links that just appeared.
      if (open) {
        var first = nav.querySelector("a");
        if (first) first.focus();
      }
    });
    nav.addEventListener("click", function (e) {
      if (e.target.closest("a")) setMenu(false);
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && nav.hasAttribute("data-open")) {
        setMenu(false);
        menuBtn.focus();
      }
    });
  }

  function legacyCopy(text) {
    var area = document.createElement("textarea");
    area.value = text;
    area.setAttribute("readonly", "");
    area.style.position = "fixed";
    area.style.opacity = "0";
    document.body.appendChild(area);
    area.select();
    var ok = false;
    try { ok = document.execCommand("copy"); } catch (e) { ok = false; }
    document.body.removeChild(area);
    return ok ? Promise.resolve() : Promise.reject(new Error("copy failed"));
  }

  function copyText(text) {
    if (navigator.clipboard && window.isSecureContext) {
      return navigator.clipboard.writeText(text).catch(function () {
        return legacyCopy(text);
      });
    }
    return legacyCopy(text);
  }

  // Screen readers hear the result of a copy through this status line.
  var live = document.querySelector("[data-live]");
  var announce = function (text) {
    if (!live) return;
    live.textContent = "";
    window.setTimeout(function () { live.textContent = text; }, 50);
  };

  var showState = function (btn, label, state) {
    btn.textContent = label;
    btn.setAttribute("data-copied", state);
    window.clearTimeout(btn._resetTimer);
    btn._resetTimer = window.setTimeout(function () {
      btn.textContent = btn.getAttribute("data-label");
      btn.removeAttribute("data-copied");
    }, 2400);
  };

  document.querySelectorAll("[data-copy]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var source = document.getElementById(btn.getAttribute("data-copy"));
      if (!source) return;
      copyText(source.textContent.replace(/\s+$/, "")).then(function () {
        showState(btn, btn.getAttribute("data-done"), "done");
        announce(btn.getAttribute("data-done"));
      }).catch(function () {
        // Clipboard blocked: select the text so Ctrl+C / Cmd+C copies it.
        var range = document.createRange();
        range.selectNodeContents(source);
        var selection = window.getSelection();
        selection.removeAllRanges();
        selection.addRange(range);
        showState(btn, btn.getAttribute("data-fail"), "fail");
        if (live) announce(live.getAttribute("data-fail"));
      });
    });
  });

  document.querySelectorAll("[data-tabs]").forEach(function (root) {
    var tabs = Array.prototype.slice.call(root.querySelectorAll('[role="tab"]'));
    var select = function (tab, focus) {
      tabs.forEach(function (t) {
        var on = t === tab;
        t.setAttribute("aria-selected", on ? "true" : "false");
        t.tabIndex = on ? 0 : -1;
        document.getElementById(t.getAttribute("aria-controls")).hidden = !on;
      });
      if (focus) tab.focus();
    };
    tabs.forEach(function (tab, i) {
      tab.addEventListener("click", function () { select(tab, false); });
      tab.addEventListener("keydown", function (e) {
        var next = null;
        if (e.key === "ArrowRight") next = tabs[(i + 1) % tabs.length];
        else if (e.key === "ArrowLeft") next = tabs[(i - 1 + tabs.length) % tabs.length];
        else if (e.key === "Home") next = tabs[0];
        else if (e.key === "End") next = tabs[tabs.length - 1];
        if (next) {
          e.preventDefault();
          select(next, true);
        }
      });
    });
  });

  // The embedded map captures drag and wheel, so it stays inert until the
  // visitor opts in; otherwise scrolling the page past it gets hijacked.
  var demo = document.querySelector("[data-demo]");
  if (demo) {
    var frame = demo.querySelector("iframe");
    var activate = demo.querySelector("[data-demo-activate]");
    var setActive = function (on) {
      demo.classList.toggle("is-active", on);
      frame.tabIndex = on ? 0 : -1;
    };
    activate.addEventListener("click", function () {
      setActive(true);
      frame.focus({ preventScroll: true });
    });
    if ("IntersectionObserver" in window) {
      new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting && demo.classList.contains("is-active")) {
            setActive(false);
          }
        });
      }).observe(demo);
    }
  }
})();
