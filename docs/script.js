const $ = id => document.getElementById(id);
let supplements = [], currentData = [], chartInstance = null, radarInstance = null, onlyFavs = false;
let chartPts = [];
let scrollBeforeModal = 0;
let BEST = [];

function chartSupByEl(chart, el) {
  const ds = (chart.data.datasets || [])[el.datasetIndex] || {};
  if (ds.label) {
    const byLabel = supplements.find(x => x.id === ds.label || x.name === ds.label);
    if (byLabel) return byLabel;
  }
  return chartPts[el.index] || chartPts[el.datasetIndex];
}

(function skeleton() {
  let h = ''; for (let i = 0; i < 8; i++) h += '<div class="card skeleton"></div>';
  $('cardsGrid').innerHTML = h;
})();

fetch('data.json?ts=' + Date.now())
  .then(r => { if (!r.ok) throw new Error('no data'); return r.json(); })
  .then(d => { supplements = d; initApp(); })
  .catch(() => { document.body.innerHTML = '<p style="color:red">❌ Не удалось загрузить data.json</p>'; });

function initApp() {
  BEST = supplements.filter(s => val(s) !== null).sort((x, y) => val(y) - val(x)).slice(0, 3).map(s => s.id);
  const saved = localStorage.getItem('theme');
  if (saved !== 'light') setDark(true);   // v1.3: по умолчанию тёмная; светлая — только по выбору
  [...new Set(supplements.map(s => s.category).filter(Boolean))].sort()
    .forEach(c => $('categoryFilter').add(new Option(c, c)));
  supplements.forEach(s => { $('compareSelect1').add(new Option(s.name, s.id)); $('compareSelect2').add(new Option(s.name, s.id)); });
  if (supplements.length >= 2) { $('compareSelect1').value = supplements[0].id; $('compareSelect2').value = supplements[1].id; }
  $('search').addEventListener('input', applyFilters);
  ['verdictFilter', 'categoryFilter', 'sortSelect'].forEach(id => $(id).addEventListener('change', applyFilters));
  $('themeToggle').onclick = () => { const on = !document.body.classList.contains('dark'); setDark(on); localStorage.setItem('theme', on ? 'dark' : 'light'); };
  $('compareBtn').onclick = renderCompare;
  $('modalClose').onclick = closeModal;
  $('modalOverlay').onclick = e => { if (e.target.id === 'modalOverlay') closeModal(); };
  document.addEventListener('keydown', e => { if (e.key === 'Escape') closeModal(); });
  const deep = decodeURIComponent(location.hash.replace('#sup=', ''));
  if (deep && supplements.some(s => s.id === deep)) setTimeout(() => openModal(deep), 300);
  applyFilters(); renderCompare();
  $('favFilter').addEventListener('click', () => {
    onlyFavs = !onlyFavs;
    $('favFilter').classList.toggle('on', onlyFavs);
    applyFilters();
  });

  $('resetFilters').addEventListener('click', () => {
    const row = $('favFilter').parentElement;
    row.querySelectorAll('input').forEach(i => { i.value = ''; });
    row.querySelectorAll('select').forEach(s => { s.selectedIndex = 0; });
    onlyFavs = false;
    $('favFilter').classList.remove('on');
    applyFilters();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });

  document.addEventListener('click', e => {
    const b = e.target.closest('[data-fav]');
    if (!b) return;
    e.stopPropagation(); e.preventDefault();
    toggleFav(b.dataset.fav);
  }, true);
}

function setDark(on) {
  document.body.classList.toggle('dark', on);
  $('themeToggle').textContent = on ? '☀️ Светлая тема' : '🌙 Тёмная тема';
  if (currentData.length) renderBubble(currentData);
}

const vColor = c => c === 1 ? '#2d8a4e' : c === 0 ? '#d4a017' : '#c0392b';
const val = s => s.price > 0 ? +(s.scienceIndex / s.price * 100).toFixed(1) : null;

