/* ── Booking Wizard ─────────────────────────────────────────────────────── */
const state = {
  service:  null,
  masterId: null,
  date:     null,
  time:     null,
  step:     1,
};

const DAYS_AHEAD = 14;

// ── Step navigation ──────────────────────────────────────────────────────────
function goStep(n) {
  document.querySelectorAll('.step-panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.step-dot').forEach((d, i) => {
    d.classList.remove('active', 'done');
    if (i + 1 < n)  d.classList.add('done');
    if (i + 1 === n) d.classList.add('active');
  });
  const panel = document.getElementById(`step${n}`);
  if (panel) { panel.classList.add('active'); panel.scrollIntoView({ behavior: 'smooth', block: 'start' }); }
  state.step = n;
  updateSidebar();
}

// ── Sidebar summary ──────────────────────────────────────────────────────────
function updateSidebar() {
  set('sum-service',  state.service ? state.service.title : '—');
  set('sum-master',   state.masterId ? masterName(state.masterId) : '—');
  set('sum-datetime', (state.date && state.time) ? `${formatDate(state.date)}, ${state.time}` : '—');
  set('sum-price',    state.service ? `${state.service.price} ₽` : '—');
  set('sum-duration', state.service ? `${state.service.duration_minutes} мин` : '—');
}

function set(id, val) {
  const el = document.getElementById(id);
  if (el) el.textContent = val;
}

function masterName(id) {
  const el = document.querySelector(`.master-pick[data-id="${id}"] .master-pick__name`);
  return el ? el.textContent : '—';
}

// ── Step 1: Service selection ────────────────────────────────────────────────
document.querySelectorAll('.service-pick').forEach(card => {
  card.addEventListener('click', () => {
    document.querySelectorAll('.service-pick').forEach(c => c.classList.remove('selected'));
    card.classList.add('selected');
    state.service = {
      id:               +card.dataset.id,
      title:            card.dataset.title,
      price:            card.dataset.price,
      duration_minutes: +card.dataset.duration,
    };
    updateSidebar();
  });
});

document.getElementById('next1')?.addEventListener('click', () => {
  if (!state.service) { toast('Выберите услугу'); return; }
  populateMasters();
  buildDatePicker();
  goStep(2);
});

// ── Step 2: Master + date + time ─────────────────────────────────────────────
function populateMasters() {
  document.querySelectorAll('.master-pick').forEach(card => {
    card.addEventListener('click', () => {
      document.querySelectorAll('.master-pick').forEach(c => c.classList.remove('selected'));
      card.classList.add('selected');
      state.masterId = +card.dataset.id;
      updateSidebar();
      if (state.date) fetchSlots();
    });
  });
}

function buildDatePicker() {
  const container = document.getElementById('date-picker');
  if (!container) return;
  container.innerHTML = '';

  const today = new Date();
  for (let i = 0; i < DAYS_AHEAD; i++) {
    const d    = new Date(today);
    d.setDate(today.getDate() + i);
    const iso  = isoDate(d);
    const btn  = document.createElement('button');
    btn.className = 'date-btn';
    btn.dataset.date = iso;
    btn.innerHTML = `<strong>${d.getDate()}</strong><br><small>${shortDay(d)}</small>`;
    btn.addEventListener('click', () => selectDate(iso, btn));
    container.appendChild(btn);
  }
}

function selectDate(iso, btn) {
  document.querySelectorAll('.date-btn').forEach(b => b.classList.remove('selected'));
  btn.classList.add('selected');
  state.date = iso;
  state.time = null;
  updateSidebar();
  fetchSlots();
}

async function fetchSlots() {
  if (!state.masterId || !state.date || !state.service) return;
  const grid = document.getElementById('time-grid');
  if (!grid) return;
  grid.innerHTML = '<span style="color:var(--text-muted);font-size:13px">Загружаем слоты…</span>';

  try {
    const url = `/api/masters/${state.masterId}/slots?date=${state.date}&service_id=${state.service.id}`;
    const res  = await fetch(url);
    const slots = await res.json();

    grid.innerHTML = '';
    if (!slots.length) {
      grid.innerHTML = '<span style="color:var(--text-muted);font-size:13px">Нет свободных слотов на эту дату</span>';
      return;
    }
    slots.forEach(t => {
      const btn = document.createElement('button');
      btn.className = 'time-btn';
      btn.textContent = t;
      btn.addEventListener('click', () => {
        document.querySelectorAll('.time-btn').forEach(b => b.classList.remove('selected'));
        btn.classList.add('selected');
        state.time = t;
        updateSidebar();
      });
      grid.appendChild(btn);
    });
  } catch (e) {
    grid.innerHTML = '<span style="color:var(--text-muted)">Ошибка загрузки</span>';
  }
}

document.getElementById('next2')?.addEventListener('click', () => {
  if (!state.masterId) { toast('Выберите мастера'); return; }
  if (!state.date)     { toast('Выберите дату');    return; }
  if (!state.time)     { toast('Выберите время');   return; }
  goStep(3);
});

document.getElementById('back2')?.addEventListener('click', () => goStep(1));

// ── Step 3: Contact form + submit ────────────────────────────────────────────
document.getElementById('back3')?.addEventListener('click', () => goStep(2));

document.getElementById('booking-form')?.addEventListener('submit', async e => {
  e.preventDefault();

  const btn = document.getElementById('submit-btn');
  btn.disabled = true;
  btn.textContent = 'Отправляем…';

  const payload = {
    service_id: state.service.id,
    master_id:  state.masterId,
    date:       state.date,
    time:       state.time,
    name:       document.getElementById('f-name').value.trim(),
    phone:      document.getElementById('f-phone').value.trim(),
    email:      document.getElementById('f-email').value.trim(),
    notes:      document.getElementById('f-notes').value.trim(),
  };

  try {
    const res  = await fetch('/api/bookings', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify(payload),
    });
    const data = await res.json();

    if (res.ok) {
      document.getElementById('step3').classList.remove('active');
      document.getElementById('step-success').classList.add('active');
      document.querySelectorAll('.step-dot').forEach(d => d.classList.add('done'));
    } else {
      toast(data.error || 'Ошибка. Попробуйте ещё раз.');
      btn.disabled  = false;
      btn.textContent = 'Записаться';
    }
  } catch {
    toast('Ошибка соединения');
    btn.disabled = false;
    btn.textContent = 'Записаться';
  }
});

// ── Helpers ──────────────────────────────────────────────────────────────────
function isoDate(d) {
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}
function pad(n) { return String(n).padStart(2, '0'); }

const DAYS = ['Вс', 'Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб'];
function shortDay(d) { return DAYS[d.getDay()]; }

function formatDate(iso) {
  const [y, m, day] = iso.split('-');
  const months = ['янв','фев','мар','апр','май','июн','июл','авг','сен','окт','ноя','дек'];
  return `${+day} ${months[+m - 1]}`;
}

function toast(msg) {
  const div = document.createElement('div');
  div.className = 'flash flash-danger';
  div.textContent = msg;
  div.style.cssText = 'position:fixed;bottom:24px;right:24px;z-index:999;padding:14px 20px;background:var(--surface-up);border-left:3px solid var(--pink-dark);border-radius:4px;font-size:14px;max-width:320px;';
  document.body.appendChild(div);
  setTimeout(() => div.remove(), 4000);
}