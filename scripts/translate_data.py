#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""FIX-77: английский оверлей данных карточек.

Проблема. Интерфейс sup-страниц переведён через docs/i18n.js, а данные
(эффекты, механизмы, дозировки, мифы, осторожность) приходят из
docs/data.json и остаются русскими. Плюс смешанные строки: шаблон
подставляет русскую форму выпуска в английское предложение
(«Look for the "триглицерид" form»).

Решение. Скрипт читает docs/data.json и пишет docs/data_en.json —
оверлей {"supplements": {"<русский id>": {переведённые поля}}}. Поля,
которых нет в оверлее, остаются русскими (фолбэк), поэтому частичный
перевод не ломает страницу. JS (docs/i18n.js, docs/script.js,
docs/hactar.js) мерджит оверлей по id, когда lang === 'en'.

Перевод — Google Translate через публичный endpoint translate_a/single
(без ключа и без установки deep-translator/googletrans). Строки уходят
пакетами с маркерами ⟦N⟧: один запрос на несколько абзацев, ответ
разрезается по тем же маркерам. Результат кешируется в
logs/translate_cache_ru_en.json (каталог в .gitignore): повторный запуск
не тратит сеть и продолжает с места обрыва.

Что НЕ переводится: pubmed_term, key_sources (title/journal/doi уже
английские), ma_top3 (английские), interactions.severity
(low/medium/high/critical уже английские), числа и id.

Запуск:
    python scripts/translate_data.py            # полный прогон
    python scripts/translate_data.py --check    # проверить готовый оверлей
    python scripts/translate_data.py --limit 5  # первые 5 карточек (отладка)

Скрипт не трогает docs/data.json — только читает.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "docs" / "data.json"
OUT_FILE = ROOT / "docs" / "data_en.json"
EN_OVERLAY_DIR = ROOT / "docs" / "data_en"   # пофайловые оверлеи: data_en/<id>.json
CACHE_FILE = ROOT / "logs" / "translate_cache_ru_en.json"
LEFTOVER_FILE = ROOT / "logs" / "translate_cyrillic_left.tsv"

API_URL = "https://translate.googleapis.com/translate_a/single"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
# Ограничение на длину q в одном запросе. 1800 символов — с запасом:
# endpoint принимает и больше, но короткие пачки реже обрываются.
BATCH_CHARS = 1800
REQUEST_PAUSE = 0.25          # пауза между запросами, сек
RETRIES = 3
CACHE_SAVE_EVERY = 15         # сохранять кеш каждые N запросов

MARK_RE = re.compile(r"⟦\s*(\d+)\s*⟧")
CYRILLIC_RE = re.compile(r"[А-Яа-яЁё]")

# ── курируемые словари ──────────────────────────────────────────────────
# Названия добавок: машинный перевод здесь даёт мусор («Пустырник» ->
# «Motherwort» он ещё осилит, а «Гуперзин А» -> «Huperzin A»). Словарь
# фиксирует написание, совпадающее с pubmed_term и заголовками источников.

