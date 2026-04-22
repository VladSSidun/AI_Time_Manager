// ===== API Helper =====

async function api(method, path, body = null) {
  const opts = {
    method,
    headers: { 'Content-Type': 'application/json' },
  };
  const token = getToken();
  if (token) opts.headers['Authorization'] = `Bearer ${token}`;
  if (body) opts.body = JSON.stringify(body);

  const res = await fetch(path, opts);
  if (res.status === 204) return null;
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
  return data;
}

// ===== Token / User storage =====

function getToken()  { return localStorage.getItem('token'); }
function setToken(t) { localStorage.setItem('token', t); }
function clearToken(){ localStorage.removeItem('token'); }

function getCachedUser()  { try { return JSON.parse(localStorage.getItem('user')); } catch { return null; } }
function setCachedUser(u) { localStorage.setItem('user', JSON.stringify(u)); }
function clearUser()      { localStorage.removeItem('user'); }

// ===== Router =====

const ROUTES = {
  '#landing':   { page: 'page-landing',   auth: false, onEnter: initScrollReveal },
  '#login':     { page: 'page-login',     auth: false },
  '#register':  { page: 'page-register',  auth: false },
  '#dashboard': { page: 'page-dashboard', auth: true,  onEnter: initDashboard },
  '#tasks':     { page: 'page-tasks',     auth: true,  onEnter: () => { loadActiveTimers(); loadTasks(); } },
  '#analytics': { page: 'page-analytics', auth: true,  onEnter: initAnalytics },
  '#admin':     { page: 'page-admin',     auth: true,  adminOnly: true, onEnter: loadAdminUsers },
};

function navigate(hash) {
  const route = ROUTES[hash];
  const loggedIn = !!getToken();

  if (!route) {
    navigate(loggedIn ? '#dashboard' : '#landing');
    return;
  }

  if (route.auth && !loggedIn) {
    navigate('#login');
    return;
  }

  if (!route.auth && loggedIn && (hash === '#login' || hash === '#register')) {
    navigate('#dashboard');
    return;
  }

  if (route.adminOnly) {
    const user = getCachedUser();
    if (!user || !user.is_admin) {
      navigate('#dashboard');
      return;
    }
  }

  if (location.hash !== hash) location.hash = hash;
  showPage(route.page);
  updateNavActive(hash);
  updateNavVisibility(loggedIn);

  if (route.onEnter) route.onEnter();
}

function showPage(pageId) {
  document.querySelectorAll('.page').forEach(p => p.style.display = 'none');
  const page = document.getElementById(pageId);
  if (!page) return;
  page.style.display = page.classList.contains('page-auth-flex') ? 'flex' : 'block';
  page.style.animation = 'none';
  page.offsetHeight;
  page.style.animation = '';
}

function updateNavActive(hash) {
  document.querySelectorAll('#main-nav [data-nav]').forEach(link => {
    link.classList.toggle('nav-active', '#' + link.dataset.nav === hash);
  });
  const logo = document.querySelector('#main-nav .logo');
  if (logo) logo.classList.toggle('nav-active', hash === '#landing');
}

function updateNavVisibility(loggedIn) {
  document.querySelectorAll('#main-nav [data-auth]').forEach(el => {
    const auth = el.dataset.auth;
    if (auth === 'true') {
      el.style.display = loggedIn ? '' : 'none';
    } else if (auth === 'false') {
      el.style.display = loggedIn ? 'none' : '';
    } else if (auth === 'admin') {
      const user = getCachedUser();
      el.style.display = (loggedIn && user && user.is_admin) ? '' : 'none';
    }
  });
}

window.addEventListener('hashchange', () => navigate(location.hash));

// ===== Auth =====

async function handleLogin(e) {
  e.preventDefault();
  const errEl = document.getElementById('login-error');
  errEl.textContent = '';
  try {
    const data = await api('POST', '/auth/login', {
      email: document.getElementById('login-email').value,
      password: document.getElementById('login-password').value,
    });
    setToken(data.access_token);
    await loadCurrentUser();
    navigate('#dashboard');
  } catch (err) {
    errEl.textContent = err.message;
  }
}