function applyFilters() {
  const q = $('search').value.toLowerCase().trim();
  const v = $('verdictFilter').value, c = $('categoryFilter').value, sort = $('sortSelect').value;
  currentData = supplements.filter(s => {
    if (v !== 'all' && String(s.code) !== v) return false;
    if (c !== 'all' && s.category !== c) return false;
    if (q && !(s.name.toLowerCase().includes(q) || (s.effects || []).join(' ').toLowerCase().includes(q))) return false;
    return true;
  });
  if (onlyFavs) currentData = currentData.filter(x => isFav(x.id));
  const cmp = {
    science: (a, b) => b.scienceIndex - a.scienceIndex,
    value: (a, b) => (val(b) || -1) - (val(a) || -1),
    price_asc: (a, b) => (a.price || 1e9) - (b.price || 1e9),
    reviews: (a, b) => (b.reviews || 0) - (a.reviews || 0),
    name: (a, b) => a.name.localeCompare(b.name, 'ru')
  };
  currentData.sort(cmp[sort]);
  $('countBadge').textContent = '(' + currentData.length + ' из ' + supplements.length + ')';
  renderCards(currentData); renderBubble(currentData);
  updateFavUI();
}

function renderCards(data) {
  const g = $('cardsGrid');
  if (!data.length) { g.innerHTML = '<p style="opacity:.6">Ничего не найдено — попробуй другие фильтры.</p>'; return; }
  g.innerHTML = data.map(s => '<div class="card" data-id="' + s.id + '">' +
    '<button class="favBtn' + (isFav(s.id) ? ' on' : '') + '" data-fav="' + s.id + '" title="В избранное">' + (isFav(s.id) ? '★' : '☆') + '</button>' +
    (BEST.includes(s.id) ? '<span class="bestBadge">🏆 Лучший выбор</span>' : '') +
    '<span class="cat">' + (s.category || '') + '</span><h3>' + s.name + '</h3>' +
    '<div class="verdict v' + s.code + '">' + s.verdict + '</div>' +
    '<div class="price">' + (s.price ? s.price + ' ₽/мес' : 'цена не указана') + '</div>' +
    (val(s) !== null ? '<div class="value">⚖️ ценность: ' + val(s) + '</div>' : '') +
    (val(s) !== null ? '<div class="valBar"><i style="width:' + Math.min(100, val(s) / 3) + '%"></i></div>' : '') +
    '<div class="effects">' + (s.effects || []).map(e => '<span>' + e + '</span>').join('') + '</div></div>').join('');
  g.querySelectorAll('.card').forEach(el => el.onclick = () => openModal(el.dataset.id));
}