NAME_EN = {
    "Креатин": "Creatine",
    "Омега-3": "Omega-3",
    "Витамин D": "Vitamin D",
    "B12": "Vitamin B12",
    "Магний": "Magnesium",
    "Кофеин": "Caffeine",
    "L-Теанин": "L-Theanine",
    "Бакопа": "Bacopa",
    "Ежовик": "Lion's Mane",
    "Гинкго": "Ginkgo",
    "Родиола": "Rhodiola",
    "Ашваганда": "Ashwagandha",
    "Фосфатидилсерин": "Phosphatidylserine",
    "Alpha-GPC": "Alpha-GPC",
    "CDP-холин": "CDP-Choline",
    "Гуперзин А": "Huperzine A",
    "Куркумин": "Curcumin",
    "Ресвератрол": "Resveratrol",
    "NAC": "NAC",
    "Цинк": "Zinc",
    "Тирозин": "Tyrosine",
    "Таурин": "Taurine",
    "CoQ10": "CoQ10",
    "Пикногенол": "Pycnogenol",
    "Готу кола": "Gotu Kola",
    "Мелатонин": "Melatonin",
    "ГАБА": "GABA",
    "Глицин": "Glycine",
    "Валериана": "Valerian",
    "Бета-аланин": "Beta-Alanine",
    "L-цитруллин": "L-Citrulline",
    "Витамин C": "Vitamin C",
    "Эхинацея": "Echinacea",
    "Бузина": "Elderberry",
    "Зверобой": "St. John's Wort",
    "5-HTP": "5-HTP",
    "Коллаген": "Collagen",
    "Пробиотики": "Probiotics",
    "B9": "Vitamin B9",
    "Железо": "Iron",
    "Триптофан": "Tryptophan",
    "Глюкозамин + хондроитин": "Glucosamine + Chondroitin",
    "Витамин E": "Vitamin E",
    "Биотин": "Biotin",
    "L-карнитин": "L-Carnitine",
    "BCAA": "BCAA",
    "Аргинин": "Arginine",
    "Кальций": "Calcium",
    "Гиалуроновая кислота": "Hyaluronic Acid",
    "Псиллиум": "Psyllium",
    "Имбирь": "Ginger",
    "Чеснок": "Garlic",
    "Клюква": "Cranberry",
    "Пустырник": "Motherwort",
    "Боярышник": "Hawthorn",
    "Бета-глюканы овса": "Oat Beta-Glucans",
    "Рибофлавин": "Riboflavin",
    "Лютеин + зеаксантин": "Lutein + Zeaxanthin",
    "Инозитол": "Inositol",
    "Альфа-липоевая кислота": "Alpha-Lipoic Acid",
    "D-манноза": "D-Mannose",
    "Мака": "Maca",
    "Хром": "Chromium",
    "Астаксантин": "Astaxanthin",
    "Расторопша": "Milk Thistle",
    "Лактоферрин": "Lactoferrin",
    "SAMe": "SAMe",
    "Йохимбин": "Yohimbine",
    "Пажитник": "Fenugreek",
    "Чёрный тмин": "Black Seed",
    "Трибулус": "Tribulus",
    "NMN": "NMN",
    "Кордицепс": "Cordyceps",
    "Рейши": "Reishi",
    "Хлорофилл": "Chlorophyll",
    "Сывороточный протеин": "Whey Protein",
    "Глутамин": "Glutamine",
    "Босвеллия": "Boswellia",
    "Витамин K2": "Vitamin K2",
    "Берберин": "Berberine",
    "Кверцетин": "Quercetin",
    "Шатавари": "Shatavari",
    "Астрагал": "Astragalus",
    "Шлемник": "Skullcap",
    "Пассифлора": "Passionflower",
    "Мелисса": "Lemon Balm",
    "Лаванда": "Lavender",
    "Чага": "Chaga",
    "Шиитаке": "Shiitake",
    "Глутатион": "Glutathione",
    "PQQ": "PQQ",
    "Сульфорафан": "Sulforaphane",
    "MSM": "MSM",
    "Гимнема": "Gymnema",
    "B1": "Vitamin B1",
    "Холин": "Choline",
    "EPA": "EPA",
    "Витамин A": "Vitamin A",
    "B2": "Vitamin B2",
    "B3": "Vitamin B3",
    "B5": "Vitamin B5",
    "B6": "Vitamin B6",
    "Лизин": "Lysine",
    "Кремний": "Silicon",
    "HMB": "HMB",
    "Карнозин": "Carnosine",
    "Женьшень": "Ginseng",
    "Селен": "Selenium",
    "Йод": "Iodine",
    "Молибден": "Molybdenum",
    "Витамин K1": "Vitamin K1",
    "Ниацинамид": "Niacinamide",
    "Цистеин": "Cysteine",
    "S. boulardii": "S. boulardii",
    "LGG": "LGG",
    "B. lactis": "B. lactis",
    "DHA": "DHA",
    "GLA": "GLA",
    "Медь": "Copper",
    "Марганец": "Manganese",
    "Калий": "Potassium",
    "Бор": "Boron",
    "Бетаин": "Betaine",
    "Метионин": "Methionine",
    "Орнитин": "Ornithine",
    "Майтаке": "Maitake",
    "PABA": "PABA",
    "Пролин": "Proline",
    "Серин": "Serine",
    "Аланин": "Alanine",
}