async function handleRegister(e) {
  e.preventDefault();
  const errEl = document.getElementById('register-error');
  errEl.textContent = '';
  try {
    const data = await api('POST', '/auth/register', {
      name: document.getElementById('reg-name').value,
      email: document.getElementById('reg-email').value,
      password: document.getElementById('reg-password').value,
    });
    setToken(data.access_token);
    await loadCurrentUser();
    navigate('#dashboard');
  } catch (err) {
    errEl.textContent = err.message;
  }
}

function logout() {
  clearToken();
  clearUser();
  document.querySelectorAll('.user-dropdown.open').forEach(d => d.classList.remove('open'));
  navigate('#landing');
}

// ===== User profile in navbar =====

async function loadCurrentUser() {
  try {
    const user = await api('GET', '/auth/me');
    setCachedUser(user);
    updateNavbar(user);
    updateNavVisibility(true);
  } catch (err) {
    clearToken();
    clearUser();
    navigate('#landing');
  }
}

function updateNavbar(user) {
  if (!user) return;
  const initials = user.name.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2);
  const nav = document.getElementById('main-nav');
  const init = nav.querySelector('.user-init');
  if (init) init.textContent = initials;
  const chipName = nav.querySelector('.user-chip-name');
  if (chipName) chipName.textContent = user.name.split(' ')[0];
  const fullname = nav.querySelector('.dropdown-fullname');
  if (fullname) fullname.textContent = user.name;
  const emailEl = nav.querySelector('.dropdown-email-text');
  if (emailEl) emailEl.textContent = user.email;
}

function toggleUserMenu(e, chip) {
  e.stopPropagation();
  const dropdown = chip.querySelector('.user-dropdown');
  const isOpen = dropdown.classList.contains('open');
  document.querySelectorAll('.user-dropdown.open').forEach(d => d.classList.remove('open'));
  if (!isOpen) dropdown.classList.add('open');
}

document.addEventListener('click', () => {
  document.querySelectorAll('.user-dropdown.open').forEach(d => d.classList.remove('open'));
});

// ===== Modal system =====

function showModal({ title, bodyHtml, onConfirm, confirmText, cancelText, hideCancel }) {
  const overlay = document.createElement('div');
  overlay.className = 'modal-overlay';
  overlay.innerHTML = `
    <div class="modal-card">
      <div class="modal-header">
        <span class="modal-title">${escHtml(title)}</span>
        <button class="modal-close" aria-label="Close">&times;</button>
      </div>
      <div class="modal-body">${bodyHtml}</div>
      <div class="modal-actions">
        ${hideCancel ? '' : `<button class="btn-modal-cancel">${escHtml(cancelText || 'Скасувати')}</button>`}
        ${onConfirm || hideCancel ? `<button class="btn-modal-confirm">${escHtml(confirmText || 'Підтвердити')}</button>` : ''}
      </div>
    </div>`;

  function close() { overlay.remove(); }

  overlay.querySelector('.modal-close').onclick = close;
  overlay.addEventListener('click', e => { if (e.target === overlay) close(); });
  document.addEventListener('keydown', function handler(e) {
    if (e.key === 'Escape') { close(); document.removeEventListener('keydown', handler); }
  });

  const cancelBtn = overlay.querySelector('.btn-modal-cancel');
  if (cancelBtn) cancelBtn.onclick = close;

  const confirmBtn = overlay.querySelector('.btn-modal-confirm');
  if (confirmBtn && onConfirm) {
    confirmBtn.onclick = async () => {
      confirmBtn.disabled = true;
      try { await onConfirm(overlay); } finally { close(); }
    };
  } else if (confirmBtn && hideCancel) {
    confirmBtn.onclick = close;
  }

  document.body.appendChild(overlay);
  return overlay;
}

// ===== Change name =====

