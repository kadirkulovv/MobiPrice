// MobiPrice — Main Application Coordinator Module
document.addEventListener('DOMContentLoaded', () => {
  // 1. Language Dropdown URL Routing (/uz/, /ru/, /en/)
  const langSelect = document.getElementById('lang-select');
  if (langSelect) {
    langSelect.addEventListener('change', (e) => {
      const selectedLang = e.target.value;
      if (!selectedLang) return;

      // Set django language cookie for session persistence
      document.cookie = `django_language=${selectedLang};path=/;max-age=31536000;SameSite=Lax`;

      // Check current pathname to preserve subpaths or route to root of selected language
      const currentPath = window.location.pathname;
      const langPattern = /^\/(uz|ru|en)(\/.*)?$/;
      const match = currentPath.match(langPattern);

      if (match) {
        const subPath = match[2] || '/';
        window.location.href = `/${selectedLang}${subPath}${window.location.search}${window.location.hash}`;
      } else {
        window.location.href = `/${selectedLang}/`;
      }
    });
  }

  // 2. FAQ Accordion Interaction
  const faqQuestions = document.querySelectorAll('.faq-question');
  faqQuestions.forEach((q) => {
    q.addEventListener('click', () => {
      const parent = q.closest('.faq-item');
      if (!parent) return;

      // Close other open FAQ items for clean accordion UX
      document.querySelectorAll('.faq-item.open').forEach((openItem) => {
        if (openItem !== parent) openItem.classList.remove('open');
      });

      parent.classList.toggle('open');
    });
  });

  // 3. Smooth scrolling for internal anchor links
  document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
    anchor.addEventListener('click', function (e) {
      const targetId = this.getAttribute('href').substring(1);
      const targetElem = document.getElementById(targetId);
      if (targetElem) {
        e.preventDefault();
        targetElem.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });

  console.log('MobiPrice App Initialized: Language =', document.documentElement.lang);
});
