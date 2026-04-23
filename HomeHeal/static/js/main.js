// ─── HomeHeal – main.js ────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {

  // ── Smooth scroll for anchor links ──────────────────────────────────────
  document.querySelectorAll('a[href^="#"]').forEach(a => {
    a.addEventListener('click', e => {
      const target = document.querySelector(a.getAttribute('href'));
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });

  // ── Animate elements on scroll ──────────────────────────────────────────
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.style.opacity = '1';
        entry.target.style.transform = 'translateY(0)';
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1 });

  document.querySelectorAll('.card, .stat-card, .feature-icon').forEach(el => {
    if (!el.closest('.auth-card')) {
      el.style.opacity = '0';
      el.style.transform = 'translateY(20px)';
      el.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
      observer.observe(el);
    }
  });

  // ── BMI Indicator position ───────────────────────────────────────────────
  const indicator = document.querySelector('.bmi-indicator');
  if (indicator) {
    const targetLeft = indicator.style.left;
    indicator.style.left = '0%';
    setTimeout(() => { indicator.style.left = targetLeft; }, 200);
  }

  // ── FAQ Toggle ───────────────────────────────────────────────────────────
  window.toggleFAQ = function(el) {
    const item = el.parentElement;
    const wasOpen = item.classList.contains('open');
    // Close all
    document.querySelectorAll('.faq-item.open').forEach(i => i.classList.remove('open'));
    if (!wasOpen) item.classList.add('open');
  };

  // ── Active nav highlight ─────────────────────────────────────────────────
  const currentPath = window.location.pathname;
  document.querySelectorAll('.navbar-nav a').forEach(link => {
    if (link.getAttribute('href') === currentPath) {
      link.classList.add('active');
    }
  });

  // ── Set today's min date on appointment date input ───────────────────────
  const dateInput = document.getElementById('date');
  if (dateInput && !dateInput.value) {
    const today = new Date().toISOString().split('T')[0];
    dateInput.setAttribute('min', today);
  }

  // ── Button loading state ─────────────────────────────────────────────────
  document.querySelectorAll('form').forEach(form => {
    form.addEventListener('submit', function () {
      const btn = this.querySelector('button[type="submit"]');
      if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<i class="ph ph-circle-notch" style="animation:spin 1s linear infinite;"></i> Processing...';
      }
    });
  });

  // ── Spin animation for loading ────────────────────────────────────────────
  const style = document.createElement('style');
  style.textContent = '@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }';
  document.head.appendChild(style);

  // ── Tooltip on reminder/appt action buttons ──────────────────────────────
  document.querySelectorAll('[title]').forEach(el => {
    el.addEventListener('mouseenter', function () {
      const tip = document.createElement('div');
      tip.textContent = this.getAttribute('title');
      tip.style.cssText = `
        position:fixed; background:#1e2740; color:#e8eaf6; font-size:0.75rem;
        padding:4px 10px; border-radius:6px; pointer-events:none; z-index:99999;
        border:1px solid rgba(255,255,255,0.1); white-space:nowrap;
        box-shadow:0 4px 12px rgba(0,0,0,0.3);
      `;
      tip.id = '__homeheal_tip__';
      document.body.appendChild(tip);
      const rect = this.getBoundingClientRect();
      tip.style.top = (rect.bottom + 6) + 'px';
      tip.style.left = (rect.left + rect.width / 2 - tip.offsetWidth / 2) + 'px';
    });
    el.addEventListener('mouseleave', () => {
      document.getElementById('__homeheal_tip__')?.remove();
    });
  });

  // ── Counter animation for stat cards ─────────────────────────────────────
  document.querySelectorAll('.stat-value').forEach(el => {
    const target = parseFloat(el.textContent);
    if (!isNaN(target) && target > 0) {
      let current = 0;
      const increment = target / 30;
      const timer = setInterval(() => {
        current += increment;
        if (current >= target) {
          el.textContent = Number.isInteger(target) ? target : target.toFixed(1);
          clearInterval(timer);
        } else {
          el.textContent = Number.isInteger(target) ? Math.floor(current) : current.toFixed(1);
        }
      }, 30);
    }
  });

});