function showEditNameModal() {
  document.querySelectorAll('.user-dropdown.open').forEach(d => d.classList.remove('open'));
  const user = getCachedUser();
  const currentName = user ? user.name : '';

  showModal({
    title: 'Змінити ім\'я',
    bodyHtml: `<input type="text" id="modal-new-name" class="modal-input" value="${escHtml(currentName)}"
               placeholder="Нове ім'я" minlength="2" maxlength="50" />`,
    confirmText: 'Зберегти',
    onConfirm: async (overlay) => {
      const newName = overlay.querySelector('#modal-new-name').value.trim();
      if (!newName || newName.length < 2 || newName.length > 50) {
        showModal({ title: 'Помилка', bodyHtml: '<p>Ім\'я має містити від 2 до 50 символів.</p>', confirmText: 'OK', hideCancel: true });
        return;
      }
      if (newName === currentName) return;

      showModal({
        title: 'Підтвердження',
        bodyHtml: `<p>Ви впевнені, що хочете змінити ім'я на <strong>${escHtml(newName)}</strong>?</p>`,
        confirmText: 'Так, змінити',
        onConfirm: async () => {
          try {
            const updated = await api('PATCH', '/auth/me', { name: newName });
            setCachedUser(updated);
            updateNavbar(updated);
            showModal({ title: 'Успіх', bodyHtml: '<p>Ім\'я успішно змінено!</p>', confirmText: 'OK', hideCancel: true });
          } catch (err) {
            showModal({ title: 'Помилка', bodyHtml: `<p>Не вдалось змінити ім'я: ${escHtml(err.message)}</p>`, confirmText: 'OK', hideCancel: true });
          }
        }
      });
    }
  });
}

// ===== Dashboard =====

async function initDashboard() {
  await loadStats('stats-grid');
}

async function loadStats(containerId) {
  try {
    const stats = await api('GET', '/analytics/stats');
    renderStats(containerId, stats);
  } catch (err) {
    document.getElementById(containerId).innerHTML = '<p style="color:#888">Не вдалось завантажити статистику</p>';
  }
}

function renderStats(containerId, stats) {
  const el = document.getElementById(containerId);
  const items = [
    { val: stats.total_sessions,             lbl: 'Сесій за 30 днів' },
    { val: stats.total_hours + ' год',       lbl: 'Загальний час' },
    { val: stats.avg_session_min + ' хв',    lbl: 'Середня сесія' },
    { val: stats.best_day,                   lbl: 'Найкращий день' },
    { val: stats.completion_rate + '%',      lbl: 'Виконано задач' },
    { val: stats.overdue_pct + '%',          lbl: 'Прострочено' },
    { val: stats.top_category,               lbl: 'Топ категорія' },
    { val: stats.pomodoro_sessions,          lbl: 'Pomodoro сесій' },
    { val: stats.productivity_score + '/100', lbl: 'Індекс продуктивності', score: true },
  ];
  el.innerHTML = items.map((item, i) =>
    `<div class="stat-card ${item.score ? 'score' : ''}" style="animation-delay:${i * 0.04}s">
       <div class="val">${item.val}</div>
       <div class="lbl">${item.lbl}</div>
     </div>`
  ).join('');
}

async function runAI() {
  const btn    = document.getElementById('btn-ai');
  const result = document.getElementById('ai-result');
  btn.disabled = true;
  btn.innerHTML = '<span class="loader"></span>Аналізую…';
  result.innerHTML = '';
  try {
    const data = await api('POST', '/analytics/ai-analysis');
    renderAIResult(result, data.recommendation);
  } catch (err) {
    result.innerHTML = '<p style="color:#ef4444">AI-аналіз тимчасово недоступний. Спробуйте пізніше.</p>';
  } finally {
    btn.disabled = false;
    btn.textContent = 'Отримати рекомендації';
  }
}

