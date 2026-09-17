import pathlib
p = pathlib.Path('tests/test_v262_radar.py')
old = p.read_text(encoding='utf-8')
# Заменяем _prof() на 4 оси (без price)
new = old.replace(
    '''def _prof(s):
    """Профиль добавки s — 5 осей радара по script.js (нормировано по базе)."""
    raw = [
        s.get("scienceIndex") or 0,
        s.get("metaCount") or 0,
        s.get("reviews") or 0,
        s.get("trends") or 0,
        s.get("price"),
    ]
    arrays = [
        [x.get("scienceIndex") or 0 for x in DATA],
        [x.get("metaCount") or 0 for x in DATA],
        [x.get("reviews") or 0 for x in DATA],
        [x.get("trends") or 0 for x in DATA],
        [x.get("price") for x in DATA],   # null → 0 в pctile (как в script.js)
    ]
    vals = []
    for i in range(5):
        if i == 4 and raw[i] is not None:
            p = _pctile(raw[i], arrays[4])
            vals.append(100 - p)
        else:
            vals.append(_pctile(raw[i], arrays[i]))
    return vals''',
    '''def _prof(s):
    """Профиль добавки s — 4 оси радара по script.js (нормировано по базе)."""
    raw = [
        s.get("scienceIndex") or 0,
        s.get("metaCount") or 0,
        s.get("reviews") or 0,
        s.get("trends") or 0,
    ]
    arrays = [
        [x.get("scienceIndex") or 0 for x in DATA],
        [x.get("metaCount") or 0 for x in DATA],
        [x.get("reviews") or 0 for x in DATA],
        [x.get("trends") or 0 for x in DATA],
    ]
    vals = []
    for i in range(4):
        vals.append(_pctile(raw[i], arrays[i]))
    return vals'''
)
# Обновляем test_kofein_radar_values
new = new.replace(
    'labels = ["scienceIndex", "metaCount", "reviews", "trends", "price_inv"]',
    'labels = ["scienceIndex", "metaCount", "reviews", "trends"]'
)
p.write_text(new, encoding='utf-8')
print('обновлён test_v262_radar.py: убрана ось price_inv')
