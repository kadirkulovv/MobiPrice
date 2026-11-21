// MobiPrice — Read-Only Telegram Authentication (Widget + Bot Deep-Link Fallback)
(function () {
  let currentUser = null;
  let pendingAction = null;
  let pollIntervalId = null;
  let pollInFlight = false;
  let activeDeepLinkToken = null;
  let activeDeepLinkDeadline = 0;

  const lang = document.documentElement.lang || 'uz';
  const i18n = {
    uz: {
      starting: "Havola tayyorlanmoqda...",
      deeplinkBtn: "Telegram Bot orqali kirish",
      waitingBot: "Telegram botda Start bosing va «📱 Telefon raqamni yuborish» tugmasi orqali +998 raqamingizni tasdiqlang...",
      uzOnlyError: "Faqat O'zbekiston (+998) telefon raqamlari orqali kirish mumkin!",
      expired: "Kirish havolasining muddati tugadi. Yangi havola oling.",
      invalidToken: "Kirish havolasi yaroqsiz yoki ishlatilgan. Qayta urinib ko'ring.",
      loginSuccess: "Telegram orqali muvaffaqiyatli kirdingiz!",
      authError: "Telegram orqali kirishda xatolik yuz berdi.",
      networkError: "Server bilan aloqa uzildi. Qaytadan urinib ko'ring.",
      logoutError: "Chiqishda xatolik yuz berdi.",
    },
    ru: {
      starting: "Подготовка ссылки...",
      deeplinkBtn: "Войти через Telegram бота",
      waitingBot: "Нажмите Start в Telegram боте и подтвердите номер +998 кнопкой «📱 Telefon raqamni yuborish»...",
      uzOnlyError: "Доступ разрешен только для номеров Узбекистана (+998)!",
      expired: "Срок действия ссылки истек. Получите новую ссылку.",
      invalidToken: "Ссылка недействительна или уже использована. Попробуйте снова.",
      loginSuccess: "Вы успешно вошли через Telegram!",
      authError: "Ошибка входа через Telegram.",
      networkError: "Ошибка соединения с сервером. Попробуйте еще раз.",
      logoutError: "Ошибка при выходе из аккаунта.",
    },
    en: {
      starting: "Preparing link...",
      deeplinkBtn: "Sign in via Telegram Bot",
      waitingBot: "Press Start in Telegram bot and share your Uzbekistan (+998) number using the button...",
      uzOnlyError: "Only Uzbekistan (+998) phone numbers are allowed to sign in!",
      expired: "Login link has expired. Please generate a new link.",
      invalidToken: "Login link is invalid or already used. Please try again.",
      loginSuccess: "Successfully signed in with Telegram!",
      authError: "Telegram sign-in failed.",
      networkError: "Connection error. Please try again.",
      logoutError: "Failed to log out.",
    },
  };
  const msg = i18n[lang] || i18n.uz;

  function getCookie(name) {
    if (!document.cookie) return null;
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const c = cookies[i].trim();
      if (c.substring(0, name.length + 1) === name + '=') {
        return decodeURIComponent(c.substring(name.length + 1));
      }
    }
    return null;
  }

  function getCsrfToken() {
    const fromCookie = getCookie('csrftoken');
    if (fromCookie) return fromCookie;
    const input = document.querySelector('#auth-modal input[name="csrfmiddlewaretoken"], input[name="csrfmiddlewaretoken"]');
    return input ? input.value : '';
  }

  function hydrateInitialUser() {
    const modal = document.getElementById('auth-modal');
    if (!modal) return;
    if (modal.getAttribute('data-authenticated') === '1') {
      currentUser = {
        id: Number(modal.getAttribute('data-user-id') || 0) || null,
        telegram_id: Number(modal.getAttribute('data-telegram-id') || 0) || null,
        full_name: modal.getAttribute('data-full-name') || '',
        username: modal.getAttribute('data-username') || '',
        phone_number: modal.getAttribute('data-phone-number') || '',
        display_handle: modal.getAttribute('data-display-handle') || '',
        photo_url: modal.getAttribute('data-photo-url') || '',
        initials: modal.getAttribute('data-initials') || 'TG',
      };
    } else {
      currentUser = null;
    }
  }

  function showAuthAlert(text, type) {
    const alertBox = document.getElementById('auth-modal-alert');
    if (!alertBox) return;
    if (!text) {
      alertBox.className = 'auth-alert hidden';
      alertBox.textContent = '';
      return;
    }
    alertBox.className = `auth-alert ${type === 'success' ? 'alert-success' : 'alert-error'}`;
    alertBox.textContent = text;
  }

  function updateAvatarContainer(container, user) {
    if (!container) return;
    const img = container.querySelector('.auth-avatar-img');
    const initialsEl = container.querySelector('.auth-avatar-initials');
    const initials = (user && user.initials) ? user.initials : 'TG';

    if (initialsEl) {
      initialsEl.textContent = initials;
    }

    if (img) {
      if (user && user.photo_url) {
        img.src = user.photo_url;
        img.alt = user.full_name || 'Telegram';
        img.classList.remove('hidden');
        if (initialsEl) initialsEl.classList.add('hidden');
      } else {
        img.removeAttribute('src');
        img.classList.add('hidden');
        if (initialsEl) initialsEl.classList.remove('hidden');
      }
    }
  }

  function syncAuthUI() {
    const btnTopbar = document.getElementById('btn-open-auth-topbar');
    const userTopbar = document.getElementById('auth-user-topbar');
    const btnSidebar = document.getElementById('btn-open-auth-sidebar');
    const userSidebar = document.getElementById('auth-user-sidebar');
    const isAuth = Boolean(currentUser);

    if (btnTopbar) btnTopbar.classList.toggle('hidden', isAuth);
    if (userTopbar) userTopbar.classList.toggle('hidden', !isAuth);
    if (btnSidebar) btnSidebar.classList.toggle('hidden', isAuth);
    if (userSidebar) userSidebar.classList.toggle('hidden', !isAuth);

    document.querySelectorAll('[data-auth-name]').forEach((el) => {
      el.textContent = isAuth ? (currentUser.full_name || '') : '';
    });
    document.querySelectorAll('[data-auth-handle]').forEach((el) => {
      el.textContent = isAuth ? (currentUser.display_handle || '') : '';
    });
    document.querySelectorAll('[data-auth-phone]').forEach((el) => {
      const phone = isAuth ? (currentUser.phone_number || '') : '';
      el.textContent = phone;
      el.classList.toggle('hidden', !phone);
    });
    document.querySelectorAll('.auth-avatar').forEach((avatar) => {
      updateAvatarContainer(avatar, currentUser);
    });

    const modal = document.getElementById('auth-modal');
    if (modal) {
      modal.setAttribute('data-authenticated', isAuth ? '1' : '0');
      modal.setAttribute('data-phone-number', isAuth ? (currentUser.phone_number || '') : '');
    }
  }

  function stopPolling() {
    if (pollIntervalId) {
      clearInterval(pollIntervalId);
      pollIntervalId = null;
    }
    pollInFlight = false;
    activeDeepLinkToken = null;
    activeDeepLinkDeadline = 0;
  }

  function resetDeepLinkUI() {
    const panel = document.getElementById('auth-deeplink-panel');
    const retryBtn = document.getElementById('btn-auth-deeplink-retry');
    const statusText = document.getElementById('auth-deeplink-status-text');
    const startBtn = document.getElementById('btn-auth-deeplink');

    if (panel) panel.classList.add('hidden');
    if (retryBtn) retryBtn.classList.add('hidden');
    if (statusText) statusText.textContent = msg.waitingBot;
    if (startBtn) {
      startBtn.disabled = false;
      const textEl = startBtn.querySelector('.btn-deeplink-text');
      if (textEl) textEl.textContent = msg.deeplinkBtn;
    }
  }

  function openLoginModal(action) {
    if (typeof action !== 'undefined' && action !== null) {
      pendingAction = action;
    }
    const modal = document.getElementById('auth-modal');
    if (!modal) return;
    showAuthAlert('', '');
    document.body.classList.remove('drawer-open');
    modal.classList.add('is-open');
    modal.setAttribute('aria-hidden', 'false');
    document.body.classList.add('modal-open');
  }

  function closeLoginModal(clearPending) {
    stopPolling();
    const modal = document.getElementById('auth-modal');
    if (modal) {
      modal.classList.remove('is-open');
      modal.setAttribute('aria-hidden', 'true');
    }
    if (!document.querySelector('.modal-backdrop.is-open, .modal-overlay.is-open')) {
      document.body.classList.remove('modal-open');
    }
    if (clearPending) {
      pendingAction = null;
    }
  }

  function resumePendingAction() {
    const action = pendingAction;
    pendingAction = null;
    if (!action) return;

    if (typeof action === 'function') {
      action(currentUser);
      return;
    }
    if (action === 'order') {
      if (window.mobiModal && typeof window.mobiModal.open === 'function') {
        window.mobiModal.open();
      }
      return;
    }
    if (action === 'review') {
      if (window.mobiReview && typeof window.mobiReview.open === 'function') {
        window.mobiReview.open();
      } else {
        const reviewBtn = document.getElementById('btn-open-review-modal');
        if (reviewBtn) reviewBtn.click();
      }
      return;
    }
    if (action === 'orders') {
      if (typeof window.openOrderTracking === 'function') {
        window.openOrderTracking();
      }
    }
  }

  function handleLoginSuccess(user) {
    stopPolling();
    currentUser = user || null;
    syncAuthUI();
    resetDeepLinkUI();
    window.dispatchEvent(new CustomEvent('mobi:auth-changed', {
      detail: { authenticated: Boolean(currentUser), user: currentUser },
    }));
    closeLoginModal(false);
    resumePendingAction();
  }

  function beginPollingForToken(token, botUrl, expiresIn, statusMessage) {
    const panel = document.getElementById('auth-deeplink-panel');
    const openLink = document.getElementById('auth-deeplink-open-link');
    const statusText = document.getElementById('auth-deeplink-status-text');
    const retryBtn = document.getElementById('btn-auth-deeplink-retry');

    stopPolling();
    activeDeepLinkToken = token;
    activeDeepLinkDeadline = Date.now() + ((Number(expiresIn) || 300) * 1000);

    if (openLink) openLink.href = botUrl;
    if (statusText) statusText.textContent = statusMessage || msg.waitingBot;
    if (retryBtn) retryBtn.classList.add('hidden');
    if (panel) panel.classList.remove('hidden');

    // Attempt to open Telegram bot directly; direct anchor link inside panel serves as iOS Safari fallback
    try {
      window.open(botUrl, '_blank', 'noopener,noreferrer');
    } catch (openErr) {
      console.warn('Popup blocked, user can tap direct link:', openErr);
    }

    pollIntervalId = setInterval(pollDeepLinkStatus, 2000);
  }

  async function pollDeepLinkStatus() {
    if (!activeDeepLinkToken || pollInFlight) return;

    if (activeDeepLinkDeadline && Date.now() >= activeDeepLinkDeadline) {
      stopPolling();
      const statusText = document.getElementById('auth-deeplink-status-text');
      const retryBtn = document.getElementById('btn-auth-deeplink-retry');
      if (statusText) statusText.textContent = msg.expired;
      if (retryBtn) retryBtn.classList.remove('hidden');
      showAuthAlert(msg.expired, 'error');
      return;
    }

    pollInFlight = true;
    try {
      const res = await fetch(
        `/api/auth/telegram/deeplink/status/?token=${encodeURIComponent(activeDeepLinkToken)}&lang=${encodeURIComponent(lang)}`,
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

      if (data.status === 'confirmed' && data.authenticated && data.user) {
        handleLoginSuccess(data.user);
        return;
      }

      if (data.status === 'rejected') {
        stopPolling();
        const errText = data.error || msg.uzOnlyError;
        const statusText = document.getElementById('auth-deeplink-status-text');
        const retryBtn = document.getElementById('btn-auth-deeplink-retry');
        if (statusText) statusText.textContent = errText;
        if (retryBtn) retryBtn.classList.remove('hidden');
        showAuthAlert(errText, 'error');
        return;
      }

      if (data.status === 'expired') {
        stopPolling();
        const statusText = document.getElementById('auth-deeplink-status-text');
        const retryBtn = document.getElementById('btn-auth-deeplink-retry');
        if (statusText) statusText.textContent = msg.expired;
        if (retryBtn) retryBtn.classList.remove('hidden');
        showAuthAlert(msg.expired, 'error');
        return;
      }

      if (data.status === 'used' || data.status === 'invalid') {
        stopPolling();
        const statusText = document.getElementById('auth-deeplink-status-text');
        const retryBtn = document.getElementById('btn-auth-deeplink-retry');
        if (statusText) statusText.textContent = msg.invalidToken;
        if (retryBtn) retryBtn.classList.remove('hidden');
        showAuthAlert(msg.invalidToken, 'error');
      }
    } catch (err) {
      // Transient network hiccup during polling; retry on next tick
      console.warn('Deep-link status poll error:', err);
    } finally {
      pollInFlight = false;
    }
  }

  async function startDeepLinkLogin() {
    const startBtn = document.getElementById('btn-auth-deeplink');

    stopPolling();
    showAuthAlert('', '');

    if (startBtn) {
      startBtn.disabled = true;
      const textEl = startBtn.querySelector('.btn-deeplink-text');
      if (textEl) textEl.textContent = msg.starting;
    }

    try {
      const res = await fetch('/api/auth/telegram/deeplink/start/', {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCsrfToken(),
        },
        body: JSON.stringify({ lang: lang }),
      });

      let data = {};
      try {
        data = await res.json();
      } catch (_) {
        data = {};
      }
      if (!res.ok || !data.success || !data.token || !data.bot_url) {
        throw new Error(data.error || msg.authError);
      }

      beginPollingForToken(data.token, data.bot_url, data.expires_in, msg.waitingBot);
    } catch (err) {
      showAuthAlert(err.message || msg.networkError, 'error');
    } finally {
      if (startBtn) {
        startBtn.disabled = false;
        const textEl = startBtn.querySelector('.btn-deeplink-text');
        if (textEl) textEl.textContent = msg.deeplinkBtn;
      }
    }
  }

  async function logout() {
    try {
      const res = await fetch('/api/auth/logout/', {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCsrfToken(),
        },
      });
      if (!res.ok) {
        throw new Error(msg.logoutError);
      }
      currentUser = null;
      pendingAction = null;
      syncAuthUI();
      document.body.classList.remove('drawer-open');
      window.dispatchEvent(new CustomEvent('mobi:auth-changed', {
        detail: { authenticated: false, user: null },
      }));
    } catch (err) {
      console.error('Logout error:', err);
    }
  }

  async function refresh() {
    try {
      const res = await fetch('/api/auth/me/', {
        method: 'GET',
        credentials: 'same-origin',
        headers: { Accept: 'application/json' },
      });
      if (!res.ok) return currentUser;
      const data = await res.json();
      currentUser = data.authenticated && data.user ? data.user : null;
      syncAuthUI();
      return currentUser;
    } catch (err) {
      console.warn('Auth refresh error:', err);
      return currentUser;
    }
  }

  // Global Auth API for calculators, order modal, review modal & navbar
  window.mobiAuth = {
    isAuthenticated: function () {
      return Boolean(currentUser);
    },
    getUser: function () {
      return currentUser ? Object.assign({}, currentUser) : null;
    },
    openLoginModal: openLoginModal,
    closeLoginModal: function () {
      closeLoginModal(true);
    },
    logout: logout,
    refresh: refresh,
  };

  document.addEventListener('DOMContentLoaded', () => {
    hydrateInitialUser();
    syncAuthUI();

    // Fallback to monogram/initials if Telegram avatar fails to load
    document.querySelectorAll('.auth-avatar-img').forEach((img) => {
      img.addEventListener('error', () => {
        img.classList.add('hidden');
        const avatar = img.closest('.auth-avatar');
        const initials = avatar ? avatar.querySelector('.auth-avatar-initials') : null;
        if (initials) initials.classList.remove('hidden');
      });
    });

    const btnOpenTopbar = document.getElementById('btn-open-auth-topbar');
    const btnOpenSidebar = document.getElementById('btn-open-auth-sidebar');
    const btnLogoutTopbar = document.getElementById('btn-logout-topbar');
    const btnLogoutSidebar = document.getElementById('btn-logout-sidebar');
    const btnCloseModal = document.getElementById('btn-close-auth-modal');
    const btnDeepLink = document.getElementById('btn-auth-deeplink');
    const btnDeepLinkRetry = document.getElementById('btn-auth-deeplink-retry');
    const modal = document.getElementById('auth-modal');

    if (btnOpenTopbar) {
      btnOpenTopbar.addEventListener('click', () => openLoginModal(null));
    }
    if (btnOpenSidebar) {
      btnOpenSidebar.addEventListener('click', () => openLoginModal(null));
    }
    if (btnLogoutTopbar) {
      btnLogoutTopbar.addEventListener('click', logout);
    }
    if (btnLogoutSidebar) {
      btnLogoutSidebar.addEventListener('click', logout);
    }
    if (btnCloseModal) {
      btnCloseModal.addEventListener('click', () => closeLoginModal(true));
    }
    if (btnDeepLink) {
      btnDeepLink.addEventListener('click', startDeepLinkLogin);
    }
    if (btnDeepLinkRetry) {
      btnDeepLinkRetry.addEventListener('click', startDeepLinkLogin);
    }

    if (modal) {
      modal.addEventListener('click', (e) => {
        if (e.target === modal) closeLoginModal(true);
      });
    }

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && modal && modal.classList.contains('is-open')) {
        closeLoginModal(true);
      }
    });
  });
})();

