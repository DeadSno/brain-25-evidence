# BRIEF: Q1.5 — batch 17a (5 карточек)

## Что делаешь

Заполнить **5 карточек** в `reports/q14_batch_17a_proposal.json` по abstracts из PubMed.

Все 5 — **хорошо изученные**, ожидаю grade B или A. Не выдумывать.

## Список карточек

| # | ID | Категория | Особенность |
|---|-----|-----------|-------------|
| 1 | S. boulardii | Кишечник | Saccharomyces boulardii, 3 MA (диарея, антибиотик) |
| 2 | LGG | Кишечник | Lactobacillus rhamnosus GG, 3 MA |
| 3 | B. lactis | Кишечник | Bifidobacterium lactis, 3 MA |
| 4 | DHA | Когниция | Docosahexaenoic acid, 3 MA (Альцгеймер, депрессия) |
| 5 | GLA | Кожа и суставы | Gamma-linolenic acid, 3 MA (кожа, вечерняя примула) |

## Что читать

- `reports/evidence/S. boulardii.md`
- `reports/evidence/LGG.md`
- `reports/evidence/B. lactis.md`
- `reports/evidence/DHA.md`
- `reports/evidence/GLA.md`
- `docs/data.json` — эталон (Креатин, Омега-3, Селен, HMB)

## Правила (полные)

### Не выдумывать

- **Только из abstracts.** Если нет данных → `"данных нет"` / `"не изучалось"`.
- **Не смешивать вещества.** GLA ≠ другие омега-6. DHA ≠ EPA.
- **Не использовать MA на животных** как доказательство людям.
- **Не выдумывать дозы.** Если нет — `"в абстрактах не указана"`.

### Формат полей

**adv (7):** `about` 30-160, `who_needs` 40-180, `onset` 30-150, `myths` 60-220, `food_sources` 25-180, `guidelines` 40-180, `how_to_choose` 35-180.

**База (7):** `verdict` (`работает`/`зависит от контекста`/`не подтверждено`), `grade` (A/B/C/D), `code` (-1/0/1), `dosage`, `course`, `caution`, `upper_limit`.

**effects (1-3):** 5-40 симв.

**mechs (2-4):** `[механизм 20-250, эффект 5-120, сила]`. Сила: `сильно/умеренно/слабо/контекст/маркетинг`.

**key_sources (2-3):**
```json
{"pmid": "12345678", "doi": "10.xxx/yyy", "title": "...", "year": 2024, "journal": "..."}
```
⚠️ `year` — **int**, `journal` — обязательно.

**interactions:** если нет реальных →
```json
[{"with": "нет данных", "severity": "low", "note": "известных взаимодействий нет"}]
```
Поле `with` обязательно.

### Грейды

| Код | Когда |
|-----|-------|
| A | MA показывают эффект у здоровых |
| B | Эффект есть с оговорками |
| C | Только при дефиците/в подгруппах |
| D | Нет MA на людях / отрицательные |

## Формат вывода

Один файл `reports/q14_batch_17a_proposal.json`:
```json
{
  "S. boulardii": {
    "verdict": "...", "grade": "...", "code": 0,
    "about": "...", "who_needs": "...", "onset": "...",
    "myths": "...", "food_sources": "...", "guidelines": "...", "how_to_choose": "...",
    "dosage": "...", "course": "...", "caution": "...", "upper_limit": "...",
    "effects": ["..."],
    "mechs": [["...", "...", "..."]],
    "key_sources": [{"pmid": "...", "doi": "...", "title": "...", "year": 2024, "journal": "..."}],
    "interactions": [{"with": "нет данных", "severity": "low", "note": "известных взаимодействий нет"}]
  }
}
```

## Не делать

- ❌ Не писать в `docs/data.json`
- ❌ Не коммитить
- ❌ Не выдумывать
- ❌ Не использовать «может помочь», «предположительно»

## Проверка

После заполнения — запусти:
```powershell
python scripts\validate_proposal.py --proposal q14_batch_17a_proposal.json
```
**Ожидаю: 0 errors.**