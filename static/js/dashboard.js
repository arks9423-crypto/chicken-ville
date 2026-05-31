// QRMenu Dashboard — Real-time polling & Kanban updates
'use strict';

let lastCheck = new Date().toISOString();
let soundEnabled = false;
let pollTimer = null;

function enableSound() {
  // Requires user gesture
  const ctx = new AudioContext();
  ctx.resume().then(() => {
    soundEnabled = true;
    const btn = document.getElementById('sound-btn');
    if (btn) {
      btn.textContent = '🔔 صوت الطلبات مفعّل';
      btn.style.background = 'var(--success)';
      btn.onclick = null;
      btn.style.cursor = 'default';
    }
    playBeep(); // play test beep
    startPolling();
  });
}

function playBeep() {
  if (!soundEnabled) return;
  try {
    const ctx = new AudioContext();
    [0, 0.3, 0.6].forEach(delay => {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.frequency.value = 800;
      gain.gain.setValueAtTime(0.4, ctx.currentTime + delay);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + delay + 0.25);
      osc.start(ctx.currentTime + delay);
      osc.stop(ctx.currentTime + delay + 0.25);
    });
  } catch (e) {}
}

function startPolling() {
  if (pollTimer) clearInterval(pollTimer);
  pollTimer = setInterval(poll, 5000);
}

async function poll() {
  try {
    const res = await fetch(`/api/orders/poll?since=${encodeURIComponent(lastCheck)}`);
    if (!res.ok) return;
    const data = await res.json();
    if (data.has_new) {
      playBeep();
    }
    updateKanban(data.orders);
    lastCheck = data.server_time;
  } catch (e) {}
}

function updateKanban(orders) {
  const cols = { new: 'col-new', preparing: 'col-preparing', ready: 'col-ready' };
  const counts = { new: 0, preparing: 0, ready: 0 };

  // Track existing cards
  const existingIds = new Set();
  Object.values(cols).forEach(colId => {
    const col = document.getElementById(colId);
    if (!col) return;
    col.querySelectorAll('[data-order-id]').forEach(card => {
      existingIds.add(parseInt(card.dataset.orderId));
    });
  });

  // Process orders from server
  orders.forEach(order => {
    if (!counts.hasOwnProperty(order.status)) return;
    counts[order.status]++;

    const colId = cols[order.status];
    const col = document.getElementById(colId);
    if (!col) return;

    const existing = col.querySelector(`[data-order-id="${order.id}"]`);
    if (existing) {
      // Update if status changed — card is already in correct column
      existingIds.delete(order.id);
    } else {
      // Check if card is in wrong column and move it
      let wrongCard = null;
      Object.values(cols).forEach(cId => {
        const c = document.getElementById(cId);
        if (!c) return;
        const card = c.querySelector(`[data-order-id="${order.id}"]`);
        if (card && cId !== colId) {
          wrongCard = card;
          c.removeChild(card);
        }
      });

      if (wrongCard) {
        wrongCard.dataset.status = order.status;
        prependCard(col, wrongCard);
      } else {
        // New card — add it
        const cardHtml = renderOrderCard(order);
        const tmp = document.createElement('div');
        tmp.innerHTML = cardHtml;
        const card = tmp.firstElementChild;
        prependCard(col, card);
        existingIds.delete(order.id);
      }
    }
  });

  // Remove cards not in active orders (moved to done)
  existingIds.forEach(id => {
    Object.values(cols).forEach(colId => {
      const col = document.getElementById(colId);
      if (!col) return;
      const card = col.querySelector(`[data-order-id="${id}"]`);
      if (card) {
        card.style.opacity = '0';
        card.style.transition = 'opacity .4s';
        setTimeout(() => card.remove(), 400);
      }
    });
  });

  // Update counts
  Object.entries(counts).forEach(([status, count]) => {
    const el = document.getElementById('count-' + status);
    if (el) el.textContent = count;
  });
  const newCountEl = document.getElementById('new-count');
  if (newCountEl) newCountEl.textContent = counts.new;

  // Toggle empty messages
  Object.entries(cols).forEach(([status, colId]) => {
    const col = document.getElementById(colId);
    if (!col) return;
    const cards = col.querySelectorAll('[data-order-id]');
    const emptyEl = document.getElementById('empty-' + status);
    if (emptyEl) emptyEl.style.display = cards.length > 0 ? 'none' : 'block';
  });
}

function prependCard(col, card) {
  const firstCard = col.querySelector('[data-order-id]');
  card.classList.add('fade-in');
  if (firstCard) col.insertBefore(card, firstCard);
  else col.appendChild(card);
}

function renderOrderCard(order) {
  const time = new Date(order.created_at).toLocaleTimeString('ar-SA', { hour: '2-digit', minute: '2-digit' });
  const identifier = order.order_type === 'car'
    ? `🚗 ${order.car_plate || ''}`
    : order.order_type === 'table'
    ? `🪑 طاولة ${order.table_number || ''}`
    : '🏪 كاشير';

  const items = order.items.map(i =>
    `<li style="display:flex;justify-content:space-between;font-size:.85rem;padding:.2rem 0;">
      <span>${i.product_name_ar}</span>
      <span style="color:var(--primary);font-weight:700;">×${i.quantity}</span>
    </li>`
  ).join('');

  const nextAction = order.status === 'new'
    ? `<button class="btn btn-sm" style="background:#0EA5E9;color:#fff;" onclick="changeStatus(${order.id},'preparing')">👨‍🍳 تحضير</button>`
    : order.status === 'preparing'
    ? `<button class="btn btn-success btn-sm" onclick="changeStatus(${order.id},'ready')">✅ جاهز</button>`
    : order.status === 'ready'
    ? `<button class="btn btn-sm" style="background:#6B7280;color:#fff;" onclick="changeStatus(${order.id},'delivered')">📦 تسليم</button>`
    : '';

  const indicator = order.status === 'new' ? '<div class="order-new-indicator"></div>' : '';

  return `
    <div class="order-card fade-in" data-order-id="${order.id}" data-status="${order.status}">
      <div class="order-card-header">
        <div style="display:flex;align-items:center;gap:.5rem;">
          ${indicator}
          <span class="order-number">${order.order_number}</span>
        </div>
        <span class="order-time">${time}</span>
      </div>
      <div class="order-card-body">
        <div class="order-identifier">${identifier}</div>
        <ul class="order-items">${items}</ul>
        ${order.notes ? `<div class="order-notes">📝 ${order.notes}</div>` : ''}
        <div class="order-total">${order.total_amount.toFixed(3)} OMR</div>
      </div>
      <div class="order-actions">
        ${nextAction}
        <button class="btn btn-danger btn-sm" onclick="changeStatus(${order.id},'cancelled')">إلغاء</button>
      </div>
    </div>`;
}

async function changeStatus(orderId, newStatus) {
  if (newStatus === 'cancelled' && !confirm('هل تريد إلغاء الطلب؟')) return;
  try {
    const res = await fetch(`/api/orders/${orderId}/status`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: newStatus })
    });
    const data = await res.json();
    if (data.success) {
      // Immediately trigger a poll to refresh UI
      poll();
    }
  } catch (e) {}
}

// Auto-start polling (sound will activate on user gesture)
document.addEventListener('DOMContentLoaded', () => {
  startPolling();
});
