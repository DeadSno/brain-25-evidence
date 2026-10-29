# Data Dictionary — словарь данных

> Формальное описание всех полей данных на уровне атрибутов.
> Дополняет [ERD](erd.md) детальной типизацией.

## 1. `supplement` — добавки (130)

| Поле | Тип | NOT NULL | Ограничения | Описание | Пример |
|------|-----|:--------:|-------------|----------|--------|
| id | VARCHAR(64) | ✓ | PK | Название | Креатин |
| category_id | VARCHAR(128) | ✓ | FK | Категория | Спорт/Когниция |
| grade | CHAR(1) | ✓ | CHECK A/B/C/D | Грейд | B |
| verdict | VARCHAR(32) | ✓ | CHECK | Вердикт | работает |
| code | SMALLINT | ✓ | CHECK -1/0/1 | Числовой | 1 |
| about | TEXT | | max 160 | Описание | Улучшает память |
| who_needs | TEXT | | max 180 | Кому нужен | Спортсменам |
| onset | TEXT | | max 150 | Когда эффект | 2-4 недели |
| myths | TEXT | | max 220 | Мифы | Не наращивает мышцы |
| food_sources | TEXT | | max 180 | Источники | Мясо, рыба |
| guidelines | TEXT | | max 180 | Рекомендации | 3-5 г/сут |
| how_to_choose | TEXT | | max 180 | Как выбирать | Моногидрат |
| dosage | TEXT | | | Дозировка | 3-5 г/сут |
| course | TEXT | | | Курс | Постоянно |
| caution | TEXT | | | Предостережения | При болезнях почек |
| upper_limit | TEXT | | | Верхний предел | Не установлен |
| science_index | INT | | >= 0 | Индекс | 1265 |
| rct | INT | | >= 0 | РКИ | 450 |
| meta_count | INT | | >= 0 | МА | 68 |
| citations | INT | | >= 0 | Цитирований | 12000 |

**Индексы:** idx_supplement_grade, idx_supplement_si.

## 2. `mech` — механизмы (391)

| Поле | Тип | NOT NULL | Ограничения | Описание | Пример |
|------|-----|:--------:|-------------|----------|--------|
| id | INTEGER | ✓ | PK | ID | 1 |
| supplement_id | VARCHAR(64) | ✓ | FK | Добавка | Креатин |
| mechanism | TEXT | ✓ | 20-250 | Механизм | Фосфокреатиновый буфер |
| effect | TEXT | ✓ | 5-120 | Эффект | Повышение силы |
| strength | VARCHAR(16) | ✓ | CHECK | Сила | умеренно |

## 3. `interaction` — взаимодействия (199)

| Поле | Тип | NOT NULL | Ограничения | Описание | Пример |
|------|-----|:--------:|-------------|----------|--------|
| id | INTEGER | ✓ | PK | ID | 1 |
| supplement_id | VARCHAR(64) | ✓ | FK | Добавка | Селен |
| with_target | VARCHAR(128) | ✓ | | С чем | статины |
| severity | VARCHAR(16) | ✓ | CHECK | Уровень | low |
| note | TEXT | | max 200 | Пояснение | Может снижать эффект |

## 4. `key_source` — источники (393)

| Поле | Тип | NOT NULL | Ограничения | Описание | Пример |
|------|-----|:--------:|-------------|----------|--------|
| id | INTEGER | ✓ | PK | ID | 1 |
| supplement_id | VARCHAR(64) | ✓ | FK | Добавка | Креатин |
| pmid | VARCHAR(16) | | | PMID | 12345678 |
| doi | VARCHAR(128) | | | DOI | 10.1016/j.example |
| title | TEXT | | | Название | Effect of creatine |
| year | INTEGER | | 1900-2100 | Год | 2024 |
| journal | VARCHAR(128) | | | Журнал | The Lancet |

## 5. `effect_tag` — теги (18)

| Поле | Тип | NOT NULL | Ограничения | Описание | Пример |
|------|-----|:--------:|-------------|----------|--------|
| tag | VARCHAR(32) | ✓ | PK | Тег | brain |

Список 18 тегов: brain, mood, sleep, stress, immunity, heart, gut, muscle, energy, skin, metabolism, blood, bones, joints, liver, eyes, urinary, hormones.

## 6. `supplement_tag` — M-N (226)

| Поле | Тип | NOT NULL | Ограничения | Описание |
|------|-----|:--------:|-------------|----------|
| supplement_id | VARCHAR(64) | ✓ | FK | Добавка |
| tag | VARCHAR(32) | ✓ | FK | Тег |

PK: (supplement_id, tag) — составной.

## 7. `paper` — статьи (37 618)

| Поле | Тип | NOT NULL | Ограничения | Описание | Пример |
|------|-----|:--------:|-------------|----------|--------|
| pmid | VARCHAR(16) | ✓ | PK | PMID | 12345678 |
| pmcid | VARCHAR(16) | | | PMCID | PMC7871530 |
| doi | VARCHAR(128) | | | DOI | 10.1016/j.example |
| title | TEXT | | max 1000 | Название | Meta-analysis |
| year | INTEGER | | 1900-2100 | Год | 2024 |
| journal | VARCHAR(200) | | | Журнал | Nature |
| abstract | TEXT | | max 5000 | Абстракт | Background |

## 8. `coi` — конфликты интересов (6 310)

| Поле | Тип | NOT NULL | Ограничения | Описание | Пример |
|------|-----|:--------:|-------------|----------|--------|
| pmid | VARCHAR(16) | ✓ | PK, FK | PMID | 12345678 |
| coi_type | VARCHAR(16) | ✓ | CHECK | Тип | none |
| has_funding | BOOLEAN | | | Funding | true |
| has_pharma | BOOLEAN | | | Фарма | false |

## 9. `category` — категории

| Поле | Тип | NOT NULL | Ограничения | Описание | Пример |
|------|-----|:--------:|-------------|----------|--------|
| id | VARCHAR(128) | ✓ | PK | ID | Спорт/Когниция |
| name | VARCHAR(128) | ✓ | | Имя | Спорт и когниция |

## Соглашения

| Правило | Описание |
|---------|----------|
| Кодировка | UTF-8 без BOM |
| Даты | ISO 8601 |
| Числа | Точка как десятичный |
| NULL | Отсутствие данных (не пустая строка) |

## Версия

- v1.0 — 2026-09-25, 9 сущностей, 39 полей