VERDICT_EN = {
    "работает": "works",
    "зависит от контекста": "depends on context",
    "не подтверждено": "not confirmed",
}

# mechs[2]: сила доказательств механизма.
STRENGTH_EN = {
    "сильно": "strong",
    "умеренно": "moderate",
    "слабо": "weak",
    "контекст": "context",
    "маркетинг": "marketing",
}

CATEGORY_EN = {
    "Общее": "General",
    "Когниция": "Cognition",
    "Метаболизм": "Metabolism",
    "Кожа": "Skin",
    "Кожа и суставы": "Skin & Joints",
    "Сердце": "Heart",
    "Неврология": "Neurology",
    "Иммунитет": "Immunity",
    "Кости": "Bones",
    "Спорт": "Sports",
    "Психика": "Mental Health",
    "Депрессия": "Depression",
    "ОРВИ": "Viral Infections",
    "Сексуальное здоровье": "Sexual Health",
    "Кишечник": "Gut",
    "Воспаление": "Inflammation",
    "Суставы": "Joints",
    "Сон": "Sleep",
    "ЖКТ": "GI Tract",
    "Мочеполовая система": "Urogenital System",
    "Диабет": "Diabetes",
    "Настроение": "Mood",
    "Нервная система": "Nervous System",
    "Кровь": "Blood",
    "Минерал": "Mineral",
    "Производительность": "Performance",
    "Усталость": "Fatigue",
    "Адаптоген": "Adaptogen",
    "Стресс": "Stress",
    "Дети": "Children",
    "Инсульт": "Stroke",
    "Деменция": "Dementia",
    "Циркадные ритмы": "Circadian Rhythms",
    "Нейромедиатор": "Neurotransmitter",
    "Тревожность": "Anxiety",
    "Сосуды": "Blood Vessels",
    "Антиоксидант": "Antioxidant",
    "Беременность": "Pregnancy",
    "Анемия": "Anemia",
    "Остеоартрит": "Osteoarthritis",
    "Волосы": "Hair",
    "Печень": "Liver",
    "Глаза": "Eyes",
    "Зрение": "Vision",
    "Женское здоровье": "Women's Health",
    "СПКЯ": "PCOS",
    "Старение": "Aging",
    "Почки": "Kidneys",
    "Выносливость": "Endurance",
    "Грибы": "Mushrooms",
    "Мышцы": "Muscles",
    "Критические состояния": "Critical Care",
    "Гормоны": "Hormones",
}

# Рваные формы выпуска: в data.json есть обрывки редакторского текста
# («экстракт (SHR-5», «3% розавинов)»). Машинный перевод на них useless,
# поэтому фиксируем вручную — как они должны выглядеть на этикетке.
FORM_OVERRIDES = {
    "экстракт (SHR-5": "extract (SHR-5",
    "3% розавинов)": "3% rosavins)",
    "ФФФ": "FFF",
    "МК-7": "MK-7",
    "моногидрат": "monohydrate",
    "триглицерид": "triglyceride",
    "этиловый эфир": "ethyl ester",
    "бисглицинат": "bisglycinate",
    "цитрат": "citrate",
    "малат": "malate",
    "глицинат": "glycinate",
    "таурат": "taurate",
    "сукцинат": "succinate",
    "оротат": "orotate",
    "пиколинат": "picolinate",
    "глюконат": "gluconate",
    "лактат": "lactate",
    "аспартат": "aspartate",
    "карбонат": "carbonate",
    "оксид": "oxide",
    "сульфат": "sulfate",
    "фумарат": "fumarate",
    "хлорид": "chloride",
    "йодид": "iodide",
    "селенат": "selenate",
}