function openModal(id) {
  scrollBeforeModal = window.scrollY || 0;
  const s = supplements.find(x => x.id === id); if (!s) return;

  const trialsLine = s.ongoing != null
    ? (s.ongoing > 0
        ? '<div class="mrow">🧪 <b>Активных испытаний: ' + s.ongoing + '</b> — сейчас проверяют на людях</div>'
        : '<div class="mrow warn">❄️ Активных испытаний: 0 — сейчас никто не проверяет на людях</div>')
    : '';

  const calcLine = s.dosagePerKg != null
    ? '<div class="mrow calc">' +
      '<label for="weightInput">📏 <b>Калькулятор дозировки:</b></label>' +
      '<div class="calcRow">' +
      '<input type="number" id="weightInput" placeholder="Ваш вес (кг)" min="30" max="200" step="0.1"/>' +
      '<span id="calcResult" class="calcResult"></span>' +
      '</div>' +
      '<small class="hint">Стандартная доза: ' + (s.dosage || '—') + '</small>' +
      '</div>'
    : '';

  $('modalBody').innerHTML = '<h2>' + s.name + '</h2>' +
    '<div class="mrow"><span class="verdict v' + s.code + '">' + s.verdict + '</span> · ' + (s.category || '') + '</div>' +
    '<div class="mrow">💰 <b>' + (s.price ? s.price + ' ₽/мес' : '—') + '</b> · 🔬 наука: <b>' + s.scienceIndex + '</b> · 📚 MA: <b>' + s.metaCount + '</b>' + (val(s) !== null ? ' · ⚖️ ценность: <b>' + val(s) + '</b>' : '') + '</div>' +
    '<div class="mrow">🛒 <a class="wbLink" target="_blank" rel="noopener" href="https://www.wildberries.ru/catalog/0/search.aspx?search=' + encodeURIComponent(s.name) + '">Проверить актуальную цену на WB</a></div>' +
    trialsLine +
    calcLine +
    (s.citations != null ? '<div class="mrow">📖 Цитирований ключевого MA: ' + s.citations + '</div>' : '') +
    (s.reviews != null ? '<div class="mrow">🛒 Отзывов WB: ' + s.reviews.toLocaleString('ru-RU') + ' · 📈 поиск 5 лет: ' + (s.trends ?? '—') + ' · 🌐 Wiki: ' + (s.wiki != null ? s.wiki.toLocaleString('ru-RU') : '—') + '</div>' : '') +
    '<div class="mrow"><b>Эффекты:</b> ' + ((s.effects || []).join(', ') || '—') + '</div>' +
    '<div class="mrow">💊 <b>Дозировка:</b> ' + (s.dosage || '—') + '</div>' +
    '<div class="mrow">⏳ <b>Курс:</b> ' + (s.course || '—') + '</div>' +
    (s.forms ? '<div class="mrow">🧪 <b>Формы/штаммы:</b> ' + s.forms + '</div>' : '') +
    '<div class="mrow warn">⚠️ ' + (s.caution || '—') + '</div>';
  history.replaceState(null, '', '#sup=' + encodeURIComponent(s.id));
  $('modalOverlay').style.display = 'flex';

  if (s.dosagePerKg != null) {
    const weightInput = $('weightInput');
    const calcResult = $('calcResult');
    weightInput.addEventListener('input', () => {
      const weight = parseFloat(weightInput.value);
        if (weight > 0 && weight <= 500) {
        const dose = weight * s.dosagePerKg;
        const unit = s.dosage && s.dosage.includes('мг') ? 'мг' : s.dosage && s.dosage.includes('г') ? 'г' : 'МЕ';
        let html = '<b>' + dose.toFixed(1) + ' ' + unit + '/сут</b>';
        if (s.dosageMax && dose > s.dosageMax) {
          html += ' <span class="warn">⚠️ превышает максимум (' + s.dosageMax + ' ' + unit + ')</span>';
        }
        calcResult.innerHTML = html;
      } else {
        calcResult.innerHTML = '';
      }
    });
  }
}
function closeModal() {
  $('modalOverlay').style.display = 'none';
  history.replaceState(null, '', location.pathname);
  window.scrollTo({ top: scrollBeforeModal, behavior: 'smooth' });
}

function renderBubble(data) {
  const plotted = data.filter(s => s.price > 0);
  chartPts = plotted;
  $('chartNote').textContent = plotted.length < data.length
    ? '⚠️ ' + (data.length - plotted.length) + ' добавок без цены не показаны на графике (ждут батчей WB)' : '';
  const ctx = $('bubbleChart').getContext('2d');
  if (chartInstance) chartInstance.destroy();
  const txt = getComputedStyle(document.body).getPropertyValue('--text');
  chartInstance = new Chart(ctx, {
    type: 'scatter',
    data: { datasets: plotted.map(s => ({
      label: s.name,
      data: [{ x: s.price, y: Math.max(1, s.scienceIndex) }],
      backgroundColor: vColor(s.code),
      pointRadius: Math.min(30, Math.sqrt(s.metaCount || 1) * 2.5),
      pointHoverRadius: Math.min(36, Math.sqrt(s.metaCount || 1) * 3.5)
    })) },
    options: {
      responsive: true, maintainAspectRatio: true,
      scales: {
        x: { title: { display: true, text: 'Цена за месяц (₽)', color: txt }, grid: { color: 'rgba(128,128,128,.15)' } },
        y: { type: 'logarithmic',
             title: { display: true, text: 'Индекс науки (лог)', color: txt },
             grid: { color: 'rgba(128,128,128,.15)' },
             ticks: { callback: v => [1, 10, 100, 1000, 10000].includes(v) ? v : '' } }
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: ctx => {
              const s = chartSupByEl(ctx.chart, { datasetIndex: ctx.datasetIndex, index: ctx.dataIndex });
              return s ? ' ' + s.name + ' · ' + (s.price ?? '—') + ' ₽/мес · ' + s.verdict : '';
            }
          }
        }
      },
      onClick: (e, els) => {
        if (!els.length) return;
        const s = chartSupByEl(e.chart, els[0]);
        if (!s) return;
        openModal(s.id);
      },
      onHover: (e, els) => {
        e.native.target.style.cursor = els.length ? 'pointer' : 'default';
      }
    }
  });
}

