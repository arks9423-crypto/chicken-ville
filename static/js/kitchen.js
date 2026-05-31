// QRMenu Kitchen Display — Auto-reload every 10 seconds
'use strict';

let countdown = 10;
const countdownEl = document.getElementById('countdown');

function tick() {
  countdown--;
  if (countdownEl) countdownEl.textContent = countdown;
  if (countdown <= 0) {
    location.reload();
  }
}

setInterval(tick, 1000);
