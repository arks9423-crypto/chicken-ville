// Cart state — stored in memory (reset on page reload)
let cart = [];

function addToCart(id, nameAr, nameEn, price) {
  const existing = cart.find(i => i.id === id);
  if (existing) {
    existing.qty += 1;
  } else {
    cart.push({ id, nameAr, nameEn, price: parseFloat(price), qty: 1 });
  }
  updateCartUI();
  showAddFeedback();
}

function removeFromCart(id) {
  const idx = cart.findIndex(i => i.id === id);
  if (idx === -1) return;
  if (cart[idx].qty > 1) {
    cart[idx].qty -= 1;
  } else {
    cart.splice(idx, 1);
  }
  updateCartUI();
  renderCartSummary();
}

function cartTotal() {
  return cart.reduce((sum, i) => sum + i.price * i.qty, 0);
}

function cartCount() {
  return cart.reduce((sum, i) => sum + i.qty, 0);
}

function updateCartUI() {
  const bar = document.getElementById('cartBar');
  const badge = document.getElementById('cartCountBadge');
  const totalEl = document.getElementById('cartTotalDisplay');

  const count = cartCount();
  const total = cartTotal();

  if (count > 0) {
    bar.classList.remove('hidden');
  } else {
    bar.classList.add('hidden');
  }
  if (badge) badge.textContent = count;
  if (totalEl) totalEl.textContent = total.toFixed(3) + ' ر.ع';
}

function renderCartSummary() {
  const summaryEl = document.getElementById('cartSummary');
  const modalTotal = document.getElementById('modalTotal');
  if (!summaryEl) return;

  if (cart.length === 0) {
    summaryEl.innerHTML = '<p class="text-gray-400 text-sm text-center py-2">السلة فارغة</p>';
    if (modalTotal) modalTotal.textContent = '0.000 ر.ع';
    return;
  }

  summaryEl.innerHTML = cart.map(item => `
    <div class="flex items-center justify-between text-sm">
      <div class="flex items-center gap-2">
        <button onclick="removeFromCart(${item.id})"
                class="w-6 h-6 rounded-full bg-red-100 text-red-500 font-bold text-xs flex items-center justify-center hover:bg-red-200">
          −
        </button>
        <span class="text-gray-700">${item.nameAr}</span>
        <span class="text-gray-400">× ${item.qty}</span>
      </div>
      <span class="font-medium text-gray-800">${(item.price * item.qty).toFixed(3)} ر.ع</span>
    </div>
  `).join('');

  if (modalTotal) modalTotal.textContent = cartTotal().toFixed(3) + ' ر.ع';
}

function openOrderModal() {
  if (cart.length === 0) return;
  renderCartSummary();
  document.getElementById('orderModal').classList.remove('hidden');
  document.body.style.overflow = 'hidden';
}

function closeOrderModal() {
  document.getElementById('orderModal').classList.add('hidden');
  document.body.style.overflow = '';
  document.getElementById('orderError').classList.add('hidden');
}

async function submitOrder() {
  const carPlate = document.getElementById('car_plate').value.trim();
  const carColor = document.getElementById('car_color').value.trim();
  const carModel = document.getElementById('car_model').value.trim();
  const parkingSpot = document.getElementById('parking_spot').value.trim();
  const notes = document.getElementById('order_notes').value.trim();
  const errorEl = document.getElementById('orderError');
  const btn = document.getElementById('submitOrderBtn');

  errorEl.classList.add('hidden');

  if (!carPlate) {
    showError('يرجى إدخال رقم اللوحة'); return;
  }
  if (!carColor) {
    showError('يرجى إدخال لون السيارة'); return;
  }
  if (cart.length === 0) {
    showError('السلة فارغة'); return;
  }

  btn.disabled = true;
  btn.textContent = 'جارٍ الإرسال...';

  try {
    const res = await fetch('/order/place', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        car_plate: carPlate,
        car_color: carColor,
        car_model: carModel,
        parking_spot: parkingSpot,
        notes: notes,
        items: cart.map(i => ({ id: i.id, qty: i.qty }))
      })
    });

    const data = await res.json();
    if (data.success) {
      cart = [];
      updateCartUI();
      closeOrderModal();
      window.location.href = `/order/confirm/${data.order_number}`;
    } else {
      showError(data.error || 'حدث خطأ، حاول مرة أخرى');
    }
  } catch (e) {
    showError('تعذر الاتصال بالخادم');
  } finally {
    btn.disabled = false;
    btn.textContent = 'تأكيد الطلب 🚗';
  }
}

function showError(msg) {
  const el = document.getElementById('orderError');
  el.textContent = msg;
  el.classList.remove('hidden');
}

function showAddFeedback() {
  // Brief visual pulse on the cart bar
  const bar = document.getElementById('cartBar');
  if (bar) {
    bar.style.transform = 'scale(1.02)';
    setTimeout(() => { bar.style.transform = ''; }, 150);
  }
}

function scrollToCategory(id) {
  const el = document.getElementById(id);
  if (el) {
    const offset = 140; // header height
    const top = el.getBoundingClientRect().top + window.scrollY - offset;
    window.scrollTo({ top, behavior: 'smooth' });
  }
}

// Highlight active category tab on scroll
function updateActiveTabs() {
  const sections = document.querySelectorAll('section[id^="cat-"]');
  let active = null;
  sections.forEach(sec => {
    const rect = sec.getBoundingClientRect();
    if (rect.top <= 160) active = sec.id.replace('cat-', '');
  });
  document.querySelectorAll('.category-tab').forEach(tab => {
    const tabId = tab.id.replace('tab-', '');
    if (tabId === active) {
      tab.style.background = 'rgba(255,255,255,0.25)';
      tab.style.borderColor = 'rgba(255,255,255,0.7)';
    } else {
      tab.style.background = '';
      tab.style.borderColor = '';
    }
  });
}

window.addEventListener('scroll', updateActiveTabs, { passive: true });
