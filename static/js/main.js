(function () {
  "use strict";

  var prefersReduced =
    window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* —— Page enter (class stays for CSS; optional cleanup) —— */
  if (!prefersReduced) {
    document.addEventListener("DOMContentLoaded", function () {
      var t = setTimeout(function () {
        document.body.classList.remove("page-enter");
        clearTimeout(t);
      }, 500);
    });
  } else {
    document.body.classList.remove("page-enter");
  }

  /* —— Button ripple —— */
  document.addEventListener(
    "click",
    function (e) {
      var btn = e.target.closest(".btn");
      if (!btn || btn.disabled) return;
      var rect = btn.getBoundingClientRect();
      var r = document.createElement("span");
      var size = Math.max(rect.width, rect.height);
      r.className = "ripple";
      r.style.width = r.style.height = size + "px";
      r.style.left = e.clientX - rect.left - size / 2 + "px";
      r.style.top = e.clientY - rect.top - size / 2 + "px";
      btn.appendChild(r);
      setTimeout(function () {
        r.remove();
      }, 600);
    },
    false
  );

  /* —— Form loading + progress —— */
  document.querySelectorAll("form[data-loading]").forEach(function (form) {
    var progress = form.querySelector(".form-progress-bar");
    if (!progress) {
      var wrap = document.createElement("div");
      wrap.className = "form-progress-wrap";
      wrap.innerHTML = '<div class="form-progress-bar" aria-hidden="true"></div>';
      form.insertBefore(wrap, form.firstChild);
    }
    form.addEventListener("submit", function () {
      form.classList.add("is-loading");
      var b = form.querySelector('button[type="submit"]');
      if (b) b.disabled = true;
    });
  });

  /* —— Mobile sidebar —— */
  var toggle = document.querySelector("[data-sidebar-toggle]");
  var sidebar = document.querySelector(".sidebar");
  if (toggle && sidebar) {
    toggle.addEventListener("click", function () {
      var open = sidebar.classList.toggle("is-open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
  }

  /* —— Desktop sidebar collapse —— */
  var collapseBtn = document.getElementById("sidebar-collapse");
  if (collapseBtn && sidebar) {
    var key = "ky_sidebar_collapsed";
    try {
      if (localStorage.getItem(key) === "1") {
        sidebar.classList.add("collapsed");
        collapseBtn.setAttribute("aria-pressed", "true");
      }
    } catch (err) {}
    collapseBtn.addEventListener("click", function () {
      var c = sidebar.classList.toggle("collapsed");
      collapseBtn.setAttribute("aria-pressed", c ? "true" : "false");
      try {
        localStorage.setItem(key, c ? "1" : "0");
      } catch (e) {}
    });
  }

  /* —— Language switcher —— */
  var switcher = document.getElementById("lang-switcher");
  var trigger = document.getElementById("lang-trigger");
  var panel = document.getElementById("lang-panel");
  var langForm = document.getElementById("lang-form");
  var langField = document.getElementById("lang-field");

  function closeLang() {
    if (!panel || !trigger) return;
    panel.classList.remove("is-open");
    panel.hidden = true;
    trigger.setAttribute("aria-expanded", "false");
  }

  function openLang() {
    if (!panel || !trigger) return;
    panel.hidden = false;
    requestAnimationFrame(function () {
      panel.classList.add("is-open");
    });
    trigger.setAttribute("aria-expanded", "true");
  }

  if (trigger && panel && langForm && langField) {
    trigger.addEventListener("click", function (e) {
      e.stopPropagation();
      if (panel.classList.contains("is-open")) closeLang();
      else openLang();
    });

    panel.querySelectorAll("button[data-lang]").forEach(function (opt) {
      opt.addEventListener("click", function () {
        var code = opt.getAttribute("data-lang");
        if (!code) return;
        document.body.classList.add("lang-fading");
        langField.value = code;
        setTimeout(function () {
          langForm.submit();
        }, 160);
      });
    });

    document.addEventListener("click", function (e) {
      if (switcher && !switcher.contains(e.target)) closeLang();
    });

    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") closeLang();
    });
  }

  /* —— ClaimSure: drag-drop + live preview —— */
  var dropZone = document.getElementById("claimsure-drop");
  var fileInput = document.getElementById("photo");
  var clientPreview = document.getElementById("claimsure-client-preview");
  var clientPreviewImg = clientPreview ? clientPreview.querySelector("img") : null;

  function showClientPreview(file) {
    if (!file || !file.type.match(/^image\//) || !clientPreview || !clientPreviewImg) return;
    var url = URL.createObjectURL(file);
    clientPreviewImg.src = url;
    clientPreview.hidden = false;
  }

  if (dropZone && fileInput) {
    dropZone.addEventListener("click", function () {
      fileInput.click();
    });

    dropZone.addEventListener("keydown", function (e) {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        fileInput.click();
      }
    });

    ["dragenter", "dragover"].forEach(function (ev) {
      dropZone.addEventListener(ev, function (e) {
        e.preventDefault();
        e.stopPropagation();
        dropZone.classList.add("is-dragover");
      });
    });

    ["dragleave", "drop"].forEach(function (ev) {
      dropZone.addEventListener(ev, function (e) {
        e.preventDefault();
        e.stopPropagation();
        dropZone.classList.remove("is-dragover");
      });
    });

    dropZone.addEventListener("drop", function (e) {
      var f = e.dataTransfer.files && e.dataTransfer.files[0];
      if (f && fileInput) {
        try {
          fileInput.files = e.dataTransfer.files;
        } catch (err1) {
          try {
            var dt = new DataTransfer();
            dt.items.add(f);
            fileInput.files = dt.files;
          } catch (err2) {}
        }
        showClientPreview(f);
      }
    });

    fileInput.addEventListener("change", function () {
      var f = fileInput.files && fileInput.files[0];
      showClientPreview(f);
    });
  }
})();
