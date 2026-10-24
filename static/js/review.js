// MobiPrice — Customer Review Submission with Anti-Spam (1 IP + 1 Device per 24h)
document.addEventListener('DOMContentLoaded', () => {
  const modal = document.getElementById('review-modal');
  const btnOpen = document.getElementById('btn-open-review-modal');
  const btnClose = document.getElementById('btn-close-review-modal');
  const form = document.getElementById('review-submission-form');
  const btnSubmit = document.getElementById('btn-submit-review');
  const alertBox = document.getElementById('review-alert-msg');
  const reviewsGrid = document.getElementById('reviews-grid');

  if (!modal) return;

  // 1. Persistent Device Fingerprint generator / retriever
  function getDeviceFingerprint() {
    let fp = localStorage.getItem('mobi_device_fp');
    if (!fp) {
      fp = 'dev_' + Math.random().toString(36).substring(2, 12) + '_' + Date.now().toString(36);
      localStorage.setItem('mobi_device_fp', fp);
    }
    return fp;
  }

  // 2. Modal Open / Close
  function openReviewModal() {
    modal.style.display = 'flex';
    modal.setAttribute('aria-hidden', 'false');
    document.body.style.overflow = 'hidden';
    if (alertBox) {
      alertBox.style.display = 'none';
      alertBox.textContent = '';
    }
    const nameInput = document.getElementById('review-client-name');
    if (nameInput) setTimeout(() => nameInput.focus(), 100);
  }

  function closeReviewModal() {
    modal.style.display = 'none';
    modal.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';
  }

  if (btnOpen) btnOpen.addEventListener('click', openReviewModal);
  if (btnClose) btnClose.addEventListener('click', closeReviewModal);

  modal.addEventListener('click', (e) => {
    if (e.target === modal) closeReviewModal();
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && modal.style.display === 'flex') closeReviewModal();
  });

  // 3. Interactive Star Rating
  const starBox = document.getElementById('star-rating-box');
  const ratingInput = document.getElementById('review-rating-value');
  const ratingLabel = document.getElementById('star-rating-text');

  const ratingDescriptions = {
    1: '1 / 5 — Qoniqarsiz',
    2: '2 / 5 — O‘rtacha',
    3: '3 / 5 — Yaxshi',
    4: '4 / 5 — Juda yaxshi',
    5: '5 / 5 — A’lo darajada'
  };

  if (starBox) {
    const stars = starBox.querySelectorAll('.star');
    stars.forEach(star => {
      star.addEventListener('click', () => {
        const val = parseInt(star.getAttribute('data-val'), 10);
        if (ratingInput) ratingInput.value = val;
        if (ratingLabel) ratingLabel.textContent = ratingDescriptions[val] || `${val} / 5`;

        stars.forEach(s => {
          const sVal = parseInt(s.getAttribute('data-val'), 10);
          if (sVal <= val) {
            s.classList.add('active');
          } else {
            s.classList.remove('active');
          }
        });
      });
    });
  }

  // 4. Form Submission
  if (form) {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();

      const name = document.getElementById('review-client-name').value.trim();
      const model = document.getElementById('review-device-model').value.trim();
      const service = document.getElementById('review-service-type').value.trim();
      const comment = document.getElementById('review-comment-text').value.trim();
      const rating = parseInt(ratingInput ? ratingInput.value : 5, 10);
      const lang = document.documentElement.lang || 'uz';
      const fp = getDeviceFingerprint();

      if (!name || !comment) return;

      const btnText = btnSubmit.querySelector('.btn-text');
      const btnSpinner = btnSubmit.querySelector('.btn-spinner');

      if (alertBox) alertBox.style.display = 'none';
      if (btnText && btnSpinner) {
        btnText.style.display = 'none';
        btnSpinner.style.display = 'inline-block';
        btnSubmit.disabled = true;
      }

      try {
        const res = await fetch('/api/reviews/submit/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            client_name: name,
            device_model: model,
            service_type: service,
            rating: rating,
            comment: comment,
            device_fingerprint: fp,
            lang: lang,
          }),
        });

        const data = await res.json();

        if (!res.ok || !data.success) {
          throw new Error(data.error || 'Fikr yuborishda xatolik yuz berdi');
        }

        // Show success alert
        if (alertBox) {
          alertBox.className = 'review-alert alert-success';
          alertBox.textContent = data.message || "Fikringiz muvaffaqiyatli saqlandi!";
          alertBox.style.display = 'block';
        }

        // Dynamically prepend new review card
        if (reviewsGrid && data.review) {
          const newCard = document.createElement('div');
          newCard.className = 'review-card reveal-active';
          newCard.style.animation = 'fadeInUp 0.5s ease forwards';
          const starsText = '★'.repeat(data.review.rating) + '☆'.repeat(5 - data.review.rating);
          newCard.innerHTML = `
            <div class="review-header">
              <div>
                <div class="review-author">${data.review.client_name}</div>
                <div class="review-service">${data.review.device_model} • ${data.review.service_type}</div>
              </div>
              <div class="review-stars">${starsText}</div>
            </div>
            <p class="review-text">"${data.review.comment}"</p>
          `;
          reviewsGrid.prepend(newCard);
        }

        form.reset();

        setTimeout(() => {
          closeReviewModal();
        }, 2200);

      } catch (err) {
        if (alertBox) {
          alertBox.className = 'review-alert alert-error';
          alertBox.textContent = err.message || 'Xatolik yuz berdi';
          alertBox.style.display = 'block';
        }
      } finally {
        if (btnText && btnSpinner) {
          btnText.style.display = 'inline-block';
          btnSpinner.style.display = 'none';
          btnSubmit.disabled = false;
        }
      }
    });
  }
});