function renderAIResult(container, raw) {
  let parsed;
  try { parsed = typeof raw === 'string' ? JSON.parse(raw) : raw; } catch { parsed = null; }

  if (!parsed || !parsed.summary) {
    container.textContent = raw;
    return;
  }

  const score = parsed.productivity_score || 0;
  const pct = Math.min(score * 10, 100);
  const color = pct >= 70 ? '#059669' : pct >= 40 ? '#f59e0b' : '#ef4444';

  let html = `<div class="ai-structured">`;
  html += `<div class="ai-summary">${escHtml(parsed.summary)}</div>`;
  html += `<div class="ai-score-block">
    <span class="ai-score-label">Оцінка продуктивності: ${score}/10</span>
    <div class="ai-score-gauge"><div class="gauge-fill" style="width:${pct}%;background:${color}"></div></div>
  </div>`;

  if (parsed.recommendations && parsed.recommendations.length) {
    html += `<div class="ai-section-title">Рекомендації</div><ul class="ai-list">`;
    parsed.recommendations.forEach(r => { html += `<li>${escHtml(r)}</li>`; });
    html += `</ul>`;
  }

  if (parsed.patterns && parsed.patterns.length) {
    html += `<div class="ai-section-title">Виявлені патерни</div><ul class="ai-list ai-patterns">`;
    parsed.patterns.forEach(p => { html += `<li>${escHtml(p)}</li>`; });
    html += `</ul>`;
  }

  html += `</div>`;
  container.innerHTML = html;
}

// ===== Tasks =====

const activeTimers = new Set();

async function loadActiveTimers() {
  try {
    const data = await api('GET', '/tasks/active-timers');
    activeTimers.clear();
    (data.active_task_ids || []).forEach(id => activeTimers.add(id));
  } catch (err) { /* endpoint may not exist yet */ }
}

let taskCurrentPage = 1;
const TASK_LIMIT = 10;

async function loadTasks(status = '', category = '', page = 1) {
  taskCurrentPage = page;
  const params = new URLSearchParams();
  if (status)   params.set('task_status', status);
  if (category) params.set('category', category);
  params.set('page', page);
  params.set('limit', TASK_LIMIT);

  try {
    const data = await api('GET', '/tasks?' + params.toString());
    // Підтримка як paginated так і plain list (зворотна сумісність)
    const tasks = Array.isArray(data) ? data : (data.items || []);
    renderTasks(tasks);
    if (!Array.isArray(data) && data.pages !== undefined) {
      renderTaskPagination(data.page, data.pages, status, category);
    }
  } catch (err) {
    document.getElementById('task-list').innerHTML = '<p style="color:#ef4444">Помилка завантаження задач</p>';
  }
}

function renderTaskPagination(page, pages, status, category) {
  let container = document.getElementById('task-pagination');
  if (!container) {
    container = document.createElement('div');
    container.id = 'task-pagination';
    const taskList = document.getElementById('task-list');
    if (taskList && taskList.parentNode) {
      taskList.parentNode.insertBefore(container, taskList.nextSibling);
    }
  }
  if (pages <= 1) { container.innerHTML = ''; return; }
  container.innerHTML = `
    <div class="pagination">
      <button onclick="loadTasks('${status}','${category}',${page - 1})" ${page <= 1 ? 'disabled' : ''}>Попередня</button>
      <span class="page-info">Сторінка ${page} з ${pages}</span>
      <button onclick="loadTasks('${status}','${category}',${page + 1})" ${page >= pages ? 'disabled' : ''}>Наступна</button>
    </div>`;
}

