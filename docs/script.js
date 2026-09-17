const $ = id => document.getElementById(id);
let supplements = [], currentData = [], chartInstance = null, radarInstance = null, onlyFavs = false;
// v2.8.0: пресеты-тумблеры (активны независимо от ручных фильтров, комбинация — AND)
let presetScience = false, presetVerdict = false;      // scienceSort / verdictProven
let presetOngoing = false;
// priceMax / ongoingMin
let prevSort = '';                                     // для тумблера 🏆 Топ по науке
let prevVerdict = '';                                  // для пресета 💎 Доказано
let chartPts = [];
let quadrantInstance = null, chartTab = 'price';   // v2.4: вкладки графика
let scrollBeforeModal = 0;
let curModal = null;   // v2.6: id открытой модалки для «Сравнить с»
let BEST = [];

// ===== v2.4: грейды A–D =====
const GRADE_LABEL = { A: 'крепко доказано', B: 'умеренно', C: 'изучено много, эффект мал', D: 'данных мало' };
function gradeBadge(s) {
  if (!s.grade) return '';
  return '<span class="grade g' + s.grade + '" title="Грейд ' + s.grade + ' — ' + (GRADE_LABEL[s.grade] || '') + '">грейд ' + s.grade + '</span>';
}

const GRADE_PRIOR = { A: 0, B: 1, C: 2, D: 3 };   // v2.6.1: сортировка «по грейду» A<B<C<D<нет

// ===== v2.6: бейдж «ручная вычитка» (у карточек с ручным вердиктом — все вердикты ручные) =====
// Tooltip-хелперы для метрик (наведение показывает формулу)
function scienceSpan(s) {
  return '<span title="Science Index = количество РКИ + 5 × количество мета-анализов. Показывает объём доказательной базы по добавке, а не силу её эффекта.">🔬 наука: ' + s.scienceIndex + '</span>';
}
function maSpan(s) {
  return '<span title="Количество статей типа meta-analysis в PubMed по запросу для этой добавки. Это про объём литературы, а не про подтверждение эффекта.">📚 MA: ' + s.metaCount + '</span>';
}
function citationsSpan(s) {
  if (s.citations == null) {
    return '<span title="Цитирования не рассчитаны для этой добавки.">📖 цитирований MA: —</span>';
  }
  return '<span title="Сумма цитирований ключевого мета-анализа (по данным OpenAlex).">📖 цитирований MA: ' + s.citations + '</span>';
}

function manualBadge(s) {
  if (!s.verdict) return '';
  return '<span class="manual-badge" title="Вердикт выставлен вручную по топ-2 МА методологией проекта">✋ ручная вычитка</span>';
}

// ===== v2.6: «Обновлено: дата последнего коммита data.json» =====
function updatedLine(s) {
  return s.updated ? '<span class="updatedLine">Обновлено: ' + s.updated + '</span>' : '';
}

// ===== v2.6: иконки источников =====
function pubmedLink(s) {
  return ' <a class="srcIcon" target="_blank" rel="noopener" title="Поиск в PubMed" href="https://pubmed.ncbi.nlm.nih.gov/?term=' +
    encodeURIComponent(s.name) + '">PubMed ↗</a>';
}
function wikiLink(s) {
  return ' <a class="srcIcon" target="_blank" rel="noopener" title="Википедия" href="https://ru.wikipedia.org/wiki/' +
    encodeURIComponent(s.name.replace(/\+/g, ' ')) + '">Wiki ↗</a>';
}
// ===== v2.6: кнопка «Нашли неточность?» (issue с добавка+поле) =====
function issueUrl(s, field) {
  const title = (s.name || 'добавка') + (field ? ': ' + field : '') + ' — неточность в данных';
  const body = 'Что не так?\n\n(заполните)';
  return 'https://github.com/DeadSno/brain-25-evidence/issues/new?title=' +
    encodeURIComponent(title) + '&body=' + encodeURIComponent(body);
}

// ===== v2.6: поделиться (TG/VK/копировать) в модалке =====
function shareRow(s) {
  const cardUrl = 'https://deadsno.github.io/brain-25-evidence/#sup=' + encodeURIComponent(s.id);
  const post = s.name + ': индекс ' + s.scienceIndex + ', ' + s.metaCount + ' МА · открытые данные · ' + cardUrl;
  return '<div class="shareRow"><b>📤 Поделиться:</b>' +
    ' <a class="favFilter" target="_blank" rel="noopener" href="https://t.me/share/url?url=' + encodeURIComponent(cardUrl) + '&text=' + encodeURIComponent(post) + '">TG</a>' +
    ' <a class="favFilter" target="_blank" rel="noopener" href="https://vk.com/share.php?url=' + encodeURIComponent(cardUrl) + '&title=' + encodeURIComponent(post) + '">VK</a>' +
    ' <button class="copyLink" data-copy="' + cardUrl + '">🔗 копировать</button></div>';
}

