/* Bibliotek — Client-side JavaScript */
/* ============================================================
   API helpers, barcode scanning, form handling, toast system
   ============================================================ */

/* --- Auth state (persisted in sessionStorage) --- */
const APP = {
  token: sessionStorage.getItem('bibliotek_token') || null,
  user: JSON.parse(sessionStorage.getItem('bibliotek_user') || 'null'),
};

/* --- HTTP wrapper --- */
async function api(path, options = {}) {
  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
  if (APP.token) {
    headers['Authorization'] = `Bearer ${APP.token}`;
  }
  const res = await fetch(path, { ...options, headers });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }));
    throw new Error(err.detail || `Request failed (${res.status})`);
  }
  if (res.status === 204) return null;
  return res.json();
}

/* --- Toast notifications --- */
function toast(message, type = 'info') {
  const container = document.querySelector('.toast-container') || createToastContainer();
  const el = document.createElement('div');
  el.className = `toast toast-${type}`;
  el.textContent = message;
  container.appendChild(el);
  setTimeout(() => {
    el.style.opacity = '0';
    el.style.transition = 'opacity .2s';
    setTimeout(() => el.remove(), 200);
  }, 3500);
}

function createToastContainer() {
  const c = document.createElement('div');
  c.className = 'toast-container';
  document.body.appendChild(c);
  return c;
}

/* --- Auth helpers --- */
function setAuth(token, user) {
  APP.token = token;
  APP.user = user;
  sessionStorage.setItem('bibliotek_token', token);
  sessionStorage.setItem('bibliotek_user', JSON.stringify(user));
}

function clearAuth() {
  APP.token = null;
  APP.user = null;
  sessionStorage.removeItem('bibliotek_token');
  sessionStorage.removeItem('bibliotek_user');
}

function isLoggedIn() {
  return APP.token !== null;
}

function isAdmin() {
  return APP.user && APP.user.role === 'admin';
}

function isLibrarian() {
  return APP.user && (APP.user.role === 'admin' || APP.user.role === 'librarian');
}

/* --- Barcode scanner (html5-qrcode) --- */
let barcodeScanner = null;

function startScanner(containerId, onScan) {
  const container = document.getElementById(containerId);
  if (!container) {
    toast('Avscannings-container hittades inte', 'error');
    return;
  }

  if (barcodeScanner) {
    barcodeScanner.clear();
  }

  barcodeScanner = new Html5Qrcode(containerId);

  const config = {
    fps: 10,
    qrbox: { width: 250, height: 150 },
    aspectRatio: 1.5,
  };

  barcodeScanner.start(
    { facingMode: 'environment' },
    config,
    (decodedText) => {
      // Barcode detected — stop scanner and call callback
      barcodeScanner.stop().then(() => {
        onScan(decodedText);
      }).catch(() => {
        onScan(decodedText);
      });
    },
    () => { /* no scan — ignore */ }
  ).catch((err) => {
    toast('Kunde inte starta kameran: ' + err, 'error');
  });
}

function stopScanner() {
  if (barcodeScanner) {
    barcodeScanner.stop().then(() => {
      barcodeScanner.clear();
      barcodeScanner = null;
    }).catch(() => {
      barcodeScanner = null;
    });
  }
}

/* --- Modal helpers --- */
function openModal(modalEl) {
  if (modalEl) modalEl.classList.add('active');
}

function closeModal(modalEl) {
  if (modalEl) modalEl.classList.remove('active');
}

function closeAllModals() {
  document.querySelectorAll('.modal-overlay.active').forEach(m => m.classList.remove('active'));
  stopScanner();
}

/* --- HCF category label (Swedish) --- */
function hcfLabel(code) {
  const map = {
    hcf: 'HCF',
    hcg: 'HCG',
    hcb: 'HCB',
    adult: 'Adult',
  };
  return map[code] || code || '—';
}

/* --- Date formatting --- */
function formatDate(iso) {
  if (!iso) return '—';
  const d = new Date(iso);
  return d.toLocaleDateString('sv-SE', { year: 'numeric', month: 'short', day: 'numeric' });
}

function formatDateTime(iso) {
  if (!iso) return '—';
  const d = new Date(iso);
  return d.toLocaleDateString('sv-SE', {
    year: 'numeric', month: 'short', day: 'numeric',
    hour: '2-digit', minute: '2-digit',
  });
}

function daysUntilDue(dueDateIso) {
  const now = new Date();
  const due = new Date(dueDateIso);
  const diff = Math.ceil((due - now) / (1000 * 60 * 60 * 24));
  return diff;
}

/* --- Navigation --- */
function navigateTo(path) {
  window.location.href = path;
}

/* --- Form helpers --- */
function serializeForm(formEl) {
  const fd = new FormData(formEl);
  const obj = {};
  for (const [key, value] of fd.entries()) {
    obj[key] = value;
  }
  return obj;
}

function showFormErrors(formEl, errors) {
  /* Remove old error messages */
  formEl.querySelectorAll('.form-error').forEach(e => e.remove());
  for (const [field, msg] of Object.entries(errors)) {
    const input = formEl.querySelector(`[name="${field}"]`);
    if (input) {
      const errEl = document.createElement('div');
      errEl.className = 'form-error';
      errEl.textContent = msg;
      input.parentNode.appendChild(errEl);
    }
  }
}

/* --- Expose globally --- */
window.APP = APP;
window.api = api;
window.toast = toast;
window.setAuth = setAuth;
window.clearAuth = clearAuth;
window.isLoggedIn = isLoggedIn;
window.isAdmin = isAdmin;
window.isLibrarian = isLibrarian;
window.startScanner = startScanner;
window.stopScanner = stopScanner;
window.openModal = openModal;
window.closeModal = closeModal;
window.closeAllModals = closeAllModals;
window.hcfLabel = hcfLabel;
window.formatDate = formatDate;
window.formatDateTime = formatDateTime;
window.daysUntilDue = daysUntilDue;
window.navigateTo = navigateTo;
window.serializeForm = serializeForm;
window.showFormErrors = showFormErrors;
