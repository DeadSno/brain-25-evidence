let supplements = [], currentData = [], chartInstance = null;

fetch('data.json')
  .then(r => { if (!r.ok) throw new Error('no data.json'); return r.json(); })
  .then(d => { supplements = d; currentData = d; initApp(); })
  .catch(e => { console.error(e); document.body.innerHTML = '<p style="color:red">❌ Не удалось загрузить data.json</p>'; });

function initApp() {
  populateSymptomFilter(); setupSymptomFilter();
  renderCards(currentData); renderBubbleChart(currentData);
  populateCompareSelects(); setupCompareButton(); setupThemeToggle();
}

function populateSymptomFilter() {
  const set = new Set();
  supplements.forEach(s => (s.effects || []).forEach(e => set.add(e)));
  const sel = document.getElementById('symptomSelect');
  set.forEach(e => sel.add(new Option(e, e)));
}
function setupSymptomFilter() {
  document.getElementById('symptomSelect').addEventListener('change', function () {
    currentData = this.value === 'all' ? supplements
      : supplements.filter(s => (s.effects || []).includes(this.value));
    renderCards(currentData); renderBubbleChart(currentData);
  });
}

function verdictColor(code) { return code === 1 ? '#2d8a4e' : code === 0 ? '#d4a017' : '#c0392b'; }

function renderCards(data) {
  const grid = document.getElementById('cardsGrid');
  if (!data.length) { grid.innerHTML = '<p style="opacity:.6">Нет добавок</p>'; return; }
  grid.innerHTML = data.map(s => `
    <div class="card">
      <h3>${s.name}</h3>
      <div class="verdict" style="background:${verdictColor(s.code)}">${s.verdict}</div>
      <div class="price">${s.price ? s.price + ' ₽/мес' : 'цена не указана'}</div>
      <div class="effects">${(s.effects || []).map(e => `<span>${e}</span>`).join('')}</div>
    </div>`).join('');
}

function renderBubbleChart(data) {
  const ctx = document.getElementById('bubbleChart').getContext('2d');
  if (chartInstance) chartInstance.destroy();
  const txt = getComputedStyle(document.body).getPropertyValue('--text');
  chartInstance = new Chart(ctx, {
    type: 'scatter',
    data: { datasets: data.map(s => ({
      label: s.name,
      data: [{ x: s.price || 0, y: s.scienceIndex || 0 }],
      backgroundColor: verdictColor(s.code),
      pointRadius: Math.min(30, Math.sqrt(s.metaCount || 1) * 2.5),
      pointHoverRadius: Math.min(36, Math.sqrt(s.metaCount || 1) * 3.5)
    })) },
    options: {
      responsive: true, maintainAspectRatio: true,
      scales: {
        x: { title: { display: true, text: 'Цена за месяц (₽)', color: txt }, grid: { color: 'rgba(128,128,128,.15)' } },
        y: { title: { display: true, text: 'Индекс науки', color: txt }, grid: { color: 'rgba(128,128,128,.15)' } }
      },
      plugins: { legend: { display: false }, tooltip: { enabled: false } },
      onHover: (evt, els) => {
        if (els && els.length) showTooltip(evt, data[els[0].datasetIndex]);
        else hideTooltip();
      }
    }
  });
  document.getElementById('bubbleChart').addEventListener('mouseleave', hideTooltip);
}

function showTooltip(evt, s) {
  if (!s) return;
  const wrap = document.getElementById('chartWrap');
  const rect = wrap.getBoundingClientRect();
  const nx = evt.native ? evt.native.clientX : evt.clientX;
  const ny = evt.native ? evt.native.clientY : evt.clientY;
  const t = document.getElementById('tooltip');
  t.style.display = 'block';
  t.innerHTML = `<strong>${s.name}</strong>
    <div class="detail">Вердикт: ${s.verdict} | наука: ${s.scienceIndex}</div>
    <div class="detail">Мета-анализов: ${s.metaCount}${s.citations != null ? ', цитирований: ' + s.citations : ''}</div>
    <div class="detail">💊 ${s.dosage || 'дозировка не указана'}</div>
    <div class="detail">⏳ ${s.course || '—'}</div>
    <div class="detail">⚠️ ${s.caution || '—'}</div>`;
  t.style.left = (nx - rect.left + 12) + 'px';
  t.style.top = (ny - rect.top - 10) + 'px';
}
function hideTooltip() { document.getElementById('tooltip').style.display = 'none'; }

function populateCompareSelects() {
  const s1 = document.getElementById('compareSelect1'), s2 = document.getElementById('compareSelect2');
  supplements.forEach(s => { s1.add(new Option(s.name, s.id)); s2.add(new Option(s.name, s.id)); });
  if (supplements.length >= 2) { s1.value = supplements[0].id; s2.value = supplements[1].id; }
}
function setupCompareButton() {
  document.getElementById('compareBtn').addEventListener('click', () => {
    const a = supplements.find(s => s.id === document.getElementById('compareSelect1').value);
    const b = supplements.find(s => s.id === document.getElementById('compareSelect2').value);
    if (!a || !b) return;
    const rows = [
      ['Вердикт', a.verdict, b.verdict],
      ['Цена (₽/мес)', a.price ?? '—', b.price ?? '—'],
      ['Индекс науки', a.scienceIndex, b.scienceIndex],
      ['Мета-анализов', a.metaCount, b.metaCount],
      ['Цитирований ключевого MA', a.citations ?? '—', b.citations ?? '—'],
      ['Отзывов на WB', a.reviews ?? '—', b.reviews ?? '—'],
      ['Поиск (5 лет)', a.trends ?? '—', b.trends ?? '—'],
      ['Эффекты', (a.effects || []).join(', '), (b.effects || []).join(', ')],
      ['Дозировка', a.dosage ?? '—', b.dosage ?? '—'],
      ['Курс', a.course ?? '—', b.course ?? '—'],
      ['⚠️ Осторожно', a.caution ?? '—', b.caution ?? '—']
    ];
    document.getElementById('compareResult').innerHTML =
      '<table><tr><th>Параметр</th><th>' + a.name + '</th><th>' + b.name + '</th></tr>' +
      rows.map(r => `<tr><td>${r[0]}</td><td>${r[1]}</td><td>${r[2]}</td></tr>`).join('') + '</table>';
  });
  document.getElementById('compareBtn').click();
}

function setupThemeToggle() {
  document.getElementById('themeToggle').addEventListener('click', function () {
    document.body.classList.toggle('dark');
    this.textContent = document.body.classList.contains('dark') ? '☀️ Светлая тема' : '🌙 Тёмная тема';
    renderBubbleChart(currentData);   // ФИКС: не теряем фильтр
  });
}