# ── пред/пост-обработка текста ──────────────────────────────────────────
# Аббревиатуры: MT переводит их как слова («РКИ» -> «RCT» он обычно знает,
# а «ЖКТ» -> «gastrointestinal tract» рвёт фразу). Подставляем до отправки.
ABBREV = [
    ("ССЗ-события", "CVD events"),
    ("ССЗ", "CVD"),
    ("ЖКТ", "GI"),
    ("РКИ", "RCT"),
    ("НПВС", "NSAIDs"),
    ("ГЭРБ", "GERD"),
    ("СПКЯ", "PCOS"),
    ("СД2", "T2D"),
    ("ЛПНП", "LDL"),
    ("ЛПВП", "HDL"),
    ("ЧСС", "HR"),
    ("ЦНС", "CNS"),
    ("ГАМК", "GABA"),
    ("АТФ", "ATP"),
    ("ИМТ", "BMI"),
    ("ОРВИ", "ARI"),
    ("ФП", "AF"),
    ("ТГ", "TG"),
]

UNIT_POST = [
    (re.compile(r"(?<=\d)\s*мкг\b"), " mcg"),
    (re.compile(r"(?<=\d)\s*мг\b"), " mg"),
    (re.compile(r"(?<=\d)\s*г\b"), " g"),
    (re.compile(r"(?<=\d)\s*мл\b"), " ml"),
    (re.compile(r"(?<=\d)\s*ккал\b"), " kcal"),
    (re.compile(r"(?<=\d)\s*ммоль\b"), " mmol"),
    (re.compile(r"(?<=\d)\s*моль\b"), " mol"),
    (re.compile(r"(?<=\d)\s*МЕ\b"), " IU"),
    (re.compile(r"\bмкг\b"), "mcg"),
    (re.compile(r"\bмг\b"), "mg"),
    (re.compile(r"\bмл\b"), "ml"),
]

# Имена добавок внутри synergists/antagonists — свободный текст, а не
# справочник NAME_EN. Что не покрыто словарём, переводим как обычный текст.
SYNERGIST_EN = {
    "Витамин B6": "Vitamin B6",
    "Пиперин (чёрный перец)": "Piperine (black pepper)",
}

# Кириллические гомоглифы: в data.json встречается «Н^ 1.11» (гетерогенность
# I²), MT сохраняет кириллическую «Н» рядом с латиницей — это уже не перевод,
# а битая строка. Меняем на латинскую H.
HOMOGLYPHS = [("Н^", "H^"), ("Н²", "H²"), ("Н2", "H2")]

SPACE_FIX = [
    (re.compile(r"\s+([,.;:!?%])"), r"\1"),
    (re.compile(r"\(\s+"), "("),
    (re.compile(r"\s+\)"), ")"),
    (re.compile(r"[ \t]{2,}"), " "),
]


def _prep(text: str) -> str:
    s = str(text).replace("&nbsp;", " ")
    for ru, en in ABBREV:
        s = re.sub(r"(?<![А-Яа-яЁёA-Za-z])" + re.escape(ru) + r"(?![А-Яа-яЁёA-Za-z])", en, s)
    return s


def _fix_homoglyphs(text: str) -> str:
    s = text
    for ru, en in HOMOGLYPHS:
        s = s.replace(ru, en)
    return s


def _post(text: str) -> str:
    s = _fix_homoglyphs(text)
    for rx, rep in UNIT_POST:
        s = rx.sub(rep, s)
    for rx, rep in SPACE_FIX:
        s = rx.sub(rep, s)
    # « 3» перед единицей не должно превращаться в «3 g» с двойным пробелом
    s = re.sub(r"(\d)\s+(g|mg|mcg|ml|IU|kcal|mmol|mol)\b", r"\1 \2", s)
    return s.strip()


