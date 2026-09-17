import pathlib

t = pathlib.Path('docs/index.html').read_text(encoding='utf-8')
i = t.find('<section id="qaSection"')

if i == -1:
    print('qaSection не найден!')
else:
    # Правильная концовка
    correct_tail = '''<section id="qaSection" style="background:var(--card-bg);padding:1.2rem 1.5rem;border-radius:12px;border:1px solid var(--border)">
  <h2>Сначала ответим на 3 вопроса</h2>
  <div class="qaGrid">
    <div class="qa">
      <h3>1. Чем БАД отличается от лекарства?</h3>
      <p>Лекарство лечит болезнь и проходит жёсткую регистрацию. БАД — пищевой продукт. Мы показываем где эффект подтверждён мета-анализами, а где — маркетинг.</p>
    </div>
    <div class="qa">
      <h3>2. Зачем он мне?</h3>
      <p>Чтобы не платить за пустышку. У 12 из 81 добавок эффект не подтверждён (грейд D), ещё у 26 — только в специфических условиях (грейд C).</p>
    </div>
    <div class="qa">
      <h3>3. Как выбирать?</h3>
      <p>По грейду и вердикту. A/B — работает при своей дозе; C — только при конкретных условиях; D — не тратить деньги. Доза и ограничения — в карточке каждой добавки.</p>
    </div>
  </div>
</section>

<footer>
  <p>v3.1.0 · 81 добавка верифицирована · <a href="methodology.html">Методология</a></p>
</footer>

<div id="modalOverlay" style="display:none">
  <div id="modal">
    <button id="modalClose">✕</button>
    <div id="modalBody"></div>
  </div>
</div>
<script src="script.js?v=281"></script>
<script src="science2.js?v=280" defer></script>
<script src="tracker.js?v=280" defer></script>
<script src="pwa.js?v=280" defer></script>
</body>
</html>
'''
    
    t2 = t[:i] + correct_tail
    pathlib.Path('docs/index.html').write_text(t2, encoding='utf-8')
    print('index.html починен: qaSection восстановлен')