// ===== v2.6: «Сравнить с» — топ-3 той же категории (по доказательности, не случайные) =====
function compareBlock(s) {
  const same = supplements.filter(x => x.id !== s.id && x.category === s.category)
    .sort((a, b) => (b.scienceIndex || 0) - (a.scienceIndex || 0)).slice(0, 3);
  if (!same.length) return '';
  return '<div class="mrow"><b>🔀 Сравнить с:</b><div class="compareChips">' +
    same.map(x => '<span class="chipbx" data-cmp="' + encodeURIComponent(x.id) + '">' + x.name + '</span>').join('') +
    '</div></div>';
}

// ===== v2.3: шаблон полной карточки (15 блоков, структура фиксирована) =====
const BLOCK_EMPTY = '<span class="cbEmpty">для этой добавки проверяемых данных по пункту нет</span>';
const CARDBLOCKS = [
  { key: 'what',      title: 'Что это',                    get: s => s.about || (s.effects || []).join(', ') || '' },
  { key: 'who',       title: 'Кому нужно',                 get: s => s.who_needs || s.who || '' },
  { key: 'works',     title: 'Работает ли',                get: s => '<span class="verdict v' + s.code + '">' + s.verdict + '</span> · ' + gradeBadge(s) },
  { key: 'evidence',  title: 'На чём основано',            get: s => '<div>' + scienceSpan(s) + pubmedLink(s) + ' · ' + maSpan(s) + ' · ' + citationsSpan(s) + '</div>' +
    ((s.mechs || []).length ? '<div class="hline">Механизмы: ' + s.mechs.map(m => m[0]).join('; ') + '</div>' : '') },
  { key: 'how',       title: 'Как принимать',              get: s => [s.dosage, s.course].filter(Boolean).join(' · ') || '' },
  { key: 'onset',     title: 'Когда почувствую',           get: s => s.onset || '' },
  { key: 'notwho',    title: 'Кому нельзя',                get: s => s.caution || '' },
  { key: 'conflicts', title: 'С чем конфликтует',          get: renderConflicts },
  { key: 'friends',   title: 'С чем дружит',               get: s => (s.synergists || []).length
    ? '<span class="goodPair">🤝 Хорошая пара: ' + s.synergists.join(', ') + '</span>' : '' },
  { key: 'ul',        title: 'Передозировка (UL)',         get: s => s.upper_limit || s.ul || '' },
  { key: 'food',      title: 'Можно ли из еды',            get: s => s.food_sources || s.food || '' },
  { key: 'official',  title: 'Что говорят официалы',       get: s => s.guidelines || s.official || '' },
  { key: 'shop',      title: 'Как выбрать в магазине',     get: s => s.how_to_choose || s.forms || '' },
  { key: 'myths',     title: 'Мифы и ловушки',             get: s => s.myths || '' }
];

