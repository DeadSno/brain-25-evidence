/* v2.7-C (Пульс науки + спарклайн): инвазивно-минимальный слой.
   - Пульс науки: линия «мета-анализы по годам» (2015–2026) из docs/data_ma_timeline.json.
   - Спарклайн цены в блоке «Экономика» модалки: 90 дней price_history.csv.
   Изоляция P12: читаем данные, ничего не пишем. Модалку НЕ переопределяем
   (не воюем с веткой A трекера) — только MutationObserver. */
(() => {
  'use strict';
// ── XSS protection ─────────────────────────────────────────────
function esc(s) {
  return String(s == null ? '' : s).replace(/[&<>"']/g, c => (
    { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
  ));
}
  if (window.__science2Loaded) return;
  window.__science2Loaded = true;

  // ========== C3: «Пульс науки» — Chart.js линия 2015–2026 ==========
  function renderPulse(rows) {
    if (!rows || !rows.length || document.getElementById('maTimelineBox')) return;
    const main = document.getElementById('chartSection');
    if (!main) return;
    const box = document.createElement('section');
    box.id = 'maTimelineBox';
    box.style.cssText =
      'background:var(--card-bg);padding:1.2rem 1.5rem;border-radius:12px;' +
      'border:1px solid var(--border);margin-bottom:2rem';
    box.innerHTML =
      '<h2>Пульс науки: мета-анализы по годам</h2>' +
      '<p class="hint" style="margin-top:-.4rem;margin-bottom:.6rem">' +
      'Топ-5 по приросту к прошлому году — в инспекторе элемента.<br>' +
      'Источник: PubMed (esearch+esummary, запрос как в scienceIndex), по каждой добавке.' +
      '</p>' +
      '<div style="position:relative;height:260px">' +
      '<canvas id="maTimelineCanvas"></canvas>' +
      '</div>' +
      '<p class="hint" style="margin-top:.5rem">' +
      'Годы без мета-анализов в выборке = 0 (честно). Кэш: data/processed/ma_years.json.</p>';
    main.insertAdjacentElement('beforebegin', box);

    const css = getComputedStyle(document.body);
    const txt = (css.getPropertyValue('--text') || '#333').trim();
    const accent = (css.getPropertyValue('--accent') || '#007bff').trim();
    const grid = 'rgba(128,128,128,.18)';

    let chart = null;
    try {
      if (typeof Chart === 'undefined') throw new Error('Chart.js не загружен');
      chart = new Chart(document.getElementById('maTimelineCanvas'), {
        type: 'line',
        data: {
          labels: rows.map(r => String(r.year)),
          datasets: [{
            label: 'Мета-анализы',
            data: rows.map(r => r.total),
            borderColor: accent,
            backgroundColor: accent + '1a',
            fill: true,
            tension: .3,
            pointRadius: 4,
            pointHoverRadius: 6,
            borderWidth: 2,
          }],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: {
            x: { ticks: { color: txt, maxRotation: 0 }, grid: { color: grid } },
            y: { beginAtZero: true, ticks: { color: txt, precision: 0 }, grid: { color: grid } },
          },
        },
      });
    } catch (err) {
      console.warn('Пульс науки (Chart.js): ' + err.message);
    }

    window.maPulseChart = chart || null;
    window.maPulseData = { years: rows.map(r => r.year), totals: rows.map(r => r.total) };
    window.dispatchEvent(new CustomEvent('maPulseReady'));
  }

  function loadPulse() {
    fetch('data_ma_timeline.json', { cache: 'no-store' })
      .then(r => (r.ok ? r.json() : Promise.reject(new Error('http ' + r.status))))
      .then(rows => renderPulse(rows))
      .catch(err => {
        console.warn('Пульс науки: нет данных — ' + err.message);
        window.maPulseFailed = true;
      });
  }

  // ========== C4: спарклайн цены (блок «Экономика» модалки) ==========
  // Данные: docs/data_price_history.json (собрано из data/processed/price_history.csv
  // скриптом scripts/build_ma_timeline.py). CSV живёт вне docs/ и в deploy не сервится —
  // агрегируем при сборке, поле id сохраняется. Пустой/отсутствующий → фолбэк-текст.
  function curId() {
    try { if (curModal) return String(curModal); } catch (e) { /* другие части не трогаем */ }
    const m = location.hash.match(/#sup=([^&]*)/);
    if (m && m[1]) { try { return decodeURIComponent(m[1]); } catch (e) { return m[1]; } }
    const h2 = document.querySelector('#modalBody h2');
    return h2 ? h2.textContent.trim() : '';
  }

  function priceFor(id, doc) {
    const pts = doc && doc[id];
    if (!Array.isArray(pts)) return [];
    const out = [];
    for (const pair of pts) {
      if (!Array.isArray(pair) || pair.length < 2) continue;
      const d = String(pair[0] || '').trim();
      const p = Number(pair[1]);
      if (d && !isNaN(p) && p > 0) out.push({ d, p });
    }
    out.sort((a, b) => a.d.localeCompare(b.d));
    return out.slice(-90);
  }

  function fetchPriceDoc() {
    return fetch('data_price_history.json', { cache: 'no-store' })
      .then(r => (r.ok ? r.json() : Promise.reject(new Error('http ' + r.status))))
      .catch(() => ({}));
  }

  function drawSpark(cv, w, h, pts) {
    const dpr = window.devicePixelRatio || 1;
    cv.width = Math.round(w * dpr);
    cv.height = Math.round(h * dpr);
    const ctx = cv.getContext('2d');
    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, w, h);
    if (pts.length < 2) return;
    const min = Math.min(...pts.map(p => p.p));
    const max = Math.max(...pts.map(p => p.p));
    const rng = (max - min) || 1;
    const X = i => pts.length === 1 ? w / 2 : 2 + i / (pts.length - 1) * (w - 4);
    const Y = v => h - 4 - ((v - min) / rng) * (h - 10);
    ctx.beginPath();
    pts.forEach((p, i) => {
      const x = X(i), y = Y(p.p);
      i ? ctx.lineTo(x, y) : ctx.moveTo(x, y);
    });
    ctx.strokeStyle = '#007bff';
    ctx.lineWidth = 1.6;
    ctx.lineJoin = 'round';
    ctx.stroke();
    ctx.beginPath();
    ctx.arc(X(pts.length - 1), Y(pts[pts.length - 1].p), 2.4, 0, Math.PI * 2);
    ctx.fillStyle = '#007bff';
    ctx.fill();
  }

  function renderSpark(id) {
    const el = document.getElementById('ecoSpark');
    if (!el || el.dataset.state) return;
    el.innerHTML = '<span class="hint">…</span>';
    fetchPriceDoc().then(doc => {
      if (el.dataset.state) return;
      const pts = priceFor(id, doc);
      if (pts.length < 2) {
        const have = pts.length;
        const need = Math.max(90 - have, 2);
        el.dataset.state = 'fallback';
        el.dataset.points = String(have);
        el.innerHTML =
          '<span class="hint">история копится с v2.1, спарклайн появится после ' +
          need + ' замеров' + (have ? ' (сейчас ' + have + ')' : '') + '</span>';
        return;
      }
      el.dataset.state = 'canvas';
      el.dataset.points = String(pts.length);
      const box = el.parentNode;
      const w = Math.max(140, (box.getBoundingClientRect().width || 200));
      const h = 34;
      el.innerHTML = '';
      const cv = document.createElement('canvas');
      cv.style.cssText = 'width:100%;height:' + h + 'px';
      cv.setAttribute('data-eco-spark', 'canvas');
      el.appendChild(cv);
      drawSpark(cv, w, h, pts);
      const fmt = new Intl.DateTimeFormat('ru-RU', { day: '2-digit', month: 'short', year: 'numeric' });
      const s = document.createElement('div');
      s.className = 'hint';
      s.style.cssText = 'font-size:.7rem;margin-top:.2rem';
      s.textContent = fmt.format(new Date(pts[0].d)) + ' → ' + fmt.format(new Date(pts[pts.length - 1].d));
      el.appendChild(s);
    });
  }

  function sparkContainer() {
    const wrap = document.createElement('div');
    wrap.style.cssText =
      'margin-top:.45rem;padding:.5rem .6rem;background:var(--bg);' +
      'border-radius:8px;border:1px solid var(--border)';
    const head = document.createElement('div');
    head.style.cssText =
      'font-size:.72rem;font-weight:600;opacity:.7;text-transform:uppercase;' +
      'letter-spacing:.02em;margin-bottom:.3rem';
    head.textContent = '📈 Цена: динамика 90 дней';
    wrap.appendChild(head);
    const el = document.createElement('div');
    el.id = 'ecoSpark';
    wrap.appendChild(el);
    return { wrap, el };
  }

  function hookSparkline() {
    const overlay = document.getElementById('modalOverlay');
    if (!overlay) return;
    const obs = new MutationObserver(() => {
      const body = document.getElementById('modalBody');
      if (!body || document.getElementById('ecoSpark')) return;
      const btns = body.querySelectorAll('.blockTitle');
      let econ = null;
      for (const b of btns) {
        if ((b.textContent || '').includes('История цены')) { econ = b; break; }
      }
      if (!econ) return;
      const id = curId();
      if (!id) return;
      const { wrap, el } = sparkContainer();
      econ.insertAdjacentElement('afterend', wrap);
      renderSpark(id);
    });
    obs.observe(overlay, { childList: true, subtree: true });
  }

  // ========== init ==========
  function init() {
    if (document.getElementById('chartSection')) loadPulse();
    hookSparkline();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();