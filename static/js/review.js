// MobiPrice — Customer Review Submission (Telegram Auth Gated + 24h Anti-Spam)
document.addEventListener('DOMContentLoaded', () => {
  const modal = document.getElementById('review-modal');
  const btnOpen = document.getElementById('btn-open-review-modal');
  const btnClose = document.getElementById('btn-close-review-modal');
  const form = document.getElementById('review-submission-form');
  const btnSubmit = document.getElementById('btn-submit-review');
  const alertBox = document.getElementById('review-alert-msg');
  const reviewsGrid = document.getElementById('reviews-grid');

  if (!modal) return;

  function getCookie(name) {
    if (!document.cookie) return null;
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const c = cookies[i].trim();
      if (c.substring(0, name.length + 1) === `${name}=`) {
        return decodeURIComponent(c.substring(name.length + 1));
      }
    }
    return null;
  }

  function getCsrfToken() {
    const fromCookie = getCookie('csrftoken');
    if (fromCookie) return fromCookie;
    const input = form
      ? form.querySelector('input[name="csrfmiddlewaretoken"]')
      : document.querySelector('input[name="csrfmiddlewaretoken"]');
    return input ? input.value : '';
  }

  function escapeHtml(str) {
    return String(str ?? '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  // 1. Persistent Device Fingerprint generator / retriever
  function getDeviceFingerprint() {
    let fp = localStorage.getItem('mobi_device_fp');
    if (!fp) {
      fp = 'dev_' + Math.random().toString(36).substring(2, 12) + '_' + Date.now().toString(36);
      localStorage.setItem('mobi_device_fp', fp);
    }
    return fp;
  }

  // 2. Modal Open / Close (Gated by Telegram Auth)
  function openReviewModal() {
    if (window.mobiAuth && !window.mobiAuth.isAuthenticated()) {
      window.mobiAuth.openLoginModal('review');
      return;
    }

    modal.classList.add('is-open');
    modal.setAttribute('aria-hidden', 'false');
    document.body.classList.add('modal-open');
    if (alertBox) {
      alertBox.className = 'review-alert hidden';
      alertBox.textContent = '';
    }
    const modelInput = document.getElementById('review-device-model');
    if (modelInput) setTimeout(() => modelInput.focus(), 100);
  }

  function closeReviewModal() {
    modal.classList.remove('is-open');
    modal.setAttribute('aria-hidden', 'true');
    if (!document.querySelector('.modal-backdrop.is-open, .modal-overlay.is-open')) {
      document.body.classList.remove('modal-open');
    }
  }

  if (btnOpen) btnOpen.addEventListener('click', openReviewModal);
  if (btnClose) btnClose.addEventListener('click', closeReviewModal);

  modal.addEventListener('click', (e) => {
    if (e.target === modal) closeReviewModal();
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && modal.classList.contains('is-open')) {
      closeReviewModal();
    }
  });

  window.addEventListener('mobi:auth-changed', (e) => {
    if (!e.detail || !e.detail.authenticated) {
      if (modal.classList.contains('is-open')) {
        closeReviewModal();
      }
    }
  });

  // 3. Interactive Star Rating
  const starBox = document.getElementById('star-rating-box');
  const ratingInput = document.getElementById('review-rating-value');
  const ratingLabel = document.getElementById('star-rating-text');
  const lang = document.documentElement.lang || 'uz';

  const ratingDescriptionsByLang = {
    uz: {
      1: '1 / 5 — Qoniqarsiz',
      2: '2 / 5 — O‘rtacha',
      3: '3 / 5 — Yaxshi',
      4: '4 / 5 — Juda yaxshi',
      5: '5 / 5 — A’lo darajada',
    },
    ru: {
      1: '1 / 5 — Плохо',
      2: '2 / 5 — Средне',
      3: '3 / 5 — Хорошо',
      4: '4 / 5 — Очень хорошо',
      5: '5 / 5 — Отлично',
    },
    en: {
      1: '1 / 5 — Poor',
      2: '2 / 5 — Fair',
      3: '3 / 5 — Good',
      4: '4 / 5 — Very Good',
      5: '5 / 5 — Excellent',
    },
  };
  const ratingDescriptions = ratingDescriptionsByLang[lang] || ratingDescriptionsByLang.uz;

  const uiMessagesByLang = {
    uz: {
      submitError: 'Fikr yuborishda xatolik yuz berdi',
      submitSuccess: 'Fikringiz muvaffaqiyatli saqlandi!',
    },
    ru: {
      submitError: 'Произошла ошибка при отправке отзыва',
      submitSuccess: 'Ваш отзыв успешно сохранен!',
    },
    en: {
      submitError: 'Failed to submit review',
      submitSuccess: 'Your review has been saved successfully!',
    },
  };
  const uiMsg = uiMessagesByLang[lang] || uiMessagesByLang.uz;

  function setStarsVisual(val) {
    if (ratingInput) ratingInput.value = val;
    if (ratingLabel) ratingLabel.textContent = ratingDescriptions[val] || `${val} / 5`;
    if (starBox) {
      starBox.querySelectorAll('.star').forEach((s) => {
        const sVal = parseInt(s.getAttribute('data-val'), 10);
        s.classList.toggle('active', sVal <= val);
      });
    }
  }

  if (starBox) {
    const stars = starBox.querySelectorAll('.star');
    stars.forEach((star) => {
      star.addEventListener('click', () => {
        const val = parseInt(star.getAttribute('data-val'), 10);
        setStarsVisual(val);
      });
    });
  }

  // 4. Form Submission
  if (form) {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();

      if (window.mobiAuth && !window.mobiAuth.isAuthenticated()) {
        closeReviewModal();
        window.mobiAuth.openLoginModal('review');
        return;
      }

      const modelEl = document.getElementById('review-device-model');
      const serviceEl = document.getElementById('review-service-type');
      const commentEl = document.getElementById('review-comment-text');

      const model = modelEl ? modelEl.value.trim() : '';
      const service = serviceEl ? serviceEl.value.trim() : '';
      const comment = commentEl ? commentEl.value.trim() : '';
      const rating = parseInt(ratingInput ? ratingInput.value : 5, 10);
      const fp = getDeviceFingerprint();

      if (!comment) return;

      const btnText = btnSubmit ? btnSubmit.querySelector('.btn-text') : null;
      const btnSpinner = btnSubmit ? btnSubmit.querySelector('.btn-spinner') : null;

      if (alertBox) alertBox.className = 'review-alert hidden';
      if (btnText && btnSpinner && btnSubmit) {
        btnText.classList.add('hidden');
        btnSpinner.classList.remove('hidden');
        btnSubmit.disabled = true;
      }

      try {
        const res = await fetch('/api/reviews/submit/', {
          method: 'POST',
          credentials: 'same-origin',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken(),
          },
          body: JSON.stringify({
            device_model: model,
            service_type: service,
            rating: rating,
            comment: comment,
            device_fingerprint: fp,
            lang: lang,
          }),
        });

        let data = {};
        try {
          data = await res.json();
        } catch (_) {
          data = {};
        }

        if (res.status === 401 || data.auth_required) {
          closeReviewModal();
          if (window.mobiAuth) {
            if (typeof window.mobiAuth.refresh === 'function') {
              window.mobiAuth.refresh();
            }
            window.mobiAuth.openLoginModal('review');
          }
          return;
        }

        if (!res.ok || !data.success) {
          throw new Error(data.error || uiMsg.submitError);
        }

        // Show success alert
        if (alertBox) {
          alertBox.className = 'review-alert alert-success';
          alertBox.textContent = data.message || uiMsg.submitSuccess;
        }

        // Dynamically prepend new review card
        if (reviewsGrid && data.review) {
          const newCard = document.createElement('div');
          newCard.className = 'review-card review-card-new is-revealed';
          const starsText = '★'.repeat(data.review.rating) + '☆'.repeat(5 - data.review.rating);
          newCard.innerHTML = `
            <div class="review-header">
              <div>
                <div class="review-author">${escapeHtml(data.review.client_name)}</div>
                <div class="review-service">${escapeHtml(data.review.device_model)} • ${escapeHtml(data.review.service_type)}</div>
              </div>
              <div class="review-stars">${starsText}</div>
            </div>
            <p class="review-text">"${escapeHtml(data.review.comment)}"</p>
          `;
          reviewsGrid.prepend(newCard);
        }

        form.reset();
        setStarsVisual(5);

        setTimeout(() => {
          closeReviewModal();
        }, 2200);
      } catch (err) {
        if (alertBox) {
          alertBox.className = 'review-alert alert-error';
          alertBox.textContent = err.message || uiMsg.submitError;
        }
      } finally {
        if (btnText && btnSpinner && btnSubmit) {
          btnText.classList.remove('hidden');
          btnSpinner.classList.add('hidden');
          btnSubmit.disabled = false;
        }
      }
    });
  }

  // Expose globally so auth.js can resume pending 'review' action after login
  window.mobiReview = {
    open: openReviewModal,
    close: closeReviewModal,
  };
});
