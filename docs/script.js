function esc(s) {
  return String(s == null ? '' : s).replace(/[&<>"']/g, c => (
    { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
  ));
}
const $ = id => document.getElementById(id);

// ===== A11Y-13: skip-link должен не только прыгнуть по якорю, но и
// перевести фокус на <main> (index.html: main[tabindex="-1"]).
// Браузер по клику на #main-якорь фокус не ставит — делаем это вручную.
(function initSkipLink() {
  const skip = document.querySelector('.skip-link');
  const main = document.getElementById('main');
  if (skip && main) {
    skip.addEventListener('click', () => {
      main.focus({ preventScroll: false });
    });
  }
})();

// ===== A11Y-10: единая точка синхронизации aria-expanded у input#search
// (role="combobox") с состоянием live-search дропдауна #searchDrop.
function setSearchDropOpen(open) {
  const search = $('search');
  if (search) search.setAttribute('aria-expanded', open ? 'true' : 'false');
}

// ===== slug: кириллическое id -> транслит для URL sup/<slug>.html =====
const TRANS = {
  "а":"a","б":"b","в":"v","г":"g","д":"d","е":"e","ё":"e",
  "ж":"zh","з":"z","и":"i","й":"y","к":"k","л":"l","м":"m",
  "н":"n","о":"o","п":"p","р":"r","с":"s","т":"t","у":"u",
  "ф":"f","х":"h","ц":"ts","ч":"ch","ш":"sh","щ":"sch",
  "ъ":"","ы":"y","ь":"","э":"e","ю":"yu","я":"ya"
};
function slugify(name) {
  const out = [];
  for (const ch of String(name || '').toLowerCase()) {
    if (ch in TRANS) out.push(TRANS[ch]);
    else if (ch === '-' || ch === '_' || ch === ' ') out.push('-');
    else if (ch >= 'a' && ch <= 'z' || ch >= '0' && ch <= '9') out.push(ch);
    else out.push('-');
  }
  return out.join('').replace(/-{2,}/g, '-').replace(/^-|-$/g, '');
}

// 13A2a (I18N-P2-01): LOCALE, I18N и t() перенесены в глобальный
// docs/i18n.js (classic-скрипт, подключается до script.js и до
// inline-скриптов тем). Здесь — только потребление I18N / t / LOCALE.

let supplements = [], currentData = [], chartInstance = null, radarInstance = null, onlyFavs = false;
let supplementsFull = null;         // {id: {...}} — загружается при первом клике
let supplementsFullPromise = null;  // in-flight запрос data.json
window.getData = window.getData || (() => window.__dataPromise || (window.__dataPromise = fetchJson('data.json')));
// v5.6.2 (батч C, T4): поиск по PMID возвращал 0 результатов. Причина —
// PMID лежит в data.json (key_sources[].pmid), а фильтр работал по
// data_index.json, где таких полей нет: index отдаёт только id / name /
// category / code / verdict / grade / scienceIndex / metaCount / citations /
// wiki / ongoing / effects / updated / interactions / upper_limit / hedges_g.
// Поэтому «42027564» не совпадало ни с именем, ни с effects.
// Решение — не тянуть 0.73 МБ на каждый ввод: индекс PMID строится один
// раз лениво, по общему supplementsFullPromise, и только когда запрос
// похож на PMID (цифры). matchPmidIds возвращает null, пока индекс не
// готов, — тогда запрос не сужает выборку и пользователь получает
// обычный список, а не ложные нули.
let pmidIndex = null, pmidIndexPromise = null;
const PMID_QUERY_RE = /^\d{4,}$/;

// v5.6.2 (батч C, T4): единая точка загрузки полного data.json.
// Раньше одинаковый код был продублирован в трёх местах (prefetch,
// openModal, compare) и различался только текстом ошибки. Здесь retry
// после неудачи общий: supplementsFullPromise сбрасывается, поэтому
// следующий вызов действительно повторит запрос.
function ensureFullData() {
  if (supplementsFull) return Promise.resolve(supplementsFull);
  if (!supplementsFullPromise) {
    // FIX-77: в EN к data.json добавляется оверлей data_en.json. В RU
    // loadEnCards() резолвится в null без сетевого запроса, поэтому
    // русская версия грузит ровно те же файлы, что и раньше.
    supplementsFullPromise = Promise.all([getData(), loadEnCards()])
      .then(([data, enCards]) => {
        const list = enCards ? data.map(c => mergeEnCard(c, enCards[c.id])) : data;
        supplementsFull = Object.fromEntries(list.map(c => [c.id, c]));
        return supplementsFull;
      }).catch(err => {
        supplementsFullPromise = null;   // разрешаем retry
        throw err;
      });
  }
  return supplementsFullPromise;
}

function buildPmidIndex(map) {
  const idx = new Map();
  for (const card of Object.values(map)) {
    for (const src of card.key_sources || []) {
      const p = String(src.pmid || src);
      if (!p) continue;
      if (!idx.has(p)) idx.set(p, []);
      if (!idx.get(p).includes(card.id)) idx.get(p).push(card.id);
    }
  }
  return idx;
}

function ensurePmidIndex() {
  if (pmidIndex) return Promise.resolve(pmidIndex);
  if (!pmidIndexPromise) {
    pmidIndexPromise = ensureFullData()
      .then(map => { pmidIndex = buildPmidIndex(map); return pmidIndex; })
      .catch(() => null);   // индекс — улучшение поиска, его отсутствие не ломает остальное
  }
  return pmidIndexPromise;
}

function matchPmidIds(q) {
  if (!pmidIndex || !pmidIndex.size) return null;
  return pmidIndex.get(q) || [];
}
let effectTags = {}, effectLabels = {};
let effectFilterCurrent = 'all';
// v2.8.0: пресеты-тумблеры (активны независимо от ручных фильтров, комбинация — AND)
let presetScience = false, presetVerdict = false;      // scienceSort / verdictProven
let presetOngoing = false;
// priceMax / ongoingMin
let prevSort = '';                                     // для тумблера 🏆 Топ по науке
let prevVerdict = '';                                  // для пресета 💎 Доказано
// i18n: severity на русском
const SEV_LABEL = {
  low: t("sev.low"),
  medium: t("sev.medium"),
  high: t("sev.high"),
  critical: t("sev.critical"),
};
const sevRu = s => SEV_LABEL[(s || '').toLowerCase()] || s || '';
let chartPts = [];
let quadrantInstance = null, chartTab = 'price';   // v2.4: вкладки графика
let scrollBeforeModal = 0;
let modalPrevFocus = null;   // v5.6.2 (T3): элемент, получивший фокус до открытия модалки
let curModal = null;   // v2.6: id открытой модалки для «Сравнить с»
let BEST = [];

// ===== v2.4: грейды A–D =====
const GRADE_LABEL = { A: t("grade.A"), B: t("grade.B"), C: t("grade.C"), D: t("grade.D") };
function gradeBadge(s) {
  if (!s.grade) return '';
  return '<span class="grade g' + s.grade + '" title="' + t("card.gradeTitle") + ' ' + s.grade + ' — ' + (GRADE_LABEL[s.grade] || '') + '">' + t("card.grade") + ' ' + s.grade + '</span>';
}

const GRADE_PRIOR = { A: 0, B: 1, C: 2, D: 3 };   // v2.6.1: сортировка «по грейду» A<B<C<D<нет

// ===== v5.6.5: PMID-счётчик (доверие) =====
function pmidCount(s) {
  return s.key_sources ? s.key_sources.length : 0;
}
function pmidBadge(s) {
  const n = pmidCount(s);
  if (!n) return '';
  return '<span class="pmidBadge" title="' + t("cmp.pmid") + ': ' + n + '">🔬 ' + n + ' ' + t("cmp.pmid").toLowerCase() + '</span>';
}

// ===== v5.6.5: шкала эффекта (Hedges' g) — человекочитаемо =====
function gLabel(g) {
  if (g == null) return '';
  if (g < 0.2) return t("g.weak");
  if (g < 0.5) return t("g.medium");
  if (g < 0.8) return t("g.high");
  return t("g.veryHigh");
}
function gSpan(s) {
  const g = Number(s.hedges_g);
  if (!Number.isFinite(g)) return '';
  return '<span class="gBadge" title="' + t("g.tooltip", { label: gLabel(g), g: g.toFixed(2) }) + '">' + t("g.label") + g.toFixed(2) + '</span>';
}
function onsetSpan(s) {
  const o = s.onset;
  if (!o) return '';
  return '<div class="mrow">⏱ <b>' + t("card.onset") + '</b> ' + esc(o) + '</div>';
}
function cautionSpan(s) {
  const c = s.caution;
  if (!c) return '';
  return '<div class="mrow warn">⚠️ <b>' + t("card.cautionTitle") + '</b> ' + esc(c) + '</div>';
}
function unknownsBlock(s) {
  const reasons = [];
  // forms с FIX-39 — массив, поэтому пустой массив тоже «нет данных».
  if (!s.forms || !s.forms.length) reasons.push(t("card.unknowns.forms"));
  const n = pmidCount(s);
  if (n > 0 && n < 3) reasons.push(t("card.unknowns.sources", { n: n }));
  if (!reasons.length) return '';
  return '<div class="mrow unknowns">' +
    '<b>🔍 ' + t("card.unknowns") + '</b><br>' + reasons.join(' ') +
    '</div>';
}

// ===== v2.6: бейдж «ручная вычитка» (у карточек с ручным вердиктом — все вердикты ручные) =====
// Tooltip-хелперы для метрик (наведение показывает формулу)
function scienceSpan(s) {
  return '<span title="' + t("sci.tooltip") + '">' + t("sci.label") + s.scienceIndex + '</span>';
}
function maSpan(s) {
  return '<span title="' + t("ma.tooltip") + '">' + t("ma.label") + s.metaCount + '</span>';
}
function citationsSpan(s) {
  if (s.citations == null || s.citations === 0) {
    return '<span title="' + t("cit.none.tooltip") + '">' + t("cit.none") + '</span>';
  }
  return '<span title="' + t("cit.tooltip") + '">' + t("cit.label") + s.citations + '</span>';
}

function manualBadge(s) {
  if (!s.verdict) return '';
  return '<span class="manual-badge" title="' + t("card.handcheckTitle") + '">' + t("card.handcheck") + '</span>';
}

// ===== v2.6: «Обновлено: дата последнего коммита data.json» =====
function updatedLine(s) {
  const fromVersion = (window.APP_VERSION && window.APP_VERSION.data) || null;
  const d = fromVersion || s.updated || '—';
  return '<div class="updated" title="' + t("card.updatedTitle") + '">' + t("card.updated") + ': ' + esc(d) + '</div>';
}

// ===== v2.6: иконки источников =====
function pubmedLink(s) {
  return ' <a class="srcIcon" target="_blank" rel="noopener" title="' + t("sources.pubmedTitle") + '" href="https://pubmed.ncbi.nlm.nih.gov/?term=' +
    encodeURIComponent(s.name) + '">' + t("sources.pubmed") + '</a>';
}
function wikiLink(s) {
  return ' <a class="srcIcon" target="_blank" rel="noopener" title="' + t("sources.wikiTitle") + '" href="https://ru.wikipedia.org/wiki/' +
    encodeURIComponent(s.name.replace(/\+/g, ' ')) + '">' + t("sources.wiki") + '</a>';
}

// ===== v5.6.5: блок «Где искать» + «Что искать при покупке» в модалке =====
function shopBlock(s) {
  const name = s.name || '';
  // «первая форма из массива»: с FIX-39 (D2-04) в данных forms — массив
  // строк, берём первый элемент и режем его по « — » или «;»
  // (например «оксид — плохо усваивается; цитрат…» → «оксид»).
  const formRaw = Array.isArray(s.forms) ? (s.forms[0] || '') : (s.forms || '');
  const form = formRaw ? String(formRaw).split(/[;—–]/)[0].trim() : '';
  const q = form ? encodeURIComponent(name + '+' + form) : encodeURIComponent(name);
  const yandex = 'https://market.yandex.ru/search?text=' + q;
  const ozon = 'https://www.ozon.ru/search/?text=' + q;
  const wb = 'https://www.wildberries.ru/catalog/0/search.aspx?search=' + q;
  let html = '<div class="mrow shopBlock">' +
    '<div class="shopTitle">' + t("shop.whereBuy") + '</div>' +
    '<div class="shopButtons">' +
    '<a class="shopBtn" href="' + yandex + '" target="_blank" rel="noopener">' + t("shop.market") + ' ↗</a>' +
    '<a class="shopBtn" href="' + ozon + '" target="_blank" rel="noopener">' + t("shop.ozon") + ' ↗</a>' +
    '<a class="shopBtn" href="' + wb + '" target="_blank" rel="noopener">' + t("shop.wb") + ' ↗</a>' +
    '</div></div>';
  // Блок «Что искать при покупке» — заголовок и текст всегда; дозировка —
  // только если в данных есть dosage.min/dosage.max (сейчас dosage — строка,
  // поэтому рекомендация не показывается, блок остаётся).
  html += '<div class="mrow shopLookBlock">' +
    '<div class="shopLookTitle">' + t("shop.lookFor") + '</div>' +
    '<div class="shopLookText">' + t("shop.lookForText") + '</div>';
  const dos = s.dosage;
  if (dos && typeof dos === 'object' && dos.min != null && dos.max != null) {
    html += '<div class="shopLookDose">' + t("shop.dosageRec", { min: dos.min, max: dos.max }) + '</div>';
  }
  html += '</div>';
  return html;
}
// ===== v2.6: кнопка «Нашли неточность?» (issue с добавка+поле) =====
function issueUrl(s, field) {
  const title = t("card.issueTitle", { name: (s.name || t("card.supplement")) + (field ? ': ' + field : '') });
  const body = t("card.issueBody");
  return 'https://github.com/DeadSno/brain-25-evidence/issues/new?title=' +
    encodeURIComponent(title) + '&body=' + encodeURIComponent(body);
}

// ===== v2.6: поделиться (TG/VK/копировать) в модалке =====
function shareRow(s) {
  const cardUrl = 'https://deadsno.github.io/brain-25-evidence/#sup=' + encodeURIComponent(s.id);
  const post = t("share.post", { name: s.name, index: s.scienceIndex, ma: s.metaCount, url: cardUrl });
  return '<div class="shareRow"><b>' + t("share.title") + '</b>' +
    ' <a class="favFilter" target="_blank" rel="noopener" href="https://t.me/share/url?url=' + encodeURIComponent(cardUrl) + '&text=' + encodeURIComponent(post) + '">TG</a>' +
    ' <a class="favFilter" target="_blank" rel="noopener" href="https://vk.com/share.php?url=' + encodeURIComponent(cardUrl) + '&title=' + encodeURIComponent(post) + '">VK</a>' +
    ' <button class="copyLink" data-copy="' + cardUrl + '">' + t("share.copy") + '</button></div>';
}

// ===== v2.6: «Сравнить с» — топ-3 той же категории (по доказательности, не случайные) =====
function compareBlock(s) {
  const same = supplements.filter(x => x.id !== s.id && x.category === s.category)
    .sort((a, b) => (b.scienceIndex || 0) - (a.scienceIndex || 0)).slice(0, 3);
  if (!same.length) return '';
  return '<div class="mrow"><b>' + t("compare.title") + '</b><div class="compareChips">' +
    same.map(x => '<span class="chipbx" data-cmp="' + encodeURIComponent(x.id) + '">' + x.name + '</span>').join('') +
    '</div></div>';
}

// ===== v2.3: шаблон полной карточки (15 блоков, структура фиксирована) =====
const BLOCK_EMPTY = '<span class="cbEmpty">' + t("card.blockEmpty") + '</span>';
const CARDBLOCKS = [
  { key: 'what',      title: t("block.what"),                    get: s => s.about || (s.effects || []).join(', ') || '' },
  { key: 'who',       title: t("block.who"),                 get: s => s.who_needs || '' },
  { key: 'works',     title: t("block.works"),                get: s => '<span class="verdict v' + esc(s.code) + '">' + esc(s.verdict) + '</span> · ' + gradeBadge(s) },
  { key: 'evidence',  title: t("block.evidence"),            get: s => '<div>' + scienceSpan(s) + pubmedLink(s) + ' · ' + maSpan(s) + ' · ' + citationsSpan(s) + '</div>' +
    ((s.mechs || []).length ? '<div class="hline">' + t("block.mechs") + s.mechs.map(m => esc(m[0])).join('; ') + '</div>' : '') },
  { key: 'how',       title: t("block.how"),              get: s => [s.dosage, s.course].filter(v => v && v !== '—' && v !== '-').join(' · ') || t("block.noData") },
  { key: 'onset',     title: t("block.onset"),           get: s => s.onset || '' },
  { key: 'notwho',    title: t("block.notwho"),                get: s => s.caution || '' },
  { key: 'conflicts', title: t("block.conflicts"),          get: renderConflicts },
  { key: 'friends',   title: t("block.friends"),               get: s => (s.synergists || []).length
    ? '<span class="goodPair">' + t("block.goodPair") + s.synergists.map(esc).join(', ') + '</span>' : '' },
  { key: 'ul',        title: t("block.ul"),         get: s => s.upper_limit || '' },
  { key: 'food',      title: t("block.food"),            get: s => s.food_sources || '' },
  { key: 'official',  title: t("block.official"),       get: s => s.guidelines || '' },
  { key: 'shop',      title: t("block.shop"),     get: s => s.how_to_choose || (Array.isArray(s.forms) ? s.forms.join(', ') : (s.forms || '')) || '' },
  { key: 'myths',     title: t("block.myths"),             get: s => s.myths || '' }
];

function renderConflicts(s) {
  const list = s.interactions || [];
  if (!list.length) return '';
  return list.map(i => '<div class="sev sev-' + esc(i.severity) + '"><b>' + esc(i.with) + '</b> · ' + esc(sevRu(i.severity)) + (i.note ? ' — ' + esc(i.note) : '') + '</div>').join('');
}
const CARD_GROUPS = [
  { title: t("group.main"), keys: ['what','who','works','evidence'] },
  { title: t("group.usage"), keys: ['how','onset'] },
  { title: t("group.caution"), keys: ['notwho','conflicts','friends','ul'] },
  { title: t("group.more"), keys: ['food','official','shop','myths'] }
];
function renderCardBlocks(s) {
  return '<div class="cblocks">' + CARD_GROUPS.map(g => {
    const inner = g.keys.map(k => {
      const b = CARDBLOCKS.find(x => x.key === k);
      if (!b) return '';
      // HTML-блоки рендерят свой HTML (esc внутри get). Остальные — экранируем.
      const RAW_HTML_KEYS = new Set(['works', 'evidence', 'conflicts', 'friends']);
      const raw = b.get(s);
      const content = raw ? (RAW_HTML_KEYS.has(b.key) ? raw : esc(raw)) : BLOCK_EMPTY;
      return '<div class="cblock" data-block-key="' + esc(b.key) + '"><h4>' + esc(b.title) + '</h4><div class="cbbody">' + content + '</div></div>';
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

// v4.0: переключатель темы вынесен из initApp() на верхний уровень,
// чтобы работал даже если данные не загрузились (шапка живёт всегда)
function initTheme() {
  const b = $('themeBtn');
  if (!b) return;
  const saved = localStorage.getItem('theme');
  // v5.4.0 (dark-first): светлая только по выбору пользователя.
  // Тёмная — по умолчанию, то есть класс light просто снимается.
  if (saved === 'light') setLight(true);
  // v5.4.0 (dark-first): on означает «переключаем В светлую», а не
  // «включаем тёмную», как раньше. Поэтому в localStorage пишется
  // on ? 'light' : 'dark' — наоборот прежнего.
  b.onclick = () => { const on = !document.documentElement.classList.contains('light'); setLight(on); localStorage.setItem('theme', on ? 'light' : 'dark'); };
}
initTheme();

// A2-05 (24.10.2026): <details>/<summary> уже отдают состояние раскрытия
// нативно (Chrome: роль DisclosureTriangle + свойство expanded), но
// aria-expanded делает его явным и не зависит от движка: у старых WebKit
// нативный expanded появлялся с задержкой. Ставим значение из фактического
// состояния, а не из разметки: браузер помнит открытые details после
// перезагрузки, и жёсткое «false» разошлось бы с картинкой.
// role="button" намеренно не ставим: <summary> и так кнопка в дереве
// доступности, а явная роль стёрла бы семантику disclosure.
function initDisclosures() {
  document.querySelectorAll('details').forEach(d => {
    const s = d.querySelector(':scope > summary');
    if (!s) return;
    const sync = () => s.setAttribute('aria-expanded', d.open ? 'true' : 'false');
    sync();
    d.addEventListener('toggle', sync);
    // Событие toggle браузер ставит в очередь задач и доставляет заметно
    // позже клика — всё это время атрибут врал бы. Поэтому на клик ставим
    // значение сразу: активация summary ещё не прошла, значит новое
    // состояние — противоположное текущему. toggle потом подтверждает его
    // и заодно выравнивает любой рассинхрон.
    s.addEventListener('click', () => s.setAttribute('aria-expanded', d.open ? 'false' : 'true'));
  });
}
initDisclosures();

// INDEX_CTA_FIX (MKT-P1-02 follow-up): кнопка «Найти свою добавку»
// ведёт на каталог (#cardsContainer), а не на #search: поле поиска стоит
// ВЫШЕ CTA по DOM, якорь почти не двигал страницу и не ставил фокус.
// Селектор по href, а не по id: id не нужен разметке, а связка
// href -> обработчик не разъезжается, если кнопку переставят.
// Обработчик на верхнем уровне (как initTheme): секция статичная, кнопка
// должна работать даже если данные ещё не загрузились.
// Фокус — на первой кнопке фильтра: «Все эффекты» (#tagPresets рендерит
// renderEffectChips после загрузки данных) либо фолбэк «Топ по науке»
// (статичный .preset в #presetRow). preventScroll обязателен: без него
// focus() немедленно дёргает прокрутку и обрывает smooth-анимацию.
//
// v5.6.5 (A-1): селектор потерял уточнение .calc. Кнопка «Найти свою
// добавку» переехала на первый экран и стала вторичной (класс .btn),
// потому что главный CTA теперь «Открыть Project Hactar» (.btn.calc).
// Уточнение .calc больше не различало две кнопки, а по одному href
// обе они не поймались бы.
//
// v5.6.5 (A-1.1): уточнение .btn тоже снято — «Найти свою добавку»
// больше не кнопка, а текстовая ссылка tertiary (класс .hero-search).
// Селектор по одному href и так однозначен: на странице такая ссылка
// ровно одна.
document.querySelectorAll('a[href="#cardsContainer"]').forEach((cta) => {
  cta.addEventListener('click', (e) => {
    e.preventDefault();
    const target = $('cardsContainer');
    if (target) {
      // scrollIntoView({behavior:'smooth'}) игнорирует CSS, поэтому
      // prefers-reduced-motion проверяем здесь, а не только в style.css.
      const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
      target.scrollIntoView({ behavior: reduce ? 'auto' : 'smooth', block: 'start' });
    }
    const filterBtn = document.querySelector('#tagPresets .tagPreset[data-tag="all"]')
                   || document.querySelector('#presetRow .preset');
    if (filterBtn) filterBtn.focus({ preventScroll: true });
  });
});

// CWV-03 (BATCH-3): было '?ts=' + Date.now() — уникальный URL на каждый
// запрос, поэтому data.json (742 КБ) и data_index.json (87 КБ) не попадали
// в HTTP-кэш никогда, даже при повторном визите. Теперь параметр зависит
// только от версии сборки (её задаёт i18n.js): в релизе меняется один раз,
// между релизами кэш работает.
const DATA_VERSION = (typeof window !== 'undefined' && window.BUILD_VERSION) || '5.6.5';
const fetchJson = (url) => fetch(url + '?v=' + DATA_VERSION)
  .then(r => { if (!r.ok) throw new Error('no data for ' + url); return r.json(); });

// v5.6.5 (CWV-03): loadGzJson удалён. Функция не использовалась нигде:
// эти данные (data_index.json, effect_tags.json, effect_labels.json,
// data.json) грузятся через fetchJson, а .json.gz в проекте нет.
// DecompressionStream-вариант можно вернуть, когда появятся .gz-артефакты
// в пайплайне сборки данных.
// FIX-77: подписи мишеней («Сон», «ЖКТ / кишечник») — такой же контент,
// как данные карточек, поэтому в EN берём английский оверлей. Язык читаем
// из <html lang>: i18n.js выставляет его при загрузке, раньше этого скрипта.
const LABELS_SRC = document.documentElement.lang === 'en'
  ? 'effect_labels_en.json' : 'effect_labels.json';
Promise.allSettled([fetchJson('data_index.json'), fetchJson('effect_tags.json'), fetchJson(LABELS_SRC)])
  .then(([d, tg, lb]) => {
    if (d.status !== 'fulfilled') throw new Error('data_index.json не загружен');
    const idx = d.value;
    supplements = Array.isArray(idx) ? idx : (idx.supplements || []);
    effectTags = tg.status === 'fulfilled' ? tg.value : {};
    effectLabels = lb.status === 'fulfilled' ? lb.value : {};
    if (tg.status !== 'fulfilled') console.warn('[effect_tags.json] ?? ???????? ? ???? ?????????');
    if (lb.status !== 'fulfilled') console.warn('[' + LABELS_SRC + '] ?? ???????? ? ???? ?????????');
    // FIX-77: index-карточки тоже берут имя/категорию/вердикт/эффекты из
    // data.json, поэтому в EN накладываем тот же оверлей. Поля, которых
    // в оверлее нет, остаются русскими.
    return loadEnCards().then((enCards) => {
      if (enCards) supplements = supplements.map(c => mergeEnCard(c, enCards[c.id]));
      initApp();
    });
  })
  .catch((err) => {
    console.error('[boot] фатально:', err);
    // Страницу не стираем: шапка, футер и навигация остаются на месте
    // Раньше текст звал «обновите страницу», но кнопки рядом не было —
    // единственный «Обновить» находился в шапке. Теперь она рядом (P1-6).
    const msg = '<div style="padding:40px;text-align:center;color:var(--muted)">' +
                t("boot.error") + '<br>' +
                '<button id="dataRetry" class="btn" style="margin-top:12px">' + t("boot.retry") + '</button></div>';
    const grid = $('cardsGrid');
    if (grid) grid.innerHTML = msg;
    else document.body.insertAdjacentHTML('afterbegin', msg);
    // Кнопка рядом с сообщением: полная перезагрузка — единственный способ
    // перезапустить цепочку загрузки, initApp повторно не подходит.
    const retry = $('dataRetry');
    if (retry) retry.onclick = () => location.reload();
  });

function initApp() {
  BEST = supplements.filter(s => s.scienceIndex != null).sort((x, y) => y.scienceIndex - x.scienceIndex).slice(0, 3).map(s => s.id);
  supplements.forEach(s => { /* сравнение больше не рендерится на главной — только на compare.html */ });
  // v3.3: сравнение убрано с главной — см. compare.html (секция O-03/PA-02)
  $('search').addEventListener('input', applyFilters);
  $('search').addEventListener('input', (e) => { renderSearchDrop(e.target.value); });
  $('search').addEventListener('keydown', (e) => {
    const drop = $('searchDrop');
    if (!drop || drop.style.display === 'none') return;
    if (e.key === 'ArrowDown') { e.preventDefault(); searchDropActive = Math.min(searchDropActive + 1, drop.querySelectorAll('.drop-row').length - 1); updateSearchDropFocus(); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); searchDropActive = Math.max(searchDropActive - 1, 0); updateSearchDropFocus(); }
    else if (e.key === 'Enter') { e.preventDefault(); pickSearchDrop(); }
    else if (e.key === 'Escape') { drop.style.display = 'none'; searchDropActive = -1; setSearchDropOpen(false); }
  });
  ['verdictFilter', 'sortSelect'].forEach(id => { const el = $(id); if (el) el.addEventListener('change', applyFilters); });
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
  $('modalClose').onclick = closeModal;
  $('modalOverlay').onclick = e => { if (e.target.id === 'modalOverlay') closeModal(); };
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') closeModal();
    else trapModalFocus(e);   // v5.6.2 (T3): Tab/Shift+Tab не покидают модалку
  });
  document.addEventListener('click', e => {
    // Закрыть live-search дропдаун при клике вне поля и самого дропдауна
    const drop = $('searchDrop');
    if (drop && drop.style.display !== 'none') {
      const insideDrop = e.target.closest('#searchDrop, #search');
      if (!insideDrop) { drop.style.display = 'none'; searchDropActive = -1; setSearchDropOpen(false); }
    }
    // Клик по результату live-search -> переход на страницу добавки
    const srow = e.target.closest('.drop-row[data-id]');
    if (srow) {
      e.preventDefault();
      const id = srow.dataset.id;
      $('search').value = '';
      drop.style.display = 'none';
      searchDropActive = -1;
      setSearchDropOpen(false);
      location.href = 'sup/' + slugify(id) + '.html';
      return;
    }
    const chip = e.target.closest('.tagChip');
    if (!chip) return;
    e.stopPropagation();
    e.preventDefault();
    effectFilterCurrent = chip.dataset.tag;
    renderEffectChips();
    applyFilters();
  }, true);

  document.addEventListener('click', e => {
  const preset = e.target.closest('.tagPreset');
  if (preset) {
    if (preset.dataset.more) {
      effectChipsExpanded = !effectChipsExpanded;
      renderEffectChips();
      return;
    }
    const tag = preset.dataset.tag;
    effectFilterCurrent = (tag === effectFilterCurrent || tag === 'all') ? 'all' : tag;
    renderEffectChips();
    applyFilters();
    return;
  }
  const clearEl = e.target.closest('[data-clear]');
  if (clearEl) {
    const c = clearEl.dataset.clear;
    if (c === 'effect') effectFilterCurrent = 'all';
    if (c === 'verdict') $('verdictFilter').value = 'all';
    if (c === 'search') $('search').value = '';
    renderEffectChips();
    applyFilters();
    return;
  }
  if (e.target.id === 'clearAllFilters') {
    effectFilterCurrent = 'all';
    $('verdictFilter').value = 'all';
    $('search').value = '';
    renderEffectChips();
    applyFilters();
  }
});

  /* U2-06 (25.10.2026): копирование умело только успех. Если буфер обмена
     недоступен (нет разрешения, страница открыта не по HTTPS, старый
     браузер), обработчик молчал: человек нажимал и не понимал, сработало
     ли. Теперь у обеих веток есть отклик — «Скопировано» или «Не удалось
     скопировать», плюс запасной путь через execCommand. Тост здесь не
     годится: showToast живёт внутри IIFE в hactar.js и наружу не отдан. */
  function copyMark(el, text) {
    const old = el.textContent;
    el.setAttribute('aria-live', 'polite');
    el.textContent = text;
    setTimeout(() => { el.textContent = old; }, 1500);
  }
  function copyLegacy(text) {
    const area = document.createElement('textarea');
    area.value = text;
    area.setAttribute('readonly', '');
    area.style.position = 'fixed';
    area.style.opacity = '0';
    document.body.appendChild(area);
    area.select();
    let ok = false;
    try { ok = document.execCommand('copy'); } catch (err) { ok = false; }
    document.body.removeChild(area);
    return ok;
  }
  document.addEventListener('click', e => {
    const b = e.target.closest('.copyLink');
    if (!b) return;
    const text = b.dataset.copy || '';
    if (!navigator.clipboard || !navigator.clipboard.writeText) {
      const ok = copyLegacy(text);
      copyMark(b, ok ? t("common.copied") : t("share.fail"));
      return;
    }
    navigator.clipboard.writeText(text).then(() => {
      copyMark(b, t("common.copied"));
    }).catch(err => {
      console.error('[copy] clipboard.writeText не сработал, пробуем execCommand:', err);
      const ok = copyLegacy(text);
      copyMark(b, ok ? t("common.copied") : t("share.fail"));
    });
  });
  const deep = decodeURIComponent(location.hash.replace('#sup=', ''));
  if (deep && supplements.some(s => s.id === deep)) setTimeout(() => openModal(deep), 300);
  renderEffectChips(); applyFilters(); checkInteractions();
  // v2.4: вкладки графика «Цена vs наука | Квадрант доказательности»
  // v2.6: оси X графика
    $('axisMA').onclick = () => setAxisX('ma');
  $('axisRCT').onclick = () => setAxisX('rct');
  $('viewTabs').addEventListener('click', e => {
    const btn = e.target.closest('.chartTab');
    if (btn && btn.dataset.view) setChartTab(btn.dataset.view);
  });
  $('quadrantChart').style.display = 'none';
  $('quadrantNote').style.display = 'none';
  $('favFilter').addEventListener('click', () => {
    onlyFavs = !onlyFavs;
    $('favFilter').classList.toggle('on', onlyFavs);
    applyFilters();
  });

  $('resetFilters').addEventListener('click', () => {
    // v5.6.5: чистим всю панель #controls, а не только ряд кнопок.
    // Раньше row = $('favFilter').parentElement (.filter-actions), а в нём
    // одни кнопки — ни #search, ни #verdictFilter, ни #sortSelect не
    // сбрасывались, и «Сбросить фильтры» не возвращал карточки после
    // поиска. Найдено тестом test_ui_verify (сброс не вернул карточки).
    const row = $('controls');
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
  // v4.1 — находка №12: одиночный символ без доступного имени.
  // Статический скан аудита эту кнопку не видел: её создаёт скрипт.
  up.setAttribute('aria-label', t("a11y.toTop"));
  up.title = t("common.toTop");
  up.onclick = () => scrollTo({top: 0, behavior: 'smooth'});
  document.body.appendChild(up);
  addEventListener('scroll', () => up.classList.toggle('show', scrollY > 500));

  // ── Prefetch полного data.json в простое ─────────────────────
  // Главная нарисована, теперь догружаем 472 KB когда браузер свободен.
  // К моменту клика на карточку/сравнение — данные уже в памяти.
  const prefetch = () => {
    if (supplementsFull || supplementsFullPromise) return;
    console.log('[prefetch] загружаем полный data.json в фоне…');
    ensureFullData().then(() => autoRenderCompare()).catch(() => {});
  };

  if ('requestIdleCallback' in window) {
    requestIdleCallback(prefetch, { timeout: 3000 });
  } else {
    setTimeout(prefetch, 1500);
  }

  // Радар: рендерим автоматически когда данные готовы
  const autoRenderCompare = () => {
    const s1 = $('compareSelect1'), s2 = $('compareSelect2');
    if (s1 && s2 && s1.value && s2.value) {
      try { renderCompare(); } catch (e) { console.warn('[compare auto]', e); }
    }
  };
}

// v5.4.0 (dark-first): параметр переименован в on, но смысл тот же —
// true = светлая тема. Тёмная теперь это ОТСУТСТВИЕ класса, поэтому
// setLight(false) ничего не добавляет. Название setDark вводило в
// заблуждение: при on=true включалась светлая тема.
// FIX-35 (I18N-05b): подпись кнопки темы может жить в <span data-i18n-text>
// (так размечены 404.html и ещё 8 статических страниц). Прежний
// btn.textContent = ... стирал span вместе с ключом, и следующий applyI18n()
// уже не мог перевести кнопку. Теперь span сохраняется, а его ключ
// синхронизируется с состоянием темы — тот же приём, что в applyTheme() на
// 404.html (FIX-34).
function setThemeBtnLabel(light) {
  const btn = $('themeBtn');
  if (!btn) return;
  const key = light ? 'theme.dark' : 'theme.light';
  const text = t(key);
  const lbl = btn.querySelector('[data-i18n-text]');
  if (lbl) { lbl.setAttribute('data-i18n-text', key); lbl.textContent = text; }
  else btn.textContent = text;
  // A2-01 (24.10.2026): доступное имя — действие, а не состояние.
  btn.setAttribute('aria-label', light ? t("a11y.themeToDark") : t("a11y.themeToLight"));
}

function setLight(on) {
  document.documentElement.classList.toggle('light', on);
  document.body.classList.toggle('light', on);
  setThemeBtnLabel(on);
  if (currentData.length) { if (chartTab === 'price') renderBubble(currentData); else renderQuadrant(currentData); }
}

// FIX-23 / CHART-01 (28.10.2026): таб «Сила эффекта (g)» перерисовывал только
// canvas, а заголовок раздела и подсказка оставались от «Доказательности» —
// переключение выглядело сломанным. Заголовок меняем вручную: новые ключи в
// i18n.js потянули бы cache-bump 149 HTML-файлов.
const CHART_HEADING_EFFECT = {
  ru: { title: "Сила эффекта: Hedges' g / индекс науки", hint: "(ось X — сила эффекта g, ось Y — индекс науки, лог-шкала)" },
  en: { title: "Effect size: Hedges' g / science index", hint: "(X axis — effect size g, Y axis — science index, log scale)" }
};
function updateChartHeading(tab) {
  const title = $('chartTitle'), hint = $('chartHint');
  if (!title || !hint) return;
  const eff = tab === 'quadrant';
  const alt = (typeof LOCALE === 'string' && LOCALE === 'en')
    ? CHART_HEADING_EFFECT.en : CHART_HEADING_EFFECT.ru;
  title.removeAttribute('data-i18n-text');
  hint.removeAttribute('data-i18n-text');
  title.textContent = eff ? alt.title : t('index.chartTitle');
  hint.textContent = eff ? alt.hint : t('index.chartHint');
}

// v2.4: переключение вкладки графика
function setChartTab(tab) {
  if (tab === chartTab) return;
  chartTab = tab;
  $('bubbleChart').style.display = tab === 'price' ? 'block' : 'none';
  $('quadrantChart').style.display = tab === 'quadrant' ? 'block' : 'none';
  $('chartNote').style.display = tab === 'price' ? '' : 'none';
  $('quadrantNote').style.display = tab === 'quadrant' ? '' : 'none';

  // axisRow (МА/РКИ) относится только к bubble — в quadrant скрываем
  const axisRow = $('axisRow');
  if (axisRow) axisRow.style.display = tab === 'price' ? '' : 'none';

  // подсветка активной кнопки
  document.querySelectorAll('#viewTabs .chartTab').forEach(b => {
    b.classList.toggle('on', b.dataset.view === tab);
  });

  // FIX-23: заголовок и подсказка раздела следуют за табом
  updateChartHeading(tab);

  if (currentData.length) { if (tab === 'price') renderBubble(currentData); else renderQuadrant(currentData); }
}

const vColor = c => c === 1 ? '#2d8a4e' : c === 0 ? '#d4a017' : '#c0392b';
const vColorAlpha = c => c === 1 ? 'rgba(45,138,78,0.75)' : c === 0 ? 'rgba(212,160,23,0.75)' : 'rgba(192,57,43,0.75)';

// ===== v2.6.1: демонтаж Value Score, честная экономика =====
/* economicsBlock removed per v2.7.1 chunk 2 — price_per_effect gone, no "Экономика" block */
/* priceTip removed 13.10.2026 — dead. Zero callers; s.price and s.price_date
   are absent from docs/data.json (0 occurrences across 130 cards). The tooltip
   text about a blocked marketplace TLS filter described a data source this
   project never had. scripts/e2e_smoke.py:210 asserts .priceTip is absent from
   the modal, and that assertion still holds. */
function verifiedCount() {
  const pool = supplementsFull ? Object.values(supplementsFull) : [];
  return pool.filter(s => (s.key_sources || []).length > 0).length;
}
function maTop3Block(s) {
  const curated = s.key_sources || [];
  const auto = s.ma_top3 || [];

  // Приоритет: ручной набор (curated). Fallback: автотоп с явной пометкой.
  const useCurated = curated.length > 0;
  const list = useCurated ? curated.slice(0, 3) : auto.slice(0, 3);

  const title = useCurated
    ? t("sources.curatedTitle")
    : t("sources.autoTitle");

  const note = useCurated
    ? t("sources.curatedNote")
    : t("sources.autoNote", { verified: verifiedCount(), total: supplements.length });

  const body = list.length
    ? '<div class="mrow">' + list.map(m => {
        const pmid = String(m.pmid || m);
        const rawTitle = String(m.title || pmid);
        const yr = m.year ? ' (' + m.year + ')' : '';
        const pmidEsc = esc(pmid);
        const titleEsc = esc(rawTitle);
        return '<div class="srcRow">'
          + '<a class="srcIcon" target="_blank" rel="noopener" '
          + 'title="' + titleEsc + '" '
          + 'href="https://pubmed.ncbi.nlm.nih.gov/' + pmidEsc + '/">'
          + titleEsc + yr + ' ↗</a>'
          + ' <span class="copyLink chip-pmid" data-copy="' + pmidEsc + '" '
          + 'title="' + t("sources.copyPmid", { pmid: pmidEsc }) + '">' + t("sources.pmid") + ' ' + pmidEsc + '</span>'
          + '</div>';
      }).join('') + '</div>'
    : '<div class="mrow cbEmpty">' + t("sources.empty") + '</div>';

  return '<div class="blockTitle">' + title + '</div>'
    + '<div class="mrow hint" style="font-size:.85rem;opacity:.9">' + note + '</div>'
    + body;
}
function applyFilters() {
  const q = $('search').value.toLowerCase().trim();
  const v = $('verdictFilter').value, ef = effectFilterCurrent, sort = presetScience ? 'science' : $('sortSelect').value;
  // v5.6.2 (T4): запрос-цифра ищем по PMID через ленивый индекс. Пока
  // индекс не построен, pmidIds === null и ветка пропускается — выборка
  // остаётся полной, а не схлопывается в ноль. Догрузив индекс, заново
  // прогоняем фильтр: пользователь не должен жать Enter второй раз.
  const pmidIds = q && PMID_QUERY_RE.test(q) ? matchPmidIds(q) : null;
  if (q && PMID_QUERY_RE.test(q) && pmidIds === null) ensurePmidIndex().then(() => applyFilters());
  currentData = supplements.filter(s => {
    if (presetVerdict && String(s.code) !== '1') return false;
    if (!presetVerdict && v !== 'all' && String(s.code) !== v) return false;
    if (ef !== 'all' && !(effectTags[s.id] || []).includes(ef)) return false;    if (presetOngoing && !((s.ongoing || 0) >= 1)) return false;
    if (pmidIds) { if (!pmidIds.includes(s.id)) return false; }
    else if (q && !(s.name.toLowerCase().includes(q) || (s.effects || []).join(' ').toLowerCase().includes(q))) return false;
    return true;
  });
  if (onlyFavs) currentData = currentData.filter(x => isFav(x.id));
  const cmp = {
    science: (a, b) => b.scienceIndex - a.scienceIndex,
    name: (a, b) => a.name.localeCompare(b.name, 'ru'),
    grade: (a, b) => ((GRADE_PRIOR[a.grade] ?? 4) - (GRADE_PRIOR[b.grade] ?? 4)) || (b.scienceIndex - a.scienceIndex)
  };
  currentData.sort(cmp[sort]);
  renderActiveFilters();
  $('countBadge').textContent = t("filter.count", { shown: currentData.length, total: supplements.length });
  /* UIUX-02: скелетоны при фильтрации — мягкий визуальный отклик до
     появления карточек. Данные уже в памяти, задержка имитирует отклик
     сети; renderCards сам по себе рендерит синхронно (тестовый стенд
     вызывает его напрямую, где setTimeout не выполняется). */
  const g = $('cardsGrid');
  g.innerHTML = '<div class="card skeleton" style="height: 100px; margin-bottom: 10px;"></div>' +
                '<div class="card skeleton" style="height: 100px; margin-bottom: 10px;"></div>' +
                '<div class="card skeleton" style="height: 100px; margin-bottom: 10px;"></div>';
  setTimeout(() => { renderCards(currentData); }, 150);
  if (chartTab === 'price') renderBubble(currentData); else renderQuadrant(currentData);
  updateFavUI();
  // F2.2: подпись под чартом — показано N из M
  const filterParts = [];
  if (v !== 'all') filterParts.push(t("filter.verdict"));
  if (q) filterParts.push(t("filter.search"));
  if (onlyFavs) filterParts.push(t("filter.favs"));
  const summary = $('chartSummary');
  if (summary) {
    summary.textContent = t("filter.shown", { shown: currentData.length, total: supplements.length }) +
      (filterParts.length ? ' ' + t("filter.suffix", { list: filterParts.join(', ') }) : '');
  }
}


// ===== Live-search дропдаун под строкой поиска (index.html) =====
let searchDropActive = -1;

function renderSearchDrop(q) {
  const drop = $('searchDrop');
  if (!drop) return;
  const v = (q || '').trim();
  if (!v) { drop.style.display = 'none'; drop.innerHTML = ''; searchDropActive = -1; setSearchDropOpen(false); return; }
  const vl = v.toLowerCase();
  const results = supplements.filter(s =>
    s.name.toLowerCase().includes(vl) || (s.effects || []).join(' ').toLowerCase().includes(vl)
  ).slice(0, 8);
  if (!results.length) {
    // 13A2a: строка вынесена в словарь (ключ empty.notFound)
    drop.innerHTML = '<div class="drop-empty">' + esc(t("empty.notFound")) + '</div>';
    drop.style.display = 'block';
    searchDropActive = -1;
    setSearchDropOpen(true);
    return;
  }
  drop.innerHTML = results.map((s, i) =>
    // A11Y-10: id на каждой опции — нужен для aria-activedescendant на #search
    '<div class="drop-row" role="option" id="searchDropOpt' + i + '" data-id="' + esc(s.id) + '" data-index="' + i + '">' +
    '<span class="drop-name">' + esc(s.name) + '</span>' +
    '<span class="drop-cat">' + esc(s.category || '') + '</span>' +
    '</div>'
  ).join('');
  drop.style.display = 'block';
  searchDropActive = -1;
  setSearchDropOpen(true);
  updateSearchDropFocus();
}

function updateSearchDropFocus() {
  const drop = $('searchDrop');
  if (!drop || drop.style.display === 'none') return;
  const rows = drop.querySelectorAll('.drop-row');
  rows.forEach((r, i) => {
    r.classList.toggle('focused', i === searchDropActive);
    r.setAttribute('aria-selected', i === searchDropActive ? 'true' : 'false');
  });
  // A11Y-10: активная опция рассказывается скринридеру через
  // aria-activedescendant на input#search (role="combobox")
  const search = $('search');
  if (search) {
    const active = rows[searchDropActive];
    if (active && searchDropActive >= 0) search.setAttribute('aria-activedescendant', active.id);
    else search.removeAttribute('aria-activedescendant');
  }
}

function pickSearchDrop() {
  const drop = $('searchDrop');
  if (!drop || drop.style.display === 'none') return;
  const row = drop.querySelector('.drop-row.focused') || drop.querySelector('.drop-row');
  if (!row) return;
  const id = row.dataset.id;
  $('search').value = '';
  drop.style.display = 'none';
  searchDropActive = -1;
  setSearchDropOpen(false);
  location.href = 'sup/' + slugify(id) + '.html';
}

const EFFECT_PRIORITY = [
  'sleep', 'stress', 'mood', 'brain', 'energy', 'immunity',
  'heart', 'blood', 'muscle', 'joints', 'skin'
];
let effectChipsExpanded = false;

function renderEffectChips() {
  const box = document.getElementById('tagPresets');
  if (!box) return;

  const allTags = Object.keys(effectLabels);
  const primary = EFFECT_PRIORITY.filter(t => allTags.includes(t));
  const rest = allTags.filter(t => !primary.includes(t));
  const visible = effectChipsExpanded ? [...primary, ...rest] : primary;

  const allBtn = '<button class="tagPreset' + (effectFilterCurrent === 'all' ? ' active' : '') +
                 '" data-tag="all">' + t("filter.allEffects") + '</button>';

  const chips = visible.map(slug => {
    const label = effectLabels[slug] || slug;
    const active = effectFilterCurrent === slug ? ' active' : '';
    return '<button class="tagPreset' + active + '" data-tag="' + slug + '">' + label + '</button>';
  }).join('');

  const more = rest.length
    ? (effectChipsExpanded
        ? '<button class="tagPreset tagPresetMore" data-more="1">' + t("common.collapse") + '</button>'
        : '<button class="tagPreset tagPresetMore" data-more="1">' + t("filter.more", { n: rest.length }) + '</button>')
    : '';

  box.innerHTML = allBtn + chips + more;
}

function renderActiveFilters() {
  const box = document.getElementById('activeFilters');
  if (!box) return;
  const chips = [];

  if (effectFilterCurrent !== 'all') {
    chips.push({ label: t("filter.effectPrefix") + (effectLabels[effectFilterCurrent] || effectFilterCurrent), clear: 'effect' });
  }
  const v = $('verdictFilter').value;
  if (v !== 'all') {
    const map = { '1': t("verdict.works"), '0': t("verdict.depends"), '-1': t("verdict.unproven") };
    chips.push({ label: t("filter.verdictPrefix") + (map[v] || v), clear: 'verdict' });
  }
  const q = $('search').value.trim();
  if (q) chips.push({ label: t("filter.searchPrefix") + q, clear: 'search' });

  if (!chips.length) { box.innerHTML = ''; return; }

  box.innerHTML = chips.map(c =>
    '<span class="activeFilter" data-clear="' + esc(c.clear) + '">' + esc(c.label) +
    ' <span class="activeFilterX">×</span></span>'
  ).join('') + '<button class="activeFilterClear" id="clearAllFilters">' + t("common.clear") + '</button>';

  const reset = $('resetFilters');
  if (reset) {
    const hasFilters = chips.length > 0 || presetScience || presetVerdict || presetOngoing || onlyFavs;
    reset.disabled = !hasFilters;
  }
}

// v5.6.2 E2: разбор названия категории на группу для цветного значка.
// FIX-14 (I18N-02): первоисточник группы — структурное поле category_group
// (добавлено в data.json / data_en.json скриптом scripts/add_category_group.py).
// catGroup() оставлен только как fallback для tagChips (effectLabels), где
// нет category_group: теперь проверяет и RU-, и EN-подстроки.
const CAT_GROUPS = [
  ['gut',      ['жкт', 'кишечник', 'пищевар', 'gi', 'digest', 'stomach', 'intestinal', 'gut']],
  ['cardio',   ['сердце', 'сосуд', 'кров', 'почки', 'мочеполов', 'мочевывод', 'вены', 'давлен', 'heart', 'vessel', 'blood', 'kidney', 'urogen', 'vein', 'pressure']],
  ['bone',     ['кост', 'сустав', 'минерал', 'кожа', 'остео', 'bone', 'joint', 'mineral', 'skin', 'osteo']],
  ['liver',    ['печень', 'liver']],
  ['brain',    ['мозг', 'когни', 'невролог', 'нервн', 'психи', 'сон', 'настроен', 'стресс', 'усталость', 'адаптоген', 'памят', 'деменц', 'brain', 'cogn', 'neurolog', 'nerv', 'psych', 'sleep', 'mood', 'stress', 'adaptogen', 'memor', 'dement', 'mental', 'depress']],
  ['immune',   ['иммунитет', 'орви', 'антиоксид', 'воспален', 'грибы', 'грипп', 'immune', 'immunity', 'ori', 'antioxid', 'inflamm', 'mushroom', 'flu']],
  ['metab',    ['метабол', 'гормон', 'энерг', 'сексуальн', 'производительн', 'диабет', 'холестерин', 'вес', 'инсулин', 'metabol', 'hormon', 'energ', 'sexual', 'perform', 'diabet', 'cholesterol', 'weight', 'insulin']],
  ['sport',    ['спорт', 'мышц', 'выносл', 'бодрость', 'sport', 'muscle', 'endur', 'vigor']],
  ['women',    ['беременн', 'женск', 'спкя', 'дети', 'pregnan', 'women', 'pcos', 'children']],
  ['vision',   ['зрени', 'глаза', 'сетчат', 'зрительн', 'vision', 'eye', 'retin', 'visual']],
  ['general',  ['общее', 'старени', 'долголет', 'гериатр', 'general', 'aging', 'longev', 'geriatr']],
  ['critical', ['критическ', 'реанимац', 'интенсив', 'critical', 'resusc', 'intensiv']],
];
const catGroup = (raw) => {
  const s = String(raw || '').toLowerCase();
  // Первый сегмент: до «/», до « и », до запятой.
  const head = s.split(/[\/,]|[ ]и[ ]/)[0].trim();
  for (const [g, keys] of CAT_GROUPS) {
    if (keys.some(k => head.includes(k))) return g;
  }
  // Заголовок мог не разделиться — проверяем по всей строке.
  for (const [g, keys] of CAT_GROUPS) {
    if (keys.some(k => s.includes(k))) return g;
  }
  return 'neutral';
};

function renderCards(data) {
  const g = $('cardsGrid');
  if (!data.length) { g.innerHTML = '<div class="empty">' + t("empty.notFound") + ' ' +
      '<button id="resetAll" class="favFilter">' + t("empty.resetFavs") + '</button></div>'; return; }
  // v5.6.2 батч C (T3): карточка получает tabindex="-1" — она становится
  // фокусируемой (фокус возвращается на неё после закрытия модалки), но
  // НЕ входит в порядок обхода Tab: перебор 130 карточек стрелками не
  // нужен, открывать их с клавиатуры можно в любом случае через Enter.
  g.innerHTML = data.map(s => '<div class="card" data-id="' + esc(s.id) + '" tabindex="-1">' +
    '<button class="favBtn' + (isFav(s.id) ? ' on' : '') + '" data-fav="' + esc(s.id) + '" title="' + t("card.favTitle") + '">' + (isFav(s.id) ? '★' : '☆') + '</button>' +
    (BEST.includes(s.id) ? '<span class="bestBadge">' + t("card.top3") + '</span>' : '') +
    // Заголовок карточки — НЕ h3: на index их было 134 (по одной на добавку),
    // из-за чего структура документа переставала отражать реальные разделы.
    // Название добавки — strong, разделы остались h2 (P2-16).
    '<span class="cat" data-cat-group="' + (s.category_group || 'neutral') + '">' + esc(s.category || '') + '</span><strong class="card-title">' + esc(s.name) + '</strong>' +
    updatedLine(s) + manualBadge(s) +
    '<div class="verdict v' + esc(s.code) + '">' + esc(s.verdict) + '</div>' + gradeBadge(s) +     '<div class="effects">' + (s.effects || []).map(e => '<span>' + esc(e) + '</span>').join('') + '</div>' +
    '<div class="tagChips">' + (effectTags[s.id] || []).map(t =>
      '<span class="tagChip" data-cat-group="' + catGroup(effectLabels[t] || t) + '" data-tag="' + esc(t) + '" title="' + esc(effectLabels[t] || t) + '">' + esc(effectLabels[t] || t) + '</span>'
    ).join('') + '</div></div>').join('');
  g.querySelectorAll('.card').forEach(el => {
    const url = 'sup/' + slugify(el.dataset.id) + '.html';
    el.onclick = (e) => {
      if (e.target.closest('a')) return;
      location.href = url;
    };
    // v5.6.2 батч C (T3): карточка — div с onclick, без неё она
    // недостижима с клавиатуры: ни Enter, ни Пробел ничего не делали.
    // Роли не назначаем — div-карточка не ссылка.
    el.onkeydown = (e) => {
      if (e.key !== 'Enter' && e.key !== ' ') return;
      if (e.target.closest('a, button')) return;   // свои элементы обработают сами
      e.preventDefault();
      location.href = url;
    };
  });
}

// v5.6.2 (батч C, T3): ловушка фокуса внутри модалки. Без неё Tab
// выходил из диалога на элементы страницы под ним — то есть модалка
// выглядела открытой, но клавиатурный пользователь управлял уже
// невидимым интерфейсом. Список фокусируемых собирается на каждый
// вызов, потому что содержимое #modalBody перерисовывается при открытии.
const FOCUSABLE_SEL =
  'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), ' +
  'textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';

function modalFocusables() {
  const box = $('modalOverlay');
  if (!box) return [];
  return Array.from(box.querySelectorAll(FOCUSABLE_SEL))
    .filter(el => el.offsetParent !== null || el === document.activeElement);
}

function focusModalFirst() {
  const list = modalFocusables();
  if (list.length) list[0].focus();
}

function trapModalFocus(e) {
  if (!$('modalOverlay') || $('modalOverlay').style.display === 'none') return;
  if (e.key !== 'Tab') return;
  const list = modalFocusables();
  if (!list.length) return;
  const first = list[0], last = list[list.length - 1];
  const active = document.activeElement;
  if (!list.includes(active)) { e.preventDefault(); first.focus(); return; }
  if (e.shiftKey && active === first) { e.preventDefault(); last.focus(); }
  else if (!e.shiftKey && active === last) { e.preventDefault(); first.focus(); }
}

function showModalError(id, errMsg, retryLabel) {
  const html =
    '<div class="mrow error">' +
    '<div class="errTitle">⚠ ' + esc(errMsg) + '</div>' +
    '<div class="errDetail">' + t("modal.cardNotFound", { id: esc(id) }) + '</div>' +
    '<button class="modalRetry" data-id="' + esc(id) + '" onclick="openModal(this.dataset.id)">' + esc(retryLabel) + '</button>' +
    '</div>';
  $('modalBody').innerHTML = html;
  $('modalOverlay').style.display = 'flex';
  document.body.classList.add('modal-open');
  focusModalFirst();
}

async function openModal(id) {
  scrollBeforeModal = window.scrollY || 0;

  // FIX-77: раньше здесь был свой fetchJson('data.json') — дубль
  // ensureFullData() и обход EN-оверлея. Теперь единая точка загрузки.
  let s = supplementsFull ? supplementsFull[id] : null;
  if (!s) {
    try {
      const map = await ensureFullData();
      s = map[id];
    } catch (err) {
      showModalError(id, t('ui.error.network'), t('ui.error.retry'));
      return;
    }
  }
  if (!s) {
    showModalError(id, t('ui.error.network'), t('ui.error.retry'));
    return;
  }
  curModal = id;

  const trialsLine = s.ongoing != null
    ? (s.ongoing > 0
        ? '<div class="mrow">🧪 <b>' + t("trials.activeLabel") + ': ' + s.ongoing + '</b>' + t("trials.activeSuffix") + '</div>'
        : '<div class="mrow warn">' + t("trials.none") + '</div>')
    : '';

  const calcLine = s.dosagePerKg != null
    ? '<div class="mrow calc">' +
      '<label for="weightInput">' + t("calc.label") + '</label>' +
      '<div class="calcRow">' +
      '<input type="number" id="weightInput" placeholder="' + t("calc.placeholder") + '" min="30" max="200" step="0.1"/>' +
      '<span id="calcResult" class="calcResult"></span>' +
      '</div>' +
      '<small class="hint">' + t("calc.standard") + (s.dosage || '—') + '</small>' +
      '</div>'
    : '';

  $('modalBody').innerHTML = '<h2 id="modalTitle">' + esc(s.name) + '</h2>' + updatedLine(s) + manualBadge(s) +
    '<div class="mrow"><span class="verdict v' + esc(s.code) + '">' + esc(s.verdict) + '</span> · ' + esc(s.category || '') + (s.grade ? ' · <span class="grade g' + esc(s.grade) + '">' + t("card.grade") + ' ' + esc(s.grade) + '</span> · ' + esc(GRADE_LABEL[s.grade] || '') : '') + pmidBadge(s) + '</div>' +     '<div class="mrow">' + scienceSpan(s) + gSpan(s) + pubmedLink(s) + ' · ' + maSpan(s) + '</div>' +
    maTop3Block(s) +    trialsLine +
    calcLine +
    (s.citations != null ? '<div class="mrow">' + t("modal.citations") + s.citations + '</div>' : '') +
    (s.wiki != null ? '<div class="mrow">' + t("modal.wikiViews") + s.wiki.toLocaleString(LOCALE) + wikiLink(s) + '</div>' : '') +
    '<div class="mrow"><b>' + t("modal.effects") + '</b> ' + ((s.effects || []).join(', ') || '—') + '</div>' +
    '<div class="mrow">💊 <b>' + t("modal.dosage") + '</b> ' + (s.dosage || '—') + '</div>' +
    '<div class="mrow">⏳ <b>' + t("modal.course") + '</b> ' + (s.course || '—') + '</div>' +
    onsetSpan(s) +
    (s.forms && s.forms.length ? '<div class="mrow">🧪 <b>' + t("modal.forms") + '</b> ' + esc(Array.isArray(s.forms) ? s.forms.join(', ') : s.forms) + '</div>' : '') +
    unknownsBlock(s) +
    shopBlock(s) +
    shareRow(s) +
    compareBlock(s) +
    cautionSpan(s) +
    // Кнопку копирования ссылки здесь убрали как дубль: выше, в shareRow(),
    // уже есть «🔗 копировать» с тем же действием (docs/script.js, P1-3).
    ' <a class="favFilter" target="_blank" rel="noopener" href="' + issueUrl(s, '') + '">' + t("modal.issue") + '</a></div>' +
    '<div class="blockTitle">' + t("modal.fullCard") + '</div>' + renderCardBlocks(s);
  history.replaceState(null, '', '#sup=' + encodeURIComponent(s.id));
  $('modalOverlay').style.display = 'flex';
  // v5.6.2 (батч C, T3): модалка без role="dialog" и без ловушки фокуса —
  // клавиатурный пользователь уходил из диалога на страницу под ним, не
  // возвращаясь. ARIA-атрибуты на #modal проставлены в index.html:433,
  // заголовок-подпись получает id в innerHTML выше. Фокус переносим внутрь
  // и держим Tab/Shift+Tab внутри, пока диалог открыт.
  modalPrevFocus = document.activeElement;
  focusModalFirst();
  // Класс на <body> — сигнал открытой модалки для CSS. Раньше приходилось
  // ловить состояние селектором body:has(#modalOverlay[style*="display: flex"]),
  // а он зависит от того, как движок сериализует инлайновый style: замена
  // 'flex' на 'block' в строке выше молча сломала бы правило, и шапка снова
  // легла бы поверх диалога. Класс от такого не зависит.
  document.body.classList.add('modal-open');

  if (s.dosagePerKg != null) {
    const weightInput = $('weightInput');
    const calcResult = $('calcResult');
    weightInput.addEventListener('input', () => {
      const weight = parseFloat(weightInput.value);
        if (weight > 0 && weight <= 500) {
        const dose = weight * s.dosagePerKg;
        const unit = s.dosage && s.dosage.includes('мг') ? 'мг' : s.dosage && s.dosage.includes('г') ? 'г' : 'МЕ';
        let html = '<b>' + t("calc.perDay", { dose: dose.toFixed(1), unit }) + '</b>';
        if (s.dosageMax && dose > s.dosageMax) {
          html += ' <span class="warn">' + t("calc.overMax", { max: s.dosageMax, unit }) + '</span>';
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
  document.body.classList.remove('modal-open');
  history.replaceState(null, '', location.pathname);
  window.scrollTo({ top: scrollBeforeModal, behavior: 'smooth' });
  // v5.6.2 (T3): вернуть фокус на карточку, из которой модалка открыта,
  // иначе после закрытия фокус падал на <body> и Tab начинал снова
  // с шапки — пользователь терял место в списке.
  if (modalPrevFocus && document.contains(modalPrevFocus)) modalPrevFocus.focus();
  modalPrevFocus = null;
}

// ===== v2.6: сменная ось X графика (Цена/MА/РКИ/Год) =====
let axisX = 'ma';
const AXIS_IDS = { ma: 'axisMA', rct: 'axisRCT' };
const AXIS_LABEL = { ma: t("axis.ma"), rct: t("axis.rct") };
function axisVal(s) {
  if (axisX === 'ma') return (s.metaCount || 0) > 0 ? s.metaCount : null;
  if (axisX === 'rct') { const r = Math.max(0, (s.scienceIndex || 0) - 5 * (s.metaCount || 0)); return r > 0 ? r : null; }
  return null;
}
function setAxisX(ax) {
  if (ax === axisX) return;
  axisX = ax;
  ['ma', 'rct'].forEach(k => $(AXIS_IDS[k]).classList.toggle('on', k === ax));
  if (currentData.length && chartTab === 'price') renderBubble(currentData);
}

function gotoCompare(idA, idB) {
  closeModal();
  location.href = 'hactar.html?tab=compare&ids=' + encodeURIComponent(idA) + (idB ? ',' + encodeURIComponent(idB) : '');
}

// ── Адаптивные размеры пузырей: на мобильном меньше ─────────
function bubbleRadii() {
  const isMobile = window.innerWidth < 640;
  const R_MAX = isMobile ? 12 : 22;
  const R_HOVER_MAX = isMobile ? 16 : 28;
  const R_SCALE = isMobile ? 1.0 : 2.5;
  const R_HOVER_SCALE = isMobile ? 1.4 : 3.5;
  return {
    rFor:      (s) => Math.max(5, Math.min(R_MAX, Math.sqrt(s.metaCount || 1) * R_SCALE)),
    rHoverFor: (s) => Math.max(7, Math.min(R_HOVER_MAX, Math.sqrt(s.metaCount || 1) * R_HOVER_SCALE)),
  };
}

// E1.5 (батч 5): ветки оси «Цена» удалены как мёртвые. В разметке
// только axisMA/axisRCT (docs/index.html:347-348), setAxisX вызывается
// лишь с 'ma'/'rct', поэтому axisX !== 'price' всегда.
function renderBubble(data) {
  const { rFor, rHoverFor } = bubbleRadii();
  const plotted = data.filter(s => { const v = axisVal(s); return v != null && v > 0; });
  // Явный max по данным для X-оси (Chart.js на лог-шкале оставляет большой запас)
  // min/max по данным — плотная посадка точек в обоих табах
  const xVals = plotted.map(s => axisVal(s)).filter(v => v != null && v > 0);
  const xMax = xVals.length ? xVals.reduce((m, v) => Math.max(m, v), 1) : 1;
  const xMin = xVals.length ? xVals.reduce((m, v) => Math.min(m, v), Infinity) : 1;
  chartPts = plotted;
  $('chartNote').textContent = plotted.length < data.length
    ? t("chart.missingMsg", { count: data.length - plotted.length, axis: AXIS_LABEL[axisX] }) : '';
  const ctx = $('bubbleChart').getContext('2d');
  if (chartInstance) chartInstance.destroy();
  const txt = getComputedStyle(document.body).getPropertyValue('--text');
  chartInstance = new Chart(ctx, {
    type: 'scatter',
    data: { datasets: plotted.map(s => ({
      label: s.name,
      data: [{ x: axisVal(s), y: Math.max(1, s.scienceIndex) }],
      backgroundColor: vColorAlpha(s.code),
      pointRadius: rFor(s),
      pointHoverRadius: rHoverFor(s)
    })) },
    options: {
      responsive: true, maintainAspectRatio: false,
      layout: { padding: { left: 12, right: 8, top: 4, bottom: 4 } },
      scales: {
        x: { type: 'logarithmic', min: xMin * 0.75, max: xMax * 1.25,
             title: { display: true, text: AXIS_LABEL[axisX] + t("chart.logSuffix"), color: txt },
             grid: { color: 'rgba(128,128,128,.15)' },
             ticks: { callback: v => [1, 10, 100, 1000, 10000].includes(v) ? v : '' } },
        y: { type: 'logarithmic',
             title: { display: true, text: t("chart.yTitleLog"), color: txt },
             grid: { color: 'rgba(128,128,128,.15)' },
             ticks: { callback: v => [1, 10, 100, 1000, 10000].includes(v) ? v : '' } }
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: ctx => {
              const s = chartSupByEl(ctx.chart, { datasetIndex: ctx.datasetIndex, index: ctx.dataIndex });
              return s ? ' ' + s.name + ' · ' + AXIS_LABEL[axisX] + ': ' + axisVal(s) + ' · ' + s.verdict : '';
            }
          }
        }
      },
      onClick: (e, els) => {
        if (!els.length) return;
        const s = chartSupByEl(e.chart, els[0]);
        if (!s) return;
        location.href = 'sup/' + slugify(s.id) + '.html';
      },
      onHover: (e, els) => {
        e.native.target.style.cursor = els.length ? 'pointer' : 'default';
      }
    }
  });
  window.chart = chartInstance;
}

// ===== v2.4: квадрант доказательности (Hedges' g vs scienceIndex) =====
function renderQuadrant(data) {
  // FIX-40 (MAN-05): hedges_g мог прийти строкой («0.71») — из data.json,
  // api/v1 или правки руками. Chart.js в scatter молча не рисует точку с
  // нечисловым x, и график выглядит пустым без единой ошибки в консоли.
  // Поэтому значение приводим к числу, а всё нефинитное (null, "", NaN,
  // «н/д») отбрасываем — это же число попадает в подпись «ждут проверки».
  const verified = data
    .map(s => {
      if (s.hedges_g == null || s.scienceIndex == null) return null;
      const g = Number(s.hedges_g), si = Number(s.scienceIndex);
      return Number.isFinite(g) && Number.isFinite(si) ? { s, g, si } : null;
    })
    .filter(Boolean);
  $('quadrantNote').textContent = verified.length < data.length
    ? t("quadrant.waiting", { count: data.length - verified.length }) : '';
  const ctx = $('quadrantChart').getContext('2d');
  if (quadrantInstance) quadrantInstance.destroy();
  const txt = getComputedStyle(document.body).getPropertyValue('--text');
  quadrantInstance = new Chart(ctx, {
    type: 'scatter',
    data: { datasets: (() => {
      const { rFor, rHoverFor } = bubbleRadii();
      return verified.map(({ s, g, si }) => ({
        label: s.name,
        data: [{ x: g, y: Math.max(1, si) }],
        backgroundColor: vColorAlpha(s.code),
        pointRadius: rFor(s),
        pointHoverRadius: rHoverFor(s),
      }));
    })() },
    options: {
      responsive: true, maintainAspectRatio: false,
      scales: {
        x: {
          title: { display: true, text: t("quadrant.xTitle"), color: txt },
          suggestedMin: -2.5,
          suggestedMax: 2.5,
          grid: { color: ctx => ctx.tick.value === 0 ? 'rgba(128,128,128,.5)' : 'rgba(128,128,128,.15)' }
        },
        y: {
          type: 'logarithmic',
          title: { display: true, text: t("quadrant.yTitle"), color: txt },
          grid: { color: 'rgba(128,128,128,.15)' }
        }
      },
      plugins: {
        legend: { display: false },
        tooltip: { callbacks: { label: ctx => {
          const s = chartSupByEl(ctx.chart, { datasetIndex: ctx.datasetIndex, index: ctx.dataIndex });
          return s ? ' ' + s.name + ' · g=' + s.hedges_g + ' · ' + (s.grade || '—') + ' · ' + s.verdict : '';
        } } }
      },
      onClick: (e, els) => { if (!els.length) return; const s = chartSupByEl(e.chart, els[0]); if (!s) return; location.href = 'sup/' + slugify(s.id) + '.html'; },
      onHover: (e, els) => { e.native.style.cursor = els.length ? 'pointer' : 'default'; }
    }
  });
  window.quadrantChart = quadrantInstance;
}

function radarFill(ctx) {
  const { chart } = ctx; const { ctx: c, chartArea } = chart;
  if (!chartArea) return 'rgba(52,152,219,.25)';
  const cx = (chartArea.left + chartArea.right) / 2, cy = (chartArea.top + chartArea.bottom) / 2;
  const g = c.createRadialGradient(cx, cy, 8, cx, cy, Math.max(chartArea.width, chartArea.height) / 2);
  g.addColorStop(0, 'rgba(46,204,130,.38)');
  g.addColorStop(1, 'rgba(52,152,219,.12)');
  return g;
}

async function renderCompare() {
  const idA = $('compareSelect1').value;
  const idB = $('compareSelect2').value;

  // Ленивая загрузка полного data.json если prefetch ещё не отработал
  let a = supplementsFull ? supplementsFull[idA] : null;
  let b = supplementsFull ? supplementsFull[idB] : null;
  if (!a || !b) {
    try {
      const map = await ensureFullData();
      a = map[idA];
      b = map[idB];
    } catch {
      // UX-01/UX-02 (FIX-SPRINT B2): раньше был тихой return — пользователь
      // нажимал «Сравнить», ничего не происходило и не было видно, что
      // запрос упал. Теперь показываем ошибку с кнопкой повтора.
      const res = $('compareResult');
      if (res) {
        res.innerHTML =
          '<div style="padding:.6rem .8rem;border:1px solid var(--aborder);border-radius:var(--radius-lg);background:var(--apanel)">' +
          '<span role="alert">' + t("boot.error") + '</span>' +
          ' <button type="button" class="btn" id="compareRetry" style="margin-inline-start:.4rem">' + t("boot.retry") + '</button></div>';
        const retry = $('compareRetry');
        if (retry) retry.onclick = () => { renderCompare(); };
      }
      return;
    }
  }
  if (!a || !b) return;
  const rows = [
    [t("cmp.verdict"), a.verdict, b.verdict],
        [t("cmp.science"), a.scienceIndex, b.scienceIndex],
    [t("cmp.ma"), a.metaCount, b.metaCount],
    [t("cmp.trials"), a.ongoing ?? '—', b.ongoing ?? '—'],
    [t("cmp.citations"), a.citations ?? '—', b.citations ?? '—'],
    [t("cmp.effects"), (a.effects || []).join(', '), (b.effects || []).join(', ')],
    [t("cmp.dosage"), a.dosage ?? '—', b.dosage ?? '—'],
    [t("cmp.course"), a.course ?? '—', b.course ?? '—'],
    [t("cmp.caution"), a.caution ?? '—', b.caution ?? '—']
  ];
  $('compareResult').innerHTML = '<table><tr><th>' + t("cmp.param") + '</th><th>' + esc(a.name) + '</th><th>' + esc(b.name) + '</th></tr>' +
    rows.map(r => '<tr><td>' + esc(r[0]) + '</td><td>' + esc(r[1]) + '</td><td>' + esc(r[2]) + '</td></tr>').join('') + '</table>';

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
  const BASE_FOR_PCT = supplements;   // нормировка по всей базе 130
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
  const PROF_LABELS = [t("prof.science"), t("prof.maBase"), t("prof.verified"), t("prof.completeness")];
  const rc = $('radarChart');
  if (rc) {
    if (radarInstance) radarInstance.destroy();
    radarInstance = new Chart(rc, {
      type: 'radar',
    data: {
      labels: [
        t("prof.long.science"),
        t("prof.long.maBase"),
        t("prof.long.verified"),
        t("prof.long.completeness")
      ],
      datasets: [
        { label: a.name, data: prof(a), borderColor: '#3498db', backgroundColor: radarFill,
          pointBackgroundColor: '#3498db' },
        { label: b.name, data: prof(b), borderColor: '#e67e22', backgroundColor: radarFill,
          pointBackgroundColor: '#e67e22' }
      ]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
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
    ? t("banner.dangerPrefix") + critical.map(c => c.s1 + ' + ' + c.s2).join(', ') + '. ' + critical[0].note : '');
  renderBanner('medium', 'conflict-banner medium', medium.length
    ? t("banner.warnPrefix") + medium.map(c => c.s1 + t("banner.and") + c.s2).join(', ') + t("banner.conflictSuffix") : '');
  renderBanner('synergy', 'synergy-banner', synergy.length
    ? t("banner.synergyPrefix") + synergy.map(c => c.s1 + ' + ' + c.s2).join(', ') : '');
}

['addFav', 'removeFav'].forEach(event => {
  window.addEventListener(event, checkInteractions);
});

// ── Haptic feedback (Android) ───────────────────────
function haptic(ms) {
  if (!('vibrate' in navigator)) return;
  try { navigator.vibrate(ms || 8); } catch(e) {}
}
document.addEventListener('click', e => {
  const el = e.target.closest('button, .btn, .chip, .chartTab, a.cta');
  if (el) haptic(8);
}, { passive: true });

// ===== Автообновление при выходе новой версии =====
(function () {
  const CHECK_INTERVAL = 2 * 60 * 1000; // 2 минуты
  const STORAGE_KEY = 'brain25_version_seen';

  async function checkVersion() {
    try {
      const r = await fetch('version.json?_=' + Date.now(), { cache: 'no-store' });
      if (!r.ok) return;
      const v = await r.json();

      // Считаем «слепок» из app + data — меняются при каждом релизе
      const current = `${v.app}|${v.data}|${v.tests}`;
      const last = localStorage.getItem(STORAGE_KEY);

      if (last && last !== current) {
        // Новая версия доступна — перезагружаем
        console.log('[auto-update] Новая версия:', current, '(было', last + ')');
        localStorage.setItem(STORAGE_KEY, current);
        // Небольшая пауза, чтобы пользователь увидел уведомление
        showUpdateToast();
      } else if (!last) {
        localStorage.setItem(STORAGE_KEY, current);
      }
    } catch (e) {
      // тихо игнорируем — нет связи, нет version.json
    }
  }

  function showUpdateToast() {
    const el = document.createElement('div');
    el.textContent = t("update.toast");
    el.style.cssText = `
      position:fixed;bottom:1rem;left:50%;transform:translateX(-50%);
      background:var(--info-fill,#1f6fa5);color:#fff;padding:.6rem 1.2rem;border-radius:8px;
      font-size:.9rem;z-index:99999;box-shadow:0 4px 12px rgba(0,0,0,.3);
    `;
    document.body.appendChild(el);
    setTimeout(() => location.reload(true), 1200);
  }

  // Проверяем сразу + каждые 2 минуты
  setTimeout(checkVersion, 3000);
  setInterval(checkVersion, CHECK_INTERVAL);
})();