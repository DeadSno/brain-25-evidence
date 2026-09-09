"""brain-25-evidence: единая конфигурация и словари проекта."""

MAILTO = "deadsno1613@gmail.com"   # polite-пул NCBI/OpenAlex

# Общий когнитивный фильтр для PubMed
COG = "cognition OR cognitive OR memory OR attention"

# Запросы PubMed (фикс-датасет собран 07.09.2026 и лежит в data/raw;
# эти строки нужны только для ПОВТОРНОГО сбора при обновлении)
SUPPLEMENTS = {
    "Креатин": "creatine",
    "Омега-3": '"omega-3" OR "fish oil"',
    "Витамин D": '"vitamin d" OR cholecalciferol',
    "B12": '"vitamin B12" OR cobalamin',
    "Магний": "magnesium",
    "Кофеин": "caffeine",
    "L-Теанин": "theanine OR \"l-theanine\"",
    "Бакопа": '"bacopa monnieri" OR bacopa',
    "Ежовик": '"hericium erinaceus" OR "lion\'s mane"',
    "Гинкго": '"ginkgo biloba" OR ginkgo',
    "Родиола": '"rhodiola rosea" OR rhodiola',
    "Ашваганда": 'ashwagandha OR "withania somnifera"',
    "Фосфатидилсерин": "phosphatidylserine",
    "Alpha-GPC": '"alpha-gpc" OR "choline alfoscerate"',
    "CDP-холин": 'citicoline OR "cdp-choline"',
    "Гуперзин А": 'huperzine OR "huperzine a"',
    "Куркумин": "curcumin",
    "Ресвератрол": "resveratrol",
    "NAC": '"n-acetylcysteine" OR acetylcysteine',
    "Цинк": "zinc",
    "Тирозин": 'tyrosine OR "l-tyrosine"',
    "Таурин": "taurine",
    "CoQ10": '"coenzyme q10" OR ubiquinone',
    "Пикногенол": 'pycnogenol OR "pine bark"',
    "Готу кола": '"centella asiatica" OR "gotu kola"',
}

# Английские имена для OpenAlex
EN = {"Креатин":"creatine","Омега-3":"omega-3 fatty acids","Витамин D":"vitamin D",
"B12":"vitamin B12","Магний":"magnesium","Кофеин":"caffeine","L-Теанин":"theanine",
"Бакопа":"bacopa monnieri","Ежовик":"hericium erinaceus","Гинкго":"ginkgo biloba",
"Родиола":"rhodiola rosea","Ашваганда":"ashwagandha","Фосфатидилсерин":"phosphatidylserine",
"Alpha-GPC":"alpha-gpc","CDP-холин":"citicoline","Гуперзин А":"huperzine",
"Куркумин":"curcumin","Ресвератрол":"resveratrol","NAC":"n-acetylcysteine",
"Цинк":"zinc","Тирозин":"tyrosine","Таурин":"taurine","CoQ10":"coenzyme q10",
"Пикногенол":"pycnogenol","Готу кола":"centella asiatica"}

# Суточная норма в единицах упаковки за 30 дней
NORM = {"Креатин":150,"Омега-3":60,"Витамин D":30,"B12":30,"Магний":30,
"Кофеин":30,"L-Теанин":30,"Бакопа":30,"Ежовик":60,"Гинкго":30,"Родиола":30,
"Ашваганда":30,"Фосфатидилсерин":30,"Alpha-GPC":30,"CDP-холин":30,
"Гуперзин А":30,"Куркумин":60,"Ресвератрол":30,"NAC":60,"Цинк":30,
"Тирозин":60,"Таурин":60,"CoQ10":30,"Пикногенол":30,"Готу кола":30}

# Вердикты мета-анализов (ручная разметка по Examine/Cochrane)
VERDICT = {"Креатин":1,"Омега-3":1,"Кофеин":1,"L-Теанин":1,"Бакопа":1,
"Ашваганда":1,"Витамин D":0,"B12":0,"Цинк":0,"Магний":0,"Родиола":0,
"CDP-холин":0,"Alpha-GPC":0,"Фосфатидилсерин":0,"Гуперзин А":0,"NAC":0,
"Тирозин":0,"Таурин":-1,"Ежовик":-1,"Пикногенол":-1,"Готу кола":-1,
"Куркумин":-1,"Ресвератрол":-1,"CoQ10":-1,"Гинкго":-1}