function renderConflicts(s) {
  const list = s.interactions || [];
  if (!list.length) return '';
  return list.map(i => '<div class="sev sev-' + i.severity + '"><b>' + i.with + '</b> · ' + i.severity + (i.note ? ' — ' + i.note : '') + '</div>').join('');
}
const CARD_GROUPS = [
  { title: '📋 Основное', keys: ['what','who','works','evidence'] },
  { title: '💊 Как принимать', keys: ['how','onset'] },
  { title: '⚠️ Осторожно', keys: ['notwho','conflicts','friends','ul'] },
  { title: '📚 Дополнительно', keys: ['food','official','shop','myths'] }
];
function renderCardBlocks(s) {
  return '<div class="cblocks">' + CARD_GROUPS.map(g => {
    const inner = g.keys.map(k => {
      const b = CARDBLOCKS.find(x => x.key === k);
      if (!b) return '';
      const content = b.get(s) || BLOCK_EMPTY;
      return '<div class="cblock" data-block-key="' + b.key + '"><h4>' + b.title + '</h4><div class="cbbody">' + content + '</div></div>';
    }).join('');
    return '<div class="cgroup"><div class="cgTitle">' + g.title + '</div>' + inner + '</div>';
  }).join('') + '</div>';
}
// ===== v2.3: баннеры избранного (critical/medium/synergy) =====

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
  BEST = supplements.filter(s => s.scienceIndex != null).sort((x, y) => y.scienceIndex - x.scienceIndex).slice(0, 3).map(s => s.id);
  const saved = localStorage.getItem('theme');
  if (saved !== 'light') setDark(true);   // v1.3: по умолчанию тёмная; светлая — только по выбору
  [...new Set(supplements.map(s => s.category).filter(Boolean))].sort()
    .forEach(c => $('categoryFilter').add(new Option(c, c)));
  supplements.forEach(s => { $('compareSelect1').add(new Option(s.name, s.id)); $('compareSelect2').add(new Option(s.name, s.id)); });
  if (supplements.length >= 2) { $('compareSelect1').value = supplements[0].id; $('compareSelect2').value = supplements[1].id; }
  $('search').addEventListener('input', applyFilters);
  ['verdictFilter', 'categoryFilter', 'sortSelect'].forEach(id => $(id).addEventListener('change', applyFilters));
  document.querySelectorAll('.preset').forEach(btn => {
    btn.addEventListener('click', () => {
      const p = btn.dataset.preset;
      let on;
      if (p === 'science') { presetScience = !presetScience; on = presetScience; if (on && !prevSort) prevSort = $('sortSelect').value; }
      else if (p === 'verdict') { presetVerdict = !presetVerdict; on = presetVerdict; }
      else if (p === 'ongoing') { presetOngoing = !presetOngoing; on = presetOngoing; }
      btn.classList.toggle('on', !!on);
      applyFilters();
    });
  });
  $('themeToggle').onclick = () => { const on = !document.body.classList.contains('dark'); setDark(on); localStorage.setItem('theme', on ? 'dark' : 'light'); };
  $('compareBtn').onclick = renderCompare;
  const pageUrl = encodeURIComponent('https://deadsno.github.io/brain-25-evidence/');
  const pageTitle = encodeURIComponent('БАДы: цена vs наука — 81 добавка через мета-анализы');
  $('shareTg').href = 'https://t.me/share/url?url=' + pageUrl + '&text=' + pageTitle;
  $('shareVk').href = 'https://vk.com/share.php?url=' + pageUrl + '&title=' + pageTitle;
  $('modalClose').onclick = closeModal;
  $('modalOverlay').onclick = e => { if (e.target.id === 'modalOverlay') closeModal(); };
  document.addEventListener('keydown', e => { if (e.key === 'Escape') closeModal(); });
  document.addEventListener('click', e => {
    const b = e.target.closest('.copyLink');
    if (!b) return;
    navigator.clipboard.writeText(b.dataset.copy).then(() => {
      const old = b.textContent; b.textContent = '✅ Скопировано!';
      setTimeout(() => { b.textContent = old; }, 1500);
    });
  });
  const deep = decodeURIComponent(location.hash.replace('#sup=', ''));
  if (deep && supplements.some(s => s.id === deep)) setTimeout(() => openModal(deep), 300);
  applyFilters(); renderCompare(); checkInteractions();
  // v2.4: вкладки графика «Цена vs наука | Квадрант доказательности»
  // v2.6: оси X графика
    $('axisMA').onclick = () => setAxisX('ma');
  $('axisRCT').onclick = () => setAxisX('rct');
  $('quadrantChart').style.display = 'none';
  $('quadrantNote').style.display = 'none';
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
    const rb = e.target.closest('#resetAll');
    if (rb) { $('resetFilters').click(); }
  });

  document.addEventListener('click', e => {
    const b = e.target.closest('[data-fav]');
    if (!b) return;
    e.stopPropagation(); e.preventDefault();
    toggleFav(b.dataset.fav);
  }, true);

  // v2.6: чипы «🔀 Сравнить с:» в модалке
  document.addEventListener('click', e => {
    const chip = e.target.closest('.chipbx[data-cmp]');
    if (!chip || !curModal) return;
    e.stopPropagation();
    gotoCompare(curModal, decodeURIComponent(chip.dataset.cmp));
  });

  const up = document.createElement('button');
  up.id = 'toTop'; up.textContent = '↑';
  up.onclick = () => scrollTo({top: 0, behavior: 'smooth'});
  document.body.appendChild(up);
  addEventListener('scroll', () => up.classList.toggle('show', scrollY > 500));
}

function setDark(on) {
  document.body.classList.toggle('dark', on);
  $('themeToggle').textContent = on ? '☀️ Светлая тема' : '🌙 Тёмная тема';
  if (currentData.length) { if (chartTab === 'price') renderBubble(currentData); else renderQuadrant(currentData); }
}

// v2.4: переключение вкладки графика
function setChartTab(tab) {
  if (tab === chartTab) return;
  chartTab = tab;
  $('bubbleChart').style.display = tab === 'price' ? 'block' : 'none';
  $('quadrantChart').style.display = tab === 'quadrant' ? 'block' : 'none';
  $('chartNote').style.display = tab === 'price' ? '' : 'none';
  $('quadrantNote').style.display = tab === 'quadrant' ? '' : 'none';
  if (currentData.length) { if (tab === 'price') renderBubble(currentData); else renderQuadrant(currentData); }
}