function renderTasks(tasks) {
  const el = document.getElementById('task-list');
  if (!tasks.length) {
    el.innerHTML = '<p style="color:#888;padding:16px 0">Задач немає</p>';
    return;
  }

  el.innerHTML = tasks.map((t, i) => {
    const isCompleted = t.status === 'completed';
    const deadlineStr = t.deadline
      ? `Дедлайн: ${new Date(t.deadline).toLocaleString('uk-UA')}`
      : '';
    const isOverdue = t.deadline && !isCompleted && new Date(t.deadline) < new Date();
    const deadlineHtml = deadlineStr
      ? `<span class="${isOverdue ? 'overdue' : ''}">${deadlineStr}${isOverdue ? ' !' : ''}</span>`
      : '';

    const timerRunning = activeTimers.has(t.id);
    const timerBtn = isCompleted ? '' : `
      <button class="action-btn timer-btn ${timerRunning ? 'stop' : ''}"
              onclick="${timerRunning ? `stopTimer(${t.id})` : `startTimer(${t.id})`}">
        ${timerRunning ? 'Stop' : 'Start'}
      </button>`;

    return `
      <div class="task-item ${isCompleted ? 'completed' : ''}" style="animation-delay:${i * 0.04}s">
        <div class="task-info">
          <div class="task-title">${escHtml(t.title)}</div>
          <div class="task-meta">
            <span class="badge badge-${t.category}">${t.category}</span>
            <span class="badge badge-${t.status}">${t.status === 'pending' ? 'Очікує' : 'Завершено'}</span>
            ${t.estimated_minutes ? `~${t.estimated_minutes} хв` : ''}
            ${deadlineHtml}
          </div>
        </div>
        <div class="task-actions">
          ${timerBtn}
          ${!isCompleted ? `<button class="action-btn btn-complete" onclick="completeTask(${t.id})">Done</button>` : ''}
          <button class="action-btn btn-delete" onclick="deleteTask(${t.id})">Del</button>
        </div>
      </div>`;
  }).join('');
}

async function createTask(e) {
  e.preventDefault();
  const deadline = document.getElementById('task-deadline').value;
  try {
    await api('POST', '/tasks', {
      title: document.getElementById('task-title').value,
      category: document.getElementById('task-category').value,
      estimated_minutes: Number(document.getElementById('task-est').value) || null,
      deadline: deadline ? new Date(deadline).toISOString() : null,
    });
    e.target.reset();
    loadTasks();
  } catch (err) {
    showModal({ title: 'Помилка', bodyHtml: `<p>${escHtml(err.message)}</p>`, confirmText: 'OK', hideCancel: true });
  }
}

async function completeTask(id) {
  try { await api('POST', `/tasks/${id}/complete`); loadTasks(); }
  catch (err) { showModal({ title: 'Помилка', bodyHtml: `<p>${escHtml(err.message)}</p>`, confirmText: 'OK', hideCancel: true }); }
}

async function deleteTask(id) {
  showModal({
    title: 'Видалити задачу?',
    bodyHtml: '<p>Цю дію неможливо скасувати.</p>',
    confirmText: 'Видалити',
    onConfirm: async () => {
      try { await api('DELETE', `/tasks/${id}`); loadTasks(); }
      catch (err) { showModal({ title: 'Помилка', bodyHtml: `<p>${escHtml(err.message)}</p>`, confirmText: 'OK', hideCancel: true }); }
    }
  });
}

async function startTimer(taskId) {
  try {
    await api('POST', `/tasks/${taskId}/timer/start`);
    activeTimers.add(taskId);
    loadTasks();
  } catch (err) {
    showModal({ title: 'Помилка', bodyHtml: `<p>${escHtml(err.message)}</p>`, confirmText: 'OK', hideCancel: true });
  }
}

async function stopTimer(taskId) {
  try {
    const log = await api('POST', `/tasks/${taskId}/timer/stop`);
    activeTimers.delete(taskId);
    const min = Math.round(log.duration_seconds / 60);
    showModal({ title: 'Таймер зупинено', bodyHtml: `<p>Сесію завершено: ${min} хв</p>`, confirmText: 'OK', hideCancel: true });
    loadTasks();
  } catch (err) {
    showModal({ title: 'Помилка', bodyHtml: `<p>${escHtml(err.message)}</p>`, confirmText: 'OK', hideCancel: true });
  }
}

// ===== Analytics =====

async function initAnalytics() {
  await loadStats('analytics-stats');
  await loadAIHistory();
}