# ── сеть ────────────────────────────────────────────────────────────────
def _api(query: str) -> str:
    body = urllib.parse.urlencode(
        {"client": "gtx", "sl": "ru", "tl": "en", "dt": "t", "q": query}
    ).encode("utf-8")
    req = urllib.request.Request(
        API_URL, data=body, headers={"User-Agent": USER_AGENT,
                                     "Content-Type": "application/x-www-form-urlencoded"}
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    chunks = payload[0] if payload and payload[0] else []
    return "".join(seg[0] for seg in chunks if seg and seg[0])


def _api_retry(query: str) -> str:
    last = None
    for attempt in range(RETRIES):
        try:
            return _api(query)
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError) as exc:
            last = exc
            time.sleep(1.0 + attempt * 1.5)
    raise RuntimeError("translate failed: %s" % last)


class Translator:
    def __init__(self):
        self.cache = {}
        if CACHE_FILE.exists():
            try:
                self.cache = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                self.cache = {}
        self.dirty = 0
        self.leftovers = []
        self.requests = 0

    def save(self):
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        tmp = CACHE_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.cache, ensure_ascii=False, indent=0), encoding="utf-8")
        tmp.replace(CACHE_FILE)
        self.dirty = 0

    def _translate_batch(self, items):
        """items: list[(key, text)] -> dict key -> перевод."""
        keys = [k for k, _ in items]
        joined = "\n".join("⟦%d⟧\n%s" % (i, _prep(t)) for i, (_, t) in enumerate(items))
        out = _api_retry(joined)
        self.requests += 1
        parts = MARK_RE.split(out)
        # split даёт [до первого маркера, номер, текст, номер, текст, ...]
        found = {}
        for i in range(1, len(parts) - 1, 2):
            n = int(parts[i])
            body = parts[i + 1]
            found[n] = body
        if sorted(found) != list(range(len(items))):
            # маркеры не выжили — переводим поштучно, это медленнее, но надёжно
            result = {}
            for key, text in items:
                result[key] = _api_retry(_prep(text))
                self.requests += 1
                time.sleep(REQUEST_PAUSE)
            return result
        return {keys[n]: found[n] for n in found}

    def translate_many(self, texts):
        """Возвращает {исходная строка: перевод}. Дубли переводятся один раз."""
        uniq = []
        seen = set()
        for t in texts:
            t = str(t or "").strip()
            if not t or t in seen:
                continue
            seen.add(t)
            if t in self.cache:
                continue
            uniq.append(t)
        # пачки по бюджету символов
        batch, size = [], 0
        for t in uniq:
            ln = len(t) + 1
            if batch and size + ln > BATCH_CHARS:
                self._flush(batch)
                batch, size = [], 0
            batch.append(t)
            size += ln
        if batch:
            self._flush(batch)
        return {str(t).strip(): _fix_homoglyphs(self.cache.get(str(t).strip(), str(t).strip()))
                for t in texts if str(t or "").strip()}

    def _flush(self, batch):
        items = [(t, t) for t in batch]
        got = self._translate_batch(items)
        for src, dst in got.items():
            tr = _post(dst)
            if CYRILLIC_RE.search(tr):
                # второй шанс: иногда кусок остаётся непереведённым
                try:
                    tr2 = _post(_api_retry(_prep(src)))
                    self.requests += 1
                    if not CYRILLIC_RE.search(tr2):
                        tr = tr2
                    else:
                        self.leftovers.append((src, tr2))
                except RuntimeError:
                    self.leftovers.append((src, tr))
            self.cache[src] = tr
            self.dirty += 1
        if self.dirty >= CACHE_SAVE_EVERY:
            self.save()
        time.sleep(REQUEST_PAUSE)