const vColor = c => c === 1 ? '#2d8a4e' : c === 0 ? '#d4a017' : '#c0392b';

// ===== v2.6.1: демонтаж Value Score, честная экономика =====
// ₽ за единицу эффекта = round(цена / Hedges' g) при обоих ненулевых;
// иначе — честная причина, а не ноль/прочерк-обманка.
function priceTip(s) {
  const d = s.price_date || 'дата неизвестна';
  return '<span class="priceTip" title="Цена на ' + d +
    '; ночной сбор временно заблокирован TLS-фильтром маркетплейса, трек reliability в работе">' +
    (s.price != null ? s.price + ' ₽/мес' : 'цена не найдена') + '</span>';
}
/* economicsBlock removed per v2.7.1 chunk 2 — price_per_effect gone, no "Экономика" block */
function verifiedCount() {
  return supplements.filter(x => (x.key_sources || []).length).length;
}
function maTop3Block(s) {
  const curated = s.key_sources || [];
  const auto = s.ma_top3 || [];

  // Приоритет: ручной набор (curated). Fallback: автотоп с явной пометкой.
  const useCurated = curated.length > 0;
  const list = useCurated ? curated.slice(0, 3) : auto.slice(0, 3);

  const title = useCurated
    ? '📚 Проверенные источники (топ-3)'
    : '📚 Мета-анализы (топ-3 авто-поиска)';

  const note = useCurated
    ? 'Отобраны вручную по топ-2 МА. Полный список — в блоке key_sources карточки.'
    : '⚠ Автоматический топ-3 запроса PubMed — не верифицировано вручную. '
      + 'Проверенные карточки помечены бейджем «ручная вычитка»; верифицировано сейчас: '
      + verifiedCount() + ' из ' + supplements.length + '.';

  const body = list.length
    ? '<div class="mrow">' + list.map(m => {
        const pmid = m.pmid || m;
        const t = m.title || pmid;
        const yr = m.year ? ' (' + m.year + ')' : '';
        return '<a class="srcIcon" target="_blank" rel="noopener" '
          + 'href="https://pubmed.ncbi.nlm.nih.gov/' + pmid + '/">'
          + t + yr + ' ↗</a>';
      }).join('<br>') + '</div>'
    : '<div class="mrow cbEmpty">Источники для этой добавки пока не собраны</div>';

  return '<div class="blockTitle">' + title + '</div>'
    + '<div class="mrow hint" style="font-size:.85rem;opacity:.9">' + note + '</div>'
    + body;
}
function applyFilters() {
  const q = $('search').value.toLowerCase().trim();
  const v = $('verdictFilter').value, c = $('categoryFilter').value, sort = presetScience ? 'science' : $('sortSelect').value;
  currentData = supplements.filter(s => {
    if (presetVerdict && String(s.code) !== '1') return false;
    if (!presetVerdict && v !== 'all' && String(s.code) !== v) return false;
    if (c !== 'all' && s.category !== c) return false;    if (presetOngoing && !((s.ongoing || 0) >= 1)) return false;
    if (q && !(s.name.toLowerCase().includes(q) || (s.effects || []).join(' ').toLowerCase().includes(q))) return false;
    return true;
  });
  if (onlyFavs) currentData = currentData.filter(x => isFav(x.id));
  const cmp = {
    science: (a, b) => b.scienceIndex - a.scienceIndex,
    name: (a, b) => a.name.localeCompare(b.name, 'ru'),
    grade: (a, b) => ((GRADE_PRIOR[a.grade] ?? 4) - (GRADE_PRIOR[b.grade] ?? 4)) || (b.scienceIndex - a.scienceIndex)
  };
  currentData.sort(cmp[sort]);
  $('countBadge').textContent = '(' + currentData.length + ' из ' + supplements.length + ')';
  renderCards(currentData);
  if (chartTab === 'price') renderBubble(currentData); else renderQuadrant(currentData);
  updateFavUI();
  // F2.2: подпись под чартом — показано N из M
  const filterParts = [];
  if (v !== 'all') filterParts.push('вердикт');
  if (c !== 'all') filterParts.push(c);
  if (q) filterParts.push('поиск');
  if (onlyFavs) filterParts.push('избранное');
  const summary = $('chartSummary');
  if (summary) {
    summary.textContent = 'показано ' + currentData.length + ' из ' + supplements.length + ' добавок' +
      (filterParts.length ? ' (фильтр: ' + filterParts.join(', ') + ')' : '');
  }
}

