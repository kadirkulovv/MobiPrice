// MobiPrice — 5-Step Interactive Pricing Calculator Module
(function () {
  const currentLang = document.documentElement.lang || 'uz';

  const translations = {
    uz: {
      selectBtn: "Tanlash →",
      btnBook: "Buyurtma berish / Usta band qilish",
      btnPreorder: "Buyurtma qilish (Kutilmoqda)",
      loadingSeries: "Model seriyalari yuklanmoqda...",
      noSeries: "Bu brend bo‘yicha hozircha modellar qo‘shilmagan.",
      loadingPhones: "Telefonlar yuklanmoqda...",
      noPhones: "Ushbu seriyada hozircha telefonlar mavjud emas.",
      loadingIssues: "Muammolar va xizmatlar yuklanmoqda...",
      noIssues: "Ushbu telefon uchun xizmatlar hali kiritilmagan. Ma'lumot uchun qo‘ng‘iroq qiling.",
      loadingOptions: "Narxlar taqqoslanmoqda...",
      noOptions: "Ushbu muammo bo‘yicha hozircha narxlar kiritilmagan. Ma'lumot uchun qo‘ng‘iroq qiling.",
      loadError: "Xatolik yuz berdi. Iltimos qaytadan urinib ko'ring.",
      warranty: "Kafolat:",
      repairTime: "Vaqt:",
      inStock: "Omborda mavjud",
      outOfStock: "Buyurtma asosida",
      comparePrompt: "Narxlarni solishtirish →",
      yearSuffix: " yil",
      currencySuffix: " so'm",
    },
    ru: {
      selectBtn: "Выбрать →",
      btnBook: "Записаться на ремонт / Заказать",
      btnPreorder: "Под заказ (Ожидается)",
      loadingSeries: "Загрузка серий моделей...",
      noSeries: "Для этого бренда пока нет добавленных серий.",
      loadingPhones: "Загрузка телефонов...",
      noPhones: "Для этой серии пока нет добавленных телефонов.",
      loadingIssues: "Загрузка видов ремонта...",
      noIssues: "Для этого телефона виды ремонта пока не указаны.",
      loadingOptions: "Сравнение цен и вариантов...",
      noOptions: "Для этой проблемы цены пока не указаны. Пожалуйста, позвоните нам.",
      loadError: "Произошла ошибка при загрузке данных. Попробуйте еще раз.",
      warranty: "Гарантия:",
      repairTime: "Время:",
      inStock: "В наличии",
      outOfStock: "Под заказ",
      comparePrompt: "Сравнить цены →",
      yearSuffix: " г.",
      currencySuffix: " сум",
    },
    en: {
      selectBtn: "Select →",
      btnBook: "Book Repair / Order Part",
      btnPreorder: "Pre-order (On Order)",
      loadingSeries: "Loading model series...",
      noSeries: "No model series available for this brand yet.",
      loadingPhones: "Loading phones...",
      noPhones: "No phones available in this series yet.",
      loadingIssues: "Loading repair issues...",
      noIssues: "No repair issues listed for this phone yet.",
      loadingOptions: "Comparing prices and options...",
      noOptions: "Prices for this issue are not available yet. Please call us.",
      loadError: "An error occurred while loading data. Please try again.",
      warranty: "Warranty:",
      repairTime: "Time:",
      inStock: "In Stock",
      outOfStock: "On Order",
      comparePrompt: "Compare Prices →",
      yearSuffix: "",
      currencySuffix: " UZS",
    }
  };
  const t = translations[currentLang] || translations.uz;

  function escapeHtml(str) {
    return String(str ?? '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  window.mobiState = {
    currentLang: currentLang,
    brandId: null,
    brandName: '',
    seriesId: null,
    seriesName: '',
    phoneId: null,
    phoneName: '',
    issueId: null,
    issueTitle: '',
    comparisonId: null,
    comparisonTitle: '',
    totalPrice: 0,
  };

  document.addEventListener('DOMContentLoaded', () => {
    const stepItems = document.querySelectorAll('.calc-steps-indicator .step-item');
    const stepContainers = {
      1: document.getElementById('step-1-brands'),
      2: document.getElementById('step-2-series'),
      3: document.getElementById('step-3-phones'),
      4: document.getElementById('step-4-issues'),
      5: document.getElementById('step-5-results'),
    };

    const seriesList = document.getElementById('series-list');
    const phonesList = document.getElementById('phones-list');
    const issuesList = document.getElementById('issues-list');
    const comparisonsGrid = document.getElementById('comparisons-grid');

    const selectedBrandLabel = document.getElementById('selected-brand-label');
    const selectedSeriesLabel = document.getElementById('selected-series-label');
    const selectedPhoneLabel = document.getElementById('selected-phone-label');
    const selectedIssueLabel = document.getElementById('selected-issue-label');

    const backToStep1 = document.getElementById('back-to-step-1');
    const backToStep2 = document.getElementById('back-to-step-2');
    const backToStep3 = document.getElementById('back-to-step-3');
    const backToStep4 = document.getElementById('back-to-step-4');

    function goToStep(stepNum) {
      stepItems.forEach((item) => {
        const itemStep = parseInt(item.getAttribute('data-step'), 10);
        item.classList.remove('active', 'completed');
        if (itemStep < stepNum) {
          item.classList.add('completed');
        } else if (itemStep === stepNum) {
          item.classList.add('active');
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

      const calcElem = document.getElementById('calculator');
      if (calcElem && stepNum > 1) {
        const yOffset = -80;
        const y = calcElem.getBoundingClientRect().top + window.pageYOffset + yOffset;
        window.scrollTo({ top: y, behavior: 'smooth' });
      }
    }

    // Allow clicking completed steps in progress bar to navigate back
    stepItems.forEach((item) => {
      item.addEventListener('click', () => {
        if (!item.classList.contains('completed')) return;
        const targetStep = parseInt(item.getAttribute('data-step'), 10);
        if (targetStep >= 1 && targetStep <= 5) {
          goToStep(targetStep);
        }
      });
    });

    // Step 1: Click Brand -> Load Series
    const brandCards = document.querySelectorAll('.brand-card');
    brandCards.forEach((card) => {
      card.addEventListener('click', () => {
        brandCards.forEach((c) => c.classList.remove('selected'));
        card.classList.add('selected');

        const brandId = card.getAttribute('data-brand-id');
        const brandName = card.getAttribute('data-brand-name');

        window.mobiState.brandId = brandId;
        window.mobiState.brandName = brandName;

        loadSeriesByBrand(brandId, brandName);
      });
    });

    async function loadSeriesByBrand(brandId, brandName) {
      if (!seriesList) return;
      if (selectedBrandLabel) selectedBrandLabel.textContent = brandName;

      seriesList.innerHTML = `
        <div class="calc-state-box">
          <div class="loader-spinner"></div>
          <p class="calc-state-text">${escapeHtml(t.loadingSeries)}</p>
        </div>
      `;
      goToStep(2);

      try {
        const res = await fetch(`/api/series/by-brand/${brandId}/`);
        const data = await res.json();

        if (!data.series || data.series.length === 0) {
          seriesList.innerHTML = `
            <div class="calc-state-box">
              <p class="calc-state-text">${escapeHtml(t.noSeries)}</p>
            </div>
          `;
          return;
        }

        seriesList.innerHTML = data.series.map((s) => `
          <div class="series-card" data-series-id="${escapeHtml(s.id)}" data-series-name="${escapeHtml(s.name)}">
            <div class="series-card-name">${escapeHtml(s.name)}</div>
            <div class="series-arrow">→</div>
          </div>
        `).join('');

        const sCards = seriesList.querySelectorAll('.series-card');
        sCards.forEach((sCard) => {
          sCard.addEventListener('click', () => {
            sCards.forEach((c) => c.classList.remove('selected'));
            sCard.classList.add('selected');
            const sId = sCard.getAttribute('data-series-id');
            const sName = sCard.getAttribute('data-series-name');
            loadPhonesBySeries(sId, sName);
          });
        });
      } catch (err) {
        console.error('Error fetching series:', err);
        seriesList.innerHTML = `
          <div class="calc-state-box calc-state-error">
            <p class="calc-state-text">${escapeHtml(t.loadError)}</p>
          </div>
        `;
      }
    }

    // Step 2: Click Series -> Load Phones
    async function loadPhonesBySeries(seriesId, seriesName) {
      if (!phonesList) return;
      window.mobiState.seriesId = seriesId;
      window.mobiState.seriesName = seriesName;

      if (selectedSeriesLabel) {
        selectedSeriesLabel.textContent = window.mobiState.brandName
          ? `${window.mobiState.brandName} — ${seriesName}`
          : seriesName;
      }

      phonesList.innerHTML = `
        <div class="calc-state-box">
          <div class="loader-spinner"></div>
          <p class="calc-state-text">${escapeHtml(t.loadingPhones)}</p>
        </div>
      `;
      goToStep(3);

      try {
        const res = await fetch(`/api/phones/by-series/${seriesId}/`);
        const data = await res.json();

        if (!data.phones || data.phones.length === 0) {
          phonesList.innerHTML = `
            <div class="calc-state-box">
              <p class="calc-state-text">${escapeHtml(t.noPhones)}</p>
            </div>
          `;
          return;
        }

        phonesList.innerHTML = data.phones.map((p) => `
          <div class="model-duo-card" data-phone-id="${escapeHtml(p.id)}" data-phone-name="${escapeHtml(p.name)}">
            <div class="model-duo-img-wrapper">
              <img src="${escapeHtml(p.image_url)}" alt="${escapeHtml(p.name)}" class="model-duo-img" loading="lazy" onerror="this.onerror=null;this.src='/static/img/models/iphone_16_pro_max.jpg'">
              <div class="model-name-overlay">
                <span class="overlay-brand">${escapeHtml(window.mobiState.brandName || p.brand_name || '')}</span>
                <span class="overlay-title">${escapeHtml(p.name)}</span>
              </div>
            </div>
            <div class="model-duo-content">
              <div class="model-meta">
                <span class="model-year">${p.release_year ? escapeHtml(p.release_year + t.yearSuffix) : ''}</span>
                <button type="button" class="model-select-btn">${escapeHtml(t.selectBtn)}</button>
              </div>
            </div>
          </div>
        `).join('');

        const pCards = phonesList.querySelectorAll('.model-duo-card');
        pCards.forEach((pCard) => {
          pCard.addEventListener('click', () => {
            pCards.forEach((c) => c.classList.remove('selected'));
            pCard.classList.add('selected');
            const pId = pCard.getAttribute('data-phone-id');
            const pName = pCard.getAttribute('data-phone-name');
            selectPhone(pId, pName);
          });
        });
      } catch (err) {
        console.error('Error fetching phones:', err);
        phonesList.innerHTML = `
          <div class="calc-state-box calc-state-error">
            <p class="calc-state-text">${escapeHtml(t.loadError)}</p>
          </div>
        `;
      }
    }

    // Step 3: Select Phone -> Load Issues
    function selectPhone(pId, pName) {
      window.mobiState.phoneId = pId;
      window.mobiState.phoneName = pName;

      if (selectedPhoneLabel) {
        selectedPhoneLabel.textContent = pName;
      }

      loadIssuesByPhone(pId, pName);
    }

    async function loadIssuesByPhone(phoneId) {
      if (!issuesList) return;
      issuesList.innerHTML = `
        <div class="calc-state-box">
          <div class="loader-spinner"></div>
          <p class="calc-state-text">${escapeHtml(t.loadingIssues)}</p>
        </div>
      `;
      goToStep(4);

      try {
        const res = await fetch(`/api/issues/by-phone/${phoneId}/?lang=${currentLang}`);
        const data = await res.json();

        if (!data.issues || data.issues.length === 0) {
          issuesList.innerHTML = `
            <div class="calc-state-box">
              <p class="calc-state-text">${escapeHtml(t.noIssues)}</p>
              <a href="tel:+998909197600" class="btn-primary calc-state-cta">+998 90 919 76 00</a>
            </div>
          `;
          return;
        }

        issuesList.innerHTML = data.issues.map((iss) => `
          <div class="issue-card" data-issue-id="${escapeHtml(iss.id)}" data-issue-title="${escapeHtml(iss.title)}">
            <div class="issue-card-icon">
              <img src="${escapeHtml(iss.icon_svg_url)}" alt="${escapeHtml(iss.title)}" onerror="this.onerror=null;this.src='/static/img/icons/1.svg'">
            </div>
            <div>
              <div class="part-card-title">${escapeHtml(iss.title)}</div>
              <span class="issue-card-sub">${escapeHtml(t.comparePrompt)}</span>
            </div>
          </div>
        `).join('');

        const iCards = issuesList.querySelectorAll('.issue-card');
        iCards.forEach((iCard) => {
          iCard.addEventListener('click', () => {
            iCards.forEach((c) => c.classList.remove('selected'));
            iCard.classList.add('selected');
            const issId = iCard.getAttribute('data-issue-id');
            const issTitle = iCard.getAttribute('data-issue-title');
            selectIssue(issId, issTitle);
          });
        });
      } catch (err) {
        console.error('Error fetching issues:', err);
        issuesList.innerHTML = `
          <div class="calc-state-box calc-state-error">
            <p class="calc-state-text">${escapeHtml(t.loadError)}</p>
          </div>
        `;
      }
    }

    // Step 4: Select Issue -> Load Comparisons
    function selectIssue(issId, issTitle) {
      window.mobiState.issueId = issId;
      window.mobiState.issueTitle = issTitle;

      if (selectedIssueLabel) {
        selectedIssueLabel.textContent = `${window.mobiState.phoneName} — ${issTitle}`;
      }

      loadComparisonsByIssue(issId, issTitle);
    }

    async function loadComparisonsByIssue(issueId) {
      if (!comparisonsGrid) return;
      comparisonsGrid.innerHTML = `
        <div class="calc-state-box">
          <div class="loader-spinner"></div>
          <p class="calc-state-text">${escapeHtml(t.loadingOptions)}</p>
        </div>
      `;
      goToStep(5);

      try {
        const res = await fetch(`/api/comparisons/by-issue/${issueId}/?lang=${currentLang}`);
        const data = await res.json();

        if (!data.options || data.options.length === 0) {
          comparisonsGrid.innerHTML = `
            <div class="calc-state-box">
              <p class="calc-state-text">${escapeHtml(t.noOptions)}</p>
              <a href="tel:+998909197600" class="btn-primary calc-state-cta">+998 90 919 76 00</a>
            </div>
          `;
          return;
        }

        comparisonsGrid.innerHTML = data.options.map((opt) => {
          const isOriginal = opt.quality_type === 'original_service_pack';
          const cardClass = isOriginal ? 'option-card card-original-highlight' : 'option-card';
          const badgeClass = isOriginal ? 'option-badge badge-orig' : 'option-badge';
          const isAvailable = opt.is_in_stock !== false && (opt.quantity === undefined || opt.quantity > 0);
          const stockClass = isAvailable ? 'option-stock in-stock' : 'option-stock out-of-stock';
          const btnText = isAvailable ? t.btnBook : t.btnPreorder;
          const totalPriceVal = opt.total_price_uzs || opt.part_price_uzs || 0;

          let specsHtml = '';
          if (opt.warranty || opt.repair_time) {
            specsHtml = `
              <div class="option-specs">
                ${opt.warranty ? `<div class="spec-row"><span class="spec-label">${escapeHtml(t.warranty)}</span><span class="spec-val highlight-warranty">${escapeHtml(opt.warranty)}</span></div>` : ''}
                ${opt.repair_time ? `<div class="spec-row"><span class="spec-label">${escapeHtml(t.repairTime)}</span><span class="spec-val">${escapeHtml(opt.repair_time)}</span></div>` : ''}
              </div>
            `;
          }

          const descHtml = opt.description
            ? `<p class="option-desc">${escapeHtml(opt.description)}</p>`
            : '';

          const featuresHtml = Array.isArray(opt.features) && opt.features.length > 0
            ? `<ul class="option-features-list">${opt.features.map((f) => `<li><span class="feat-check">✓</span><span>${escapeHtml(f)}</span></li>`).join('')}</ul>`
            : '';

          return `
            <div class="${cardClass}" data-option-id="${escapeHtml(opt.id)}" data-option-title="${escapeHtml(opt.title)}" data-option-price="${escapeHtml(totalPriceVal)}">
              <div>
                <div class="option-header">
                  <span class="${badgeClass}">${escapeHtml(opt.badge || (isOriginal ? 'Original' : 'Kopiya'))}</span>
                  <span class="${stockClass}">${escapeHtml(opt.stock_display || (isAvailable ? t.inStock : t.outOfStock))}</span>
                </div>

                <h3 class="option-title">${escapeHtml(opt.title)}</h3>

                <div class="option-price-box">
                  <div class="price-uzs">${Number(totalPriceVal).toLocaleString('uz-UZ')}${escapeHtml(t.currencySuffix)}</div>
                  <div class="price-usd">~$${escapeHtml(opt.price_usd)} USD</div>
                </div>

                ${specsHtml}
                ${descHtml}
                ${featuresHtml}
              </div>

              <button type="button" class="btn-book-option btn-primary ${isAvailable ? '' : 'btn-out-stock'}">${escapeHtml(btnText)}</button>
            </div>
          `;
        }).join('');

        // Attach booking modal trigger
        comparisonsGrid.querySelectorAll('.option-card').forEach((card) => {
          const btn = card.querySelector('.btn-book-option');
          if (btn) {
            btn.addEventListener('click', (e) => {
              e.stopPropagation();
              const optId = card.getAttribute('data-option-id');
              const optTitle = card.getAttribute('data-option-title');
              const optPrice = card.getAttribute('data-option-price');

              window.mobiState.comparisonId = optId;
              window.mobiState.comparisonTitle = optTitle;
              window.mobiState.totalPrice = optPrice;

              if (window.mobiAuth && !window.mobiAuth.isAuthenticated()) {
                window.mobiAuth.openLoginModal('order');
                return;
              }

              if (window.mobiModal && typeof window.mobiModal.open === 'function') {
                window.mobiModal.open();
              }
            });
          }
        });
      } catch (err) {
        console.error('Error fetching comparisons:', err);
        comparisonsGrid.innerHTML = `
          <div class="calc-state-box calc-state-error">
            <p class="calc-state-text">${escapeHtml(t.loadError)}</p>
          </div>
        `;
      }
    }

    // Step Back Buttons
    if (backToStep1) backToStep1.addEventListener('click', () => goToStep(1));
    if (backToStep2) backToStep2.addEventListener('click', () => goToStep(2));
    if (backToStep3) backToStep3.addEventListener('click', () => goToStep(3));
    if (backToStep4) backToStep4.addEventListener('click', () => goToStep(4));

    // Expose global methods
    window.mobiCalculator = {
      goToStep,
      selectPhone,
      loadSeriesByBrand,
      loadPhonesBySeries,
      loadIssuesByPhone,
      loadComparisonsByIssue,
    };
  });
})();