# ── сборка оверлея ──────────────────────────────────────────────────────
TEXT_FIELDS = [
    "about", "who_needs", "onset", "dosage", "course", "upper_limit",
    "caution", "myths", "how_to_choose", "food_sources", "guidelines",
]
LIST_FIELDS = ["effects", "forms"]


def load_cards():
    raw = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    if isinstance(raw, dict):
        raw = raw.get("supplements") or []
    if not isinstance(raw, list):
        raise SystemExit("docs/data.json: ожидался список карточек")
    return raw


def category_en(cat: str) -> str:
    parts = [p.strip() for p in str(cat).split("/") if p.strip()]
    out = [CATEGORY_EN.get(p) for p in parts]
    missing = [p for p, e in zip(parts, out) if not e]
    if missing:
        raise SystemExit("CATEGORY_EN: нет перевода для %r" % (missing,))
    return " / ".join(out)


def collect_texts(cards):
    texts = []
    for c in cards:
        for f in TEXT_FIELDS:
            if c.get(f):
                texts.append(c[f])
        for f in LIST_FIELDS:
            for v in c.get(f) or []:
                texts.append(v)
        for body, effect, _strength in c.get("mechs") or []:
            texts.append(body)
            texts.append(effect)
        for it in c.get("interactions") or []:
            if it.get("with"):
                texts.append(it["with"])
            if it.get("note"):
                texts.append(it["note"])
    return texts


def build_overlay(cards, tr: Translator):
    cards = [c for c in cards if c.get("id")]
    texts = collect_texts(cards)
    table = tr.translate_many(texts)

    def t(value):
        s = str(value or "").strip()
        return table.get(s, s)

    out = {}
    for c in cards:
        cid = str(c["id"])
        name_ru = str(c.get("name") or cid)
        name_en = NAME_EN.get(name_ru)
        if not name_en:
            raise SystemExit("NAME_EN: нет перевода для имени %r" % (name_ru,))
        item = {"name": name_en, "title": name_en}
        if c.get("category"):
            item["category"] = category_en(c["category"])
        if c.get("verdict"):
            v = VERDICT_EN.get(str(c["verdict"]).strip())
            if not v:
                raise SystemExit("VERDICT_EN: нет перевода для %r" % (c["verdict"],))
            item["verdict"] = v
        for f in TEXT_FIELDS:
            if c.get(f):
                item[f] = t(c[f])
        for f in LIST_FIELDS:
            vals = c.get(f) or []
            if vals:
                item[f] = [FORM_OVERRIDES.get(str(v).strip()) or t(v) for v in vals]
        mechs = []
        for body, effect, strength in c.get("mechs") or []:
            lvl = STRENGTH_EN.get(str(strength).strip())
            if not lvl:
                raise SystemExit("STRENGTH_EN: нет перевода для %r" % (strength,))
            mechs.append([t(body), t(effect), lvl])
        if mechs:
            item["mechs"] = mechs
        inters = []
        for it in c.get("interactions") or []:
            inters.append({
                "with": t(it.get("with")),
                "severity": it.get("severity"),
                "note": t(it.get("note")),
            })
        if inters:
            item["interactions"] = inters
        for f in ("synergists", "antagonists"):
            vals = c.get(f) or []
            if vals:
                item[f] = [SYNERGIST_EN.get(str(v)) or NAME_EN.get(str(v)) or t(v) for v in vals]
        out[cid] = item
    return out


def emit_per_card(overlay):
    """Пишет docs/data_en/<id>.json для каждой карточки — оверлей из одной
    записи. Карточная страница (sup/*.html с data-sup-id) грузит только свой
    файл (~2–3 КБ) вместо полного data_en.json (326 КБ) — FIX-55 (CWV-06).
    Каталог и Hactar по-прежнему грузят полный data_en.json. """
    EN_OVERLAY_DIR.mkdir(parents=True, exist_ok=True)
    for cid, item in overlay.items():
        payload = {
            "_meta": {
                "generated": "2026-10-29",
                "source": "docs/data.json",
                "translator": "google-translate-free",
                "card": cid,
            },
            "supplements": {cid: item},
        }
        (EN_OVERLAY_DIR / (cid + ".json")).write_text(
            json.dumps(payload, ensure_ascii=False, indent=1, sort_keys=True),
            encoding="utf-8",
        )


