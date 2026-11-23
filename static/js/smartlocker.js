(function () {
  "use strict";

  var root = document.documentElement;
  var themeButton = document.getElementById("themeToggle");
  var themeIcon = themeButton ? themeButton.querySelector("use") : null;

  function syncThemeButton() {
    if (!themeButton || !themeIcon) return;
    var isDark = root.getAttribute("data-theme") === "dark";
    themeIcon.setAttribute("href", isDark ? "#i-sun" : "#i-moon");
    themeButton.setAttribute("aria-label", isDark ? "Activar tema claro" : "Activar tema oscuro");
    themeButton.setAttribute("title", isDark ? "Activar tema claro" : "Activar tema oscuro");
  }

  syncThemeButton();

  if (themeButton) {
    themeButton.addEventListener("click", function () {
      var isDark = root.getAttribute("data-theme") !== "dark";
      root.setAttribute("data-theme", isDark ? "dark" : "light");
      try {
        localStorage.setItem("sl-theme", isDark ? "dark" : "light");
      } catch (error) {
        /* Almacenamiento no disponible: el tema sigue funcionando en la sesión. */
      }
      syncThemeButton();
    });
  }

  var shell = document.querySelector(".app-shell");
  var sidebarToggle = document.getElementById("sidebarToggle");
  var sidebarClose = document.getElementById("sidebarClose");
  var backdrop = document.getElementById("sidebarBackdrop");

  function isMobile() {
    return window.innerWidth < 992;
  }

  function syncToggle() {
    if (!sidebarToggle || !shell) return;
    var visible = isMobile()
      ? shell.classList.contains("sidebar-open")
      : !shell.classList.contains("sidebar-collapsed");
    sidebarToggle.setAttribute("aria-expanded", visible ? "true" : "false");
    sidebarToggle.setAttribute("aria-label", visible ? "Ocultar menú" : "Mostrar menú");
  }

  function setSidebar(open) {
    if (!shell) return;
    var mobile = isMobile();

    shell.classList.toggle("sidebar-open", mobile && open);
    shell.classList.toggle("sidebar-collapsed", !mobile && !open);
    document.body.classList.toggle("sl-no-scroll", mobile && open);
    syncToggle();
  }

  function toggleSidebar() {
    var visible = isMobile()
      ? shell.classList.contains("sidebar-open")
      : !shell.classList.contains("sidebar-collapsed");
    setSidebar(!visible);
  }

  syncToggle();

  if (sidebarToggle) sidebarToggle.addEventListener("click", toggleSidebar);
  if (sidebarClose) sidebarClose.addEventListener("click", function () { setSidebar(false); });
  if (backdrop) backdrop.addEventListener("click", function () { setSidebar(false); });

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape" && isMobile() && shell.classList.contains("sidebar-open")) {
      setSidebar(false);
    }
  });

  var sidebarLinks = document.querySelectorAll(".sl-sidebar a");
  sidebarLinks.forEach(function (link) {
    link.addEventListener("click", function () {
      if (isMobile()) setSidebar(false);
    });
  });

  window.addEventListener("resize", function () {
    if (!shell) return;
    if (isMobile()) {
      shell.classList.remove("sidebar-collapsed");
    } else {
      shell.classList.remove("sidebar-open");
      document.body.classList.remove("sl-no-scroll");
    }
    syncToggle();
  });
})();
