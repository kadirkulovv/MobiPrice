// MobiPrice — Live Model Search Autocomplete Module
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
        const res = await fetch(`/api/models/search/?q=${encodeURIComponent(query)}`);
        const data = await res.json();

        if (!data.models || data.models.length === 0) {
          searchDropdown.innerHTML = `
            <div class="search-item-empty" style="padding: 12px 16px; color: var(--text-dim); font-size: 13px;">
              Model topilmadi
            </div>
          `;
          searchDropdown.style.display = 'block';
          return;
        }

        searchDropdown.innerHTML = data.models.map(m => `
          <div class="search-item" data-id="${m.id}" data-name="${m.name}" data-brand="${m.brand_name || ''}">
            <img src="${m.image_url}" alt="${m.name}" class="search-item-img" onerror="this.src='/static/img/models/iphone_16_pro_max.jpg'">
            <div>
              <div class="search-item-brand">${m.brand_name || ''}</div>
              <div class="search-item-title">${m.name}</div>
            </div>
          </div>
        `).join('');

        searchDropdown.style.display = 'block';

        searchDropdown.querySelectorAll('.search-item').forEach(item => {
          item.addEventListener('click', () => {
            const mId = item.getAttribute('data-id');
            const mName = item.getAttribute('data-name');

            searchDropdown.style.display = 'none';
            searchInput.value = '';

            if (window.mobiCalculator && typeof window.mobiCalculator.selectModel === 'function') {
              window.mobiCalculator.selectModel(mId, mName);
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
