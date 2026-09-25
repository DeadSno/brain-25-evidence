-- 10 аналитических запросов для DuckDB.
-- Запуск: python scripts/db/run_queries.py

-- 1. Топ-10 добавок по научному индексу
-- Business: какие добавки наиболее изучены?
SELECT id, grade, science_index, rct, meta_count
FROM supplement
WHERE science_index IS NOT NULL
ORDER BY science_index DESC
LIMIT 10;

-- 2. Распределение по грейдам
-- Business: сколько надёжных (A+B) vs слабых (C+D)?
SELECT grade, COUNT(*) AS cnt,
       ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS pct
FROM supplement
GROUP BY grade
ORDER BY grade;

-- 3. Категории с наибольшим числом добавок
-- Business: какие направления наиболее покрыты?
SELECT category_id, COUNT(*) AS cnt
FROM supplement
WHERE category_id IS NOT NULL
GROUP BY category_id
ORDER BY cnt DESC
LIMIT 10;

-- 4. Взаимодействия по severity
-- Business: сколько критичных взаимодействий?
SELECT severity, COUNT(*) AS cnt
FROM interaction
GROUP BY severity
ORDER BY CASE severity
    WHEN 'critical' THEN 1 WHEN 'high' THEN 2
    WHEN 'medium' THEN 3 ELSE 4 END;

-- 5. Добавки с наибольшим числом механизмов
-- Business: у кого лучше изучены механизмы?
SELECT s.id, COUNT(m.id) AS mech_count
FROM supplement s
JOIN mech m ON m.supplement_id = s.id
GROUP BY s.id
ORDER BY mech_count DESC, s.id
LIMIT 10;

-- 6. Топ-10 тегов по числу добавок
-- Business: какие эффекты самые частые?
SELECT tag, COUNT(*) AS cnt
FROM supplement_tag
GROUP BY tag
ORDER BY cnt DESC
LIMIT 10;

-- 7. Добавки без key_sources (плохое качество данных)
-- Business: где не хватает источников?
SELECT s.id, s.grade
FROM supplement s
LEFT JOIN key_source ks ON ks.supplement_id = s.id
WHERE ks.id IS NULL
ORDER BY s.id;

-- 8. Оконная функция: ранг добавок внутри категории по scienceIndex
-- Business: кто лидер в каждой категории?
WITH ranked AS (
    SELECT
        category_id, id, science_index,
        ROW_NUMBER() OVER (
            PARTITION BY category_id
            ORDER BY science_index DESC NULLS LAST
        ) AS rn
    FROM supplement
    WHERE category_id IS NOT NULL
)
SELECT category_id, id, science_index, rn
FROM ranked
WHERE rn = 1
ORDER BY science_index DESC;

-- 9. Median scienceIndex (оконная функция)
-- Business: медиана надёжности базы
WITH ranked AS (
    SELECT science_index,
           ROW_NUMBER() OVER (ORDER BY science_index) AS rn,
           COUNT(*) OVER () AS cnt
    FROM supplement
    WHERE science_index IS NOT NULL
)
SELECT AVG(science_index) AS median_science_index
FROM ranked
WHERE rn IN ((cnt + 1) / 2, (cnt + 2) / 2);

-- 10. Papers по годам (тренд исследований)
-- Business: растёт ли интерес к добавкам?
SELECT year, COUNT(*) AS papers
FROM paper
WHERE year BETWEEN 2000 AND 2026
GROUP BY year
ORDER BY year;
