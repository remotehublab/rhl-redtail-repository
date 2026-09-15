(function () {
  "use strict";

  function formatDates() {
    document.querySelectorAll("[data-datetime]").forEach(function (element) {
      var date = new Date(element.getAttribute("data-datetime"));
      if (Number.isNaN(date.getTime())) return;

      element.textContent = date.toLocaleString([], {
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit"
      });
      element.setAttribute("data-local-datetime", date.toISOString());
    });

    document.querySelectorAll("[data-date]").forEach(function (element) {
      var date = new Date(element.getAttribute("data-date"));
      if (Number.isNaN(date.getTime())) return;

      element.textContent = date.toLocaleString([], {
        year: "numeric",
        month: "2-digit",
        day: "2-digit"
      });
    });
  }

  function setNavigationState() {
    var navigation = document.querySelector(".navbar-modern");
    if (!navigation) return;

    var update = function () {
      navigation.classList.toggle("is-scrolled", window.scrollY > 12);
    };
    update();
    window.addEventListener("scroll", update, { passive: true });
  }

  function initializeVideoFacades() {
    document.querySelectorAll(".video-facade").forEach(function (button) {
      button.addEventListener("click", function () {
        var videoId = button.getAttribute("data-youtube-id");
        if (!videoId) return;

        var iframe = document.createElement("iframe");
        iframe.className = "video-embed";
        iframe.src = "https://www.youtube-nocookie.com/embed/" + encodeURIComponent(videoId) + "?autoplay=1&rel=0";
        iframe.title = button.getAttribute("data-youtube-title") || "REDTAIL video";
        iframe.allow = "autoplay; encrypted-media; picture-in-picture";
        iframe.allowFullscreen = true;
        button.replaceWith(iframe);
      });
    });
  }

  function initializeSectionNavigation() {
    var rail = document.querySelector(".section-nav");
    var header = document.querySelector(".site-header");
    if (!rail || !header) return;
    var links = Array.from(rail.querySelectorAll('a[href^="#"]'));
    var scheduled = false;
    function update() {
      scheduled = false;
      var height = header.getBoundingClientRect().height;
      document.documentElement.style.setProperty("--rt-header-height", height + "px");
      var sticky = getComputedStyle(rail).position === "sticky";
      var offset = height + (sticky ? rail.getBoundingClientRect().height : 0) + 16;
      document.documentElement.style.scrollPaddingTop = offset + "px";
      var active = null;
      links.forEach(function (link) {
        var section = document.getElementById(link.hash.slice(1));
        if (section && section.getBoundingClientRect().top <= offset + 1) active = link;
      });
      links.forEach(function (link) {
        if (link === active) link.setAttribute("aria-current", "location");
        else link.removeAttribute("aria-current");
      });
    }
    function schedule() {
      if (!scheduled) { scheduled = true; requestAnimationFrame(update); }
    }
    window.addEventListener("scroll", schedule, { passive: true });
    window.addEventListener("resize", schedule);
    if (window.ResizeObserver) {
      var observer = new ResizeObserver(schedule);
      observer.observe(header);
      observer.observe(rail);
    }
    update();
  }

  function describeNewTabs() {
    document.querySelectorAll('a[target="_blank"]').forEach(function (link) {
      var descriptions = (link.getAttribute("aria-describedby") || "").split(/\s+/).filter(Boolean);
      if (descriptions.indexOf("new-tab-description") === -1) descriptions.push("new-tab-description");
      link.setAttribute("aria-describedby", descriptions.join(" "));
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    formatDates();
    setNavigationState();
    initializeVideoFacades();
    initializeSectionNavigation();
    describeNewTabs();
  });
}());