function radarFill(ctx) {
  const { chart } = ctx; const { ctx: c, chartArea } = chart;
  if (!chartArea) return 'rgba(52,152,219,.25)';
  const cx = (chartArea.left + chartArea.right) / 2, cy = (chartArea.top + chartArea.bottom) / 2;
  const g = c.createRadialGradient(cx, cy, 8, cx, cy, Math.max(chartArea.width, chartArea.height) / 2);
  g.addColorStop(0, 'rgba(46,204,113,.38)');
  g.addColorStop(1, 'rgba(52,152,219,.12)');
  return g;
}

function renderCompare() {
  const a = supplements.find(s => s.id === $('compareSelect1').value);
  const b = supplements.find(s => s.id === $('compareSelect2').value);
  if (!a || !b) return;
  const rows = [
    ['Вердикт', a.verdict, b.verdict],
    ['Цена (₽/мес)', a.price ?? '—', b.price ?? '—'],
    ['⚖️ Ценность', val(a) ?? '—', val(b) ?? '—'],
    ['Индекс науки', a.scienceIndex, b.scienceIndex],
    ['Мета-анализов', a.metaCount, b.metaCount],
    ['🧪 Испытания сейчас', a.ongoing ?? '—', b.ongoing ?? '—'],
    ['Цитирований MA', a.citations ?? '—', b.citations ?? '—'],
    ['Отзывов на WB', a.reviews ?? '—', b.reviews ?? '—'],
    ['Поиск (5 лет)', a.trends ?? '—', b.trends ?? '—'],
    ['Эффекты', (a.effects || []).join(', '), (b.effects || []).join(', ')],
    ['Дозировка', a.dosage ?? '—', b.dosage ?? '—'],
    ['Курс', a.course ?? '—', b.course ?? '—'],
    ['⚠️ Осторожно', a.caution ?? '—', b.caution ?? '—']
  ];
  $('compareResult').innerHTML = '<table><tr><th>Параметр</th><th>' + a.name + '</th><th>' + b.name + '</th></tr>' +
    rows.map(r => '<tr><td>' + r[0] + '</td><td>' + r[1] + '</td><td>' + r[2] + '</td></tr>').join('') + '</table>';

  const mx = k => Math.max(1, ...supplements.map(s => s[k] || 0));
  const mPr = Math.max(1, ...supplements.map(s => s.price || 0));
  const prof = s => [
    s.scienceIndex / mx('scienceIndex') * 100,
    (s.metaCount || 0) / mx('metaCount') * 100,
    (s.reviews || 0) / mx('reviews') * 100,
    (s.trends || 0) / mx('trends') * 100,
    Math.max(0, (1 - (s.price || mPr) / mPr) * 100)
  ];
  if (radarInstance) radarInstance.destroy();
  radarInstance = new Chart($('radarChart'), {
    type: 'radar',
    data: {
      labels: ['Наука', 'База MA', 'Спрос (WB)', 'Интерес (trends)', 'Доступность'],
      datasets: [
        { label: a.name, data: prof(a), borderColor: '#3498db', backgroundColor: radarFill },
        { label: b.name, data: prof(b), borderColor: '#e67e22', backgroundColor: radarFill }
      ]
    },
    options: { scales: { r: { min: 0, max: 100, ticks: { display: false } } }, plugins: { legend: { position: 'bottom' } } }
  });
}

// ===== v1.3: избранное =====
function getFavs() { try { return JSON.parse(localStorage.getItem('favs') || '[]'); } catch (e) { return []; } }
function setFavs(a) { localStorage.setItem('favs', JSON.stringify(a)); }
function isFav(id) { return getFavs().includes(id); }
function toggleFav(id) {
  const f = getFavs();
  const i = f.indexOf(id);
  if (i >= 0) f.splice(i, 1); else f.push(id);
  setFavs(f);
  updateFavUI();
}
function updateFavUI() {
  const favs = getFavs();
  const c = $('favCount'); if (c) c.textContent = favs.length;
  document.querySelectorAll('[data-fav]').forEach(b => {
    const on = favs.includes(b.dataset.fav);
    b.classList.toggle('on', on);
    b.textContent = on ? '★' : '☆';
  });
}