async function loadAIHistory() {
  try {
    const history = await api('GET', '/analytics/ai-analysis');
    const el = document.getElementById('ai-history');
    if (!history.length) {
      el.innerHTML = '<p style="color:#888">Аналізів ще немає</p>';
      return;
    }
    el.innerHTML = history.map(h => {
      let parsed = null;
      try { parsed = JSON.parse(h.recommendation); } catch { parsed = null; }
      const summary = parsed && parsed.summary ? escHtml(parsed.summary) : escHtml(h.recommendation).slice(0, 200) + '…';
      const score = parsed && parsed.productivity_score ? ` · Оцінка: ${parsed.productivity_score}/10` : '';
      return `
        <div class="history-item">
          <div class="date">${new Date(h.created_at).toLocaleString('uk-UA')}${score}</div>
          <div class="text">${summary}</div>
        </div>`;
    }).join('');
  } catch (err) {
    document.getElementById('ai-history').innerHTML = '<p style="color:#888">Не вдалось завантажити історію</p>';
  }
}

async function exportStats() {
  try {
    const token = getToken();
    const resp = await fetch('/analytics/export', {
      headers: { 'Authorization': 'Bearer ' + token },
    });
    if (!resp.ok) throw new Error('HTTP ' + resp.status);
    const blob = await resp.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'stats_export.json';
    a.click();
    URL.revokeObjectURL(url);
  } catch (err) {
    showModal({ title: 'Помилка', bodyHtml: `<p>Не вдалось експортувати: ${escHtml(err.message)}</p>`, confirmText: 'OK', hideCancel: true });
  }
}

// ===== Admin Panel =====

let adminPage = 1;
const ADMIN_LIMIT = 15;

async function loadAdminUsers(page = 1) {
  adminPage = page;
  const el = document.getElementById('admin-users');
  if (!el) return;
  el.innerHTML = '<p style="color:#888">Завантаження...</p>';
  try {
    const data = await api('GET', `/admin/users?page=${page}&limit=${ADMIN_LIMIT}`);
    renderAdminUsers(el, data);
  } catch (err) {
    el.innerHTML = `<p style="color:#ef4444">Помилка: ${escHtml(err.message)}</p>`;
  }
}

function renderAdminUsers(container, data) {
  const { items, total, page, pages } = data;
  if (!items.length) {
    container.innerHTML = '<p style="color:#888">Користувачів немає</p>';
    return;
  }

  let html = `<table class="admin-table">
    <thead><tr>
      <th>ID</th><th>Ім'я</th><th>Email</th><th>Роль</th>
      <th>Задачі</th><th>Реєстрація</th><th></th>
    </tr></thead>
    <tbody>`;

  items.forEach(u => {
    html += `<tr id="user-row-${u.id}">
      <td>${u.id}</td>
      <td>${escHtml(u.name)}</td>
      <td>${escHtml(u.email)}</td>
      <td>${u.is_admin ? '<span class="badge badge-work">admin</span>' : '<span class="badge badge-other">user</span>'}</td>
      <td>${u.task_count}</td>
      <td>${new Date(u.created_at).toLocaleDateString('uk-UA')}</td>
      <td><button class="btn-expand" onclick="toggleUserTasks(${u.id}, this)">Задачі</button></td>
    </tr>
    <tr class="admin-tasks-row" id="tasks-row-${u.id}" style="display:none">
      <td colspan="7"><div class="admin-tasks-inner" id="tasks-inner-${u.id}">Завантаження...</div></td>
    </tr>`;
  });

  html += `</tbody></table>`;

  // Пагінація
  html += `<div class="pagination">
    <button onclick="loadAdminUsers(${page - 1})" ${page <= 1 ? 'disabled' : ''}>Попередня</button>
    <span class="page-info">Сторінка ${page} з ${pages} (всього ${total})</span>
    <button onclick="loadAdminUsers(${page + 1})" ${page >= pages ? 'disabled' : ''}>Наступна</button>
  </div>`;

  container.innerHTML = html;
}

