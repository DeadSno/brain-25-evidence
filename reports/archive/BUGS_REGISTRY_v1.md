> **Архивный документ.** Статусы в этом файле не поддерживаются и относятся к Rerun 1. Актуальный план фиксов — в reports/FIX_PLAN.md.

# Реестр багов v5.6.5 (Rerun 1) — база для кросс-проверки

| ID | Скилл | Критичность | Краткое описание | Статус на 23.10.2026 |
|----|-------|-------------|------------------|----------------------|
| P2-01 | product-audit | Med | Кнопка «Найти свою добавку →» скроллит к #cardsContainer, но не фокусирует поле поиска #search. | Актуально |
| P2-02 | product-audit | Low | Чипы Ozon/WB на плитках ведут на поиск в магазине, а не на конкретный товар. | Актуально |
| P2-03 | product-audit | Med | На compare.html нет путей к покупке (магазины, чипы, кнопка «Купить»). | Закрыто |
| P2-04 | product-audit | Med | Enter в калькуляторе работает только по точному совпадению id. | Закрыто |
| P2-05 | product-audit | Low | На sup-страницах запрос магазина включает форму выпуска, на главной — только название. | Актуально |
| Q2-01 | qa-deep | Med | compare.html без ?ids= открывается пустой без сообщения об ошибке. | Закрыто |
| Q2-02 | qa-deep | Low | Чипы Ozon/WB на главной имеют пустой атрибут class="". | Актуально |
| Q2-03 | qa-deep | Low | Поиск на 404.html не редиректит на sup при нажатии Enter. | Актуально |
| A2-01 | accessibility-check | Med | Кнопка смены темы не имеет aria-label (только эмодзи). | Актуально |
| A2-02 | accessibility-check | Low | Кнопка «Удиви меня» с избыточными атрибутами (aria-label + title + span). | Закрыто |
| A2-03 | accessibility-check | Low | Чипы Ozon/WB: aria-label есть, но класс отсутствует. | Актуально |
| A2-04 | accessibility-check | Med | CTA после скролла фокусирует кнопку фильтра, а не #search. | Актуально |
| A2-05 | accessibility-check | Low | summary без role="button" и aria-expanded (блок «Сравнить 3+»). | Актуально |
| A2-06 | accessibility-check | Med | Граф interactions.html недоступен с клавиатуры (нет фокуса/роли на canvas). | Актуально |
| A2-07 | accessibility-check | Low | 404.html навигация без data-i18n-aria-label, нет связи #nfSearch–#nfResults. | Актуально |
| A2-08 | accessibility-check | Med | Чип в тёмной теме контраст ~3.27:1 < 4.5:1 (WCAG AA). | Актуально |
| M2-01 | mobile-deep-audit | Med | Навбар на 320px не влезает в ширину экрана (maxRight=536px > 320px). | Актуально |
| M2-02 | mobile-deep-audit | Med | trends.html на 320px: горизонтальный скролл (scrollWidth=341 > 320). | Актуально |
| M2-03 | mobile-deep-audit | Med | 404.html не адаптивна на 320px (maxRight=701px > 320px). | Актуально |
| M2-04 | mobile-deep-audit | Low | CTA font-size 12.48px на 320px (< 14px). | Закрыто |
| SE2-01 | seo-check | Low | Чипы магазинов на sup-страницах без rel="nofollow". | Актуально |
| SE2-02 | seo-check | Low | compare.html без JSON-LD structured data. | Закрыто |
| SE2-03 | seo-check | Low | index.html без SearchAction и ItemList в JSON-LD. | Актуально |
| SE2-04 | seo-check | Low | Кнопка «+ Сравнить» — не ссылка (130 sup-страниц, навигация через JS). | Актуально |
| SE2-05 | seo-check | Low | 10 внешних ссылок без rel="nofollow". | Актуально |
| D2-01 | data-audit | Med | В docs/api/v1/ отсутствуют interactions.json и graph.json. | Актуально |
| D2-02 | data-audit | Med | 5 битых PMID (не 8-значные) в key_sources. | Актуально |
| D2-03 | data-audit | Low | 2 пустых поля doi в key_sources (Витамин K1, PABA). | Частично |
| D2-04 | data-audit | Med | forms — строка, а не массив (все 130 карточек). | Актуально |
| D2-05 | data-audit | Low | Отсутствуют поля papers и safety у всех 130 карточек. | Актуально |
| D2-06 | data-audit | Med | 2 точных дубля строк взаимодействий в DuckDB таблице interaction. | Закрыто |
| D2-07 | data-audit | Low | «4 карточки Блока 6» не верифицируются (8 карточек с updated=2026-09-25). | Актуально |
| C2-01 | cwv | Med | CLS Poor на index 0.262–0.267 > 0.25 (FOUT шрифтов без preload). | Актуально |
| C2-02 | cwv | Med | CLS Poor на calculator (светлая) 0.271 > 0.25 (FOUT шрифтов). | Закрыто |
| C2-03 | cwv | Med | vis-network 673 КБ загружается не лениво при каждой загрузке interactions.html. | Актуально |
| C2-04 | cwv | Low | script.js (74 КБ) и style.css (178 КБ) не минифицированы. | Актуально |
| C2-05 | cwv | Low | 5 файлов шрифтов (~560 КБ) без rel="preload". | Актуально |
| MAN-01 | Manual | Med | Кнопки навбара «Светлая тема»/«Удиви меня» без цветового выделения. |
| MAN-02 | Manual | Med | Текст «Почему этому можно верить» канцелярит, непонятен. |
| MAN-03 | Manual | Blocker | Граф interactions.html#graph — нечитаемый клубок, текст наезжает. |
| MAN-04 | Manual | Low | Кружочки методологии разного диаметра. |
| MAN-05 | Manual | Blocker | Вкладка «Сила эффекта (g)» не рендерит данные (график пуст/старые данные). |
| I2-01 | i18n-rtl-audit | Med | Нет механизма смены локали (LOCALE только из html lang="ru"). | Актуально |
| I2-02 | i18n-rtl-audit | Med | Словарь рассеян по 4 файлам (i18n.js + share.js/science2.js/tracker.js). | Актуально |
| I2-03 | i18n-rtl-audit | Low | В словаре только ключ ru, нет en. | Актуально |
| U2-01 | ui-ux-deep-audit | Med | Кнопки навбара без цветового выделения (выбиваются из дизайн-системы). | Закрыто |
| U2-02 | ui-ux-deep-audit | Med | Ввод букв в дозу → NaN считается «в норме» (cntOk++), нет ошибки пользователю. | Частично |
| U2-03 | ui-ux-deep-audit | Low | Чипы магазинов без визуального отклика при клике (нет :active/тоста). | Частично |
| U2-04 | ui-ux-deep-audit | Low | Хаб карточек на главной без :hover отклика (неочевидно, что кликабельно). | Закрыто |
| U2-05 | ui-ux-deep-audit | Low | Кнопка «Удиви меня» слабая микроинтеракция. | Частично |
| U2-06 | ui-ux-deep-audit | Low | Копирование ссылки без .catch() (при ошибке нет отклика пользователю). | Актуально |
| MK2-01 | marketing-deep-audit | Med | Основная CTA не на первом экране (после секции whyTrust). | Закрыто |
| MK2-02 | marketing-deep-audit | Low | На главной >15 кнопок, нет иерархии primary/secondary. | Актуально |
| MK2-03 | marketing-deep-audit | Med | twitter:title/description/image отсутствуют на 134 из 148 страниц. | Актуально |
| MK2-04 | marketing-deep-audit | Low | Блок цифр heroStats без контекста источника. | Частично |
| MK2-05 | marketing-deep-audit | Low | Текст «Почему этому можно верить» содержит канцеляризмы. | Актуально |
| MK2-06 | marketing-deep-audit | Low | УТП не сформулировано явно, H1 абстрактен. | Актуально |
| PR2-01 | project-audit | Low | Отсутствует .editorconfig. | Актуально |
| PR2-02 | project-audit | Low | Отсутствует SECURITY.md. | Актуально |
| PR2-03 | project-audit | Low | Отсутствует CODE_OF_CONDUCT.md. | Актуально |
| PR2-04 | project-audit | Low | 17 скриптов в scripts/ — кандидаты в мёртвый код. | Закрыто |
| PR2-05 | project-audit | Low | 10 скриптов в scripts/ без модульного docstring. | Частично |
| S1-01 | site-navigation | Blocker | 6 разных наборов ссылок навбара на страницах вместо единого. | Закрыто |
| S1-02 | site-navigation | Blocker | 262 битых ссылки на sup-страницы (несуществующие/опечатанные URL). | Закрыто |
| S1-03 | site-navigation | Med | Футер не единый (различается на index / sup / compare / 404). | Актуально |
| S1-04 | site-navigation | Low | Нет хлебных крошек на любой странице. | Частично |
| V2-01 | visual-design-audit | Low | Нет использования тега h6 на страницах. | Актуально |
| V2-02 | visual-design-audit | Med | Нет брейкпоинтов 320px и 1440px в media queries. | Актуально |
| V2-03 | visual-design-audit | Low | Жёсткие hex-цвета (не через CSS-переменные). | Актуально |
| V2-04 | visual-design-audit | Med | Размер шрифта 12px (< 14px минимум для читаемости). | Актуально |
| V2-05 | visual-design-audit | Low | Страница 404 не имеет site-footer. | Актуально |
| V2-06 | visual-design-audit | Low | 14 хардкодных hex-цвета в рендере графа связей. | Актуально |
| V2-07 | visual-design-audit | Med | Селектор html.light не переопределяет CSS-переменные темы. | Закрыто |
| V2-08 | visual-design-audit | Low | Чипы font-size 11.52px (< 14px). | Актуально |
| L2-01 | legal-compliance-audit | Med | Отсутствует страница Terms of Use. | Актуально |
| L2-02 | legal-compliance-audit | Med | Нет лицензии на данные в HTML-страницах. | Актуально |
| L2-03 | legal-compliance-audit | Low | Нет локального предупреждения в калькуляторе (не мед. рекомендация). | Частично |
| L2-04 | legal-compliance-audit | Med | Нет пометки о партнёрских (аффилиатных) ссылках на магазины. | Актуально |
| PW2-01 | pwa-audit | Med | 404.html не подключает manifest и pwa.js (SW не регистрируется). | Актуально |
| PW2-02 | pwa-audit | Med | 404.html не входит в STATIC_ASSETS sw.js. | Актуально |
| PW2-03 | pwa-audit | Low | Маскабельные иконки не кэшируются SW. | Актуально |
| PW2-04 | pwa-audit | Med | Кэш SW не инвалидируется при изменении version.json. | Актуально |
| PW2-05 | pwa-audit | Low | meta theme-color отсутствует на atlas.html, graph.html, google-верификации. | Актуально |
| DS2-01 | docs-sync | Blocker | Разное число тестов: version.json=1982, а в README/CONVENTIONS/AGENTS.md — 1979. | Актуально |
| DS2-02 | docs-sync | Med | AGENTS.md:13 указывает ветку v5.6-dev, реально v5.6.5-dev. | Закрыто |
| DS2-03 | docs-sync | Low | Хеши хотфиксов не привязаны к секции [v5.6.5] в CHANGELOG.md. | Актуально |
| RC2-01 | release-check | Low | Тег v5.6.5 не создан в репозитории. | Актуально |
| RC2-02 | release-check | Med | Тег v5.6.4 не является предком HEAD v5.6.5-dev. | Актуально |
| RC2-03 | release-check | Med | pytest -q завис (таймаут 10 мин), не завершён. | Частично |
| SK2-02 | skill-audit | Med | Битая ссылка reports/AUDIT_MASTER.md в SKILLS_INDEX.md:231. |
| RS2-01 | repo-size-audit | Med | .git раздут ~1 060 МБ (крупные бинарные в истории pack-файлов). | Актуально |
| RS2-02 | repo-size-audit | Med | tests/snapshots 214 файлов / 145,42 МБ отслеживаются в git. | Частично |
| RS2-03 | repo-size-audit | Low | 3 .json.gz файла в индексе git (уже в .gitignore, но отслеживаются). | Актуально |
| RS2-06 | repo-size-audit | Low | tests/snapshots не в .gitignore. | Частично |
