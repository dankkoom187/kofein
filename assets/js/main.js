/* Кофеin — интерактив лендинга: меню на мобильном и просмотр фотографий. */
(function () {
  "use strict";

  /* ---------- Мобильное меню ---------- */
  var burger = document.querySelector(".burger");
  var nav = document.querySelector(".nav");

  if (burger && nav) {
    burger.addEventListener("click", function () {
      var open = burger.getAttribute("aria-expanded") === "true";
      burger.setAttribute("aria-expanded", String(!open));
      nav.classList.toggle("is-open", !open);
    });

    nav.addEventListener("click", function (event) {
      if (event.target.closest("a")) {
        burger.setAttribute("aria-expanded", "false");
        nav.classList.remove("is-open");
      }
    });

    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape" && nav.classList.contains("is-open")) {
        burger.setAttribute("aria-expanded", "false");
        nav.classList.remove("is-open");
        burger.focus();
      }
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

  function show(index) {
    current = (index + items.length) % items.length;
    var item = items[current];
    lbImage.src = item.getAttribute("data-full");
    lbImage.alt = item.getAttribute("data-caption") || "Фотография кофейни";
    lbCaption.textContent = (item.getAttribute("data-caption") || "") +
      " (" + (current + 1) + " из " + items.length + ")";
  }

  function open(index) {
    lastFocused = document.activeElement;
    show(index);
    lightbox.setAttribute("aria-hidden", "false");
    document.body.style.overflow = "hidden";
    closeBtn.focus();
  }

  function close() {
    lightbox.setAttribute("aria-hidden", "true");
    document.body.style.overflow = "";
    if (lastFocused) lastFocused.focus();
  }

  items.forEach(function (item, index) {
    item.addEventListener("click", function () {
      open(index);
    });
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
