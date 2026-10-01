/* Тестовый стенд для docs/script.js без браузера (jsdom в проекте нет).
 *
 * Загружает САМ script.js — не копию функций — и выполняет реальный код
 * renderCards()/esc() на минимальном DOM-шиме. Это единственный способ
 * проверить поведение карточек в pytest: Chromium в CI не установлен
 * (в workflows/tests.yml нет `playwright install chromium`), а без DOM
 * script.js не запускается.
 *
 * Печатает JSON в stdout, дальше его разбирает tests/test_js_behavior.py.
 * stderr не используется — всё в stdout, чтобы pytest не путал вывод node
 * с выводом скрипта.
 */
const fs = require('fs');
const vm = require('vm');

const SCRIPT = process.env.SCRIPT_JS || 'docs/script.js';
const out = { ok: false, results: {}, errors: [] };

function makeEl(tag) {
  const el = {
    tagName: String(tag || 'div').toUpperCase(),
    style: {}, dataset: {}, children: [], attrs: {},
    innerHTML: '', textContent: '', value: '',
    classList: {
      _s: new Set(),
      add(...c) { c.forEach(x => this._s.add(x)); },
      remove(...c) { c.forEach(x => this._s.delete(x)); },
      contains(c) { return this._s.has(c); },
      toggle(c, f) { if (f === undefined) { this._s.has(c) ? this._s.delete(c) : this._s.add(c); } else if (f) { this._s.add(c); } else { this._s.delete(c); } },
    },
    setAttribute(k, v) { this.attrs[k] = String(v); },
    getAttribute(k) { return k in this.attrs ? this.attrs[k] : null; },
    removeAttribute(k) { delete this.attrs[k]; },
    appendChild(c) { this.children.push(c); return c; },
    insertAdjacentHTML() {}, replaceChildren() {},
    addEventListener() {}, removeEventListener() {}, dispatchEvent() { return true; },
    querySelector() { return null; },
    querySelectorAll() { return []; },
    closest() { return null; }, matches() { return false; },
    remove() {}, focus() {}, click() {}, scrollIntoView() {},
    getBoundingClientRect() { return { top: 0, left: 0, right: 0, bottom: 0, width: 0, height: 0 }; },
  };
  return el;
}

const nodes = Object.create(null);
const doc = {
  documentElement: makeEl('html'),
  body: makeEl('body'),
  head: makeEl('head'),
  cookie: '', readyState: 'complete', hidden: false,
  getElementById(id) { if (!(id in nodes)) nodes[id] = makeEl('div'); return nodes[id]; },
  querySelector() { return null; },
  querySelectorAll() { return []; },
  createElement: makeEl,
  createTextNode: (t) => ({ nodeType: 3, textContent: t }),
  addEventListener() {}, removeEventListener() {},
};

const store = Object.create(null);
const localStorage = {
  getItem: (k) => (k in store ? store[k] : null),
  setItem: (k, v) => { store[k] = String(v); },
  removeItem: (k) => { delete store[k]; },
};

const sandbox = {
  console: { log() {}, warn() {}, error() {}, info() {}, debug() {} },
  document: doc,
  localStorage,
  location: { href: 'http://localhost/', search: '', hash: '', pathname: '/', reload() {} },
  navigator: { onLine: true, vibrate() {}, userAgent: 'node-harness' },
  matchMedia: () => ({ matches: false, addEventListener() {}, addListener() {} }),
  requestIdleCallback: (fn) => { try { fn(); } catch (e) { /* фоновые задачи не важны */ } },
  setTimeout: (fn) => 0,          // таймеры НЕ выполняем: иначе бот-загрузка живёт вечно
  clearTimeout() {}, setInterval: () => 0, clearInterval() {},
  fetch: () => Promise.reject(new Error('нет сети в стенде')),
  Chart: function () { return { destroy() {}, update() {}, data: {} }; },
  innerWidth: 1280, innerHeight: 900, devicePixelRatio: 1,
  URLSearchParams, URL, Promise, Math, JSON, Date, RegExp, Object, Array, String, Number, Boolean, Error,
  addEventListener() {}, removeEventListener() {}, scrollTo() {},
};
sandbox.window = sandbox;
sandbox.globalThis = sandbox;
sandbox.self = sandbox;
sandbox.fetchJson = undefined;
vm.createContext(sandbox);

