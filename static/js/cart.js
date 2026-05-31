// QRMenu Customer Cart — Vanilla JS
'use strict';

let cart = [];
let discount = 0;
let discountCode = '';

function addToCart(id, nameAr, nameEn, price) {
  const existing = cart.find(i => i.id === id);
  if (existing) {
    existing.qty++;
  } else {
    cart.push({ id, nameAr, nameEn, price, qty: 1 });
  }
  updateCartUI();
  showAddFeedback(id);
}

function removeFromCart(id) {
  const existing = cart.find(i => i.id === id);
  if (!existing) return;
  if (existing.qty > 1) {
    existing.qty--;
  } else {
    cart = cart.filter(i => i.id !== id);
  }
  updateCartUI();
}

function cartTotal() {
  return cart.reduce((sum, i) => sum + i.price * i.qty, 0);
}

function cartCount() {
  return cart.reduce((sum, i) => sum + i.qty, 0);
}

function updateCartUI() {
  const count = cartCount();
  const total = cartTotal();
  const finalTotal = Math.max(0, total - discount);

  const countEl = document.getElementById('cart-count');
  const totalEl = document.getElementById('cart-total');
  const cartBar = document.getElementById('cart-bar');

  if (countEl) countEl.textContent = count;
  if (totalEl) totalEl.textContent = finalTotal.toFixed(3) + ' OMR';
  if (cartBar) {
    if (count > 0) cartBar.classList.add('visible');
    else cartBar.classList.remove('visible');
  }

  // Update product quantity controls
  cart.forEach(item => {
    const addBtn = document.getElementById('add-' + item.id);
    const qtyCtrl = document.getElementById('qty-' + item.id);
    const qtyVal = document.getElementById('qty-val-' + item.id);
    if (addBtn) addBtn.style.display = 'none';
    if (qtyCtrl) qtyCtrl.classList.add('visible');
    if (qtyVal) qtyVal.textContent = item.qty;
  });

  // Hide qty controls for removed items
  document.querySelectorAll('[id^="qty-"]').forEach(el => {
    const id = parseInt(el.id.replace('qty-', ''));
    if (!cart.find(i => i.id === id)) {
      el.classList.remove('visible');
      const addBtn = document.getElementById('add-' + id);
      if (addBtn) addBtn.style.display = 'flex';
    }
  });

  updateSummary();
}

function updateSummary() {
  const subtotal = cartTotal();
  const finalTotal = Math.max(0, subtotal - discount);

  const stEl = document.getElementById('summary-subtotal');
  const ttEl = document.getElementById('summary-total');
  const discRow = document.getElementById('discount-row');
  const discEl = document.getElementById('summary-discount');

  if (stEl) stEl.textContent = subtotal.toFixed(3) + ' OMR';
  if (ttEl) ttEl.textContent = finalTotal.toFixed(3) + ' OMR';
  if (discRow) discRow.style.display = discount > 0 ? 'flex' : 'none';
  if (discEl) discEl.textContent = '- ' + discount.toFixed(3) + ' OMR';
}

function renderCartItems() {
  const container = document.getElementById('cart-items-list');
  if (!container) return;
  if (cart.length === 0) {
    container.innerHTML = '<div style="text-align:center;color:var(--text-muted);padding:1rem;">السلة فارغة</div>';
    return;
  }
  container.innerHTML = cart.map(item => `
    <div style="display:flex;align-items:center;justify-content:space-between;padding:.6rem 0;border-bottom:1px solid var(--border);">
      <div>
        <div style="font-weight:700;font-size:.9rem;">${item.nameAr}</div>
        <div style="font-size:.8rem;color:var(--text-muted);">${item.price.toFixed(3)} × ${item.qty}</div>
      </div>
      <div style="display:flex;align-items:center;gap:.5rem;">
        <span style="font-weight:700;color:var(--primary);">${(item.price * item.qty).toFixed(3)} OMR</span>
        <div style="display:flex;align-items:center;gap:.3rem;">
          <button class="qty-btn" onclick="removeFromCart(${item.id});renderCartItems();" style="width:26px;height:26px;font-size:.9rem;">−</button>
          <span style="min-width:20px;text-align:center;font-weight:700;">${item.qty}</span>
          <button class="qty-btn" onclick="addToCart(${item.id},'${item.nameAr.replace(/'/g,"\\'")}','${item.nameEn.replace(/'/g,"\\'")}',${item.price});renderCartItems();" style="width:26px;height:26px;font-size:.9rem;">+</button>
        </div>
      </div>
    </div>
  `).join('');
}

function openOrderModal() {
  if (cart.length === 0) return;
  renderCartItems();
  updateSummary();
  document.getElementById('order-overlay').classList.add('open');
  document.getElementById('order-sheet').classList.add('open');
  document.body.style.overflow = 'hidden';
}

