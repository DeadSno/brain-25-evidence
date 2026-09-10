"""Конфигурация проекта: список добавок, запросы PubMed/WB, нормы."""

MAILTO = "brain25-evidence@users.noreply.github.com"  # для PubMed E-utilities

# ============ БАЗОВЫЕ 25 КОГНИТИВНЫХ ДОБАВОК (v1.0) ============
SUPPLEMENTS = {
    "Креатин":            "creatine",
    "Омега-3":            "omega-3 OR omega 3 OR EPA OR DHA OR fish oil",
    "Витамин D":          "vitamin D OR cholecalciferol",
    "B12":                "vitamin B12 OR cobalamin",
    "Магний":             "magnesium",
    "Кофеин":             "caffeine",
    "L-Теанин":           "theanine OR L-theanine",
    "Бакопа":             "Bacopa monnieri",
    "Ежовик":             "Hericium erinaceus OR lion's mane",
    "Гинкго":             "Ginkgo biloba",
    "Родиола":            "Rhodiola rosea",
    "Ашваганда":          "Withania somnifera OR ashwagandha",
    "Фосфатидилсерин":    "phosphatidylserine",
    "Alpha-GPC":          "alpha-GPC OR choline alfoscerate",
    "CDP-холин":          "citicoline OR CDP-choline",
    "Гуперзин А":         "huperzine A",
    "Куркумин":           "curcumin OR turmeric",
    "Ресвератрол":        "resveratrol",
    "NAC":                "N-acetylcysteine",
    "Цинк":               "zinc",
    "Тирозин":            "tyrosine",
    "Таурин":             "taurine",
    "CoQ10":              "coenzyme Q10 OR ubiquinol",
    "Пикногенол":         "pycnogenol OR pine bark extract",
    "Готу кола":          "Centella asiatica OR gotu kola",
}

COG = '(cognition OR cognitive OR memory OR attention OR "executive function" OR "reaction time" OR "working memory")'

EN = {
    "Креатин": "creatine", "Омега-3": "omega-3", "Витамин D": "vitamin D",
    "B12": "vitamin B12", "Магний": "magnesium", "Кофеин": "caffeine",
    "L-Теанин": "L-theanine", "Бакопа": "Bacopa monnieri",
    "Ежовик": "lion's mane", "Гинкго": "Ginkgo biloba",
    "Родиола": "Rhodiola rosea", "Ашваганда": "ashwagandha",
    "Фосфатидилсерин": "phosphatidylserine", "Alpha-GPC": "alpha-GPC",
    "CDP-холин": "citicoline", "Гуперзин А": "huperzine A",
    "Куркумин": "curcumin", "Ресвератрол": "resveratrol",
    "NAC": "N-acetylcysteine", "Цинк": "zinc",
    "Тирозин": "tyrosine", "Таурин": "taurine",
    "CoQ10": "coenzyme Q10", "Пикногенол": "pycnogenol",
    "Готу кола": "gotu kola",
}

# норма_мес: сколько единиц в месяц (для расчёта цены_мес)
NORM = {
    "Креатин": 30, "Омега-3": 30, "Витамин D": 30, "B12": 30,
    "Магний": 30, "Кофеин": 30, "L-Теанин": 30, "Бакопа": 30,
    "Ежовик": 30, "Гинкго": 30, "Родиола": 30, "Ашваганда": 30,
    "Фосфатидилсерин": 30, "Alpha-GPC": 30, "CDP-холин": 30,
    "Гуперзин А": 30, "Куркумин": 30, "Ресвератрол": 30,
    "NAC": 30, "Цинк": 30, "Тирозин": 10, "Таурин": 30,
    "CoQ10": 30, "Пикногенол": 30, "Готу кола": 30,
}

# WB-запросы v1.0: (поисковый запрос, единица "г"/"капс"/"табл")
WB_QUERY = {
    "Креатин":            ("креатин моногидрат",     "г"),
    "Омега-3":            ("омега 3 1000 мг",        "капс"),
    "Витамин D":          ("витамин D 2000 МЕ",      "капс"),
    "B12":                ("витамин B12 1000 мкг",   "табл"),
    "Магний":             ("магний глицинат 400 мг", "капс"),
    "Кофеин":             ("кофеин 200 мг",          "табл"),
    "L-Теанин":           ("теанин 200 мг",          "капс"),
    "Бакопа":             ("бакопа монье",           "капс"),
    "Ежовик":             ("ежовик гребенчатый",     "капс"),
    "Гинкго":             ("гинкго билоба",          "капс"),
    "Родиола":            ("родиола розовая",        "капс"),
    "Ашваганда":          ("ашваганда KSM-66",       "капс"),
    "Фосфатидилсерин":    ("фосфатидилсерин",        "капс"),
    "Alpha-GPC":          ("альфа GPC 300 мг",       "капс"),
    "CDP-холин":          ("цитиколин",              "капс"),
    "Гуперзин А":         ("гуперзин А",             "капс"),
    "Куркумин":           ("куркумин с пиперином",   "капс"),
    "Ресвератрол":        ("ресвератрол 500 мг",     "капс"),
    "NAC":                ("NAC 600 мг",             "капс"),
    "Цинк":               ("цинк хелат 25 мг",       "капс"),
    "Тирозин":            ("тирозин 500 мг",         "капс"),
    "Таурин":             ("таурин 1000 мг",         "капс"),
    "CoQ10":              ("коэнзим Q10 100 мг",     "капс"),
    "Пикногенол":         ("пикногенол",             "капс"),
    "Готу кола":          ("готу кола",              "капс"),
}