async function toggleUserTasks(userId, btn) {
  const row = document.getElementById(`tasks-row-${userId}`);
  const inner = document.getElementById(`tasks-inner-${userId}`);
  const isVisible = row.style.display !== 'none';

  if (isVisible) {
    row.style.display = 'none';
    btn.textContent = 'Задачі';
    return;
  }

  row.style.display = '';
  btn.textContent = 'Закрити';
  inner.innerHTML = 'Завантаження...';

  try {
    const tasks = await api('GET', `/admin/users/${userId}/tasks`);
    if (!tasks.length) {
      inner.innerHTML = '<p style="color:#888;padding:8px 0">Задач немає</p>';
      return;
    }
    inner.innerHTML = tasks.map(t => `
      <div class="task-item" style="margin-bottom:6px;font-size:13px">
        <div class="task-info">
          <div class="task-title">${escHtml(t.title)}</div>
          <div class="task-meta">
            <span class="badge badge-${t.category}">${t.category}</span>
            <span class="badge badge-${t.status}">${t.status === 'pending' ? 'Очікує' : 'Завершено'}</span>
            ${t.estimated_minutes ? `~${t.estimated_minutes} хв` : ''}
            ${t.deadline ? `Дедлайн: ${new Date(t.deadline).toLocaleDateString('uk-UA')}` : ''}
            ${t.description ? `· ${escHtml(t.description.slice(0, 60))}` : ''}
          </div>
        </div>
      </div>`).join('');
  } catch (err) {
    inner.innerHTML = `<p style="color:#ef4444">Помилка: ${escHtml(err.message)}</p>`;
  }
}

// ===== Help modal =====

function showHelpModal() {
  const overlay = document.createElement('div');
  overlay.className = 'modal-overlay help-overlay';
  overlay.innerHTML = `
    <div class="modal-card help-card">
      <div class="modal-header">
        <span class="modal-title">Довідка / Help</span>
        <div style="display:flex;gap:8px;align-items:center">
          <div class="help-lang-toggle">
            <button class="help-lang-btn active" id="btn-ua" onclick="switchHelpLang('ua')">UA</button>
            <button class="help-lang-btn" id="btn-en" onclick="switchHelpLang('en')">EN</button>
          </div>
          <button class="modal-close" aria-label="Close">&times;</button>
        </div>
      </div>
      <div class="modal-body help-body">
        <div class="help-ua">
          <h4>Задачі</h4>
          <p>Натисни <b>"Задачі"</b> у навбарі. Заповни назву, вибери категорію, встанови дедлайн або оцінку часу і натисни <b>"+ Додати"</b>. Фільтруй список за статусом або категорією. Натисни <b>"Done"</b> щоб завершити задачу, <b>"Del"</b> — щоб видалити.</p>
          <h4>Таймер</h4>
          <p>На сторінці задач натисни <b>"Start"</b> поруч із задачею. Таймер зберігається на сервері — при перезавантаженні сторінки він продовжиться. Натисни <b>"Stop"</b> щоб завершити сесію і побачити тривалість.</p>
          <h4>AI Рекомендації</h4>
          <p>На дашборді натисни <b>"Отримати рекомендації"</b>. Claude AI проаналізує твою статистику за 30 днів і дасть персональні поради. Повний аналіз також доступний у розділі "Аналітика → Історія AI аналізів".</p>
          <h4>Аналітика та Експорт</h4>
          <p>Розділ <b>"Аналітика"</b> показує статистику за 30 днів: кількість сесій, загальний час, найпродуктивніший день тощо. Кнопка <b>"Завантажити stats_export.json"</b> зберігає всі метрики у файл.</p>
          <h4>Пагінація задач</h4>
          <p>Відображається по 10 задач на сторінку. Кнопки <b>"Попередня / Наступна"</b> з'являються автоматично коли задач більше 10.</p>
          <h4>Зміна імені</h4>
          <p>Натисни на своє ім'я у правому верхньому куті → <b>"Змінити ім'я"</b>. Введи нове ім'я (2–50 символів), підтверди у вікні-запиті.</p>
          <h4>Адмін панель</h4>
          <p>Доступна тільки для адміністраторів (посилання <b>"Адмін"</b> у навбарі). Показує список усіх користувачів з кількістю задач, пагінацією (15/сторінка). Натисни <b>"Задачі"</b> біля користувача щоб розгорнути його задачі.</p>
        </div>
        <div class="help-en" style="display:none">
          <h4>Tasks</h4>
          <p>Click <b>"Tasks"</b> in the navbar. Fill in a title, choose a category, set a deadline or time estimate, then click <b>"+ Add"</b>. Filter the list by status or category. Click <b>"Done"</b> to complete a task, <b>"Del"</b> to delete it.</p>
          <h4>Timer</h4>
          <p>On the Tasks page click <b>"Start"</b> next to a task. The timer is stored on the server — reloading the page will not reset it. Click <b>"Stop"</b> to end the session and see its duration.</p>
          <h4>AI Recommendations</h4>
          <p>On the Dashboard click <b>"Get Recommendations"</b>. Claude AI analyses your 30-day stats and gives personalised advice. Full history is available under <b>Analytics → AI Analysis History</b>.</p>
          <h4>Analytics & Export</h4>
          <p>The <b>"Analytics"</b> section shows 30-day stats: sessions, total hours, best day of the week, and more. Click <b>"Download stats_export.json"</b> to save all metrics to a file.</p>
          <h4>Task Pagination</h4>
          <p>Tasks are shown 10 per page. <b>"Previous / Next"</b> buttons appear automatically when there are more than 10 tasks.</p>
          <h4>Change Name</h4>
          <p>Click your name in the top-right corner → <b>"Change name"</b>. Enter a new name (2–50 chars) and confirm in the dialog.</p>
          <h4>Admin Panel</h4>
          <p>Available to admins only (the <b>"Admin"</b> link in the navbar). Shows all registered users with task counts, paginated at 15 per page. Click <b>"Tasks"</b> next to a user to expand their task list.</p>
        </div>
      </div>
    </div>`;

  overlay.querySelector('.modal-close').onclick = () => overlay.remove();
  overlay.addEventListener('click', e => { if (e.target === overlay) overlay.remove(); });
  document.addEventListener('keydown', function h(e) {
    if (e.key === 'Escape') { overlay.remove(); document.removeEventListener('keydown', h); }
  });

  document.body.appendChild(overlay);
}