def check_overlay():
    cards = load_cards()
    if not OUT_FILE.exists():
        print("FAIL: docs/data_en.json отсутствует")
        return 1
    payload = json.loads(OUT_FILE.read_text(encoding="utf-8"))
    ov = payload.get("supplements") or {}
    problems = []
    if len(ov) != len(cards):
        problems.append("карточек в оверлее %d, в data.json %d" % (len(ov), len(cards)))
    for c in cards:
        cid = str(c.get("id") or "")
        item = ov.get(cid)
        if not item:
            problems.append("нет карточки %s" % cid)
            continue
        if CYRILLIC_RE.search(json.dumps(item, ensure_ascii=False).replace(cid, "")):
            problems.append("кириллица в %s" % cid)
        for f in ("name", "title", "verdict", "category"):
            if c.get(f) and not item.get(f):
                problems.append("%s: пустое поле %s" % (cid, f))
        for f in LIST_FIELDS + ["synergists", "antagonists"]:
            if len(c.get(f) or []) != len(item.get(f) or []):
                problems.append("%s: длина %s не совпадает" % (cid, f))
        for f in TEXT_FIELDS:
            if bool(c.get(f)) != bool(item.get(f)):
                problems.append("%s: %s есть/нет расходится" % (cid, f))
        if len(c.get("mechs") or []) != len(item.get("mechs") or []):
            problems.append("%s: число механизмов не совпадает" % cid)
        if len(c.get("interactions") or []) != len(item.get("interactions") or []):
            problems.append("%s: число взаимодействий не совпадает" % cid)
    if problems:
        print("FAIL: %d problem(s)" % len(problems))
        for p in problems[:40]:
            print("  -", p)
        return 1
    size = OUT_FILE.stat().st_size
    print("OK: %d cards, %d bytes, no cyrillic" % (len(ov), size))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="translate docs/data.json to English")
    ap.add_argument("--check", action="store_true", help="check docs/data_en.json only")
    ap.add_argument("--limit", type=int, default=0, help="translate first N cards")
    args = ap.parse_args(argv)

    if args.check:
        return check_overlay()

    cards = load_cards()
    if args.limit:
        cards = cards[: args.limit]

    if len(NAME_EN) < 130:
        print("WARN: NAME_EN has %d names (<130)" % len(NAME_EN))

    tr = Translator()
    started = time.time()
    print("cards=%d cache=%d" % (len(cards), len(tr.cache)))
    try:
        overlay = build_overlay(cards, tr)
    finally:
        tr.save()

    if not args.limit:
        payload = {
            "_meta": {
                "generated": "2026-10-26",
                "source": "docs/data.json",
                "translator": "google-translate-free",
                "note": "overlay keyed by russian card id; missing field = russian fallback",
                "cards": len(overlay),
            },
            "supplements": overlay,
        }
        OUT_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=1, sort_keys=True),
                            encoding="utf-8")
        emit_per_card(overlay)

    if tr.leftovers:
        LEFTOVER_FILE.parent.mkdir(parents=True, exist_ok=True)
        with LEFTOVER_FILE.open("w", encoding="utf-8") as fh:
            for src, dst in tr.leftovers:
                fh.write("%s\t%s\n" % (src.replace("\n", " "), dst.replace("\n", " ")))

    print("done: cards=%d requests=%d leftovers=%d sec=%d"
          % (len(overlay), tr.requests, len(tr.leftovers), int(time.time() - started)))
    if tr.leftovers:
        print("leftovers written to logs/translate_cyrillic_left.tsv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
