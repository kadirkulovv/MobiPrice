document.addEventListener('DOMContentLoaded', () => {
  // State
  const state = {
    brandId: null,
    brandName: '',
    modelId: null,
    modelName: '',
    categoryId: null,
    categoryName: '',
    optionId: null,
    optionTitle: '',
  };

  // DOM Elements
  const stepItems = document.querySelectorAll('.step-item');
  const stepContainers = {
    1: document.getElementById('step-1-brands'),
    2: document.getElementById('step-2-models'),
    3: document.getElementById('step-3-parts'),
    4: document.getElementById('step-4-results'),
  };

  const modelsList = document.getElementById('models-list');
  const optionsGrid = document.getElementById('options-grid');
  const selectedModelLabel = document.getElementById('selected-model-label');
  const selectedPartLabel = document.getElementById('selected-part-label');

  // Set Step
  function setStep(stepNum) {
    stepItems.forEach((item) => {
      const step = parseInt(item.dataset.step);
      item.classList.remove('active', 'completed');
      if (step === stepNum) item.classList.add('active');
      else if (step < stepNum) item.classList.add('completed');
    });

    Object.keys(stepContainers).forEach((key) => {
      if (parseInt(key) === stepNum) {
        stepContainers[key].classList.remove('hidden');
      } else {
        stepContainers[key].classList.add('hidden');
      }
    });

    // Smooth scroll to calc
    const calcEl = document.getElementById('calculator');
    if (calcEl && stepNum > 1) {
      calcEl.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  }

  // Step 1: Brand Selection
  document.querySelectorAll('.brand-card').forEach((card) => {
    card.addEventListener('click', async () => {
      state.brandId = card.dataset.brandId;
      state.brandName = card.dataset.brandName;

      document.querySelectorAll('.brand-card').forEach((c) => c.classList.remove('selected'));
      card.classList.add('selected');

      // Fetch models
      modelsList.innerHTML = '<div style="color: var(--text-dim); padding: 20px;">Modellar yuklanmoqda...</div>';
      setStep(2);

      try {
        const res = await fetch(`/api/models/by-brand/${state.brandId}/`);
        const data = await res.json();

        if (data.models && data.models.length > 0) {
          modelsList.innerHTML = '';
          data.models.forEach((m) => {
            const cardEl = document.createElement('div');
            cardEl.className = 'model-card';
            cardEl.innerHTML = `
              <img src="${m.image_url}" alt="${m.name}" class="model-card-bg" onerror="this.src='/static/img/models/iphone_16_pro_max.jpg'">
              <div class="model-card-overlay"></div>
              <div class="model-card-brand-badge">${state.brandName}</div>
              <div class="model-card-info">
                <div class="model-card-name">${m.name}</div>
                <div class="model-card-meta">
                  <span class="model-card-year">${m.release_year} yil</span>
                  <span class="model-card-cta">Tanlash →</span>
                </div>
              </div>
            `;
            cardEl.addEventListener('click', () => {
              state.modelId = m.id;
              state.modelName = m.name;
              selectedModelLabel.textContent = `${state.brandName} ${m.name}`;
              setStep(3);
            });
            modelsList.appendChild(cardEl);
          });
        } else {
          modelsList.innerHTML = '<div style="color: var(--text-dim); padding: 20px;">Bu brend uchun hozircha modellar kiritilmagan.</div>';
        }
      } catch (err) {
        modelsList.innerHTML = '<div style="color: var(--neon-red);">Xatolik yuz berdi. Qayta urinib ko‘ring.</div>';
      }
    });
  });

  // Back buttons
  document.getElementById('back-to-step-1')?.addEventListener('click', () => setStep(1));
  document.getElementById('back-to-step-2')?.addEventListener('click', () => setStep(2));
  document.getElementById('back-to-step-3')?.addEventListener('click', () => setStep(3));

  // Step 3: Part Selection
  document.querySelectorAll('.part-card').forEach((card) => {
    card.addEventListener('click', async () => {
      state.categoryId = card.dataset.categoryId;
      state.categoryName = card.dataset.categoryName;
      selectedPartLabel.textContent = state.categoryName;

      document.querySelectorAll('.part-card').forEach((c) => c.classList.remove('selected'));
      card.classList.add('selected');

      optionsGrid.innerHTML = '<div style="color: var(--text-dim); padding: 30px; text-align: center;">Narxlar hisoblanmoqda...</div>';
      setStep(4);

      try {
        const res = await fetch(`/api/parts/options/?model_id=${state.modelId}&category_id=${state.categoryId}`);
        const data = await res.json();

        if (data.options && data.options.length > 0) {
          optionsGrid.innerHTML = '';
          data.options.forEach((opt, idx) => {
            const isOriginal = opt.quality_type.includes('original');
            const cardEl = document.createElement('div');
            cardEl.className = `option-card ${isOriginal ? 'featured' : ''}`;

            let badgeHtml = '';
            if (opt.badge) {
              const badgeClass = isOriginal ? 'badge-original' : (opt.badge.includes('Optimal') ? 'badge-optimal' : 'badge-budget');
              badgeHtml = `<span class="option-badge ${badgeClass}">${opt.badge}</span>`;
            }

            const featuresList = opt.features.map(f => `<li>${f}</li>`).join('');

            cardEl.innerHTML = `
              ${badgeHtml}
              <div>
                <h3 class="option-title">${opt.title}</h3>
                <div class="option-meta">
                  <span class="option-meta-item">⏱ ${opt.repair_time}</span>
                  <span class="option-meta-item">🛡 ${opt.warranty}</span>
                </div>
                <div class="option-price-box">
                  <div class="option-price-main">${opt.total_price_uzs.toLocaleString()} so'm</div>
                  <div class="option-price-sub">Zapchast: ${opt.part_price_uzs.toLocaleString()} + Usta: ${opt.service_fee_uzs.toLocaleString()} ($${opt.price_usd})</div>
                </div>
                <p class="option-desc">${opt.description}</p>
                <ul class="option-features">${featuresList}</ul>
              </div>
              <button class="btn-book" data-opt-id="${opt.id}" data-opt-title="${opt.title}">
                Buyurtma berish / Usta band qilish
              </button>
            `;
            optionsGrid.appendChild(cardEl);
          });

          // Bind book buttons
          optionsGrid.querySelectorAll('.btn-book').forEach((btn) => {
            btn.addEventListener('click', () => {
              state.optionId = btn.dataset.optId;
              state.optionTitle = btn.dataset.optTitle;
              openModal();
            });
          });
        } else {
          optionsGrid.innerHTML = `
            <div style="grid-column: 1/-1; text-align: center; padding: 40px; color: var(--text-sub);">
              Ushbu model uchun narxlar tez kunda kiritiladi. <br>
              Aniq narxni bilish uchun ustadan konsultatsiya oling.
              <br><br>
              <button class="btn-book" style="max-width: 250px; margin: 0 auto;" id="btn-empty-consult">Ustadan maslahat olish</button>
            </div>
          `;
          document.getElementById('btn-empty-consult')?.addEventListener('click', openModal);
        }
      } catch (err) {
        optionsGrid.innerHTML = '<div style="color: var(--neon-red); text-align: center;">Narxlarni yuklashda xatolik yuz berdi.</div>';
      }
    });
  });

  // Live Search
  const searchInput = document.getElementById('search-model-input');
  const searchDropdown = document.getElementById('search-dropdown');
  let searchTimer;

  searchInput?.addEventListener('input', () => {
    clearTimeout(searchTimer);
    const query = searchInput.value.trim();

    if (query.length < 2) {
      searchDropdown.style.display = 'none';
      return;
    }

    searchTimer = setTimeout(async () => {
      try {
        const res = await fetch(`/api/models/search/?q=${encodeURIComponent(query)}`);
        const data = await res.json();

        if (data.models && data.models.length > 0) {
          searchDropdown.innerHTML = '';
          data.models.forEach((m) => {
            const item = document.createElement('div');
            item.className = 'search-dropdown-item';
            item.innerHTML = `
              <strong>${m.brand_name} ${m.name}</strong>
              <span style="font-size: 12px; color: var(--neon-cyan);">Narxni ko‘rish →</span>
            `;
            item.addEventListener('click', () => {
              state.brandId = m.brand_id;
              state.brandName = m.brand_name;
              state.modelId = m.id;
              state.modelName = m.name;
              selectedModelLabel.textContent = `${m.brand_name} ${m.name}`;
              searchDropdown.style.display = 'none';
              searchInput.value = '';
              setStep(3);
            });
            searchDropdown.appendChild(item);
          });
          searchDropdown.style.display = 'block';
        } else {
          searchDropdown.style.display = 'none';
        }
      } catch (e) {
        searchDropdown.style.display = 'none';
      }
    }, 250);
  });

  document.addEventListener('click', (e) => {
    if (!searchInput?.contains(e.target) && !searchDropdown?.contains(e.target)) {
      if (searchDropdown) searchDropdown.style.display = 'none';
    }
  });

  // Modal
  const modal = document.getElementById('order-modal');
  const modalClose = document.getElementById('modal-close');
  const modalModelDetail = document.getElementById('modal-model-detail');
  const orderForm = document.getElementById('order-form');
  const modalAlert = document.getElementById('modal-alert');

  function openModal() {
    if (modal) {
      modalModelDetail.textContent = `${state.modelName || 'Tanlangan model'} — ${state.optionTitle || state.categoryName || 'Konsultatsiya'}`;
      modal.style.display = 'flex';
      modalAlert.classList.add('hidden');
    }
  }

  function closeModal() {
    if (modal) modal.style.display = 'none';
  }

  modalClose?.addEventListener('click', closeModal);
  modal?.addEventListener('click', (e) => {
    if (e.target === modal) closeModal();
  });

  orderForm?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const clientName = document.getElementById('client-name').value.trim();
    const phoneNumber = document.getElementById('phone-number').value.trim();
    const serviceType = document.getElementById('service-type').value;

    const submitBtn = orderForm.querySelector('button[type="submit"]');
    submitBtn.disabled = true;
    submitBtn.textContent = "Yuborilmoqda...";

    try {
      const res = await fetch('/api/orders/submit/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCookie('csrftoken'),
        },
        body: JSON.stringify({
          client_name: clientName,
          phone_number: phoneNumber,
          model_id: state.modelId,
          option_id: state.optionId,
          service_type: serviceType,
        }),
      });

      const result = await res.json();
      if (result.success) {
        orderForm.innerHTML = `
          <div style="text-align: center; padding: 20px;">
            <div style="font-size: 40px; margin-bottom: 12px;">✅</div>
            <h3 style="font-size: 20px; font-weight: 800; margin-bottom: 8px;">Arizangiz qabul qilindi!</h3>
            <p style="color: var(--neon-cyan); font-weight: 700; margin-bottom: 12px;">Buyurtma kodingiz: #${result.order_id}</p>
            <p style="color: var(--text-sub); font-size: 14px;">Mutaxassisimiz 10 daqiqa ichida siz bilan bog‘lanadi.</p>
          </div>
        `;
      } else {
        modalAlert.textContent = result.error || "Xatolik yuz berdi.";
        modalAlert.classList.remove('hidden');
        submitBtn.disabled = false;
        submitBtn.textContent = "Tasdiqlash va Yuborish";
      }
    } catch (e) {
      modalAlert.textContent = "Aloqa uzildi. Iltimos qayta urinib ko'ring.";
      modalAlert.classList.remove('hidden');
      submitBtn.disabled = false;
      submitBtn.textContent = "Tasdiqlash va Yuborish";
    }
  });

  // Before / After Slider Drag
  const baContainer = document.querySelector('.ba-slider-container');
  const baBefore = document.querySelector('.ba-before');
  const baHandle = document.querySelector('.ba-handle');
  const baBeforeImg = document.querySelector('.ba-before-img');

  if (baContainer && baBefore && baHandle && baBeforeImg) {
    let isDragging = false;

    function syncImageWidth() {
      if (baContainer && baBeforeImg) {
        baBeforeImg.style.width = `${baContainer.offsetWidth}px`;
      }
    }
    syncImageWidth();
    window.addEventListener('resize', syncImageWidth);

    function updateSlider(clientX) {
      const rect = baContainer.getBoundingClientRect();
      let pos = ((clientX - rect.left) / rect.width) * 100;
      if (pos < 5) pos = 5;
      if (pos > 95) pos = 95;

      baBefore.style.width = `${pos}%`;
      baHandle.style.left = `${pos}%`;
    }

    baContainer.addEventListener('mousedown', (e) => {
      isDragging = true;
      updateSlider(e.clientX);
    });

    window.addEventListener('mousemove', (e) => {
      if (isDragging) updateSlider(e.clientX);
    });

    window.addEventListener('mouseup', () => {
      isDragging = false;
    });

    baContainer.addEventListener('touchstart', (e) => {
      isDragging = true;
      updateSlider(e.touches[0].clientX);
    });

    window.addEventListener('touchmove', (e) => {
      if (isDragging) updateSlider(e.touches[0].clientX);
    });

    window.addEventListener('touchend', () => {
      isDragging = false;
    });
  }

  // FAQ Accordion
  document.querySelectorAll('.faq-question').forEach((item) => {
    item.addEventListener('click', () => {
      const parent = item.parentElement;
      parent.classList.toggle('open');
    });
  });

  // CSRF Helper
  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }
});
