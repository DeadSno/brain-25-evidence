# ROADMAP — brain-25-evidence

**Обновлено:** 2026-09-24
**Состояние:** 103 добавки, 113 тестов зелёные

## 📊 Текущее состояние

| Компонент | Статус |
|-----------|--------|
| База | **103 карточки** |
| Papers | 37 618 |
| Full texts | 9 075 (TXT + XML) |
| Funders | 5 135 (CrossRef) + 1 342 (Europe PMC) |
| Теги эффектов | 18 тегов, 103 покрыты |
| Тесты | 113 passed |
| Live demo | https://deadsno.github.io/brain-25-evidence/ |
| BI dashboard | https://brain-25-evidence.streamlit.app |

## ✅ Сделано

- Расширение базы 81 → **103 карточки** (витамины группы B, холин, EPA, лизин и др.)
- **Funders analysis** — Китай в 4.5× больше США (кросс-валидация CrossRef × Europe PMC)
- **Europe PMC парсер** — 5 059 XML полных текстов
- **trends.html** — executive summary, scatter-матрица наука × интерес, категории, методология
- **Streamlit BI** — финансирование, экспорт CSV
- PWA, трекер «Мой курс», FAQ, глоссарий, публичный журнал правок

## 🚧 В работе

- [ ] Досчитать Hedges' g для оставшихся карточек
- [ ] Батчи 16–19: +17 добавок до 120
- [ ] Обновить README (актуальные цифры)

## 🎯 План

### Ближайшее
- [ ] Публичный API `docs/api/v1/supplements.json`
- [ ] Расширение до 150 добавок
- [ ] Отдельные страницы на каждую добавку (SSG)

### Дальше
- [ ] DWH на DuckDB + dbt
- [ ] BI в Metabase
- [ ] Telegram-бот

## 📐 Методология

- **Индекс науки** = РКИ + 5 × мета-анализы (PubMed)
- **Вердикты** — ручная вычитка по PRISMA
- **Funding** — CrossRef + Europe PMC XML
- **Hedges' g** — из abstracts мета-анализов

Подробнее: [methodology.html](https://deadsno.github.io/brain-25-evidence/methodology.html)

## ⚠️ Принципы

- Правдивость данных важнее охвата и красоты
- Прозрачная методология
- Никаких медицинских рекомендаций
- MIT, открытые данные