/**
 * MobiPrice — High-Performance Scroll Reveal Engine
 * Uses native IntersectionObserver with fallback for ultra-smooth 60fps animations.
 */
(() => {
  'use strict';

  function initScrollReveal() {
    // Check for prefers-reduced-motion
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      document.querySelectorAll('[data-reveal], .reveal-on-scroll').forEach(el => {
        el.classList.add('is-revealed');
      });
      return;
    }

    // Auto-decorate standard sections & cards if not already decorated
    const autoTargets = [
      { selector: '.section-header', reveal: 'fade-up', delay: '50' },
      { selector: '.brand-card', reveal: 'zoom-in', stagger: 60 },
      { selector: '.step-head-wrap', reveal: 'fade-up', delay: '50' },
      { selector: '.faq-item', reveal: 'fade-up', stagger: 80 },
      { selector: '.review-card', reveal: 'fade-up', stagger: 100 },
      { selector: '.consultation-card', reveal: 'zoom-in', delay: '100' },
      { selector: '.ba-container', reveal: 'fade-up', delay: '100' },
      { selector: '.search-box-wrapper', reveal: 'fade-up', delay: '150' },
      { selector: 'footer', reveal: 'fade-up', delay: '50' }
    ];

    autoTargets.forEach(target => {
      const elements = document.querySelectorAll(target.selector);
      elements.forEach((el, index) => {
        if (!el.hasAttribute('data-reveal')) {
          el.setAttribute('data-reveal', target.reveal);
          if (target.stagger) {
            const delay = Math.min((index % 6) * target.stagger, 400);
            el.setAttribute('data-delay', delay.toString());
          } else if (target.delay) {
            el.setAttribute('data-delay', target.delay);
          }
        }
      });
    });

    // Setup IntersectionObserver
    const observerOptions = {
      root: null,
      rootMargin: '0px 0px -40px 0px',
      threshold: 0.12
    };

    const observer = new IntersectionObserver((entries, obs) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-revealed');
          // Once revealed, no need to observe again (one-shot smooth entrance)
          obs.unobserve(entry.target);
        }
      });
    }, observerOptions);

    // Observe all targets
    function observeElements() {
      const revealElements = document.querySelectorAll('[data-reveal]:not(.is-revealed), .reveal-on-scroll:not(.is-revealed)');
      revealElements.forEach(el => observer.observe(el));
    }

    observeElements();

    // Re-observe when dynamic items are appended (e.g. calculator steps)
    const mutationObserver = new MutationObserver((mutations) => {
      let shouldScan = false;
      mutations.forEach(m => {
        if (m.addedNodes.length > 0) shouldScan = true;
      });
      if (shouldScan) {
        // Auto-decorate dynamic option cards & step items
        document.querySelectorAll('.option-card, .series-btn, .phone-card, .issue-card').forEach((el, idx) => {
          if (!el.hasAttribute('data-reveal')) {
            el.setAttribute('data-reveal', 'fade-up');
            el.setAttribute('data-delay', Math.min((idx % 6) * 50, 300).toString());
          }
        });
        observeElements();
      }
    });

    mutationObserver.observe(document.body, { childList: true, subtree: true });

    // Expose utility to manually trigger reveal scan
    window.mobiScrollReveal = {
      scan: observeElements
    };
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initScrollReveal);
  } else {
    initScrollReveal();
  }
})();
