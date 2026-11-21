// MobiPrice — Authenticated Client Orders Status Module (Auto-loaded + 10-per-page Pagination)
document.addEventListener('DOMContentLoaded', () => {
  const trackModal = document.getElementById('track-modal');
  const modalCard = trackModal ? trackModal.querySelector('.track-modal-card') : null;
  const btnOpenDesktop = document.getElementById('btn-open-track-modal');
  const btnOpenMobile = document.getElementById('btn-open-track-mobile');
  const btnClose = document.getElementById('btn-close-track-modal');
  const btnRefresh = document.getElementById('btn-refresh-my-orders');
  const btnEmptyGoCalc = document.getElementById('btn-empty-go-calc');

  const countBadge = document.getElementById('my-orders-count-badge');
  const loadingBox = document.getElementById('my-orders-loading');
  const errorBox = document.getElementById('track-error-msg');
  const emptyBox = document.getElementById('my-orders-empty');
  const ordersListEl = document.getElementById('my-orders-list');
  const paginationEl = document.getElementById('my-orders-pagination');
  const rangeEl = document.getElementById('my-orders-range');
  const pageNumbersEl = document.getElementById('my-orders-page-numbers');
  const btnPrev = document.getElementById('btn-orders-prev');
  const btnNext = document.getElementById('btn-orders-next');

  if (!trackModal) return;

  const lang = document.documentElement.lang || 'uz';
  const i18n = {
    uz: {
      totalBadge: (n) => `Jami: ${n} ta`,
      rangeLabel: (from, to, total) => `${from}–${to} / ${total} ta buyurtma`,
      currency: " so'm",
      serviceIn: "🏪 Servis markaziga",
      serviceCourier: "🛵 Kuryer orqali",
      priceLabel: "Summa",
      masterLabel: "Usta",
      sendLocationBtn: "📍 Botga lokatsiya yuborish →",
      pendingExpiryHint: (mins) => `⏳ ${mins} daqiqa ichida lokatsiya yuborilmasa avtomatik bekor qilinadi`,
      pendingReopenHint: "Botda holat o'zgarib qolsa ham, shu tugmani qayta bosib davom ettirishingiz mumkin.",
      loadError: "Buyurtmalarni yuklashda xatolik yuz berdi.",
      step1: "Qabul",
      step2: "Diagnostika",
      step3: "Ta'mir",
      step4: "Tayyor",
    },
    ru: {
      totalBadge: (n) => `Всего: ${n}`,
      rangeLabel: (from, to, total) => `${from}–${to} из ${total} заказов`,
      currency: ' сум',
      serviceIn: "🏪 В сервисный центр",
      serviceCourier: "🛵 Через курьера",
      priceLabel: "Сумма",
      masterLabel: "Мастер",
      sendLocationBtn: "📍 Отправить геолокацию в бот →",
      pendingExpiryHint: (mins) => `⏳ Если не отправить локацию за ${mins} мин., заказ отменится автоматически`,
      pendingReopenHint: "Даже если в боте переключился раздел, нажмите кнопку снова для этого заказа.",
      loadError: "Не удалось загрузить список заказов.",
      step1: "Принято",
      step2: "Диагностика",
      step3: "В ремонте",
      step4: "Готов",
    },
    en: {
      totalBadge: (n) => `Total: ${n}`,
      rangeLabel: (from, to, total) => `Showing ${from}–${to} of ${total}`,
      currency: ' UZS',
      serviceIn: "🏪 Service center",
      serviceCourier: "🛵 Courier pickup",
      priceLabel: "Total",
      masterLabel: "Technician",
      sendLocationBtn: "📍 Send location to bot →",
      pendingExpiryHint: (mins) => `⏳ Auto-cancels if location is not sent within ${mins} min`,
      pendingReopenHint: "If your bot state changes accidentally, tap this button again anytime to resume.",
      loadError: "Failed to load your orders.",
      step1: "Received",
      step2: "Diagnostic",
      step3: "Repair",
      step4: "Ready",
    },
  };
  const t = i18n[lang] || i18n.uz;

  let currentPage = 1;
  let totalPages = 1;
  let isLoading = false;
  let highlightOrderCode = '';
  let hasPendingLocationOrders = false;
  let expiryRefreshTimer = null;
  let lastAutoRefreshAt = 0;

  function clearExpiryTimer() {
    if (expiryRefreshTimer) {
      clearTimeout(expiryRefreshTimer);
      expiryRefreshTimer = null;
    }
  }

  function schedulePendingExpiryRefresh(orders) {
    clearExpiryTimer();
    hasPendingLocationOrders = false;
    if (!Array.isArray(orders)) return;

    let minRemainingSec = null;
    orders.forEach((order) => {
      if (order && order.status === 'pending_location') {
        hasPendingLocationOrders = true;
        if (typeof order.location_remaining_seconds === 'number' && order.location_remaining_seconds >= 0) {
          if (minRemainingSec === null || order.location_remaining_seconds < minRemainingSec) {
            minRemainingSec = order.location_remaining_seconds;
          }
        }
      }
    });

    if (hasPendingLocationOrders && minRemainingSec !== null && trackModal.classList.contains('is-open')) {
      const delayMs = Math.max(1500, (minRemainingSec + 2) * 1000);
      if (delayMs <= 3700000) {
        expiryRefreshTimer = setTimeout(() => {
          if (trackModal.classList.contains('is-open')) {
            loadMyOrders(currentPage, { silent: true });
          }
        }, delayMs);
      }
    }
  }

  function escapeHtml(str) {
    return String(str ?? '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function setSectionVisibility(state) {
    if (loadingBox) loadingBox.classList.toggle('hidden', state !== 'loading');
    if (emptyBox) emptyBox.classList.toggle('hidden', state !== 'empty');
    if (ordersListEl) ordersListEl.classList.toggle('hidden', state !== 'list');
    if (errorBox && state !== 'error') {
      errorBox.classList.add('hidden');
      errorBox.textContent = '';
    }
    if (paginationEl && state !== 'list') {
      paginationEl.classList.add('hidden');
    }
  }

  function openTrackModal(highlightCode) {
    if (highlightCode) {
      highlightOrderCode = String(highlightCode).replace('#', '').trim().toUpperCase();
    }

    if (window.mobiAuth && !window.mobiAuth.isAuthenticated()) {
      window.mobiAuth.openLoginModal('orders');
      return;
    }

    document.body.classList.remove('drawer-open');
    trackModal.classList.add('is-open');
    trackModal.setAttribute('aria-hidden', 'false');
    document.body.classList.add('modal-open');

    loadMyOrders(1);
  }

  function closeTrackModal() {
    clearExpiryTimer();
    trackModal.classList.remove('is-open');
    trackModal.setAttribute('aria-hidden', 'true');
    if (!document.querySelector('.modal-backdrop.is-open, .modal-overlay.is-open')) {
      document.body.classList.remove('modal-open');
    }
  }

  function buildStatusPillClass(status) {
    if (status === 'ready' || status === 'completed') return 'track-status-pill status-ready';
    if (status === 'cancelled') return 'track-status-pill status-cancelled';
    if (status === 'pending_location') return 'track-status-pill status-pending';
    return 'track-status-pill';
  }

  function renderOrderCard(order) {
    const cleanId = String(order.order_id || '').toUpperCase();
    const isHighlighted = Boolean(highlightOrderCode && cleanId === highlightOrderCode);
    const step = typeof order.current_step === 'number' ? order.current_step : 1;

    const displayPrice = order.final_total_uzs != null ? order.final_total_uzs : order.price_uzs;
    let priceHtml = '-';
    if (displayPrice != null) {
      priceHtml = `${Number(displayPrice).toLocaleString('uz-UZ')}${escapeHtml(t.currency)}`;
      if (order.delivery_fee_uzs != null && order.delivery_fee_uzs > 0 && order.distance_km != null) {
        priceHtml += ` <span class="my-order-fee-sub">(+${Number(order.delivery_fee_uzs).toLocaleString('uz-UZ')} / ${Number(order.distance_km).toFixed(1)} km)</span>`;
      }
    }

    const serviceBadge = order.service_type === 'courier' ? t.serviceCourier : t.serviceIn;
    const masterRow = order.master_name
      ? `<div class="my-order-meta-chip"><span>👨‍🔧 ${escapeHtml(t.masterLabel)}:</span> <strong>${escapeHtml(order.master_name)}</strong></div>`
      : '';

    const stepsMeta = [
      { num: 1, ico: '📥', label: t.step1 },
      { num: 2, ico: '🔍', label: t.step2 },
      { num: 3, ico: '🔧', label: t.step3 },
      { num: 4, ico: '✅', label: t.step4 },
    ];

    let stepperHtml = '';
    if (order.status !== 'cancelled' && order.status !== 'pending_location') {
      const parts = [];
      stepsMeta.forEach((st, idx) => {
        const cls = step > 0
          ? (st.num < step ? 'stepper-step completed' : (st.num === step ? 'stepper-step active' : 'stepper-step'))
          : 'stepper-step';
        parts.push(`
          <div class="${cls}">
            <div class="step-circle"><span class="step-ico">${st.ico}</span></div>
            <div class="step-label">${escapeHtml(st.label)}</div>
          </div>
        `);
        if (idx < stepsMeta.length - 1) {
          const lineCls = step > 0 && st.num < step ? 'stepper-line completed' : 'stepper-line';
          parts.push(`<div class="${lineCls}"></div>`);
        }
      });
      stepperHtml = `<div class="track-stepper track-stepper-compact">${parts.join('')}</div>`;
    }

    let pendingBotHtml = '';
    if (order.status === 'pending_location' && order.bot_url) {
      const remSec = typeof order.location_remaining_seconds === 'number'
        ? order.location_remaining_seconds
        : null;
      const remMin = remSec !== null ? Math.max(1, Math.ceil(remSec / 60)) : 60;
      pendingBotHtml = `
        <div class="my-order-pending-box">
          <div class="my-order-pending-meta">${escapeHtml(t.pendingExpiryHint(remMin))}</div>
          <a href="${escapeHtml(order.bot_url)}" target="_blank" rel="noopener noreferrer" class="btn-order-pending-bot">${escapeHtml(t.sendLocationBtn)}</a>
          <div class="my-order-pending-hint">${escapeHtml(t.pendingReopenHint)}</div>
        </div>
      `;
    }

    return `
      <article class="my-order-card${isHighlighted ? ' is-highlighted' : ''}">
        <div class="my-order-top">
          <div class="my-order-id-wrap">
            <span class="track-badge-id">#${escapeHtml(order.order_id)}</span>
            <span class="my-order-date">${escapeHtml(order.created_at || '')}</span>
          </div>
          <span class="${buildStatusPillClass(order.status)}">${escapeHtml(order.status_display || order.status)}</span>
        </div>

        <div class="my-order-main">
          <h4 class="my-order-device">${escapeHtml(order.device_model || 'Smartfon')}</h4>
          <p class="my-order-issue">${escapeHtml(order.issue_title || '-')}</p>
        </div>

        <div class="my-order-meta-row">
          <div class="my-order-meta-chip">${escapeHtml(serviceBadge)}</div>
          ${masterRow}
          <div class="my-order-price">
            <span class="my-order-price-label">${escapeHtml(t.priceLabel)}:</span>
            <span class="my-order-price-val">${priceHtml}</span>
          </div>
        </div>

        ${stepperHtml}
        ${pendingBotHtml}
      </article>
    `;
  }

  function buildPageNumbers(current, total) {
    if (total <= 5) {
      return Array.from({ length: total }, (_, i) => i + 1);
    }
    const pages = [1];
    const start = Math.max(2, current - 1);
    const end = Math.min(total - 1, current + 1);
    if (start > 2) pages.push('...');
    for (let p = start; p <= end; p++) pages.push(p);
    if (end < total - 1) pages.push('...');
    pages.push(total);
    return pages;
  }

  function renderPagination(data) {
    if (!paginationEl || !rangeEl || !pageNumbersEl) return;

    const totalCount = Number(data.total_count) || 0;
    const page = Number(data.page) || 1;
    const perPage = Number(data.per_page) || 10;
    totalPages = Number(data.total_pages) || 1;
    currentPage = page;

    if (totalCount === 0) {
      paginationEl.classList.add('hidden');
      return;
    }

    const fromIdx = (page - 1) * perPage + 1;
    const toIdx = Math.min(totalCount, fromIdx + (data.orders ? data.orders.length : 0) - 1);
    rangeEl.textContent = t.rangeLabel(fromIdx, toIdx, totalCount);

    if (btnPrev) {
      btnPrev.disabled = !data.has_previous;
      btnPrev.classList.toggle('hidden', totalPages <= 1);
    }
    if (btnNext) {
      btnNext.disabled = !data.has_next;
      btnNext.classList.toggle('hidden', totalPages <= 1);
    }

    if (totalPages <= 1) {
      pageNumbersEl.innerHTML = '';
      pageNumbersEl.classList.add('hidden');
    } else {
      pageNumbersEl.classList.remove('hidden');
      const items = buildPageNumbers(page, totalPages);
      pageNumbersEl.innerHTML = items.map((item) => {
        if (item === '...') {
          return '<span class="pager-ellipsis" aria-hidden="true">…</span>';
        }
        const activeCls = item === page ? 'btn-pager-num active' : 'btn-pager-num';
        return `<button type="button" class="${activeCls}" data-page="${item}"${item === page ? ' aria-current="page"' : ''}>${item}</button>`;
      }).join('');

      pageNumbersEl.querySelectorAll('.btn-pager-num').forEach((btn) => {
        btn.addEventListener('click', () => {
          const target = parseInt(btn.getAttribute('data-page'), 10);
          if (target && target !== currentPage) {
            loadMyOrders(target);
          }
        });
      });
    }

    paginationEl.classList.remove('hidden');
  }

  async function loadMyOrders(pageNum, options) {
    if (isLoading) return;
    isLoading = true;

    const silent = Boolean(options && options.silent);
    const safePage = Math.max(1, parseInt(pageNum, 10) || 1);
    if (!silent) {
      setSectionVisibility('loading');
    }
    if (btnRefresh) btnRefresh.classList.add('is-spinning');

    try {
      const res = await fetch(
        `/api/orders/my/?page=${encodeURIComponent(safePage)}&lang=${encodeURIComponent(lang)}`,
        {
          method: 'GET',
          credentials: 'same-origin',
          headers: { Accept: 'application/json' },
        }
      );

      let data = {};
      try {
        data = await res.json();
      } catch (_) {
        data = {};
      }

      if (res.status === 401 || data.auth_required) {
        closeTrackModal();
        if (window.mobiAuth) {
          if (typeof window.mobiAuth.refresh === 'function') {
            window.mobiAuth.refresh();
          }
          window.mobiAuth.openLoginModal('orders');
        }
        return;
      }

      if (!res.ok || !data.success) {
        throw new Error(data.error || t.loadError);
      }

      const totalCount = Number(data.total_count) || 0;
      if (countBadge) {
        countBadge.textContent = t.totalBadge(totalCount);
        countBadge.classList.remove('hidden');
      }

      if (!Array.isArray(data.orders) || data.orders.length === 0) {
        schedulePendingExpiryRefresh([]);
        setSectionVisibility('empty');
        return;
      }

      if (ordersListEl) {
        ordersListEl.innerHTML = data.orders.map(renderOrderCard).join('');
      }
      setSectionVisibility('list');
      renderPagination(data);
      schedulePendingExpiryRefresh(data.orders);

      if (!silent && modalCard) {
        modalCard.scrollTo({ top: 0, behavior: 'smooth' });
      }
    } catch (err) {
      if (!silent) {
        setSectionVisibility('error');
        if (errorBox) {
          errorBox.textContent = err.message || t.loadError;
          errorBox.classList.remove('hidden');
        }
      }
    } finally {
      isLoading = false;
      if (btnRefresh) btnRefresh.classList.remove('is-spinning');
    }
  }

  function triggerSilentReturnRefresh() {
    if (!trackModal.classList.contains('is-open') || !hasPendingLocationOrders || isLoading) {
      return;
    }
    const nowMs = Date.now();
    if (nowMs - lastAutoRefreshAt < 2000) return;
    lastAutoRefreshAt = nowMs;
    loadMyOrders(currentPage, { silent: true });
  }

  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') {
      triggerSilentReturnRefresh();
    }
  });
  window.addEventListener('focus', triggerSilentReturnRefresh);

  if (btnOpenDesktop) {
    btnOpenDesktop.addEventListener('click', () => {
      highlightOrderCode = '';
      openTrackModal();
    });
  }

  if (btnOpenMobile) {
    btnOpenMobile.addEventListener('click', () => {
      highlightOrderCode = '';
      openTrackModal();
    });
  }

  if (btnClose) {
    btnClose.addEventListener('click', closeTrackModal);
  }

  if (btnRefresh) {
    btnRefresh.addEventListener('click', () => loadMyOrders(currentPage));
  }

  if (btnPrev) {
    btnPrev.addEventListener('click', () => {
      if (currentPage > 1) loadMyOrders(currentPage - 1);
    });
  }

  if (btnNext) {
    btnNext.addEventListener('click', () => {
      if (currentPage < totalPages) loadMyOrders(currentPage + 1);
    });
  }

  if (btnEmptyGoCalc) {
    btnEmptyGoCalc.addEventListener('click', () => {
      closeTrackModal();
      const calcEl = document.getElementById('calculator');
      if (calcEl) calcEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
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

  // Close immediately on logout
  window.addEventListener('mobi:auth-changed', (e) => {
    if (!e.detail || !e.detail.authenticated) {
      highlightOrderCode = '';
      if (trackModal.classList.contains('is-open')) {
        closeTrackModal();
      }
    }
  });

  // Expose global helper so order confirmation modal & auth resume can open orders list directly
  window.openOrderTracking = openTrackModal;
});
