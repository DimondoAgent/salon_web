/* ── Navigation ─────────────────────────────────────────────────────────── */
const nav = document.querySelector('.nav');

// Highlight current page link
document.querySelectorAll('.nav__links a').forEach(a => {
  if (a.href === window.location.href) a.classList.add('active');
});

// ── Category tabs (services page) ────────────────────────────────────────────
const tabs = document.querySelectorAll('.category-tab');
const rows = document.querySelectorAll('.service-row[data-category]');

tabs.forEach(tab => {
  tab.addEventListener('click', () => {
    tabs.forEach(t => t.classList.remove('active'));
    tab.classList.add('active');

    const cat = tab.dataset.category;
    rows.forEach(row => {
      row.style.display = (cat === 'all' || row.dataset.category === cat) ? '' : 'none';
    });
  });
});

// ── Scroll-triggered fade-in ──────────────────────────────────────────────────
const observer = new IntersectionObserver(entries => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.style.opacity  = '1';
      entry.target.style.transform = 'translateY(0)';
      observer.unobserve(entry.target);
    }
  });
}, { threshold: 0.1 });

document.querySelectorAll('.service-card, .master-card, .portfolio-item').forEach(el => {
  el.style.opacity   = '0';
  el.style.transform = 'translateY(20px)';
  el.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
  observer.observe(el);
});

// ── Flash messages auto-dismiss ───────────────────────────────────────────────
setTimeout(() => {
  document.querySelectorAll('.flash').forEach(el => {
    el.style.transition = 'opacity 0.5s';
    el.style.opacity    = '0';
    setTimeout(() => el.remove(), 500);
  });
}, 4000);