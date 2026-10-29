/* Тестовый стенд для проверки PREG_RE из docs/hactar.js (LEGAL-03, FIX-48).
 *
 * hactar.js — большая IIFE: PREG_RE лежит внутри замыкания и наружу не
 * отдаётся. Чтобы тестировать именно production-регулярку, а не её копию,
 * стенд вырезает определение `var PREG_RE = /.../i;` и исполняет его в vm
 * с пустым контекстом.
 *
 * Вырезание по маркерам, а не по номерам строк: номера в файле плавают.
 * Если маркер не найден — ok:false и pytest падает с внятным сообщением.
 *
 * Печатает JSON в stdout; разбирает tests/test_pregnancy_warning.py.
 */

const fs = require('fs');
const path = require('path');
const vm = require('vm');

const ROOT = path.resolve(__dirname, '..');
const HACTAR = process.env.HACTAR_JS || path.join(ROOT, 'docs', 'hactar.js');
const DATA_RU = path.join(ROOT, 'docs', 'data.json');
const DATA_EN = path.join(ROOT, 'docs', 'data_en.json');

const out = { ok: false, error: null, cases: {}, summary: {} };

function fail(msg) {
  out.error = msg;
  process.stdout.write(JSON.stringify(out));
  process.exit(0);
}

const src = fs.readFileSync(HACTAR, 'utf8');

const START = 'var PREG_RE = ';
const i = src.indexOf(START);
if (i < 0) fail('в hactar.js не найден маркер "var PREG_RE = "');

// Находим конец определения: после /.../i и ;
const afterStart = src.slice(i + START.length);
const slashSlash = afterStart.indexOf('/i;');
if (slashSlash < 0) fail('в hactar.js не найден конец определения PREG_RE (/i;)');

const block = src.slice(i, i + START.length + slashSlash + 3); // includes /i;

if (block.indexOf('PREG_RE') < 0) fail('в вырезанном блоке нет PREG_RE');

const sandbox = {};
vm.createContext(sandbox);
try {
  vm.runInContext(block + '\nthis.__api = {PREG_RE: PREG_RE};', sandbox,
    { filename: 'hactar-preg.js' });
} catch (e) {
  fail('блок не исполнился: ' + e.message);
}

const api = sandbox.__api;
const PREG_RE = api.PREG_RE;

if (typeof PREG_RE !== 'object' || typeof PREG_RE.test !== 'function') {
  fail('PREG_RE не является RegExp: ' + typeof PREG_RE);
}

/* ── данные ───────────────────────────────────────────────────────────── */

const ruList = JSON.parse(fs.readFileSync(DATA_RU, 'utf8'));
const enRaw = JSON.parse(fs.readFileSync(DATA_EN, 'utf8'));
const enMap = enRaw.supplements || enRaw;
const enItems = typeof enMap === 'object' && !Array.isArray(enMap)
  ? Object.values(enMap)
  : enMap;

for (const rec of ruList) {
  const id = rec.id;
  const en = (enMap[id] || {});
  const ruCaution = String(rec.caution || '');
  const enCaution = String(en.caution || '');
  out.cases[id] = {
    ru_match: PREG_RE.test(ruCaution),
    en_match: PREG_RE.test(enCaution),
    ru_caution: ruCaution,
    en_caution: enCaution,
  };
}

out.summary.ru_total = ruList.length;
out.summary.en_total = enItems.length;
out.summary.ru_matches = Object.values(out.cases).filter(c => c.ru_match).length;
out.summary.en_matches = Object.values(out.cases).filter(c => c.en_match).length;
out.summary.diff = Math.abs(out.summary.ru_matches - out.summary.en_matches);
out.ok = true;
process.stdout.write(JSON.stringify(out));
