/* Тестовый стенд для парсинга upper_limit из docs/hactar.js (QA-06, FIX-39).
 *
 * hactar.js — большая IIFE: parseUpperLimit/parseDosage/toMg/sameUnit лежат
 * внутри замыкания и наружу не отдаются. Чтобы тестировать именно
 * production-код, а не его копию, стенд вырезает из файла блок «разбор
 * дозировок» (от `var UNIT_SRC` до раздела «данные») и исполняет его в vm
 * с пустым контекстом: этот блок не обращается ни к DOM, ни к T(), ни к
 * fetch — только регулярные выражения и арифметика.
 *
 * Вырезание по маркерам, а не по номерам строк: номера в файле плавают.
 * Если маркеры не найдены или в блоке нет нужных функций — ok:false и
 * pytest падает с внятным сообщением, а не молча пропускает.
 *
 * Печатает JSON в stdout; разбирает tests/test_upper_limit_en.py.
 */
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const ROOT = path.resolve(__dirname, '..');
const HACTAR = process.env.HACTAR_JS || path.join(ROOT, 'docs', 'hactar.js');
const DATA_RU = path.join(ROOT, 'docs', 'data.json');
const DATA_EN = path.join(ROOT, 'docs', 'data_en.json');

const out = { ok: false, error: null, cases: {}, probes: [], units: {}, toMg: {}, sameUnit: {} };

function fail(msg) {
  out.error = msg;
  process.stdout.write(JSON.stringify(out));
  process.exit(0);
}

const src = fs.readFileSync(HACTAR, 'utf8');

const START = 'var UNIT_SRC = ';
const END = '/* ── данные';
const i = src.indexOf(START);
const j = src.indexOf(END);
if (i < 0) fail('в hactar.js не найден маркер "var UNIT_SRC = "');
if (j < 0 || j <= i) fail('в hactar.js не найден маркер конца блока разбора дозировок');

const block = src.slice(i, j);

for (const fn of ['function parseNum', 'function parseDosage', 'function parseUpperLimit',
                  'function toMg', 'function sameUnit']) {
  if (block.indexOf(fn) < 0) fail('в вырезанном блоке нет ' + fn);
}

const sandbox = {};
vm.createContext(sandbox);
try {
  vm.runInContext(
    block +
    '\nthis.__api = {parseNum: parseNum, parseDosage: parseDosage,' +
    ' parseUpperLimit: parseUpperLimit, toMg: toMg, sameUnit: sameUnit,' +
    ' UNIT_SRC: UNIT_SRC, NO_UL: NO_UL};',
    sandbox,
    { filename: 'hactar-upper-limit.js' });
} catch (e) {
  fail('блок не исполнился: ' + e.message);
}

const api = sandbox.__api;

/* ── данные: те же строки, что видит страница ─────────────────────────── */

const ruList = JSON.parse(fs.readFileSync(DATA_RU, 'utf8'));
const enRaw = JSON.parse(fs.readFileSync(DATA_EN, 'utf8'));
const enMap = enRaw.supplements || enRaw;

for (const rec of ruList) {
  const id = rec.id;
  const en = enMap[id] || {};
  out.cases[id] = {
    ru_text: String(rec.upper_limit || ''),
    en_text: String(en.upper_limit || ''),
    ru: api.parseUpperLimit(rec.upper_limit || ''),
    en: api.parseUpperLimit(en.upper_limit || ''),
  };
}

/* ── пробы единиц: по одной на каждую единицу из задания и из UNIT_SRC ── */

const UNITS = ['мг', 'mg', 'г', 'g', 'мкг', 'mcg', 'µg', 'ug', 'МЕ', 'IU',
               'мкмоль', 'ммоль', 'CFU', 'КОЕ'];
for (const u of UNITS) {
  out.units[u] = api.parseUpperLimit('100 ' + u + '/day');
}

/* ── границы и конверсия ──────────────────────────────────────────────── */

out.probes = [
  { text: '350 mg/day added (US IOM); more - diarrhea.', name: 'en_350_mg' },
  { text: '4000 IU/day (EFSA); long-term 10,000+ - risk of hypercalcemia.', name: 'en_4000_iu' },
  { text: '0.5 g/day', name: 'en_0_5_g' },
  { text: '2000 мг/сут; выше — диарея', name: 'ru_2000_mg' },
  { text: '0,5 г/сут', name: 'ru_comma_g' },
  { text: 'There is no formal UL; 3-5 g/day is safe.', name: 'en_no_ul' },
  { text: 'Формального UL нет; 3-5 г/сут безопасно', name: 'ru_no_ul' },
  { text: 'The daily limit is not specified.', name: 'en_not_specified' },
  { text: '', name: 'empty' },
  { text: '300-450 mg extract/day; higher - GI discomfort.', name: 'en_range' },
  { text: 'EFSA: single 200 mg, up to 400 mg/day; pregnancy - 200 mg/day.', name: 'en_single_vs_daily' },
].map(function (p) {
  const r = api.parseUpperLimit(p.text);
  return { name: p.name, text: p.text, result: r };
});

out.toMg = {
  '0.5_g': api.toMg(0.5, 'g'),
  '500_mg': api.toMg(500, 'mg'),
  '1000_mcg': api.toMg(1000, 'mcg'),
  '350_IU': api.toMg(350, 'IU'),
  '0.5_г': api.toMg(0.5, 'г'),
};

out.sameUnit = {
  'mg_vs_мг': api.sameUnit('mg', 'мг'),
  'IU_vs_МЕ': api.sameUnit('IU', 'МЕ'),
  'g_vs_мг': api.sameUnit('g', 'мг'),
  'mcg_vs_мкг': api.sameUnit('mcg', 'мкг'),
};

out.unit_src = String(api.UNIT_SRC);
out.no_ul_src = String(api.NO_UL);
out.ok = true;
process.stdout.write(JSON.stringify(out));