# Запросы Wildberries + тип единицы фасовки
WB_QUERY = {
    "Креатин": ("креатин моногидрат", "г"),
    "Омега-3": ("омега-3 капсулы", "капс"),
    "Витамин D": ("витамин d3 2000 ме", "капс"),
    "B12": ("витамин b12", "капс"),
    "Магний": ("магний b6", "капс"),
    "Кофеин": ("кофеин 200 мг", "капс"),
    "L-Теанин": ("l-теанин", "капс"),
    "Бакопа": ("бакопа моннье капсулы", "капс"),
    "Ежовик": ("ежовик гребенчатый", "капс"),
    "Гинкго": ("гинкго билоба", "капс"),
    "Родиола": ("родиола розовая", "капс"),
    "Ашваганда": ("ашваганда", "капс"),
    "Фосфатидилсерин": ("фосфатидилсерин", "капс"),
    "Alpha-GPC": ("alpha gpc", "капс"),
    "CDP-холин": ("цитиколин", "капс"),
    "Гуперзин А": ("гуперзин", "капс"),
    "Куркумин": ("куркумин", "капс"),
    "Ресвератрол": ("ресвератрол", "капс"),
    "NAC": ("nac ацетилцистеин", "капс"),
    "Цинк": ("цинк пиколинат", "капс"),
    "Тирозин": ("l-тирозин", "капс"),
    "Таурин": ("таурин", "капс"),
    "CoQ10": ("коэнзим q10", "капс"),
    "Пикногенол": ("пикногенол", "капс"),
    "Готу кола": ("готу кола", "капс"),
}
# ============ v1.2: РАСШИРЕНИЕ (16 добавок + оси) ============
SUPPLEMENTS_V12 = {
    "Мелатонин": "melatonin",
    "ГАБА": "GABA OR gamma-aminobutyric acid",
    "Глицин": "glycine",
    "Валериана": "valerian OR Valeriana",
    "Бета-аланин": "beta-alanine",
    "L-цитруллин": "citrulline",
    "Витамин C": "ascorbic acid OR vitamin C",
    "Эхинацея": "echinacea",
    "Бузина": "elderberry OR Sambucus",
    "Зверобой": "St John's wort OR Hypericum",
    "5-HTP": "5-hydroxytryptophan",
    "Коллаген": "collagen",
    "Пробиотики": "probiotics",
    "B9": "folic acid OR folate",
    "Железо": "iron",
    "Триптофан": "tryptophan",
}
OUTCOME_V12 = {
    "Мелатонин": '(sleep OR insomnia OR "sleep latency")',
    "ГАБА": '(sleep OR anxiety OR stress)',
    "Глицин": '(sleep OR insomnia)',
    "Валериана": '(sleep OR insomnia)',
    "Бета-аланин": '(exercise OR performance OR endurance)',
    "L-цитруллин": '(exercise OR performance OR "blood flow")',
    "Витамин C": '(immune OR "common cold" OR infection)',
    "Эхинацея": '(immune OR "common cold")',
    "Бузина": '(immune OR "common cold" OR influenza)',
    "Зверобой": '(depression OR depressive)',
    "5-HTP": '(depression OR anxiety)',
    "Коллаген": '(skin OR joint OR osteoarthritis)',
    "Пробиотики": '(gut OR IBS OR diarrhea OR immune)',
    "B9": '(cognition OR depression)',
    "Железо": '(fatigue OR anemia OR cognition)',
    "Триптофан": '(sleep OR depression)',
}
CATEGORY_V12 = {
    "Мелатонин": "Сон", "ГАБА": "Сон", "Глицин": "Сон", "Валериана": "Сон",
    "Триптофан": "Сон", "Бета-аланин": "Спорт", "L-цитруллин": "Спорт",
    "Витамин C": "Иммунитет", "Эхинацея": "Иммунитет", "Бузина": "Иммунитет",
    "Зверобой": "Настроение", "5-HTP": "Настроение",
    "Коллаген": "Кожа и суставы", "Пробиотики": "Кишечник",
    "B9": "Общее", "Железо": "Общее",
}
FORMS = {
    "Магний": "оксид — плохо усваивается; цитрат — слабит; глицинат — сон, мягкий для ЖКТ; треонат — «для мозга», доказательств слабо",
    "Пробиотики": "эффект штаммозависим: L. rhamnosus GG — диарея; S. boulardii — антибиотико-ассоциированная; B. longum 1714 — стресс (мелкие RCT)",
    "Омега-3": "смотри мг EPA+DHA на этикетке, а не «рыбий жир 1000 мг»",
    "Витамин D": "D3 (холекальциферол) поднимает уровень лучше, чем D2",
}
VERDICT_V12_DRAFT = {   # ЧЕРНОВИКИ! сверим с мета-анализами на Шаге 3
    "Мелатонин": 1, "ГАБА": 0, "Глицин": 0, "Валериана": -1,
    "Бета-аланин": 1, "L-цитруллин": 1, "Витамин C": 0, "Эхинацея": -1,
    "Бузина": 0, "Зверобой": 1, "5-HTP": 0, "Коллаген": 1,
    "Пробиотики": 0, "B9": 0, "Железо": 0, "Триптофан": 0,
}
SUPPLEMENTS.update(SUPPLEMENTS_V12)
# ============ v1.2: WB-запросы, нормы и англ. имена ============
EN_V12 = {
    "Мелатонин": "melatonin", "ГАБА": "GABA", "Глицин": "glycine",
    "Валериана": "valerian", "Бета-аланин": "beta-alanine",
    "L-цитруллин": "citrulline", "Витамин C": "vitamin C",
    "Эхинацея": "echinacea", "Бузина": "elderberry",
    "Зверобой": "St John's wort", "5-HTP": "5-HTP",
    "Коллаген": "collagen", "Пробиотики": "probiotics",
    "B9": "folic acid", "Железо": "iron", "Триптофан": "tryptophan",
}
EN.update(EN_V12)

