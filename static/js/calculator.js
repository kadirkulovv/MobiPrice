// MobiPrice — Interactive Pricing Calculator Module
(function () {
  const currentLang = document.documentElement.lang || 'uz';

  const t = {
    uz: {
      selectBtn: "Tanlash →",
      btnBook: "Buyurtma berish / Usta band qilish",
      loadingModels: "Modellar yuklanmoqda...",
      noModels: "Bu brend bo‘yicha hozircha modellar qo‘shilmagan.",
      loadingOptions: "Zapchast narxlari yuklanmoqda...",
      noOptions: "Ushbu detal bo‘yicha hozircha narxlar kiritilmagan. Ma'lumot uchun qo‘ng‘iroq qiling.",
      serviceFee: "Usta haqqi:",
      warranty: "Kafolat:",
      repairTime: "Vaqt:",
      inStock: "Mavjud (Omborda)",
      included: "narx ichida",
    },
    ru: {
      selectBtn: "Выбрать →",
      btnBook: "Записаться на ремонт / Заказать",
      loadingModels: "Загрузка моделей...",
      noModels: "Для этого бренда пока нет добавленных моделей.",
      loadingOptions: "Загрузка цен на запчасти...",
      noOptions: "Для этой детали цены пока не указаны. Пожалуйста, позвоните нам.",
      serviceFee: "Работа мастера:",
      warranty: "Гарантия:",
      repairTime: "Время:",
      inStock: "В наличии",
      included: "включено",
    },
    en: {
      selectBtn: "Select →",
      btnBook: "Book Repair / Order Part",
      loadingModels: "Loading models...",
      noModels: "No models available for this brand yet.",
      loadingOptions: "Loading part prices...",
      noOptions: "Prices for this part are not available yet. Please call us.",
      serviceFee: "Service fee:",
      warranty: "Warranty:",
      repairTime: "Time:",
      inStock: "In Stock",
      included: "included",
    }
  }[currentLang] || {
    selectBtn: "Tanlash →",
    btnBook: "Buyurtma berish / Usta band qilish",
    loadingModels: "Modellar yuklanmoqda...",
    noModels: "Bu brend bo‘yicha hozircha modellar qo‘shilmagan.",
    loadingOptions: "Zapchast narxlari yuklanmoqda...",
    noOptions: "Ushbu detal bo‘yicha hozircha narxlar kiritilmagan. Ma'lumot uchun qo‘ng‘iroq qiling.",
    serviceFee: "Usta haqqi:",
    warranty: "Kafolat:",
    repairTime: "Vaqt:",
    inStock: "Mavjud (Omborda)",
    included: "narx ichida",
  };

  window.mobiState = {
    currentLang: currentLang,
    brandId: null,
    brandName: '',
    modelId: null,
    modelName: '',
    categoryId: null,
    categoryName: '',
    optionId: null,
    optionTitle: '',
    totalPrice: 0,
  };

  document.addEventListener('DOMContentLoaded', () => {
    const stepItems = document.querySelectorAll('.calc-steps-indicator .step-item');
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

    const backToStep1 = document.getElementById('back-to-step-1');
    const backToStep2 = document.getElementById('back-to-step-2');
    const backToStep3 = document.getElementById('back-to-step-3');

    function goToStep(stepNum) {
      stepItems.forEach((item) => {
        const itemStep = parseInt(item.getAttribute('data-step'), 10);
        if (itemStep === stepNum) {
          item.classList.add('active');
        } else {
          item.classList.remove('active');
        }
      });

      Object.keys(stepContainers).forEach((k) => {
        const container = stepContainers[k];
        if (!container) return;
        if (parseInt(k, 10) === stepNum) {
          container.classList.remove('hidden');
        } else {
          container.classList.add('hidden');
        }
      });

      // Smooth scroll to calculator header
      const calcElem = document.getElementById('calculator');
      if (calcElem) {
        const yOffset = -80;
        const y = calcElem.getBoundingClientRect().top + window.pageYOffset + yOffset;
        window.scrollTo({ top: y, behavior: 'smooth' });
      }
    }

    // Step 1: Click Brand
    const brandCards = document.querySelectorAll('.brand-card');
    brandCards.forEach((card) => {
      card.addEventListener('click', () => {
        brandCards.forEach(c => c.classList.remove('selected'));
        card.classList.add('selected');

        const brandId = card.getAttribute('data-brand-id');
        const brandName = card.getAttribute('data-brand-name');

        window.mobiState.brandId = brandId;
        window.mobiState.brandName = brandName;

        loadModelsByBrand(brandId, brandName);
      });
    });

    async function loadModelsByBrand(brandId, brandName) {
      if (!modelsList) return;
      modelsList.innerHTML = `
        <div style="grid-column: 1 / -1; text-align: center; padding: 40px; color: var(--text-sub);">
          <div class="loader-spinner" style="margin: 0 auto 12px;"></div>
          ${t.loadingModels}
        </div>
      `;
      goToStep(2);

      try {
        const res = await fetch(`/api/models/by-brand/${brandId}/`);
        const data = await res.json();

        if (!data.models || data.models.length === 0) {
          modelsList.innerHTML = `
            <div style="grid-column: 1 / -1; text-align: center; padding: 40px; color: var(--text-sub);">
              <p style="font-size: 16px;">${t.noModels}</p>
            </div>
          `;
          return;
        }

        modelsList.innerHTML = data.models.map((m) => `
          <div class="model-duo-card" data-model-id="${m.id}" data-model-name="${m.name}">
            <div class="model-duo-img-wrapper">
              <img src="${m.image_url}" alt="${m.name}" class="model-duo-img" loading="lazy" onerror="this.src='/static/img/models/iphone_16_pro_max.jpg'">
              ${m.is_popular ? '<span class="model-popular-badge">Top Model</span>' : ''}
              <div class="model-name-overlay">
                <span class="overlay-brand">${brandName}</span>
                <span class="overlay-title">${m.name}</span>
              </div>
            </div>
            <div class="model-duo-content">
              <div class="model-meta">
                <span class="model-year">${m.release_year ? m.release_year + ' yil' : ''}</span>
                <button class="model-select-btn">${t.selectBtn}</button>
              </div>
            </div>
          </div>
        `).join('');

        // Attach click listeners to loaded model cards
        modelsList.querySelectorAll('.model-duo-card').forEach((mCard) => {
          mCard.addEventListener('click', () => {
            const mId = mCard.getAttribute('data-model-id');
            const mName = mCard.getAttribute('data-model-name');
            selectModel(mId, mName);
          });
        });
      } catch (err) {
        console.error('Error fetching models:', err);
        modelsList.innerHTML = `
          <div style="grid-column: 1 / -1; text-align: center; padding: 30px; color: #ef4444;">
            Xatolik yuz berdi. Iltimos qaytadan urinib ko'ring.
          </div>
        `;
      }
    }

    function selectModel(mId, mName) {
      window.mobiState.modelId = mId;
      window.mobiState.modelName = mName;

      if (selectedModelLabel) {
        selectedModelLabel.textContent = mName;
      }

      goToStep(3);
    }

    // Step 3: Click Part Category
    const partCards = document.querySelectorAll('.part-card');
    partCards.forEach((card) => {
      card.addEventListener('click', () => {
        partCards.forEach(c => c.classList.remove('selected'));
        card.classList.add('selected');

        const catId = card.getAttribute('data-category-id');
        const catName = card.getAttribute('data-category-name');

        selectPart(catId, catName);
      });
    });

    async function selectPart(catId, catName) {
      window.mobiState.categoryId = catId;
      window.mobiState.categoryName = catName;

      if (selectedPartLabel) {
        selectedPartLabel.textContent = `${window.mobiState.modelName} — ${catName}`;
      }

      goToStep(4);
      loadPartOptions(window.mobiState.modelId, catId);
    }

    async function loadPartOptions(modelId, categoryId) {
      if (!optionsGrid) return;
      optionsGrid.innerHTML = `
        <div style="grid-column: 1 / -1; text-align: center; padding: 40px; color: var(--text-sub);">
          <div class="loader-spinner" style="margin: 0 auto 12px;"></div>
          ${t.loadingOptions}
        </div>
      `;

      try {
        const res = await fetch(`/api/parts/options/?model_id=${modelId}&category_id=${categoryId}&lang=${currentLang}`);
        const data = await res.json();

        if (!data.options || data.options.length === 0) {
          optionsGrid.innerHTML = `
            <div style="grid-column: 1 / -1; text-align: center; padding: 40px; color: var(--text-sub);">
              <p style="font-size: 16px; margin-bottom: 16px;">${t.noOptions}</p>
              <a href="tel:+998909197600" class="btn-primary" style="display: inline-block;">+998 90 919 76 00</a>
            </div>
          `;
          return;
        }

        optionsGrid.innerHTML = data.options.map((opt) => {
          const isOriginal = opt.quality_type === 'original_service_pack';
          const cardClass = isOriginal ? 'option-card card-original-highlight' : 'option-card';
          const badgeClass = isOriginal ? 'option-badge badge-orig' : 'option-badge';

          const featuresHtml = (opt.features && opt.features.length)
            ? `<ul class="option-features-list">
                ${opt.features.map(f => `<li><span class="feat-check">✓</span> ${f}</li>`).join('')}
              </ul>`
            : '';

          return `
            <div class="${cardClass}" data-option-id="${opt.id}" data-option-title="${opt.title}" data-option-price="${opt.total_price_uzs}">
              <div class="option-header">
                <span class="${badgeClass}">${opt.badge || opt.quality_display}</span>
                <span class="option-stock">${opt.stock_display || t.inStock}</span>
              </div>

              <h3 class="option-title">${opt.title}</h3>

              <div class="option-price-box">
                <div class="price-uzs">${Number(opt.total_price_uzs).toLocaleString('uz-UZ')} so'm</div>
                <div class="price-usd">~$${opt.price_usd} USD</div>
              </div>

              <div class="option-specs">
                <div class="spec-row">
                  <span class="spec-label">${t.serviceFee}</span>
                  <span class="spec-val">${opt.service_fee_uzs ? Number(opt.service_fee_uzs).toLocaleString('uz-UZ') + " so'm" : t.included}</span>
                </div>
                <div class="spec-row">
                  <span class="spec-label">${t.warranty}</span>
                  <span class="spec-val highlight-warranty">🛡 ${opt.warranty}</span>
                </div>
                <div class="spec-row">
                  <span class="spec-label">${t.repairTime}</span>
                  <span class="spec-val">⏱ ${opt.repair_time}</span>
                </div>
              </div>

              ${opt.description ? `<p class="option-desc">${opt.description}</p>` : ''}
              ${featuresHtml}

              <button class="btn-book-option btn-primary">${t.btnBook}</button>
            </div>
          `;
        }).join('');

        // Attach booking listeners
        optionsGrid.querySelectorAll('.option-card').forEach((card) => {
          const btn = card.querySelector('.btn-book-option');
          if (btn) {
            btn.addEventListener('click', (e) => {
              e.stopPropagation();
              const optId = card.getAttribute('data-option-id');
              const optTitle = card.getAttribute('data-option-title');
              const optPrice = card.getAttribute('data-option-price');

              window.mobiState.optionId = optId;
              window.mobiState.optionTitle = optTitle;
              window.mobiState.totalPrice = optPrice;

              if (window.mobiModal && typeof window.mobiModal.open === 'function') {
                window.mobiModal.open();
              }
            });
          }
        });

      } catch (err) {
        console.error('Error fetching part options:', err);
        optionsGrid.innerHTML = `
          <div style="grid-column: 1 / -1; text-align: center; padding: 30px; color: #ef4444;">
            Ma'lumotlarni yuklashda xatolik yuz berdi.
          </div>
        `;
      }
    }

    // Back Buttons
    if (backToStep1) backToStep1.addEventListener('click', () => goToStep(1));
    if (backToStep2) backToStep2.addEventListener('click', () => goToStep(2));
    if (backToStep3) backToStep3.addEventListener('click', () => goToStep(3));

    // Expose methods globally for search and other modules
    window.mobiCalculator = {
      goToStep,
      selectModel,
      selectPart,
      loadModelsByBrand,
    };
  });
})();
