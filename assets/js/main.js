/* Кофеin — поведение страницы: шапка, мобильное меню, появление секций, просмотр фото. */
(function () {
  "use strict";

  /* ---------- Шапка при скролле ---------- */
  var header = document.querySelector("[data-header]");
  if (header) {
    var onScroll = function () {
      header.classList.toggle("is-stuck", window.scrollY > 40);
    };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
  }

  /* ---------- Появление секций ---------- */
  var reveals = Array.prototype.slice.call(document.querySelectorAll(".reveal"));
  if (reveals.length) {
    if ("IntersectionObserver" in window) {
      var observer = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            observer.unobserve(entry.target);
          }
        });
      }, { rootMargin: "0px 0px -8% 0px", threshold: 0.08 });
      reveals.forEach(function (node) { observer.observe(node); });
    } else {
      reveals.forEach(function (node) { node.classList.add("is-visible"); });
    }
  }

  /* ---------- Мобильное меню ---------- */
  var burger = document.querySelector(".burger");
  var nav = document.querySelector(".nav");

  if (burger && nav) {
    var setNav = function (open) {
      burger.setAttribute("aria-expanded", String(open));
      nav.classList.toggle("is-open", open);
    };

    burger.addEventListener("click", function () {
      setNav(burger.getAttribute("aria-expanded") !== "true");
    });

    nav.addEventListener("click", function (event) {
      if (event.target.closest("a")) setNav(false);
    });

    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape" && nav.classList.contains("is-open")) {
        setNav(false);
        burger.focus();
      }
    });

    window.addEventListener("resize", function () {
      if (window.innerWidth > 860) setNav(false);
    });
  }

  /* ---------- Просмотр фотографий ---------- */
  var lightbox = document.querySelector(".lightbox");
  var items = Array.prototype.slice.call(document.querySelectorAll(".gallery__item"));
  if (!lightbox || !items.length) return;

  var lbImage = lightbox.querySelector(".lightbox__figure img");
  var lbCaption = lightbox.querySelector(".lightbox__caption");
  var closeBtn = lightbox.querySelector(".lightbox__close");
  var prevBtn = lightbox.querySelector(".lightbox__nav--prev");
  var nextBtn = lightbox.querySelector(".lightbox__nav--next");
  var current = 0;
  var lastFocused = null;

  var show = function (index) {
    current = (index + items.length) % items.length;
    var item = items[current];
    lbImage.src = item.getAttribute("data-full");
    lbImage.alt = item.getAttribute("data-caption") || "Фотография кофейни";
    lbCaption.textContent = (item.getAttribute("data-caption") || "") +
      " · " + (current + 1) + " из " + items.length;
  };

  var open = function (index) {
    lastFocused = document.activeElement;
    show(index);
    lightbox.setAttribute("aria-hidden", "false");
    document.body.style.overflow = "hidden";
    closeBtn.focus();
  };

  var close = function () {
    lightbox.setAttribute("aria-hidden", "true");
    document.body.style.overflow = "";
    if (lastFocused) lastFocused.focus();
  };

  items.forEach(function (item, index) {
    item.addEventListener("click", function () { open(index); });
  });

  closeBtn.addEventListener("click", close);
  prevBtn.addEventListener("click", function () { show(current - 1); });
  nextBtn.addEventListener("click", function () { show(current + 1); });

  lightbox.addEventListener("click", function (event) {
    if (event.target === lightbox) close();
  });

  document.addEventListener("keydown", function (event) {
    if (lightbox.getAttribute("aria-hidden") === "true") return;
    if (event.key === "Escape") close();
    if (event.key === "ArrowLeft") show(current - 1);
    if (event.key === "ArrowRight") show(current + 1);
  });
})();
