# Gherkin — Given/When/Then сценарии

> Формальные сценарии поведения системы в нотации Gherkin (Cucumber).
> Дополняет [User Stories](user_stories.md) — там Acceptance Criteria чек-листами, здесь — в Given/When/Then.

Синтаксис:

```gherkin
Feature: Название фичи
  Scenario: Название сценария
    Given предыстория
    When действие
    Then ожидаемый результат
```

## Feature: Поиск добавок

```gherkin
Feature: Поиск добавок по названию
  Как посетитель сайта
  Я хочу найти добавку по названию
  Чтобы быстро получить информацию

  Scenario: Точное совпадение
    Given открыт сайт brain-25-evidence
    When в поле поиска ввожу Креатин
    Then в результатах появляется карточка Креатин
    And счётчик результатов = 1

  Scenario: Частичное совпадение
    Given открыт сайт brain-25-evidence
    When в поле поиска ввожу Омега
    Then в результатах появляются все добавки с Омега
    And среди них Омега-3, EPA, DHA

  Scenario: Регистронезависимый поиск
    Given открыт сайт brain-25-evidence
    When в поле поиска ввожу КРЕАТИН
    Then в результатах появляется карточка Креатин

  Scenario: Нет результатов
    Given открыт сайт brain-25-evidence
    When в поле поиска ввожу qwerty123
    Then отображается сообщение Ничего не найдено
    And счётчик результатов = 0
```

## Feature: Фильтрация по грейду

```gherkin
Feature: Фильтрация добавок по грейду
  Как исследователь
  Я хочу фильтровать по грейду A/B/C/D
  Чтобы видеть только надёжные добавки

  Scenario: Только grade A
    Given открыт сайт brain-25-evidence
    When выбираю фильтр grade=A
    Then отображаются только добавки с grade A
    And счётчик = 8

  Scenario: Множественный выбор
    Given открыт сайт brain-25-evidence
    When выбираю фильтры grade=A и grade=B
    Then отображаются добавки с grade A или B
    And счётчик = 53

  Scenario: URL сохраняет фильтр
    Given открыт сайт с фильтром grade=A,B
    When копирую URL
    And открываю URL в новой вкладке
    Then фильтр grade=A,B применён автоматически
```

## Feature: REST API

```gherkin
Feature: REST API для внешних потребителей
  Как внешний разработчик
  Я хочу получить данные через API
  Чтобы построить свой сервис

  Scenario: Получить метаданные
    Given API доступен по адресу https://deadsno.github.io/brain-25-evidence
    When делаю GET /api/v1/index.json
    Then получаю 200 OK
    And Content-Type = application/json
    And в body поле count = 130
    And в body поле ids содержит 130 элементов

  Scenario: Получить все добавки
    Given API доступен
    When делаю GET /api/v1/supplements.json
    Then получаю 200 OK
    And в body массив supplements с 130 элементами
    And каждый элемент содержит поля id, grade, verdict

  Scenario: Запрос несуществующего endpoint
    Given API доступен
    When делаю GET /api/v1/unknown.json
    Then получаю 404 Not Found
    And body — HTML, не JSON
```

## Feature: Обновление данных (Maintainer)

```gherkin
Feature: Batch обновление добавок
  Как Maintainer
  Я хочу добавлять новые добавки
  Чтобы расширять базу

  Scenario: Успешное добавление
    Given создан CSV с 5 новыми добавками
    When запускаю python scripts/add_supplements_batch.py
    And запускаю fetch_papers.py
    And запускаю enrich_drafts.py --apply
    And проверяю validate_proposal.py
    Then валидация проходит (0 errors)
    And при apply_drafts.py data.json увеличивается на 5

  Scenario: Ошибка валидации
    Given proposal без key_sources
    When запускаю validate_proposal.py
    Then получаю FAIL с описанием ошибки
    And data.json не изменяется

  Scenario: Каскад при 500 от EBI
    Given EBI Europe PMC возвращает 500
    When fetch_europepmc.py пытается скачать PMCID
    Then скрипт делает 3 retry
    And потом переключается на NCBI efetch
    And файл сохраняется успешно
```

## Feature: Публикация релиза

```gherkin
Feature: CI проверяет и публикует изменения
  Как Developer
  Я хочу автоматический деплой после push
  Чтобы не деплоить вручную

  Scenario: Успешный деплой
    Given локально изменён data.json
    When делаю git push в main
    Then GitHub Actions запускает pytest
    And Newman проверяет API
    And при успехе GitHub Pages пересобирает сайт
    And Streamlit автоматически обновляется

  Scenario: Провал тестов блокирует деплой
    Given локально сломанный тест
    When делаю git push
    Then CI падает на pytest
    And GitHub Pages не пересобирается
    And production остаётся рабочим
```

## Маппинг: Gherkin ↔ User Stories

| Gherkin Feature | US |
|-----------------|-----|
| Поиск добавок по названию | US-01 |
| Фильтрация добавок по грейду | US-02 |
| REST API | US-05, US-06 |
| Batch обновление | US-08, US-09 |
| CI проверяет и публикует | US-08 |

## Связанные документы

- [User Stories](user_stories.md) — источник требований
- [RTM](rtm.md) — трассировка
- [Test SQL](tests/test_sql.py), [Test API](tests/test_api_contract.py) — реализация

## Версия

- v1.0 — 2026-09-26, 5 features, 14 scenarios