# ============ v1.2: РАСШИРЕНИЕ (16 добавок + новые оси) ============
SUPPLEMENTS_V12 = {
    "Мелатонин":     "melatonin[Title/Abstract]",
    "ГАБА":          "GABA OR gamma-aminobutyric acid",
    "Глицин":        "glycine",
    "Валериана":     "valerian OR Valeriana",
    "Бета-аланин":   "beta-alanine",
    "L-цитруллин":   "citrulline",
    "Витамин C":     "ascorbic acid OR vitamin C",
    "Эхинацея":      "echinacea",
    "Бузина":        "elderberry OR Sambucus",
    "Зверобой":      "St John's wort OR Hypericum",
    "5-HTP":         "5-hydroxytryptophan",
    "Коллаген":      "collagen",
    "Пробиотики":    "probiotics",
    "B9":            "folic acid OR folate",
    "Железо":        "iron",
    "Триптофан":     "tryptophan",
}

OUTCOME_V12 = {
    "Мелатонин":     '(sleep OR insomnia OR "sleep latency")',
    "ГАБА":          '(sleep OR anxiety OR stress)',
    "Глицин":        '(sleep OR insomnia)',
    "Валериана":     '(sleep OR insomnia)',
    "Бета-аланин":   '(exercise OR performance OR endurance)',
    "L-цитруллин":   '(exercise OR performance OR "blood flow")',
    "Витамин C":     '(immune OR "common cold" OR infection)',
    "Эхинацея":      '(immune OR "common cold")',
    "Бузина":        '(immune OR "common cold" OR influenza)',
    "Зверобой":      '(depression OR depressive)',
    "5-HTP":         '(depression OR anxiety)',
    "Коллаген":      '(skin OR joint OR osteoarthritis)',
    "Пробиотики":    '(gut OR IBS OR diarrhea OR immune)',
    "B9":            '(cognition OR depression)',
    "Железо":        '(fatigue OR anemia OR cognition)',
    "Триптофан":     '(sleep OR depression)',
}

# WB-запросы v1.2: (поисковый запрос, единица)
WB_QUERY_V12 = {
    "Мелатонин":     ("мелатонин таблетки",   "капс"),
    "ГАБА":          ("GABA 500 мг",          "капс"),
    "Глицин":        ("глицин",               "табл"),
    "Валериана":     ("валериана экстракт",   "капс"),
    "Бета-аланин":   ("бета-аланин",          "г"),
    "L-цитруллин":   ("цитруллин малат",      "г"),
    "Витамин C":     ("витамин C 500 мг",     "табл"),
    "Эхинацея":      ("эхинацея",             "капс"),
    "Бузина":        ("бузина черная",        "капс"),
    "Зверобой":      ("зверобой экстракт",    "капс"),
    "5-HTP":         ("5-HTP 100 мг",         "капс"),
    "Коллаген":      ("коллаген гидролизат",  "г"),
    "Пробиотики":    ("пробиотик",            "капс"),
    "B9":            ("фолиевая кислота",     "табл"),
    "Железо":        ("железо хелат",         "капс"),
    "Триптофан":     ("L-триптофан 500 мг",   "капс"),
}

EN_V12 = {
    "Мелатонин": "melatonin", "ГАБА": "GABA", "Глицин": "glycine",
    "Валериана": "valerian", "Бета-аланин": "beta-alanine",
    "L-цитруллин": "citrulline", "Витамин C": "vitamin C",
    "Эхинацея": "echinacea", "Бузина": "elderberry",
    "Зверобой": "St John's wort", "5-HTP": "5-HTP",
    "Коллаген": "collagen", "Пробиотики": "probiotics",
    "B9": "folic acid", "Железо": "iron", "Триптофан": "tryptophan",
}

NORM_V12 = {
    "Мелатонин": 30, "ГАБА": 30, "Глицин": 60, "Валериана": 30,
    "Бета-аланин": 30, "L-цитруллин": 30, "Витамин C": 30,
    "Эхинацея": 30, "Бузина": 30, "Зверобой": 30, "5-HTP": 30,
    "Коллаген": 30, "Пробиотики": 30, "B9": 30, "Железо": 30,
    "Триптофан": 30,
}

# ============ ОБЪЕДИНЕНИЕ v1.0 + v1.2 ============
SUPPLEMENTS.update(SUPPLEMENTS_V12)
EN.update(EN_V12)
NORM.update(NORM_V12)
WB_QUERY.update(WB_QUERY_V12)