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

  document.addEventListener("DOMContentLoaded", function () {
    formatDates();
    setNavigationState();
    initializeVideoFacades();
  });
}());
