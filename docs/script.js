const $ = id => document.getElementById(id);
let supplements = [], currentData = [], chartInstance = null, radarInstance = null;

(function skeleton() {
  let h = ''; for (let i = 0; i < 8; i++) h += '<div class="card skeleton"></div>';
  $('cardsGrid').innerHTML = h;
})();

fetch('data.json')
  .then(r => { if (!r.ok) throw new Error('no data'); return r.json(); })
  .then(d => { supplements = d; initApp(); })
  .catch(() => { document.body.innerHTML = '<p style="color:red">❌ Не удалось загрузить data.json</p>'; });

function initApp() {
  const saved = localStorage.getItem('theme');
  if (saved === 'dark' || (!saved && matchMedia('(prefers-color-scheme: dark)').matches)) setDark(true);
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
  applyFilters(); renderCompare();
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
}

function renderCards(data) {
  const g = $('cardsGrid');
  if (!data.length) { g.innerHTML = '<p style="opacity:.6">Ничего не найдено — попробуй другие фильтры.</p>'; return; }
  g.innerHTML = data.map(s => '<div class="card" data-id="' + s.id + '">' +
    '<span class="cat">' + (s.category || '') + '</span><h3>' + s.name + '</h3>' +
    '<div class="verdict" style="background:' + vColor(s.code) + '">' + s.verdict + '</div>' +
    '<div class="price">' + (s.price ? s.price + ' ₽/мес' : 'цена не указана') + '</div>' +
    (val(s) !== null ? '<div class="value">⚖️ ценность: ' + val(s) + '</div>' : '') +
    '<div class="effects">' + (s.effects || []).map(e => '<span>' + e + '</span>').join('') + '</div></div>').join('');
  g.querySelectorAll('.card').forEach(el => el.onclick = () => openModal(el.dataset.id));
}

function openModal(id) {
  const s = supplements.find(x => x.id === id); if (!s) return;
  const trialsLine = s.ongoing != null
    ? (s.ongoing > 0
        ? '<div class="mrow">🧪 <b>Активных испытаний: ' + s.ongoing + '</b> — сейчас проверяют на людях</div>'
        : '<div class="mrow warn">❄️ Активных испытаний: 0 — сейчас никто не проверяет на людях</div>')
    : '';
  $('modalBody').innerHTML = '<h2>' + s.name + '</h2>' +
    '<div class="mrow"><span class="verdict" style="background:' + vColor(s.code) + '">' + s.verdict + '</span> · ' + (s.category || '') + '</div>' +
    '<div class="mrow">💰 <b>' + (s.price ? s.price + ' ₽/мес' : '—') + '</b> · 🔬 наука: <b>' + s.scienceIndex + '</b> · 📚 MA: <b>' + s.metaCount + '</b>' + (val(s) !== null ? ' · ⚖️ ценность: <b>' + val(s) + '</b>' : '') + '</div>' +
    trialsLine +
    (s.citations != null ? '<div class="mrow">📖 Цитирований ключевого MA: ' + s.citations + '</div>' : '') +
    (s.reviews != null ? '<div class="mrow">🛒 Отзывов WB: ' + s.reviews.toLocaleString('ru-RU') + ' · 📈 поиск 5 лет: ' + (s.trends ?? '—') + ' · 🌐 Wiki: ' + (s.wiki != null ? s.wiki.toLocaleString('ru-RU') : '—') + '</div>' : '') +
    '<div class="mrow"><b>Эффекты:</b> ' + ((s.effects || []).join(', ') || '—') + '</div>' +
    '<div class="mrow">💊 <b>Дозировка:</b> ' + (s.dosage || '—') + '</div>' +
    '<div class="mrow">⏳ <b>Курс:</b> ' + (s.course || '—') + '</div>' +
    (s.forms ? '<div class="mrow">🧪 <b>Формы/штаммы:</b> ' + s.forms + '</div>' : '') +
    '<div class="mrow warn">⚠️ ' + (s.caution || '—') + '</div>';
  $('modalOverlay').style.display = 'flex';
}
function closeModal() { $('modalOverlay').style.display = 'none'; }

function renderBubble(data) {
  const plotted = data.filter(s => s.price > 0);
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
      plugins: { legend: { display: false }, tooltip: { enabled: false } },
      onHover: (evt, els) => { if (els && els.length) showTooltip(evt, plotted[els[0].datasetIndex]); else hideTooltip(); }
    }
  });
  $('bubbleChart').addEventListener('mouseleave', hideTooltip);
}

function showTooltip(evt, s) {
  if (!s) return;
  const rect = $('chartWrap').getBoundingClientRect();
  const nx = evt.native ? evt.native.clientX : evt.clientX;
  const ny = evt.native ? evt.native.clientY : evt.clientY;
  const t = $('tooltip');
  t.style.display = 'block';
  t.innerHTML = '<strong>' + s.name + '</strong>' +
    '<div class="detail">' + s.verdict + ' · ' + (s.category || '') + '</div>' +
    '<div class="detail">💰 ' + (s.price ? s.price + ' ₽/мес' : '—') + ' · 🔬 ' + s.scienceIndex + ' · 📚 ' + s.metaCount + ' MA</div>' +
    (val(s) !== null ? '<div class="detail">⚖️ ценность: ' + val(s) + ' науки на 100 ₽</div>' : '') +
    (s.ongoing != null ? '<div class="detail">🧪 испытаний сейчас: ' + s.ongoing + '</div>' : '');
  t.style.left = (nx - rect.left + 12) + 'px';
  t.style.top = (ny - rect.top - 10) + 'px';
}
function hideTooltip() { $('tooltip').style.display = 'none'; }

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
        { label: a.name, data: prof(a), borderColor: '#3498db', backgroundColor: 'rgba(52,152,219,.2)' },
        { label: b.name, data: prof(b), borderColor: '#e67e22', backgroundColor: 'rgba(230,126,34,.2)' }
      ]
    },
    options: { scales: { r: { min: 0, max: 100, ticks: { display: false } } }, plugins: { legend: { position: 'bottom' } } }
  });
}