function closeOrderModal() {
  document.getElementById('order-overlay').classList.remove('open');
  document.getElementById('order-sheet').classList.remove('open');
  document.body.style.overflow = '';
}

function updateOrderTypeUI() {
  const select = document.getElementById('order-type-select');
  if (!select) return;
  const type = select.value;
  const carFields = document.getElementById('car-fields');
  const tableFields = document.getElementById('table-fields');
  if (carFields) carFields.style.display = type === 'car' ? 'block' : 'none';
  if (tableFields) tableFields.style.display = type === 'table' ? 'block' : 'none';
}

async function applyCoupon() {
  const code = (document.getElementById('coupon-input')?.value || '').trim().toUpperCase();
  const msgEl = document.getElementById('coupon-msg');
  if (!code) { if (msgEl) msgEl.textContent = ''; return; }

  try {
    const res = await fetch('/api/coupons/validate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code, slug: RESTAURANT_SLUG, total: cartTotal() })
    });
    const data = await res.json();
    if (data.valid) {
      discount = data.discount;
      discountCode = code;
      if (msgEl) {
        msgEl.style.color = 'var(--success)';
        msgEl.textContent = '✓ ' + data.message;
      }
      updateSummary();
    } else {
      discount = 0;
      discountCode = '';
      if (msgEl) {
        msgEl.style.color = 'var(--danger)';
        msgEl.textContent = '✗ ' + data.message;
      }
      updateSummary();
    }
  } catch (e) {
    if (msgEl) { msgEl.style.color = 'var(--danger)'; msgEl.textContent = 'خطأ في التحقق'; }
  }
}

async function submitOrder() {
  const errorEl = document.getElementById('order-error');
  if (errorEl) errorEl.style.display = 'none';

  if (cart.length === 0) {
    showError('السلة فارغة'); return;
  }

  // Determine order type
  let orderType = ORDER_MODE === 'table' ? 'table' : 'car';
  const typeSelect = document.getElementById('order-type-select');
  if (typeSelect) orderType = typeSelect.value;

  const carPlate = document.getElementById('car-plate')?.value.trim() || '';
  const tableNumber = document.getElementById('table-number')?.value.trim() || '';
  const notes = document.getElementById('order-notes')?.value.trim() || '';

  if (orderType === 'car' && !carPlate) {
    showError('يرجى إدخال رقم السيارة'); return;
  }
  if (orderType === 'table' && !tableNumber) {
    showError('يرجى إدخال رقم الطاولة'); return;
  }

  const payload = {
    slug: RESTAURANT_SLUG,
    order_type: orderType,
    car_plate: carPlate,
    table_number: tableNumber,
    notes,
    coupon_code: discountCode,
    items: cart.map(i => ({ id: i.id, qty: i.qty }))
  };

  try {
    const btn = document.querySelector('[onclick="submitOrder()"]');
    if (btn) { btn.disabled = true; btn.textContent = 'جار الإرسال...'; }

    const res = await fetch('/api/orders/place', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();

    if (data.success) {
      cart = [];
      window.location.href = data.redirect;
    } else {
      showError(data.error || 'حدث خطأ أثناء إرسال الطلب');
      if (btn) { btn.disabled = false; btn.textContent = '✅ تأكيد الطلب'; }
    }
  } catch (e) {
    showError('خطأ في الاتصال بالشبكة');
    const btn = document.querySelector('[onclick="submitOrder()"]');
    if (btn) { btn.disabled = false; btn.textContent = '✅ تأكيد الطلب'; }
  }
}

function showError(msg) {
  const el = document.getElementById('order-error');
  if (el) { el.textContent = msg; el.style.display = 'flex'; }
}

function showAddFeedback(id) {
  const btn = document.getElementById('add-' + id);
  if (!btn) return;
  btn.style.transform = 'scale(1.3)';
  setTimeout(() => { btn.style.transform = ''; }, 200);
}

function scrollToCategory(id) {
  const el = document.getElementById(id);
  if (!el) return;
  const offset = 130;
  const top = el.getBoundingClientRect().top + window.scrollY - offset;
  window.scrollTo({ top, behavior: 'smooth' });
  // Update active tab
  document.querySelectorAll('.category-tab').forEach(t => t.classList.remove('active'));
  const tabId = id.replace('cat-', 'tab-');
  const tab = document.getElementById(tabId);
  if (tab) tab.classList.add('active');
}

// Activate first tab on load
window.addEventListener('DOMContentLoaded', () => {
  const firstTab = document.querySelector('.category-tab');
  if (firstTab) firstTab.classList.add('active');
});
