// MobiPrice — Before & After Interactive Slider Module
document.addEventListener('DOMContentLoaded', () => {
  const baContainer = document.querySelector('.ba-slider-container');
  const baBefore = document.querySelector('.ba-before');
  const baHandle = document.querySelector('.ba-handle');
  const baBeforeImg = document.querySelector('.ba-before-img');
  const baAfterImg = document.querySelector('.ba-image');
  const badgeBefore = document.querySelector('.ba-badge.before');
  const badgeAfter = document.querySelector('.ba-badge.after');

  if (!baContainer || !baBefore || !baHandle || !baBeforeImg) return;

  let isDragging = false;

  // Locks the clipped before image to the container's exact width & height
  function syncDimensions() {
    const rect = baContainer.getBoundingClientRect();
    if (rect.width > 0 && rect.height > 0) {
      baBeforeImg.style.width = `${rect.width}px`;
      baBeforeImg.style.height = `${rect.height}px`;
    }
  }

  // Sync initially, on window resize, and when images finish loading
  syncDimensions();
  window.addEventListener('resize', syncDimensions);
  if (baAfterImg) baAfterImg.addEventListener('load', syncDimensions);
  if (baBeforeImg) baBeforeImg.addEventListener('load', syncDimensions);

  // ResizeObserver for rock-solid precision
  if (window.ResizeObserver) {
    const ro = new ResizeObserver(() => syncDimensions());
    ro.observe(baContainer);
  }

  function updateSlider(clientX) {
    const rect = baContainer.getBoundingClientRect();
    let pos = ((clientX - rect.left) / rect.width) * 100;
    if (pos < 0) pos = 0;
    if (pos > 100) pos = 100;

    baBefore.style.width = `${pos}%`;
    baHandle.style.left = `${pos}%`;

    // Smooth badge visibility handling
    if (badgeBefore) {
      if (pos < 18) {
        badgeBefore.style.opacity = '0';
        badgeBefore.style.transform = 'scale(0.9)';
      } else {
        badgeBefore.style.opacity = '1';
        badgeBefore.style.transform = 'scale(1)';
      }
    }

    if (badgeAfter) {
      if (pos > 82) {
        badgeAfter.style.opacity = '0';
        badgeAfter.style.transform = 'scale(0.9)';
      } else {
        badgeAfter.style.opacity = '1';
        badgeAfter.style.transform = 'scale(1)';
      }
    }
  }

  // Prevent native browser image drag
  baContainer.addEventListener('dragstart', (e) => e.preventDefault());

  // Mouse Events
  baContainer.addEventListener('mousedown', (e) => {
    e.preventDefault();
    isDragging = true;
    updateSlider(e.clientX);
  });

  window.addEventListener('mousemove', (e) => {
    if (!isDragging) return;
    e.preventDefault();
    updateSlider(e.clientX);
  });

  window.addEventListener('mouseup', () => {
    isDragging = false;
  });

  // Touch Events (Mobile)
  baContainer.addEventListener('touchstart', (e) => {
    if (e.touches && e.touches.length > 0) {
      isDragging = true;
      updateSlider(e.touches[0].clientX);
    }
  }, { passive: true });

  window.addEventListener('touchmove', (e) => {
    if (!isDragging || !e.touches || e.touches.length === 0) return;
    updateSlider(e.touches[0].clientX);
  }, { passive: true });

  window.addEventListener('touchend', () => {
    isDragging = false;
  });
  window.addEventListener('touchcancel', () => {
    isDragging = false;
  });
});