function renderCards(data) {
  const g = $('cardsGrid');
  if (!data.length) { g.innerHTML = '<div class="empty">🔍 Ничего не найдено. ' +
      '<button id="resetAll" class="favFilter">✖ Сбросить фильтры</button></div>'; return; }
  g.innerHTML = data.map(s => '<div class="card" data-id="' + s.id + '">' +
    '<button class="favBtn' + (isFav(s.id) ? ' on' : '') + '" data-fav="' + s.id + '" title="В избранное">' + (isFav(s.id) ? '★' : '☆') + '</button>' +
    (BEST.includes(s.id) ? '<span class="bestBadge">🔬 Топ-3 по доказательности</span>' : '') +
    '<span class="cat">' + (s.category || '') + '</span><h3>' + s.name + '</h3>' +
    updatedLine(s) + manualBadge(s) +
    '<div class="verdict v' + s.code + '">' + s.verdict + '</div>' + gradeBadge(s) +     '<div class="effects">' + (s.effects || []).map(e => '<span>' + e + '</span>').join('') + '</div></div>').join('');
  g.querySelectorAll('.card').forEach(el => el.onclick = (e) => {
    if (e.target.closest('a')) return;
    openModal(el.dataset.id);
  });
}

function openModal(id) {
  scrollBeforeModal = window.scrollY || 0;
  const s = supplements.find(x => x.id === id); if (!s) return;
  curModal = id;

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

  $('modalBody').innerHTML = '<h2>' + s.name + '</h2>' + updatedLine(s) + manualBadge(s) +
    '<div class="mrow"><span class="verdict v' + s.code + '">' + s.verdict + '</span> · ' + (s.category || '') + (s.grade ? ' · <span class="grade g' + s.grade + '">грейд ' + s.grade + '</span> · ' + (GRADE_LABEL[s.grade] || '') : '') + '</div>' +     '<div class="mrow">' + scienceSpan(s) + pubmedLink(s) + ' · ' + maSpan(s) + '</div>' +
    maTop3Block(s) +    trialsLine +
    calcLine +
    (s.citations != null ? '<div class="mrow">📖 Цитирований ключевого MA: ' + s.citations + '</div>' : '') +
    (s.reviews != null ? '<div class="mrow">🛒 Популярность (WB): ' + s.reviews.toLocaleString('ru-RU') + ' · 📈 поиск 5 лет: ' + (s.trends ?? '—') + ' · 🌐 Wiki: ' + (s.wiki != null ? s.wiki.toLocaleString('ru-RU') : '—') + wikiLink(s) + '</div>' : '') +
    '<div class="mrow"><b>Эффекты:</b> ' + ((s.effects || []).join(', ') || '—') + '</div>' +
    '<div class="mrow">💊 <b>Дозировка:</b> ' + (s.dosage || '—') + '</div>' +
    '<div class="mrow">⏳ <b>Курс:</b> ' + (s.course || '—') + '</div>' +
    (s.forms ? '<div class="mrow">🧪 <b>Формы/штаммы:</b> ' + s.forms + '</div>' : '') +
    shareRow(s) +
    compareBlock(s) +
    '<div class="mrow warn">⚠️ ' + (s.caution || '—') + '</div>' +
    '<div class="mrow"><button class="copyLink" data-copy="' + location.origin + location.pathname + '#sup=' + encodeURIComponent(s.id) + '">🔗 Скопировать ссылку на карточку</button>' +
    ' <a class="favFilter" target="_blank" rel="noopener" href="' + issueUrl(s, '') + '">❌ Нашли неточность? Сообщить</a></div>' +
    '<div class="blockTitle">🧩 Полная карточка добавки</div>' + renderCardBlocks(s);
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
  curModal = null;
  $('modalOverlay').style.display = 'none';
  history.replaceState(null, '', location.pathname);
  window.scrollTo({ top: scrollBeforeModal, behavior: 'smooth' });
}

// ===== v2.6: сменная ось X графика (Цена/MА/РКИ/Год) =====
let axisX = 'ma';
const AXIS_IDS = { ma: 'axisMA', rct: 'axisRCT' };
const AXIS_LABEL = { ma: 'Число МА', rct: 'Число РКИ' };
function axisVal(s) {
  if (axisX === 'ma') return (s.metaCount || 0) > 0 ? s.metaCount : null;
  if (axisX === 'rct') { const r = Math.max(0, (s.scienceIndex || 0) - 5 * (s.metaCount || 0)); return r > 0 ? r : null; }
  return s.year_last_ma || null;
}
function setAxisX(ax) {
  if (ax === axisX) return;
  axisX = ax;
  ['ma', 'rct'].forEach(k => $(AXIS_IDS[k]).classList.toggle('on', k === ax));
  if (currentData.length && chartTab === 'price') renderBubble(currentData);
}

function gotoCompare(idA, idB) {
  closeModal();
  $('compareSelect1').value = idA;
  $('compareSelect2').value = idB;
  renderCompare();
  document.getElementById('compareSection').scrollIntoView({ behavior: 'smooth' });
}

