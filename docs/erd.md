> Entity-Relationship Diagram. Показывает сущности, атрибуты и связи между ними.
> Используется как основа для SQL-схемы (`scripts/db/schema.sql`).
>
> Сейчас данные хранятся в JSON, но эта схема показывает реляционную модель,
> в которую они мигрируют при росте > 5 000 карточек (см. ADR-001).

## Логическая модель (Mermaid ERD)

```mermaid
erDiagram
    SUPPLEMENT ||--o{ MECH : "has"
    SUPPLEMENT ||--o{ INTERACTION : "has"
    SUPPLEMENT ||--o{ KEY_SOURCE : "has"
    SUPPLEMENT }o--o{ EFFECT_TAG : "tagged"
    SUPPLEMENT }o--|| CATEGORY : "belongs"
    KEY_SOURCE }o--|| PAPER : "references"
    PAPER ||--o| COI : "has"
    PAPER }o--o{ FUNDER : "funded by"

    SUPPLEMENT {
        string id PK
        string category_id FK
        string grade
        string verdict
        int code
        string about
        int science_index
        int rct
        int meta_count
    }

    CATEGORY {
        string id PK
        string name
    }

    MECH {
        int id PK
        string supplement_id FK
        string mechanism
        string effect
        string strength
    }

    INTERACTION {
        int id PK
        string supplement_id FK
        string with_target
        string severity
        string note
    }

    KEY_SOURCE {
        int id PK
        string supplement_id FK
        string pmid FK
        string doi
        string title
        int year
        string journal
    }

    EFFECT_TAG {
        string tag PK
    }

    PAPER {
        string pmid PK
        string pmcid
        string doi
        string title
        int year
        string journal
    }

    COI {
        string pmid PK
        string coi_type
        bool has_funding
        bool has_pharma
    }

    FUNDER {
        int id PK
        string name
    }
Таблицы — детально
supplement — 130 записей
Поле	Тип	PK/FK	Описание
id	VARCHAR(64)	PK	Название добавки
category_id	VARCHAR(64)	FK	Ссылка на category
grade	CHAR(1)		A/B/C/D
verdict	VARCHAR(32)		работает/зависит/не подтверждено
code	SMALLINT		-1/0/1
about...upper_limit	TEXT		11 полей
science_index	INT		0..inf
rct	INT		Кол-во РКИ
meta_count	INT		Кол-во MA
citations	INT		OpenAlex
Индексы: idx_supplement_grade, idx_supplement_si.

mech — 1-N к supplement
Поле	Тип	Описание
id	SERIAL PK	
supplement_id	VARCHAR(64) FK	
mechanism	TEXT	20-250 символов
effect	TEXT	5-120 символов
strength	VARCHAR(16)	сильно/умеренно/слабо
interaction — 1-N
Поле	Тип	Описание
supplement_id	VARCHAR(64) FK	
with_target	VARCHAR(128)	Лекарство или добавка
severity	VARCHAR(16)	low/medium/high/critical
note	TEXT	
key_source — 1-N
Поле	Тип	Описание
supplement_id	VARCHAR(64) FK	
pmid	VARCHAR(16) FK	Ссылка на paper
doi, title, year, journal		Кэш из paper
effect_tag — M-N через supplement_tag
sql
CREATE TABLE supplement_tag (
    supplement_id VARCHAR(64) REFERENCES supplement(id),
    tag VARCHAR(32) REFERENCES effect_tag(tag),
    PRIMARY KEY (supplement_id, tag)
);
paper — 37 618 записей
Поле	Тип
pmid	VARCHAR(16) PK
pmcid	VARCHAR(16) nullable
doi, title, year, journal, abstract	
coi — 6 310 записей
Поле	Тип
pmid	VARCHAR(16) PK, FK
coi_type	VARCHAR(16)
has_funding	BOOLEAN
has_pharma	BOOLEAN
funder — M-N через paper_funder
Топ-10 — государственные: NSFC, NIH, NCI, NIDDK.

Нормализация
Форма	Применение
1НФ	Все поля атомарные
2НФ	Зависят от полного PK
3НФ	category вынесена
Денормализация	key_source хранит doi/title — ускоряет API
Стратегия роста
Записей	Решение
< 1 000 (сейчас 130)	JSON + DuckDB
1 000 - 5 000	SQLite или DuckDB
5 000 - 50 000	PostgreSQL + FastAPI
> 50 000	PostgreSQL + ClickHouse

Версия
v1.0 — 2026-09-25, ERD для 130 карточек, 9 таблиц, 4 M-N связи