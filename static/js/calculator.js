// MobiPrice — 5-Step Interactive Pricing Calculator Module
(function () {
  const currentLang = document.documentElement.lang || 'uz';

  const t = {
    uz: {
      selectBtn: "Tanlash →",
      btnBook: "Buyurtma berish / Usta band qilish",
      loadingSeries: "Model seriyalari yuklanmoqda...",
      noSeries: "Bu brend bo‘yicha hozircha modellar qo‘shilmagan.",
      loadingPhones: "Telefonlar yuklanmoqda...",
      noPhones: "Ushbu seriyada hozircha telefonlar mavjud emas.",
      loadingIssues: "Muammolar va xizmatlar yuklanmoqda...",
      noIssues: "Ushbu telefon uchun xizmatlar hali kiritilmagan. Ma'lumot uchun qo‘ng‘iroq qiling.",
      loadingOptions: "Narxlar taqqoslanmoqda...",
      noOptions: "Ushbu muammo bo‘yicha hozircha narxlar kiritilmagan. Ma'lumot uchun qo‘ng‘iroq qiling.",
      serviceFee: "Usta haqqi:",
      warranty: "Kafolat:",
      repairTime: "Vaqt:",
      inStock: "Mavjud (Omborda)",
      included: "narx ichida",
      comparePrompt: "Narxlarni solishtirish →",
    },
    ru: {
      selectBtn: "Выбрать →",
      btnBook: "Записаться на ремонт / Заказать",
      loadingSeries: "Загрузка серий моделей...",
      noSeries: "Для этого бренда пока нет добавленных серий.",
      loadingPhones: "Загрузка телефонов...",
      noPhones: "Для этой серии пока нет добавленных телефонов.",
      loadingIssues: "Загрузка видов ремонта...",
      noIssues: "Для этого телефона виды ремонта пока не указаны.",
      loadingOptions: "Сравнение цен и вариантов...",
      noOptions: "Для этой проблемы цены пока не указаны. Пожалуйста, позвоните нам.",
      serviceFee: "Работа мастера:",
      warranty: "Гарантия:",
      repairTime: "Время:",
      inStock: "В наличии",
      included: "включено",
      comparePrompt: "Сравнить цены →",
    },
    en: {
      selectBtn: "Select →",
      btnBook: "Book Repair / Order Part",
      loadingSeries: "Loading model series...",
      noSeries: "No model series available for this brand yet.",
      loadingPhones: "Loading phones...",
      noPhones: "No phones available in this series yet.",
      loadingIssues: "Loading repair issues...",
      noIssues: "No repair issues listed for this phone yet.",
      loadingOptions: "Comparing prices and options...",
      noOptions: "Prices for this issue are not available yet. Please call us.",
      serviceFee: "Service fee:",
      warranty: "Warranty:",
      repairTime: "Time:",
      inStock: "In Stock",
      included: "included",
      comparePrompt: "Compare Prices →",
    }
  }[currentLang] || {
    selectBtn: "Tanlash →",
    btnBook: "Buyurtma berish / Usta band qilish",
    loadingSeries: "Model seriyalari yuklanmoqda...",
    noSeries: "Bu brend bo‘yicha hozircha modellar qo‘shilmagan.",
    loadingPhones: "Telefonlar yuklanmoqda...",
    noPhones: "Ushbu seriyada hozircha telefonlar mavjud emas.",
    loadingIssues: "Muammolar va xizmatlar yuklanmoqda...",
    noIssues: "Ushbu telefon uchun xizmatlar hali kiritilmagan. Ma'lumot uchun qo‘ng‘iroq qiling.",
    loadingOptions: "Narxlar taqqoslanmoqda...",
    noOptions: "Ushbu muammo bo‘yicha hozircha narxlar kiritilmagan. Ma'lumot uchun qo‘ng‘iroq qiling.",
    serviceFee: "Usta haqqi:",
    warranty: "Kafolat:",
    repairTime: "Vaqt:",
    inStock: "Mavjud (Omborda)",
    included: "narx ichida",
    comparePrompt: "Narxlarni solishtirish →",
  };

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

      // Smooth scroll to calculator container
      const calcElem = document.getElementById('calculator');
      if (calcElem) {
        const yOffset = -80;
        const y = calcElem.getBoundingClientRect().top + window.pageYOffset + yOffset;
        window.scrollTo({ top: y, behavior: 'smooth' });
      }
    }

    // Step 1: Click Brand -> Load Series
    const brandCards = document.querySelectorAll('.brand-card');
    brandCards.forEach((card) => {
      card.addEventListener('click', () => {
        brandCards.forEach(c => c.classList.remove('selected'));
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
        <div style="grid-column: 1 / -1; text-align: center; padding: 40px; color: var(--text-sub);">
          <div class="loader-spinner" style="margin: 0 auto 12px;"></div>
          ${t.loadingSeries}
        </div>
      `;
      goToStep(2);

      try {
        const res = await fetch(`/api/series/by-brand/${brandId}/`);
        const data = await res.json();

        if (!data.series || data.series.length === 0) {
          seriesList.innerHTML = `
            <div style="grid-column: 1 / -1; text-align: center; padding: 40px; color: var(--text-sub);">
              <p style="font-size: 16px;">${t.noSeries}</p>
            </div>
          `;
          return;
        }

        seriesList.innerHTML = data.series.map((s) => `
          <div class="series-card" data-series-id="${s.id}" data-series-name="${s.name}">
            <div class="series-card-name">${s.name}</div>
            <div class="series-arrow">→</div>
          </div>
        `).join('');

        seriesList.querySelectorAll('.series-card').forEach((sCard) => {
          sCard.addEventListener('click', () => {
            const sId = sCard.getAttribute('data-series-id');
            const sName = sCard.getAttribute('data-series-name');
            loadPhonesBySeries(sId, sName);
          });
        });
      } catch (err) {
        console.error('Error fetching series:', err);
        seriesList.innerHTML = `
          <div style="grid-column: 1 / -1; text-align: center; padding: 30px; color: #ef4444;">
            Xatolik yuz berdi. Iltimos qaytadan urinib ko'ring.
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
        selectedSeriesLabel.textContent = `${window.mobiState.brandName} — ${seriesName}`;
      }

      phonesList.innerHTML = `
        <div style="grid-column: 1 / -1; text-align: center; padding: 40px; color: var(--text-sub);">
          <div class="loader-spinner" style="margin: 0 auto 12px;"></div>
          ${t.loadingPhones}
        </div>
      `;
      goToStep(3);

      try {
        const res = await fetch(`/api/phones/by-series/${seriesId}/`);
        const data = await res.json();

        if (!data.phones || data.phones.length === 0) {
          phonesList.innerHTML = `
            <div style="grid-column: 1 / -1; text-align: center; padding: 40px; color: var(--text-sub);">
              <p style="font-size: 16px;">${t.noPhones}</p>
            </div>
          `;
          return;
        }

        phonesList.innerHTML = data.phones.map((p) => `
          <div class="model-duo-card" data-phone-id="${p.id}" data-phone-name="${p.name}">
            <div class="model-duo-img-wrapper">
              <img src="${p.image_url}" alt="${p.name}" class="model-duo-img" loading="lazy" onerror="this.src='/static/img/models/iphone_16_pro_max.jpg'">
              <div class="model-name-overlay">
                <span class="overlay-brand">${window.mobiState.brandName}</span>
                <span class="overlay-title">${p.name}</span>
              </div>
            </div>
            <div class="model-duo-content">
              <div class="model-meta">
                <span class="model-year">${p.release_year ? p.release_year + ' yil' : ''}</span>
                <button class="model-select-btn">${t.selectBtn}</button>
              </div>
            </div>
          </div>
        `).join('');

        phonesList.querySelectorAll('.model-duo-card').forEach((pCard) => {
          pCard.addEventListener('click', () => {
            const pId = pCard.getAttribute('data-phone-id');
            const pName = pCard.getAttribute('data-phone-name');
            selectPhone(pId, pName);
          });
        });
      } catch (err) {
        console.error('Error fetching phones:', err);
        phonesList.innerHTML = `
          <div style="grid-column: 1 / -1; text-align: center; padding: 30px; color: #ef4444;">
            Xatolik yuz berdi. Iltimos qaytadan urinib ko'ring.
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

    async function loadIssuesByPhone(phoneId, phoneName) {
      if (!issuesList) return;
      issuesList.innerHTML = `
        <div style="grid-column: 1 / -1; text-align: center; padding: 40px; color: var(--text-sub);">
          <div class="loader-spinner" style="margin: 0 auto 12px;"></div>
          ${t.loadingIssues}
        </div>
      `;
      goToStep(4);

      try {
        const res = await fetch(`/api/issues/by-phone/${phoneId}/?lang=${currentLang}`);
        const data = await res.json();

        if (!data.issues || data.issues.length === 0) {
          issuesList.innerHTML = `
            <div style="grid-column: 1 / -1; text-align: center; padding: 40px; color: var(--text-sub);">
              <p style="font-size: 16px;">${t.noIssues}</p>
              <a href="tel:+998909197600" class="btn-primary" style="display: inline-block; margin-top: 14px;">+998 90 919 76 00</a>
            </div>
          `;
          return;
        }

        issuesList.innerHTML = data.issues.map((iss) => `
          <div class="issue-card" data-issue-id="${iss.id}" data-issue-title="${iss.title}">
            <div class="issue-card-icon">
              <img src="${iss.icon_svg_url}" alt="${iss.title}" onerror="this.src='/static/img/icons/1.svg'">
            </div>
            <div>
              <div class="part-card-title">${iss.title}</div>
              <span style="font-size: 12px; color: var(--text-dim);">${t.comparePrompt}</span>
            </div>
          </div>
        `).join('');

        issuesList.querySelectorAll('.issue-card').forEach((iCard) => {
          iCard.addEventListener('click', () => {
            const issId = iCard.getAttribute('data-issue-id');
            const issTitle = iCard.getAttribute('data-issue-title');
            selectIssue(issId, issTitle);
          });
        });
      } catch (err) {
        console.error('Error fetching issues:', err);
        issuesList.innerHTML = `
          <div style="grid-column: 1 / -1; text-align: center; padding: 30px; color: #ef4444;">
            Xatolik yuz berdi.
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

    async function loadComparisonsByIssue(issueId, issueTitle) {
      if (!comparisonsGrid) return;
      comparisonsGrid.innerHTML = `
        <div style="grid-column: 1 / -1; text-align: center; padding: 40px; color: var(--text-sub);">
          <div class="loader-spinner" style="margin: 0 auto 12px;"></div>
          ${t.loadingOptions}
        </div>
      `;
      goToStep(5);

      try {
        const res = await fetch(`/api/comparisons/by-issue/${issueId}/?lang=${currentLang}`);
        const data = await res.json();

        if (!data.options || data.options.length === 0) {
          comparisonsGrid.innerHTML = `
            <div style="grid-column: 1 / -1; text-align: center; padding: 40px; color: var(--text-sub);">
              <p style="font-size: 16px; margin-bottom: 16px;">${t.noOptions}</p>
              <a href="tel:+998909197600" class="btn-primary" style="display: inline-block;">+998 90 919 76 00</a>
            </div>
          `;
          return;
        }

        comparisonsGrid.innerHTML = data.options.map((opt) => {
          const isOriginal = opt.quality_type === 'original_service_pack';
          const cardClass = isOriginal ? 'option-card card-original-highlight' : 'option-card';
          const badgeClass = isOriginal ? 'option-badge badge-orig' : 'option-badge';

          return `
            <div class="${cardClass}" data-option-id="${opt.id}" data-option-title="${opt.title}" data-option-price="${opt.total_price_uzs || opt.part_price_uzs}">
              <div class="option-header">
                <span class="${badgeClass}">${opt.badge || (isOriginal ? 'Original' : 'Kopiya')}</span>
                <span class="option-stock">${t.inStock}</span>
              </div>

              <h3 class="option-title">${opt.title}</h3>

              <div class="option-price-box" style="margin-bottom: 24px; border-bottom: none;">
                <div class="price-uzs">${Number(opt.part_price_uzs || opt.total_price_uzs).toLocaleString('uz-UZ')} so'm</div>
                <div class="price-usd">~$${opt.price_usd} USD</div>
              </div>

              <button class="btn-book-option btn-primary">${t.btnBook}</button>
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

              if (window.mobiModal && typeof window.mobiModal.open === 'function') {
                window.mobiModal.open();
              }
            });
          }
        });

      } catch (err) {
        console.error('Error fetching comparisons:', err);
        comparisonsGrid.innerHTML = `
          <div style="grid-column: 1 / -1; text-align: center; padding: 30px; color: #ef4444;">
            Ma'lumotlarni yuklashda xatolik yuz berdi.
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
