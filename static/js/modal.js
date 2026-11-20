// MobiPrice — Order Booking Modal Module (Telegram Auth Gated + Location & Courier Flows)
(function () {
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

  function getCsrfToken(formEl) {
    const fromCookie = getCookie('csrftoken');
    if (fromCookie) return fromCookie;
    const input = formEl
      ? formEl.querySelector('input[name="csrfmiddlewaretoken"]')
      : document.querySelector('input[name="csrfmiddlewaretoken"]');
    return input ? input.value : '';
  }

  document.addEventListener('DOMContentLoaded', () => {
    const modal = document.getElementById('order-modal');
    const modalClose = document.getElementById('modal-close');
    const modalModelDetail = document.getElementById('modal-model-detail');
    const orderForm = document.getElementById('order-form');
    const modalAlert = document.getElementById('modal-alert');
    const submitBtn = orderForm ? orderForm.querySelector('button[type="submit"]') : null;
    const origBtnText = submitBtn ? submitBtn.textContent : '';

    const resultInService = document.getElementById('order-result-in-service');
    const resultCourier = document.getElementById('order-result-courier');

    const serviceTitleEl = document.getElementById('order-service-title');
    const serviceIdEl = document.getElementById('order-service-id');
    const serviceMsgEl = document.getElementById('order-service-message');
    const shopAddressEl = document.getElementById('order-shop-address');
    const shopGoogleLink = document.getElementById('order-shop-google-maps');
    const shopYandexLink = document.getElementById('order-shop-yandex-maps');
    const btnTrackService = document.getElementById('btn-track-service-order');

    const courierTitleEl = document.getElementById('order-courier-title');
    const courierIdEl = document.getElementById('order-courier-id');
    const courierMsgEl = document.getElementById('order-courier-message');
    const courierBotLink = document.getElementById('order-courier-bot-link');
    const courierBotLabel = document.getElementById('order-courier-bot-label');
    const btnTrackCourier = document.getElementById('btn-track-courier-order');

    let lastCreatedOrderId = '';

    const lang = document.documentElement.lang || 'uz';
    const messages = {
      uz: {
        sending: "Yuborilmoqda...",
        serviceTitle: "Buyurtmangiz qabul qilindi!",
        serviceDesc: "Arizangiz ustalarimizga yuborildi. Quyidagi manzil orqali servis markazimizga kelishingiz mumkin:",
        courierTitle: "Lokatsiyani botga yuboring",
        courierDesc: "Kuryer narxini masofa asosida aniq hisoblash va buyurtmani tasdiqlash uchun Telegram botga o'tib lokatsiyangizni yuboring.",
        courierBtn: "Botga o'tib lokatsiya yuborish",
        trackBtn: "Holatni kuzatish →",
        errorFallback: "Xatolik yuz berdi.",
        networkError: "Server bilan aloqa uzildi. Iltimos telefon orqali bog'laning.",
      },
      ru: {
        sending: "Отправка...",
        serviceTitle: "Заявка принята!",
        serviceDesc: "Ваша заявка отправлена мастерам. Ждем вас по адресу нашего сервисного центра:",
        courierTitle: "Отправьте геолокацию в бот",
        courierDesc: "Перейдите в Telegram-бот и отправьте вашу геолокацию, чтобы рассчитать точную стоимость курьера и подтвердить заказ.",
        courierBtn: "Перейти в бот и отправить локацию",
        trackBtn: "Проверить статус →",
        errorFallback: "Произошла ошибка.",
        networkError: "Ошибка соединения с сервером. Пожалуйста, позвоните нам.",
      },
      en: {
        sending: "Sending...",
        serviceTitle: "Order confirmed!",
        serviceDesc: "Your request has been sent to our technicians. Visit our service center at the address below:",
        courierTitle: "Share location in Telegram bot",
        courierDesc: "Open our Telegram bot and send your location so we can calculate the exact courier fee and confirm your pickup.",
        courierBtn: "Open bot & send location",
        trackBtn: "Track status →",
        errorFallback: "An error occurred.",
        networkError: "Connection error. Please call us directly.",
      },
    };
    const msg = messages[lang] || messages.uz;

    function resetSubmitButton() {
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.textContent = origBtnText;
      }
    }

    function showFormView() {
      if (orderForm) orderForm.classList.remove('hidden');
      if (resultInService) resultInService.classList.add('hidden');
      if (resultCourier) resultCourier.classList.add('hidden');
    }

    function showInServiceResult(data) {
      if (orderForm) orderForm.classList.add('hidden');
      if (resultCourier) resultCourier.classList.add('hidden');
      if (modalAlert) {
        modalAlert.className = 'modal-alert hidden';
        modalAlert.textContent = '';
      }

      lastCreatedOrderId = data.order_id || '';
      if (serviceTitleEl) serviceTitleEl.textContent = msg.serviceTitle;
      if (serviceIdEl) serviceIdEl.textContent = `#${lastCreatedOrderId}`;
      if (serviceMsgEl) serviceMsgEl.textContent = data.message || msg.serviceDesc;
      if (btnTrackService) btnTrackService.textContent = msg.trackBtn;

      const loc = data.shop_location || {};
      if (shopAddressEl && loc.address) shopAddressEl.textContent = loc.address;
      if (shopGoogleLink && loc.google_maps_url) shopGoogleLink.href = loc.google_maps_url;
      if (shopYandexLink && loc.yandex_maps_url) shopYandexLink.href = loc.yandex_maps_url;

      if (resultInService) resultInService.classList.remove('hidden');
    }

    function showCourierResult(data) {
      if (orderForm) orderForm.classList.add('hidden');
      if (resultInService) resultInService.classList.add('hidden');
      if (modalAlert) {
        modalAlert.className = 'modal-alert hidden';
        modalAlert.textContent = '';
      }

      lastCreatedOrderId = data.order_id || '';
      if (courierTitleEl) courierTitleEl.textContent = msg.courierTitle;
      if (courierIdEl) courierIdEl.textContent = `#${lastCreatedOrderId}`;
      if (courierMsgEl) courierMsgEl.textContent = data.message || msg.courierDesc;
      if (courierBotLabel) courierBotLabel.textContent = msg.courierBtn;
      if (btnTrackCourier) btnTrackCourier.textContent = msg.trackBtn;

      if (courierBotLink && data.bot_url) {
        courierBotLink.href = data.bot_url;
      }

      if (resultCourier) resultCourier.classList.remove('hidden');

      // Attempt to open Telegram bot directly; prominent <a> button inside modal guarantees iOS Safari compatibility
      if (data.bot_url) {
        try {
          window.open(data.bot_url, '_blank', 'noopener,noreferrer');
        } catch (openErr) {
          console.warn('Popup blocked, user can tap bot link inside modal:', openErr);
        }
      }
    }

    function openModal() {
      if (!modal) return;
      if (window.mobiAuth && !window.mobiAuth.isAuthenticated()) {
        window.mobiAuth.openLoginModal('order');
        return;
      }

      resetSubmitButton();
      showFormView();
      if (orderForm) orderForm.reset();

      const state = window.mobiState || {};
      const detailStr = `${state.phoneName || state.modelName || 'Smartfon'} — ${state.comparisonTitle || state.optionTitle || state.issueTitle || 'Servis'}`;
      if (modalModelDetail) modalModelDetail.textContent = detailStr;

      if (modalAlert) {
        modalAlert.className = 'modal-alert hidden';
        modalAlert.textContent = '';
      }

      modal.classList.add('is-open');
      modal.setAttribute('aria-hidden', 'false');
      document.body.classList.add('modal-open');
    }

    function closeModal() {
      if (!modal) return;
      resetSubmitButton();
      modal.classList.remove('is-open');
      modal.setAttribute('aria-hidden', 'true');
      if (!document.querySelector('.modal-backdrop.is-open, .modal-overlay.is-open')) {
        document.body.classList.remove('modal-open');
      }
    }

    function handleTrackClick() {
      const code = lastCreatedOrderId;
      closeModal();
      if (code && typeof window.openOrderTracking === 'function') {
        window.openOrderTracking(code);
      }
    }

    if (modalClose) modalClose.addEventListener('click', closeModal);
    document.querySelectorAll('[data-order-close]').forEach((btn) => {
      btn.addEventListener('click', closeModal);
    });
    if (btnTrackService) btnTrackService.addEventListener('click', handleTrackClick);
    if (btnTrackCourier) btnTrackCourier.addEventListener('click', handleTrackClick);

    if (modal) {
      modal.addEventListener('click', (e) => {
        if (e.target === modal) closeModal();
      });
    }

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && modal && modal.classList.contains('is-open')) {
        closeModal();
      }
    });

    window.addEventListener('mobi:auth-changed', (e) => {
      if (!e.detail || !e.detail.authenticated) {
        if (modal && modal.classList.contains('is-open')) {
          closeModal();
        }
      }
    });

    if (orderForm) {
      orderForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        if (window.mobiAuth && !window.mobiAuth.isAuthenticated()) {
          closeModal();
          window.mobiAuth.openLoginModal('order');
          return;
        }

        const serviceSelect = document.getElementById('service-type');
        const serviceType = serviceSelect ? serviceSelect.value : 'in_service';
        const state = window.mobiState || {};

        if (submitBtn) {
          submitBtn.disabled = true;
          submitBtn.textContent = msg.sending;
        }
        if (modalAlert) {
          modalAlert.className = 'modal-alert hidden';
          modalAlert.textContent = '';
        }

        try {
          const res = await fetch('/api/orders/submit/', {
            method: 'POST',
            credentials: 'same-origin',
            headers: {
              'Content-Type': 'application/json',
              'X-CSRFToken': getCsrfToken(orderForm),
            },
            body: JSON.stringify({
              phone_id: state.phoneId || state.modelId,
              comparison_id: state.comparisonId || state.optionId,
              service_type: serviceType,
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
            closeModal();
            if (window.mobiAuth) {
              if (typeof window.mobiAuth.refresh === 'function') {
                window.mobiAuth.refresh();
              }
              window.mobiAuth.openLoginModal('order');
            }
            return;
          }

          if (res.ok && data.success) {
            orderForm.reset();
            resetSubmitButton();
            if (data.service_type === 'courier') {
              showCourierResult(data);
            } else {
              showInServiceResult(data);
            }
          } else {
            if (modalAlert) {
              modalAlert.className = 'modal-alert modal-alert-error';
              modalAlert.textContent = data.error || msg.errorFallback;
            }
            resetSubmitButton();
          }
        } catch (err) {
          console.error('Order submission error:', err);
          if (modalAlert) {
            modalAlert.className = 'modal-alert modal-alert-error';
            modalAlert.textContent = msg.networkError;
          }
          resetSubmitButton();
        }
      });
    }

    // Expose open and close globally
    window.mobiModal = {
      open: openModal,
      close: closeModal,
    };
  });
})();
