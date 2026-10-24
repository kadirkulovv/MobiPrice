// MobiPrice — Order Booking Modal Module
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

  document.addEventListener('DOMContentLoaded', () => {
    const modal = document.getElementById('order-modal');
    const modalClose = document.getElementById('modal-close');
    const modalModelDetail = document.getElementById('modal-model-detail');
    const orderForm = document.getElementById('order-form');
    const modalAlert = document.getElementById('modal-alert');
    const phoneInput = document.getElementById('phone-number');

    function openModal() {
      if (!modal) return;
      const state = window.mobiState || {};
      const detailStr = `${state.phoneName || state.modelName || 'Tanlangan model'} — ${state.comparisonTitle || state.optionTitle || state.issueTitle || 'Xizmat'}`;
      if (modalModelDetail) modalModelDetail.textContent = detailStr;

      if (modalAlert) {
        modalAlert.className = 'hidden';
        modalAlert.textContent = '';
      }

      modal.style.display = 'flex';
      document.body.style.overflow = 'hidden';
    }

    function closeModal() {
      if (!modal) return;
      modal.style.display = 'none';
      document.body.style.overflow = '';
    }

    if (modalClose) modalClose.addEventListener('click', closeModal);
    if (modal) {
      modal.addEventListener('click', (e) => {
        if (e.target === modal) closeModal();
      });
    }

    // Auto format phone number
    if (phoneInput) {
      phoneInput.addEventListener('focus', () => {
        if (!phoneInput.value.trim()) {
          phoneInput.value = '+998 ';
        }
      });
    }

    if (orderForm) {
      orderForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const clientName = document.getElementById('client-name').value.trim();
        const phoneNumber = document.getElementById('phone-number').value.trim();
        const serviceType = document.getElementById('service-type').value;

        const state = window.mobiState || {};
        const submitBtn = orderForm.querySelector('button[type="submit"]');
        const origBtnText = submitBtn.textContent;
        submitBtn.disabled = true;
        submitBtn.textContent = "Yuborilmoqda...";

        try {
          const res = await fetch('/api/orders/submit/', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'X-CSRFToken': getCookie('csrftoken') || '',
            },
            body: JSON.stringify({
              client_name: clientName,
              phone_number: phoneNumber,
              phone_id: state.phoneId || state.modelId,
              comparison_id: state.comparisonId || state.optionId,
              service_type: serviceType,
            }),
          });

          const data = await res.json();

          if (data.success) {
            if (modalAlert) {
              modalAlert.className = '';
              modalAlert.style.background = 'rgba(16, 185, 129, 0.2)';
              modalAlert.style.color = '#10b981';
              modalAlert.style.border = '1px solid rgba(16, 185, 129, 0.3)';
              modalAlert.innerHTML = `✅ <b>Arizangiz qabul qilindi!</b><br>ID: <b>#${data.order_id}</b>. Tez orada ustamiz siz bilan bog‘lanadi.<br><a href="#" onclick="window.mobiModal.close(); if(window.openOrderTracking) window.openOrderTracking('${data.order_id}'); return false;" style="color:#00f2fe; text-decoration:underline; font-weight:700; margin-top:6px; display:inline-block;">🔍 Buyurtma holatini ko'rish &rarr;</a>`;
            }
            orderForm.reset();
            setTimeout(() => {
              closeModal();
              submitBtn.disabled = false;
              submitBtn.textContent = origBtnText;
            }, 5000);
          } else {
            if (modalAlert) {
              modalAlert.className = '';
              modalAlert.style.background = 'rgba(239, 68, 68, 0.2)';
              modalAlert.style.color = '#ef4444';
              modalAlert.style.border = '1px solid rgba(239, 68, 68, 0.3)';
              modalAlert.textContent = data.error || "Xatolik yuz berdi.";
            }
            submitBtn.disabled = false;
            submitBtn.textContent = origBtnText;
          }
        } catch (err) {
          console.error('Order submission error:', err);
          if (modalAlert) {
            modalAlert.className = '';
            modalAlert.style.background = 'rgba(239, 68, 68, 0.2)';
            modalAlert.style.color = '#ef4444';
            modalAlert.textContent = "Server bilan aloqa uzildi. Iltimos telefon orqali bog'laning.";
          }
          submitBtn.disabled = false;
          submitBtn.textContent = origBtnText;
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
