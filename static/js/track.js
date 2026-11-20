// MobiPrice — Order Tracking Interactive Module
document.addEventListener('DOMContentLoaded', () => {
  const trackModal = document.getElementById('track-modal');
  const btnOpenDesktop = document.getElementById('btn-open-track-modal');
  const btnOpenMobile = document.getElementById('btn-open-track-mobile');
  const btnClose = document.getElementById('btn-close-track-modal');

  const trackForm = document.getElementById('track-order-form');
  const trackInput = document.getElementById('track-order-input');
  const btnSubmit = document.getElementById('btn-submit-track');
  const errorBox = document.getElementById('track-error-msg');
  const resultBox = document.getElementById('track-result-box');

  if (!trackModal) return;

  function openTrackModal(prefillCode) {
    trackModal.classList.add('is-open');
    trackModal.setAttribute('aria-hidden', 'false');
    document.body.classList.add('modal-open');

    if (prefillCode && trackInput) {
      trackInput.value = prefillCode.replace('#', '').trim();
      submitTracking(trackInput.value);
    } else if (trackInput) {
      setTimeout(() => trackInput.focus(), 100);
    }
  }

  function closeTrackModal() {
    trackModal.classList.remove('is-open');
    trackModal.setAttribute('aria-hidden', 'true');
    document.body.classList.remove('modal-open');
    if (errorBox) {
      errorBox.classList.add('hidden');
      errorBox.textContent = '';
    }
  }

  if (btnOpenDesktop) {
    btnOpenDesktop.addEventListener('click', () => openTrackModal());
  }

  if (btnOpenMobile) {
    btnOpenMobile.addEventListener('click', () => openTrackModal());
  }

  if (btnClose) {
    btnClose.addEventListener('click', closeTrackModal);
  }

  // Close when clicking backdrop
  trackModal.addEventListener('click', (e) => {
    if (e.target === trackModal) {
      closeTrackModal();
    }
  });

  // Close on Escape key
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && trackModal.classList.contains('is-open')) {
      closeTrackModal();
    }
  });

  // Expose global helper so order confirmation modal can trigger tracking directly
  window.openOrderTracking = openTrackModal;

  // Track Form submission
  if (trackForm) {
    trackForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const code = trackInput.value.trim();
      if (!code) return;
      submitTracking(code);
    });
  }

  const lang = document.documentElement.lang || 'uz';
  const trackText = {
    uz: {
      notFound: 'Buyurtma topilmadi',
      error: 'Xatolik yuz berdi',
      currency: " so'm",
    },
    ru: {
      notFound: 'Заказ не найден',
      error: 'Произошла ошибка',
      currency: ' сум',
    },
    en: {
      notFound: 'Order not found',
      error: 'An error occurred',
      currency: ' UZS',
    },
  }[lang] || {
    notFound: 'Buyurtma topilmadi',
    error: 'Xatolik yuz berdi',
    currency: " so'm",
  };

  async function submitTracking(code) {
    const btnText = btnSubmit.querySelector('.btn-text');
    const btnSpinner = btnSubmit.querySelector('.btn-spinner');

    if (errorBox) {
      errorBox.classList.add('hidden');
      errorBox.textContent = '';
    }
    if (resultBox) {
      resultBox.classList.add('hidden');
    }

    if (btnText && btnSpinner) {
      btnText.classList.add('hidden');
      btnSpinner.classList.remove('hidden');
      btnSubmit.disabled = true;
    }

    try {
      const clean = encodeURIComponent(code.replace('#', '').trim());
      const res = await fetch(`/api/orders/track/?order_id=${clean}&lang=${lang}`);
      const data = await res.json();

      if (!res.ok || !data.found) {
        throw new Error(data.error || trackText.notFound);
      }

      renderTrackingResult(data);
    } catch (err) {
      if (errorBox) {
        errorBox.textContent = err.message || trackText.error;
        errorBox.classList.remove('hidden');
      }
    } finally {
      if (btnText && btnSpinner) {
        btnText.classList.remove('hidden');
        btnSpinner.classList.add('hidden');
        btnSubmit.disabled = false;
      }
    }
  }

  function renderTrackingResult(order) {
    if (!resultBox) return;

    document.getElementById('track-res-id').textContent = `#${order.order_id}`;
    document.getElementById('track-res-device').textContent = order.device_model;

    const pill = document.getElementById('track-res-pill');
    pill.textContent = order.status_display;
    pill.className = 'track-status-pill';
    if (order.status === 'ready' || order.status === 'completed') {
      pill.classList.add('status-ready');
    } else if (order.status === 'cancelled') {
      pill.classList.add('status-cancelled');
    } else if (order.status === 'pending_location') {
      pill.classList.add('status-pending');
    }

    document.getElementById('track-res-client').textContent = order.client_masked || '-';
    document.getElementById('track-res-service').textContent = order.issue_title || '-';

    const priceEl = document.getElementById('track-res-price');
    const displayPrice = order.final_total_uzs != null ? order.final_total_uzs : order.price_uzs;
    if (displayPrice != null) {
      let priceStr = `${Number(displayPrice).toLocaleString('uz-UZ')}${trackText.currency}`;
      if (order.delivery_fee_uzs != null && order.delivery_fee_uzs > 0 && order.distance_km != null) {
        priceStr += ` (+${Number(order.delivery_fee_uzs).toLocaleString('uz-UZ')} / ${Number(order.distance_km).toFixed(1)} km)`;
      }
      priceEl.textContent = priceStr;
    } else {
      priceEl.textContent = '-';
    }

    document.getElementById('track-res-date').textContent = order.created_at || '-';

    // Update Stepper
    const currentStep = typeof order.current_step === 'number' ? order.current_step : 1;
    const steps = resultBox.querySelectorAll('.stepper-step');
    const lines = resultBox.querySelectorAll('.stepper-line');

    steps.forEach((stepEl) => {
      const stepNum = parseInt(stepEl.getAttribute('data-step'), 10);
      stepEl.classList.remove('completed', 'active');
      if (currentStep > 0) {
        if (stepNum < currentStep) {
          stepEl.classList.add('completed');
        } else if (stepNum === currentStep) {
          stepEl.classList.add('active');
        }
      }
    });

    lines.forEach((lineEl) => {
      const lineNum = parseInt(lineEl.getAttribute('data-line'), 10);
      lineEl.classList.remove('completed');
      if (currentStep > 0 && lineNum < currentStep) {
        lineEl.classList.add('completed');
      }
    });

    resultBox.classList.remove('hidden');
  }
});