function renderBubble(data) {
  const isPrice = axisX === 'price';
  const priced = isPrice
    ? data.filter(s => (s.price || 0) > 0)
    : data.filter(s => axisVal(s) != null && axisVal(s) >= 0);
  const nullPrice = isPrice ? data.filter(s => !((s.price || 0) > 0)) : [];
  chartPts = priced.concat(nullPrice);
  if (isPrice) {
    $('chartNote').textContent = nullPrice.length
      ? ''
      : '';
  } else {
    $('chartNote').textContent = priced.length < data.length
      ? '⚠️ ' + (data.length - priced.length) + ' добавок без значения («' + AXIS_LABEL[axisX] + '») не показаны на графике' : '';
  }
  const ctx = $('bubbleChart').getContext('2d');
  if (chartInstance) chartInstance.destroy();
  const txt = getComputedStyle(document.body).getPropertyValue('--text');
  const maxP = priced.reduce((m, s) => Math.max(m, s.price || 0), 0) || 1;
  const band = isPrice && nullPrice.length
    ? { lo: maxP * 1.1, hi: maxP * 1.25, label: 'без цены (N=' + nullPrice.length + ')' }
    : null;
  const bandDatasets = band
    ? nullPrice.map(s => ({
        label: s.name,
        data: [{ x: (band.lo + band.hi) / 2, y: Math.max(1, s.scienceIndex) }],
        backgroundColor: 'rgba(150,150,150,.55)',
        pointRadius: Math.min(30, Math.sqrt(s.metaCount || 1) * 2.5),
        pointHoverRadius: Math.min(36, Math.sqrt(s.metaCount || 1) * 3.5)
      }))
    : [];
  const noPriceBandPlugin = {
    id: 'noPriceBand',
    afterDraw(chart) {
      const cfg = chart.config._config;
      if (!cfg.$band) return;
      const { lo, hi, label } = cfg.$band;
      const xs = chart.scales.x;
      const pxLo = xs.getPixelForValue(lo);
      const pxHi = xs.getPixelForValue(hi);
      const { top, bottom, left, right } = chart.chartArea;
      const c = chart.ctx;
      c.save();
      c.fillStyle = 'rgba(128,128,128,.12)';
      c.fillRect(pxLo, top, pxHi - pxLo, bottom - top);
      c.strokeStyle = 'rgba(128,128,128,.4)';
      c.setLineDash([4, 3]);
      c.beginPath(); c.moveTo(pxLo, top); c.lineTo(pxLo, bottom);
      c.moveTo(pxHi, top); c.lineTo(pxHi, bottom); c.stroke();
      c.setLineDash([]);
      c.fillStyle = 'rgba(128,128,128,.78)';
      c.font = '11px sans-serif';
      c.textAlign = 'center';
      c.fillText(label, (pxLo + pxHi) / 2, bottom - 5);
      c.restore();
    }
  };
  chartInstance = new Chart(ctx, {
    type: 'scatter',
    data: { datasets: priced.map(s => ({
      label: s.name,
      data: [{ x: axisVal(s), y: Math.max(1, s.scienceIndex) }],
      backgroundColor: vColor(s.code),
      pointRadius: Math.min(30, Math.sqrt(s.metaCount || 1) * 2.5),
      pointHoverRadius: Math.min(36, Math.sqrt(s.metaCount || 1) * 3.5)
    })).concat(bandDatasets) },
    options: {
      responsive: true, maintainAspectRatio: true,
      scales: {
        x: { title: { display: true, text: AXIS_LABEL[axisX], color: txt }, grid: { color: 'rgba(128,128,128,.15)' }, max: band ? band.hi * 1.02 : undefined },
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
              return s ? ' ' + s.name + ' · ' + (axisX === 'price' ? (s.price ?? '—') + ' ₽/мес' : AXIS_LABEL[axisX] + ': ' + axisVal(s)) + ' · ' + s.verdict : '';
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
    },
    plugins: [noPriceBandPlugin],
    $band: band
  });
  window.chart = chartInstance;
}

// ===== v2.4: квадрант доказательности (Hedges' g vs scienceIndex) =====
function renderQuadrant(data) {
  const verified = data.filter(s => s.hedges_g != null);
  $('quadrantNote').textContent = verified.length < data.length
    ? '⏳ ' + (data.length - verified.length) + ' добавок ждут верификации эффекта' : '';
  const ctx = $('quadrantChart').getContext('2d');
  if (quadrantInstance) quadrantInstance.destroy();
  const txt = getComputedStyle(document.body).getPropertyValue('--text');
  quadrantInstance = new Chart(ctx, {
    type: 'scatter',
    data: { datasets: verified.map(s => ({
      label: s.name,
      data: [{ x: s.hedges_g, y: Math.max(1, s.scienceIndex) }],
      backgroundColor: vColor(s.code),
      pointRadius: Math.min(30, Math.sqrt(s.metaCount || 1) * 2.5),
      pointHoverRadius: Math.min(36, Math.sqrt(s.metaCount || 1) * 3.5)
    })) },
    options: {
      responsive: true, maintainAspectRatio: true,
      scales: {
        x: { min: -0.2, max: 0.6,
             title: { display: true, text: "Hedges' g (сила эффекта)", color: txt },
             grid: { color: 'rgba(128,128,128,.15)' } },
        y: { type: 'logarithmic',
             title: { display: true, text: 'Индекс науки (лог)', color: txt },
             grid: { color: 'rgba(128,128,128,.15)' },
             ticks: { callback: v => [1,10,100,1000,10000].includes(v) ? v : '' } }
      },
      plugins: {
        legend: { display: false },
        tooltip: { callbacks: { label: ctx => {
          const s = chartSupByEl(ctx.chart, { datasetIndex: ctx.datasetIndex, index: ctx.dataIndex });
          return s ? ' ' + s.name + ' · g=' + s.hedges_g + ' · ' + (s.grade || '—') + ' · ' + s.verdict : '';
        } } }
      },
      onClick: (e, els) => { if (!els.length) return; const s = chartSupByEl(e.chart, els[0]); if (!s) return; openModal(s.id); },
      onHover: (e, els) => { e.native.target.style.cursor = els.length ? 'pointer' : 'default'; }
    }
  });
  window.quadrantChart = quadrantInstance;
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
        ['Индекс науки', a.scienceIndex, b.scienceIndex],
    ['Мета-анализов', a.metaCount, b.metaCount],
    ['🧪 Испытания сейчас', a.ongoing ?? '—', b.ongoing ?? '—'],
    ['Цитирований MA', a.citations ?? '—', b.citations ?? '—'],
    ['🛒 Популярность (WB)', a.reviews ?? '—', b.reviews ?? '—'],
    ['Поиск (5 лет)', a.trends ?? '—', b.trends ?? '—'],
    ['Эффекты', (a.effects || []).join(', '), (b.effects || []).join(', ')],
    ['Дозировка', a.dosage ?? '—', b.dosage ?? '—'],
    ['Курс', a.course ?? '—', b.course ?? '—'],
    ['⚠️ Осторожно', a.caution ?? '—', b.caution ?? '—']
  ];
  $('compareResult').innerHTML = '<table><tr><th>Параметр</th><th>' + a.name + '</th><th>' + b.name + '</th></tr>' +
    rows.map(r => '<tr><td>' + r[0] + '</td><td>' + r[1] + '</td><td>' + r[2] + '</td></tr>').join('') + '</table>';

  // F4: перцентиль внутри метрики по базе (0-100); значение 100% — максимум базы
  const pctile = (x, arr) => {
    const vals = arr.map(v => (v == null ? 0 : v)).sort((a, b) => a - b);
    if (!vals.length) return 0;
    let lo = 0, hi = vals.length - 1, target = (x == null ? 0 : x);
    while (lo <= hi) {
      const mid = (lo + hi) >> 1;
      if (vals[mid] < target) lo = mid + 1; else hi = mid - 1;
    }
    return lo > 0 ? Math.round((lo / (vals.length - 1)) * 100) : 0;
  };
  const BASE_FOR_PCT = supplements;   // нормировка по всей базе 81
  const prof = s => {
    // Ось 1: Наука — перцентиль по базе
    const science = pctile(s.scienceIndex || 0, BASE_FOR_PCT.map(x => x.scienceIndex));
    // Ось 2: База МА — перцентиль по базе
    const maBase = pctile(s.metaCount || 0, BASE_FOR_PCT.map(x => x.metaCount));

    // Ось 3: Верифицированность (грейд + бонус за key_sources)
    const gradeMap = { A: 80, B: 60, C: 40, D: 20 };
    const srcBonus = Math.min((s.key_sources || []).length, 5) * 4;
    const verified = Math.min((gradeMap[s.grade] || 0) + srcBonus, 100);

    // Ось 4: Полнота карточки (база 40% + премиум 60%)
    const baseFields = ['verdict', 'effects', 'dosage', 'course', 'caution'];
    const advFields = ['about', 'who_needs', 'onset', 'myths',
                       'food_sources', 'guidelines', 'how_to_choose'];
    const baseFilled = baseFields.filter(f => {
      const v = s[f];
      return Array.isArray(v) ? v.length > 0 : !!v;
    }).length;
    const advFilled = advFields.filter(f => {
      const v = s[f];
      return Array.isArray(v) ? v.length > 0 : (typeof v === 'string' && v.length > 0);
    }).length;
    const completeness = Math.round(
      (baseFilled / baseFields.length) * 40 +
      (advFilled / advFields.length) * 60
    );

    return [science, maBase, verified, completeness];
  };
  const PROF_LABELS = ['Наука', 'База МА', 'Верифицированность', 'Полнота карточки'];
  if (radarInstance) radarInstance.destroy();
  radarInstance = new Chart($('radarChart'), {
    type: 'radar',
    data: {
      labels: [
        'Наука (перцентиль по базе)',
        'База МА (перцентиль по базе)',
        'Верифицированность (0-100)',
        'Полнота карточки (0-100)'
      ],
      datasets: [
        { label: a.name, data: prof(a), borderColor: '#3498db', backgroundColor: radarFill,
          pointBackgroundColor: '#3498db' },
        { label: b.name, data: prof(b), borderColor: '#e67e22', backgroundColor: radarFill,
          pointBackgroundColor: '#e67e22' }
      ]
    },
    options: {
      layout: { padding: 30 },
      scales: { r: { min: 0, max: 100, ticks: { display: false },
               pointLabels: { font: { size: 10 } } } },
      plugins: {
        legend: { position: 'bottom' },
        tooltip: {
          callbacks: {
            label: ctx => {
              const s = ctx.datasetIndex === 0 ? a : b;
              return ' ' + s.name + ' · ' + PROF_LABELS[ctx.dataIndex] + ': ' +
                Math.round(ctx.parsed.r) + '/100';
            }
          }
        }
      }
    }
  });
  window.radarInstance = radarInstance;
}

