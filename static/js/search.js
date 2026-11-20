// MobiPrice — Live Phone Search Autocomplete Module
document.addEventListener('DOMContentLoaded', () => {
  const searchInput = document.getElementById('search-model-input');
  const searchDropdown = document.getElementById('search-dropdown');

  if (!searchInput || !searchDropdown) return;

  const lang = document.documentElement.lang || 'uz';
  const emptyText = {
    uz: 'Telefon topilmadi',
    ru: 'Телефон не найден',
    en: 'No matching phone found',
  }[lang] || 'Telefon topilmadi';

  function escapeHtml(str) {
    return String(str ?? '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  let debounceTimer = null;

  function closeDropdown() {
    searchDropdown.classList.remove('is-open');
    searchDropdown.innerHTML = '';
  }

  searchInput.addEventListener('input', () => {
    clearTimeout(debounceTimer);
    const query = searchInput.value.trim();

    if (query.length < 2) {
      closeDropdown();
      return;
    }

    debounceTimer = setTimeout(async () => {
      try {
        const res = await fetch(`/api/phones/search/?q=${encodeURIComponent(query)}`);
        const data = await res.json();

        if (!data.phones || data.phones.length === 0) {
          searchDropdown.innerHTML = `
            <div class="search-item-empty">
              ${escapeHtml(emptyText)}
            </div>
          `;
          searchDropdown.classList.add('is-open');
          return;
        }

        searchDropdown.innerHTML = data.phones.map((p) => `
          <div class="search-item" data-id="${escapeHtml(p.id)}" data-name="${escapeHtml(p.name)}" data-brand="${escapeHtml(p.brand_name || '')}">
            <img src="${escapeHtml(p.image_url)}" alt="${escapeHtml(p.name)}" class="search-item-img" onerror="this.onerror=null;this.src='/static/img/models/iphone_16_pro_max.jpg'">
            <div>
              <div class="search-item-brand">${escapeHtml(p.brand_name || '')} ${p.series_name ? '• ' + escapeHtml(p.series_name) : ''}</div>
              <div class="search-item-title">${escapeHtml(p.name)}</div>
            </div>
          </div>
        `).join('');

        searchDropdown.classList.add('is-open');

        searchDropdown.querySelectorAll('.search-item').forEach((item) => {
          item.addEventListener('click', () => {
            const pId = item.getAttribute('data-id');
            const pName = item.getAttribute('data-name');
            const brandName = item.getAttribute('data-brand');

            closeDropdown();
            searchInput.value = '';

            if (window.mobiCalculator && typeof window.mobiCalculator.selectPhone === 'function') {
              if (window.mobiState) window.mobiState.brandName = brandName;
              window.mobiCalculator.selectPhone(pId, pName);
            }
          });
        });
      } catch (err) {
        console.error('Search error:', err);
      }
    }, 250);
  });

  // Close dropdown on outside click
  document.addEventListener('click', (e) => {
    if (!searchInput.contains(e.target) && !searchDropdown.contains(e.target)) {
      searchDropdown.classList.remove('is-open');
    }
  });
});