# норма_мес: сколько единиц нужно на месяц (для расчёта цены_мес)
NORM_V12 = {
    "Мелатонин": 30, "ГАБА": 30, "Глицин": 60, "Валериана": 30,
    "Бета-аланин": 30, "L-цитруллин": 30, "Витамин C": 30,
    "Эхинацея": 30, "Бузина": 30, "Зверобой": 30, "5-HTP": 30,
    "Коллаген": 30, "Пробиотики": 30, "B9": 30, "Железо": 30,
    "Триптофан": 30,
}
NORM.update(NORM_V12)

# WB-запросы (название для поиска + единица измерения "г" или "капс")
WB_QUERY_V12 = {
   "Мелатонин": "melatonin[Title/Abstract]",
    "ГАБА":          ("GABA 500 мг",          "капс"),
    "Глицин":        ("глицин 500 мг",        "табл"),
    "Валериана":     ("валериана экстракт",    "капс"),
    "Бета-аланин":   ("бета-аланин",          "г"),
    "L-цитруллин":   ("цитруллин малат",      "г"),
    "Витамин C":     ("витамин C 500 мг",     "табл"),
    "Эхинацея":      ("эхинацея",             "капс"),
    "Бузина":        ("бузина черная",        "капс"),
    "Зверобой":      ("зверобой экстракт",    "капс"),
    "5-HTP":         ("5-HTP 100 мг",         "капс"),
    "Пробиотики": "probiotics[Title/Abstract] AND (supplement OR supplementation OR strain)",
    "Пробиотики": "probiotics[Title/Abstract] AND (supplement OR supplementation OR strain)",
    "B9":            ("фолиевая кислота",     "табл"),
    "Железо":        ("железо хелат",         "капс"),
    "Триптофан":     ("L-триптофан 500 мг",   "капс"),
}
WB_QUERY.update(WB_QUERY_V12)