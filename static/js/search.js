// MobiPrice — Live Phone Search Autocomplete Module
document.addEventListener('DOMContentLoaded', () => {
  const searchInput = document.getElementById('search-model-input');
  const searchDropdown = document.getElementById('search-dropdown');

  if (!searchInput || !searchDropdown) return;

  let debounceTimer = null;

  searchInput.addEventListener('input', () => {
    clearTimeout(debounceTimer);
    const query = searchInput.value.trim();

    if (query.length < 2) {
      searchDropdown.style.display = 'none';
      searchDropdown.innerHTML = '';
      return;
    }

    debounceTimer = setTimeout(async () => {
      try {
        const res = await fetch(`/api/phones/search/?q=${encodeURIComponent(query)}`);
        const data = await res.json();

        if (!data.phones || data.phones.length === 0) {
          searchDropdown.innerHTML = `
            <div class="search-item-empty" style="padding: 12px 16px; color: var(--text-dim); font-size: 13px;">
              Telefon topilmadi
            </div>
          `;
          searchDropdown.style.display = 'block';
          return;
        }

        searchDropdown.innerHTML = data.phones.map(p => `
          <div class="search-item" data-id="${p.id}" data-name="${p.name}" data-brand="${p.brand_name || ''}">
            <img src="${p.image_url}" alt="${p.name}" class="search-item-img" onerror="this.src='/static/img/models/iphone_16_pro_max.jpg'">
            <div>
              <div class="search-item-brand">${p.brand_name || ''} ${p.series_name ? '• ' + p.series_name : ''}</div>
              <div class="search-item-title">${p.name}</div>
            </div>
          </div>
        `).join('');

        searchDropdown.style.display = 'block';

        searchDropdown.querySelectorAll('.search-item').forEach(item => {
          item.addEventListener('click', () => {
            const pId = item.getAttribute('data-id');
            const pName = item.getAttribute('data-name');
            const brandName = item.getAttribute('data-brand');

            searchDropdown.style.display = 'none';
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
      searchDropdown.style.display = 'none';
    }
  });
});
