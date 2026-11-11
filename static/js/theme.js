(function () {
  var root = document.documentElement;
  var buttons = document.querySelectorAll("[data-set-theme]");

  function apply(mode) {
    root.setAttribute("data-theme", mode);
    buttons.forEach(function (b) {
      b.setAttribute("aria-pressed", b.dataset.setTheme === mode ? "true" : "false");
    });
  }

  var saved = "auto";
  try { saved = localStorage.getItem("findr-theme") || "auto"; } catch (e) {}
  apply(saved);

  buttons.forEach(function (b) {
    b.addEventListener("click", function () {
      apply(b.dataset.setTheme);
      try { localStorage.setItem("findr-theme", b.dataset.setTheme); } catch (e) {}
    });
  });
})();