try {
  const code = fs.readFileSync(SCRIPT, 'utf8');
  // Скрипт — это скрипт, а не модуль: выполняем в общем контексте через Function,
  // чтобы получить доступ к объявленным через function/const сущностям.
  const factory = new Function(
    'sandboxGlobal',
    'const window = sandboxGlobal.window, document = sandboxGlobal.document, ' +
    'localStorage = sandboxGlobal.localStorage, location = sandboxGlobal.location, ' +
    'navigator = sandboxGlobal.navigator, matchMedia = sandboxGlobal.matchMedia, ' +
    'requestIdleCallback = sandboxGlobal.requestIdleCallback, setTimeout = sandboxGlobal.setTimeout, ' +
    'clearTimeout = sandboxGlobal.clearTimeout, setInterval = sandboxGlobal.setInterval, ' +
    'clearInterval = sandboxGlobal.clearInterval, fetch = sandboxGlobal.fetch, ' +
    'Chart = sandboxGlobal.Chart, innerWidth = sandboxGlobal.innerWidth, ' +
    'innerHeight = sandboxGlobal.innerHeight, devicePixelRatio = sandboxGlobal.devicePixelRatio, ' +
    'console = sandboxGlobal.console, addEventListener = sandboxGlobal.addEventListener, ' +
    'scrollTo = sandboxGlobal.scrollTo, URLSearchParams = sandboxGlobal.URLSearchParams;' +
    code +
    '\n;return { renderCards, esc, isFav, gradeBadge, updatedLine, manualBadge };'
  );
  const api = factory(sandbox);

  out.results.exported = Object.keys(api);

  // ─── esc(): экранирование ───
  out.results.esc = {
    lt: api.esc('<'),
    gt: api.esc('>'),
    amp: api.esc('&'),
    dq: api.esc('"'),
    sq: api.esc("'"),
    slash: api.esc('/'),
    backslash: api.esc('\\'),
    script: api.esc('<script>alert(1)</script>'),
    img_onerror: api.esc('<img src=x onerror=alert(1)>'),
    amp_first: api.esc('&lt;'),           // amp экранируется ПЕРВЫМ, без двойного
    cyr: api.esc('Креатин'),
    mixed: api.esc('Л-Теанин (L-theanine)'),
    null_: api.esc(null),
    undef: api.esc(undefined),
    num: api.esc(42),
  };

  // ─── XSS-инъекция через данные карточки ───
  // Кладём вредоносные значения в «карточку» и смотрим, что попало в innerHTML.
  const evil = [{
    id: '<script>window.__pwned=1</script>',
    name: '<img src=x onerror="window.__pwned=2">',
    category: '"><script>window.__pwned=3</script>',
    grade: 'A', code: 1, verdict: '<svg onload=alert(1)>',
    effects: ['<b>жир</b>'], scienceIndex: 1, rct: 0, metaCount: 0, citations: null,
    updated: '<script>window.__pwned=4</script>',
  }];
  api.renderCards(evil);
  const html = String(doc.getElementById('cardsGrid').innerHTML);
  out.results.xss = {
    html: html,
    /* Проверяем НЕ подстроку «onerror» — она законно остаётся как текст, ведь
       угловые скобки экранированы и тега не существует. Правильный критерий:
       в выводе не должно быть СЫРЫХ открывающих тегов из payload'а и не
       должно быть attribute-инъекции в кавычках. */
    hasRawScript: /<script/i.test(html),
    hasRawImg: /<img/i.test(html),
    hasRawSvg: /<svg/i.test(html),
    hasQuoteBreakout: /onerror\s*=\s*["']/i.test(html) || /onload\s*=\s*["']/i.test(html),
    hasBareOnerrorEq: /onerror=[^"'\s>]/i.test(html),
    hasEscapedScript: /&lt;script/i.test(html),
    hasEscapedImg: /&lt;img/i.test(html),
    hasEscapedSvg: /&lt;svg/i.test(html),
    rawLtCount: (html.match(/</g) || []).length,
    pwned: sandbox.window.__pwned === undefined ? null : sandbox.window.__pwned,
  };

  // ─── renderCards([]): пустое состояние ───
  api.renderCards([]);
  const emptyHtml = String(doc.getElementById('cardsGrid').innerHTML);
  out.results.empty = {
    html: emptyHtml,
    hasEmptyClass: /class="empty"/.test(emptyHtml),
    saysNothingFound: /Ничего не найдено/i.test(emptyHtml),
    hasResetButton: /id="resetAll"/.test(emptyHtml),
    noCards: !/class="card"/.test(emptyHtml),
  };

  // ─── renderCards([одна]): граничный случай ───
  const one = [{
    id: 'Один', name: 'Один', category: 'ЖКТ', grade: 'A', code: 1,
    verdict: 'работает', effects: ['Сон'], scienceIndex: 7, rct: 3, metaCount: 1,
    citations: null, effects_missing: undefined,
  }];
  api.renderCards(one);
  const oneHtml = String(doc.getElementById('cardsGrid').innerHTML);
  out.results.single = {
    len: oneHtml.length,
    cards: (oneHtml.match(/class="card"/g) || []).length,
    hasName: oneHtml.includes('Один'),
    hasUndefined: /undefined/.test(oneHtml),
    hasNaN: /NaN/.test(oneHtml),
    hasNullText: />\s*null\s*</.test(oneHtml),
  };

  // ─── renderCards с карточкой БЕЗ effects/updated (минимальный контракт) ───
  api.renderCards([{ id: 'Мини', name: 'Мини', category: '', grade: '', code: 0, verdict: '' }]);
  const minHtml = String(doc.getElementById('cardsGrid').innerHTML);
  out.results.minimal = {
    cards: (minHtml.match(/class="card"/g) || []).length,
    hasUndefined: /undefined/.test(minHtml),
    hasNaN: /NaN/.test(minHtml),
  };

  out.ok = true;
} catch (e) {
  out.errors.push(String(e && e.message ? e.message : e));
  out.stack = String(e && e.stack ? e.stack : '').split('\n').slice(0, 5);
}

process.stdout.write(JSON.stringify(out));
// setTimeout отключён, но цикл событий мог остаться — выходим явно
process.exit(out.ok ? 0 : 1);