function switchHelpLang(lang) {
  const ua = document.querySelector('.help-ua');
  const en = document.querySelector('.help-en');
  const btnUa = document.getElementById('btn-ua');
  const btnEn = document.getElementById('btn-en');
  if (!ua || !en) return;
  if (lang === 'ua') {
    ua.style.display = ''; en.style.display = 'none';
    btnUa.classList.add('active'); btnEn.classList.remove('active');
  } else {
    ua.style.display = 'none'; en.style.display = '';
    btnEn.classList.add('active'); btnUa.classList.remove('active');
  }
}

// ===== Password visibility toggle =====

function togglePasswordVisibility(btn) {
  const wrapper = btn.closest('.password-wrapper');
  const input = wrapper.querySelector('input');
  const isPassword = input.type === 'password';
  input.type = isPassword ? 'text' : 'password';
  btn.classList.toggle('visible', !isPassword);
}

// ===== Helpers =====

function escHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

// ===== Scroll Reveal (Landing Page) =====

function initScrollReveal() {
  const observer = new IntersectionObserver(
    entries => {
      entries.forEach((entry, i) => {
        if (entry.isIntersecting) {
          const delay = i * 120;
          setTimeout(() => entry.target.classList.add('visible'), delay);
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.12 }
  );
  document.querySelectorAll('#page-landing .reveal').forEach(el => observer.observe(el));
}

// ===== Init =====

(function init() {
  const loggedIn = !!getToken();
  if (loggedIn) {
    const cached = getCachedUser();
    if (cached) {
      updateNavbar(cached);
      updateNavVisibility(true);
    }
    loadCurrentUser();
    loadActiveTimers();
  }
  const hash = location.hash || (loggedIn ? '#dashboard' : '#landing');
  navigate(hash);
})();
