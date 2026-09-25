-- Schema для Brain 25 Evidence
-- Совместимо с DuckDB и PostgreSQL.
-- Миграция JSON → БД: см. scripts/db/import_to_duckdb.py

-- 1. Основная таблица добавок
CREATE TABLE IF NOT EXISTS supplement (
    id              VARCHAR(64) PRIMARY KEY,
    category_id     VARCHAR(128),
    grade           CHAR(1)     CHECK (grade IN ('A','B','C','D')),
    verdict         VARCHAR(32),
    code            SMALLINT    CHECK (code IN (-1, 0, 1)),
    about           TEXT,
    who_needs       TEXT,
    onset           TEXT,
    myths           TEXT,
    food_sources    TEXT,
    guidelines      TEXT,
    how_to_choose   TEXT,
    dosage          TEXT,
    course          TEXT,
    caution         TEXT,
    upper_limit     TEXT,
    science_index   INTEGER,
    rct             INTEGER,
    meta_count      INTEGER,
    citations       INTEGER
);

CREATE INDEX IF NOT EXISTS idx_supplement_grade ON supplement(grade);
CREATE INDEX IF NOT EXISTS idx_supplement_si    ON supplement(science_index);

-- 2. Механизмы (1-N)
CREATE TABLE IF NOT EXISTS mech (
    id              INTEGER,
    supplement_id   VARCHAR(64) REFERENCES supplement(id),
    mechanism       TEXT,
    effect          TEXT,
    strength        VARCHAR(16)
);

-- 3. Взаимодействия (1-N)
CREATE TABLE IF NOT EXISTS interaction (
    id              INTEGER,
    supplement_id   VARCHAR(64) REFERENCES supplement(id),
    with_target     VARCHAR(128),
    severity        VARCHAR(16),
    note            TEXT
);

-- 4. Источники (1-N)
CREATE TABLE IF NOT EXISTS key_source (
    id              INTEGER,
    supplement_id   VARCHAR(64) REFERENCES supplement(id),
    pmid            VARCHAR(16),
    doi             VARCHAR(128),
    title           TEXT,
    year            INTEGER,
    journal         VARCHAR(128)
);

-- 5. Теги эффектов (M-N)
CREATE TABLE IF NOT EXISTS effect_tag (
    tag             VARCHAR(32) PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS supplement_tag (
    supplement_id   VARCHAR(64) REFERENCES supplement(id),
    tag             VARCHAR(32) REFERENCES effect_tag(tag),
    PRIMARY KEY (supplement_id, tag)
);

-- 6. Papers (метаданные статей)
CREATE TABLE IF NOT EXISTS paper (
    pmid            VARCHAR(16) PRIMARY KEY,
    pmcid           VARCHAR(16),
    doi             VARCHAR(128),
    title           TEXT,
    year            INTEGER,
    journal         VARCHAR(128),
    abstract        TEXT
);

-- 7. COI (1-1 к paper)
CREATE TABLE IF NOT EXISTS coi (
    pmid            VARCHAR(16) PRIMARY KEY REFERENCES paper(pmid),
    coi_type        VARCHAR(16) CHECK (coi_type IN ('none','yes','unclear','missing')),
    has_funding     BOOLEAN,
    has_pharma      BOOLEAN
);