// ===== v1.3: избранное =====
function getFavs() { try { return JSON.parse(localStorage.getItem('favs') || '[]'); } catch (e) { return []; } }
function setFavs(a) { localStorage.setItem('favs', JSON.stringify(a)); }
function isFav(id) { return getFavs().includes(id); }
function toggleFav(id) {
  const f = getFavs();
  const i = f.indexOf(id);
  const wasFav = i >= 0;
  if (wasFav) f.splice(i, 1); else f.push(id);
  setFavs(f);
  updateFavUI();
  window.dispatchEvent(new Event(wasFav ? 'removeFav' : 'addFav'));
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

// ===== v2.2+: баннеры избранного (critical красный / medium оранжевый / synergy зелёный) =====
function named(inList, s) { return (inList || []).some(x => x === s.id || x === s.name); }
function isSynergy(s1, s2) { return named(s1.synergists, s2) || named(s2.synergists, s1); }
function isAntagonist(s1, s2) { return named(s1.antagonists, s2) || named(s2.antagonists, s1); }

function renderBanner(key, cls, html) {
  const old = document.querySelector('.banner[data-key="' + key + '"]');
  if (old) old.remove();
  if (!html) return;
  const banner = document.createElement('div');
  banner.className = 'banner ' + cls;
  banner.dataset.key = key;
  banner.innerHTML = html;
  document.body.prepend(banner);
}

function checkInteractions() {
  const favs = getFavs();
  const critical = [], medium = [], synergy = [];
  for (let i = 0; i < favs.length; i++) {
    for (let j = i + 1; j < favs.length; j++) {
      const s1 = supplements.find(s => s.id === favs[i]);
      const s2 = supplements.find(s => s.id === favs[j]);
      if (!s1 || !s2) continue;
      for (const inter of (s1.interactions || [])) {
        if (inter.with === s2.id && inter.severity === 'critical') critical.push({ s1: s1.name, s2: s2.name, note: inter.note });
      }
      for (const inter of (s2.interactions || [])) {
        if (inter.with === s1.id && inter.severity === 'critical') critical.push({ s1: s1.name, s2: s2.name, note: inter.note });
      }
      if (isAntagonist(s1, s2)) medium.push({ s1: s1.name, s2: s2.name });
      if (isSynergy(s1, s2)) synergy.push({ s1: s1.name, s2: s2.name });
    }
  }
  renderBanner('critical', 'conflict-banner', critical.length
    ? '⚠️ Опасно в избранном: ' + critical.map(c => c.s1 + ' + ' + c.s2).join(', ') + '. ' + critical[0].note : '');
  renderBanner('medium', 'conflict-banner medium', medium.length
    ? '⚠️ ' + medium.map(c => c.s1 + ' и ' + c.s2).join(', ') + ' конкурируют за всасывание — разнесите на 2-4 часа' : '');
  renderBanner('synergy', 'synergy-banner', synergy.length
    ? '🤝 Хорошая пара: ' + synergy.map(c => c.s1 + ' + ' + c.s2).join(', ') : '');
}

['addFav', 'removeFav'].forEach(event => {
  window.addEventListener(event, checkInteractions);
});