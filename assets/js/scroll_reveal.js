/*
 * Injected via st.components.v1.html (height=0) which renders inside a
 * sandboxed iframe. Streamlit's own app content lives in the PARENT
 * document, so we reach into window.parent to observe & animate it.
 */
(function () {
  function init() {
    var doc = window.parent.document;

    var attach = function () {
      var targets = doc.querySelectorAll(".reveal:not([data-observed])");
      if (!targets.length) return;

      var io = new IntersectionObserver(
        function (entries) {
          entries.forEach(function (entry) {
            if (entry.isIntersecting) {
              entry.target.classList.add("visible");
              io.unobserve(entry.target);
            }
          });
        },
        { root: null, rootMargin: "0px 0px -8% 0px", threshold: 0.12 }
      );

      targets.forEach(function (el) {
        el.setAttribute("data-observed", "1");
        io.observe(el);
      });
    };

    attach();

    // Streamlit re-renders on interaction; keep watching for newly
    // mounted .reveal nodes so animations still fire after reruns.
    var mo = new MutationObserver(function () {
      attach();
    });
    mo.observe(doc.body, { childList: true, subtree: true });

    // Scroll progress bar
    var scroller =
      doc.querySelector('[data-testid="stAppViewContainer"] section.main') ||
      doc.querySelector('section.main') ||
      doc.scrollingElement ||
      doc.documentElement;

    var updateProgress = function () {
      var bar = doc.getElementById("scroll-progress");
      if (!bar) return;
      var max = scroller.scrollHeight - scroller.clientHeight;
      var pct = max > 0 ? (scroller.scrollTop / max) * 100 : 0;
      bar.style.width = pct + "%";
    };

    scroller.addEventListener("scroll", updateProgress, { passive: true });
    updateProgress();
  }

  if (window.parent && window.parent.document) {
    if (window.parent.document.readyState === "complete") {
      init();
    } else {
      window.parent.addEventListener("load", init);
    }
  }
})();
