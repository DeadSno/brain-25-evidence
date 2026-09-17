t = open('docs/script.js', encoding='utf-8').read()
print("  key: ' count:", t.count("key: '"))
print("  данных пока нет:", 'данных пока нет' in t)
print("  cbEmpty:", 'cbEmpty' in t)
