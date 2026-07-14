(function () {
  "use strict";

  var deck = document.querySelector(".deck");
  var slides = Array.prototype.slice.call(document.querySelectorAll(".slide"));
  var prevButton = document.getElementById("prevSlide");
  var nextButton = document.getElementById("nextSlide");
  var slideCounter = document.getElementById("slideCounter");

  function clampIndex(index) {
    if (index < 0) {
      return 0;
    }
    if (index >= slides.length) {
      return slides.length - 1;
    }
    return index;
  }

  function indexFromHash() {
    var hash = window.location.hash.replace("#slide-", "");
    var parsed = Number.parseInt(hash, 10);
    if (Number.isNaN(parsed)) {
      return 0;
    }
    return clampIndex(parsed - 1);
  }

  function setSlide(index, shouldUpdateHash) {
    var activeIndex = clampIndex(index);
    slides.forEach(function (slide, slideIndex) {
      var isActive = slideIndex === activeIndex;
      slide.classList.toggle("is-active", isActive);
      slide.setAttribute("aria-hidden", isActive ? "false" : "true");
      slide.setAttribute("data-slide-index", String(slideIndex));
    });

    slideCounter.textContent = String(activeIndex + 1) + " / " + String(slides.length);
    prevButton.disabled = activeIndex === 0;
    nextButton.disabled = activeIndex === slides.length - 1;

    if (shouldUpdateHash) {
      var targetHash = "#slide-" + String(activeIndex + 1);
      if (window.location.hash !== targetHash) {
        history.replaceState(null, "", targetHash);
      }
    }
  }

  function moveBy(delta) {
    setSlide(indexFromHash() + delta, true);
  }

  prevButton.addEventListener("click", function () {
    moveBy(-1);
  });

  nextButton.addEventListener("click", function () {
    moveBy(1);
  });

  window.addEventListener("keydown", function (event) {
    if (event.key === "ArrowRight") {
      event.preventDefault();
      moveBy(1);
    }
    if (event.key === "ArrowLeft") {
      event.preventDefault();
      moveBy(-1);
    }
  });

  window.addEventListener("hashchange", function () {
    setSlide(indexFromHash(), false);
  });

  if (deck !== null) {
    deck.classList.add("is-ready");
  }
  setSlide(indexFromHash(), window.location.hash === "");
}());
