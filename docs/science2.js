/* v2.7-C (Пульс науки + спарклайн): инвазивно-минимальный слой.
   - Пульс науки: линия «мета-анализы по годам» (2015–2026) из docs/data_ma_timeline.json.
   - Спарклайн цены в блоке «Экономика» модалки: 90 дней price_history.csv.
   Изоляция P12: читаем данные, ничего не пишем. Модалку НЕ переопределяем
   (не воюем с веткой A трекера) — только MutationObserver. */
(() => {
  'use strict';
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

  })();