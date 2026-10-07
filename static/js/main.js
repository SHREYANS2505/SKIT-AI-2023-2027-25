/**
 * OZONE Smart Farming - Master Client Engine
 * Lightweight, Clean Architecture for Navigation, Auth & Modals
 */

document.addEventListener('DOMContentLoaded', () => {
  initHeader();
  initLoginModal();
  checkUserSession();
});

/* ==========================================================================
   1. Header Navigation & Sticky Scroll
   ========================================================================== */
function initHeader() {
  const header = document.querySelector('.site-header');
  const burger = document.getElementById('navBurger');
  const menu = document.getElementById('navMenu');
  const links = document.querySelectorAll('.nav__links a');

  if (burger && header) {
    burger.addEventListener('click', () => {
      const open = header.classList.toggle('is-open');
      burger.setAttribute('aria-expanded', String(open));
      burger.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
    });
  }

  if (menu && header && burger) {
    menu.addEventListener('click', (e) => {
      if (e.target.closest('a')) {
        header.classList.remove('is-open');
        burger.setAttribute('aria-expanded', 'false');
      }
    });
  }

  // Sticky header on scroll
  const onScroll = () => {
    if (header) {
      header.classList.toggle('is-stuck', window.scrollY > 10);
    }

    // Active link highlighting
    const scrollPos = window.scrollY + 140;
    const sections = ['top', 'features', 'about', 'contact'];
    let currentId = 'top';

    for (const id of sections) {
      const el = document.getElementById(id);
      if (el && scrollPos >= el.offsetTop) {
        currentId = id;
      }
    }

    links.forEach(link => {
      link.classList.remove('is-active');
      if (link.getAttribute('href') === `#${currentId}`) {
        link.classList.add('is-active');
      }
    });
  };

  onScroll();
  window.addEventListener('scroll', onScroll, { passive: true });
}

/* ==========================================================================
   2. Login Modal Management & SQLite Authentication
   ========================================================================== */
function initLoginModal() {
  const modal = document.getElementById('loginModal');
  const loginBtn = document.getElementById('navLoginBtn');
  const closeBtn = document.getElementById('modalCloseBtn');
  const form = document.getElementById('loginForm');
  const errBox = document.getElementById('loginErrorMsg');
  const submitBtn = document.getElementById('loginSubmitBtn');
  const toggleEye = document.getElementById('togglePasswordBtn');
  const passInput = document.getElementById('loginPassword');

  if (loginBtn) {
    loginBtn.addEventListener('click', (e) => {
      e.preventDefault();
      openModal();
    });
  }

  if (closeBtn) {
    closeBtn.addEventListener('click', closeModal);
  }

  if (modal) {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) closeModal();
    });
  }

  window.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeModal();
  });

  if (toggleEye && passInput) {
    toggleEye.addEventListener('click', () => {
      passInput.type = passInput.type === 'password' ? 'text' : 'password';
    });
  }

  if (form) {
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      const email = document.getElementById('loginEmail')?.value.trim() || '';
      const password = passInput?.value || '';

      if (errBox) errBox.style.display = 'none';

      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.textContent = 'Verifying... / सत्यापन हो रहा है...';
      }

      fetch('/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      })
      .then(async (res) => {
        const data = await res.json();
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.textContent = 'Sign In to Dashboard / लॉगिन करें';
        }

        if (res.ok && data.status === 'success') {
          closeModal();
          showToast(`🎉 ${data.message || 'लॉगिन सफल! Redirecting...'}`);
          setTimeout(() => {
            window.location.href = '/home';
          }, 600);
        } else {
          if (errBox) {
            errBox.textContent = `❌ ${data.message || 'Invalid email or password'}`;
            errBox.style.display = 'block';
          } else {
            showToast(`❌ ${data.message || 'Invalid email or password'}`);
          }
        }
      })
      .catch(() => {
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.textContent = 'Sign In to Dashboard / लॉगिन करें';
        }
        if (errBox) {
          errBox.textContent = '❌ Server connection failed. Please check network.';
          errBox.style.display = 'block';
        }
      });
    });
  }

  function openModal() {
    if (modal) {
      modal.classList.add('active');
      document.body.style.overflow = 'hidden';
      if (errBox) errBox.style.display = 'none';
    }
  }

  function closeModal() {
    if (modal) {
      modal.classList.remove('active');
      document.body.style.overflow = '';
    }
  }
}

/* ==========================================================================
   3. User Session Verification
   ========================================================================== */
function checkUserSession() {
  fetch('/api/user')
    .then(res => res.json())
    .then(data => {
      const userSection = document.getElementById('navUserSection');
      const guestActions = document.getElementById('navGuestActions');
      const userNameEl = document.getElementById('navUserName');

      if (data && data.logged_in && data.user) {
        if (userNameEl) userNameEl.textContent = `Welcome, ${data.user.name} 🌾`;
        if (userSection) userSection.style.display = 'flex';
        if (guestActions) guestActions.style.display = 'none';
      } else {
        if (userSection) userSection.style.display = 'none';
        if (guestActions) guestActions.style.display = 'flex';
      }
    })
    .catch(() => {});
}

/* ==========================================================================
   4. Global Toast System
   ========================================================================== */
function showToast(message) {
  let toast = document.getElementById('globalToast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'globalToast';
    toast.className = 'toast-notice';
    document.body.appendChild(toast);
  }

  toast.innerHTML = message;
  toast.classList.add('show');

  clearTimeout(window.toastTimer);
  window.toastTimer = setTimeout(() => {
    toast.classList.remove('show');
  }, 3600);
}
