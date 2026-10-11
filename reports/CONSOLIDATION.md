# CONSOLIDATION — консолидация отчётов

| | |
|---|---|
| **Дата** | 11.10.2026 |
| **Ветка** | `v5.6-dev` |
| **Задача** | Свести ~172 отчёта `reports/` к индексу + `audits/` + архив |

## Итог

| | До | После |
|---|---|---|
| Отчёты в `reports/` (верхний уровень) | 172 `.md` | 4 `.md` |
| Консолидированные аудиты | 0 | 11 (`audits/*.md`) |
| Архив | `v550` (18), `v560` (20) | + `v51` (40), `v56` (129) |

Перемещено файлов: **169** (из них в `archive/v51/` — 40, в `archive/v56/` — 129). Удалено: **0**.

## Что сделано

### 1. `reports/audits/` — консолидированные аудиты (11 файлов)

Все находки из исходных `AUDIT_*`/`STAGE_*`/`audit_*` сведены по типам, раздел «Открыто»/«Закрыто»,
у закрытых — коммит и дата, у открытых — приоритет и место.

| Файл | Открыто | Закрыто | Источники |
|---|---|---|---|
| `audits/a11y.md` | 9 | 21 | AUDIT_E_accessibility-check, AUDIT_E_ui-ux-deep-audit |
| `audits/data.md` | 24 | 4 | audit_A_data-audit, AUDIT_E_data-validation, audit_A_qa-deep-audit |
| `audits/html-css.md` | 9 | 9 | audit_C_visual-design, audit_A_docs-sync |
| `audits/js.md` | 7 | 6 | audit_A_cyberaudit, i18n/ui-ux JS-часть |
| `audits/legal.md` | 2 | 4 | audit_A_legal-compliance |
| `audits/mobile.md` | 14 | 7 | audit_B_mobile-deep, AUDIT_93_MOBILE, audit_93_a..e, STAGE1* |
| `audits/perf.md` | 13 | 3 | audit_D_cwv, audit_D_project, audit_D_release, UI_FIXES_GRAPH_PERF |
| `audits/i18n.md` | 7 | 6 | AUDIT_E_i18n-rtl-audit |
| `audits/seo.md` | 22 | 3 | audit_D_seo, audit_C_marketing |
| `audits/trends.md` | 21 | 8 | TRENDS_AUDIT |
| `audits/skills.md` | 8 | 0 | SKILLS_AUDIT_ORION, AUDIT_E_SUMMARY |

**Решения по маппингу (отклонение от исходного списка 12 типов):**

- `qa-tests` → `data.md` (секция QA данных) — тесты касаются данных/сборки;
- `security` → `js.md` — security-находки относятся к клиентскому JS;
- `marketing` → `seo.md` — маркетинг и SEO шли одним батчем C;
- `project`/`release` → `perf.md` (секция проект/релиз) — не выделялись в отдельный тип.

### 2. `AUDIT_MASTER.md` переписан

Оставлено только: индекс (`Тип | Открыто | Закрыто | Файл`) и список открытых находок
со ссылками на `audits/*.md`. Удалены §1–§29 и Приложения A–D (перенесены в `audits/` или закрыты).

### 3. `STATE_OF_AUDIT.md` — утрачен

Файла нет в worktree. Ревизия восстановлена в `AUDIT_MASTER.md` по `AUDIT_*`/`STAGE_*`:
ориентир до этапов 1B–8 — **P0 = 0, P1 ≈ 21, P2 ≈ 73**.

## Куда ушёл каждый файл

### `archive/v51/` — эра v5.1–v5.5 (создан до 05.10.2026), 40 файлов

| Файл | Дата создания |
|---|---|
| `A11Y_FIX.md` | ? |
| `ANALYTICS_DECISION.md` | ? |
| `ANALYTICS_TECHDEBT.md` | ? |
| `AUDIT_REPORT.md` | ? |
| `AUDIT_V51.md` | ? |
| `BACKUP_FIX.md` | ? |
| `CLASS_AUDIT.md` | ? |
| `COLORS_AUDIT.md` | ? |
| `COLORS_PLAN_V2.md` | ? |
| `DATA_AUDIT_SKILL.md` | ? |
| `DESIGN_SYSTEM_PLAN.md` | ? |
| `DIAGNOSTIC_FIX.md` | ? |
| `FINAL_REGRESSION.md` | ? |
| `FIX_GSC_FILE.md` | ? |
| `FIX_V51.md` | ? |
| `GRAPH_ACCENT_INVESTIGATION.md` | ? |
| `HEALTH_CHECK.md` | ? |
| `IDEAS_REMOVAL.md` | ? |
| `LEGAL_SKILL.md` | ? |
| `LOCAL_STYLES_INVENTORY.md` | ? |
| `MARKETING_AUDIT.md` | ? |
| `MOBILE_AUDIT.md` | ? |
| `P0_FEEDBACK_DIAGNOSIS.md` | ? |
| `PREPARE_RENAME.md` | ? |
| `PRE_MERGE_CLEANUP.md` | ? |
| `PRODUCT_AUDIT.md` | ? |
| `QA_AUDIT.md` | ? |
| `RENAME_LAYOUT.md` | ? |
| `RENAME_SIDEBAR.md` | ? |
| `RENAME_TAB.md` | ? |
| `SKILLS_INSTALL.md` | ? |
| `SKILLS_RECOMMENDATIONS.md` | ? |
| `SKILLS_REVISION.md` | ? |
| `STEP6_COMMIT.md` | ? |
| `STEP8_CLOSE.md` | ? |
| `STEP8_FINAL.md` | ? |
| `TECHDEBT_UPDATE.md` | ? |
| `UI_UX_AUDIT.md` | ? |
| `VERSION_JS_FIX.md` | ? |
| `VISUAL_DESIGN_AUDIT.md` | ? |

### `archive/v56/` — эра v5.6 (создан с 05.10.2026), 129 файлов

| Файл | Дата создания |
|---|---|
| `AGENT_QUESTIONS_CLOSE.md` | ? |
| `AUDIT_93_MOBILE.md` | ? |
| `AUDIT_A_FINAL.md` | ? |
| `AUDIT_A_SUMMARY.md` | ? |
| `AUDIT_C_FIX.md` | ? |
| `AUDIT_C_SUMMARY.md` | ? |
| `AUDIT_D_SUMMARY.md` | ? |
| `AUDIT_E_SUMMARY.md` | ? |
| `AUDIT_E_accessibility-check.md` | ? |
| `AUDIT_E_data-validation.md` | ? |
| `AUDIT_E_i18n-rtl-audit.md` | ? |
| `AUDIT_E_site-navigation.md` | ? |
| `AUDIT_E_ui-ux-deep-audit.md` | ? |
| `BOM_NORMALIZATION.md` | ? |
| `CI_AND_AUDIT_B.md` | ? |
| `CODEBASE_MEMORY_INSTALL.md` | ? |
| `CODEBASE_MEMORY_RESEARCH.md` | ? |
| `DATA_COMMIT.md` | ? |
| `DATA_LIVE_RUN.md` | ? |
| `DATA_P1_FIX.md` | ? |
| `DELEGATION_RESEARCH.md` | ? |
| `DOCS_AUDIT.md` | ? |
| `DOCS_CLEANUP_AUDIT.md` | ? |
| `DOCS_COMMIT.md` | ? |
| `DOCS_FIX.md` | ? |
| `FALLBACK_PLUGIN.md` | ? |
| `GIT_COURER_SETUP.md` | ? |
| `GIT_MCP_SETUP.md` | ? |
| `GLOSSARY_BOM_INVESTIGATION.md` | ? |
| `GRAPH_DETERMINISM.md` | ? |
| `GRAPH_INTERACTIVITY_FIX.md` | ? |
| `GRAPH_LIVING_FIX.md` | ? |
| `HEADER_STICKY_CLOSE.md` | ? |
| `HEADER_STICKY_FIX.md` | ? |
| `HEADER_UNIFY.md` | ? |
| `HOOK_MIGRATION_v5.6.3.md` | ? |
| `INFRA_CLOSE_FINAL.md` | ? |
| `INFRA_FINAL.md` | ? |
| `LIGHT_THEME_CLOSE.md` | ? |
| `LIGHT_THEME_FIX.md` | ? |
| `LOCAL_DELEGATION.md` | ? |
| `LOCAL_DELEGATION_FINAL.md` | ? |
| `LOCAL_FAST_TUNING.md` | ? |
| `METRIKA_INSTALL.md` | ? |
| `MODAL_ZINDEX_FIX.md` | ? |
| `OFFLINE_CACHE.md` | ? |
| `OLLAMA_REMOVE.md` | ? |
| `ORION_SETUP.md` | ? |
| `P0_P1_COMMIT.md` | ? |
| `P0_P1_FINAL.md` | ? |
| `P0_P1_FIX.md` | ? |
| `PARALLEL_PASS_1.md` | ? |
| `PARALLEL_PASS_2.md` | ? |
| `PARALLEL_PASS_3_PARTIAL.md` | ? |
| `QWEN_FIX.md` | ? |
| `README_FIX.md` | ? |
| `README_FIX_V2.md` | ? |
| `RELEASE_BLOCKERS.md` | ? |
| `SAFEAREA_INFRA.md` | ? |
| `SERENA_DISABLED.md` | ? |
| `SERENA_RESTORE.md` | ? |
| `SKILLS_AUDIT_ORION.md` | ? |
| `SKILLS_BENCHMARK.md` | ? |
| `SNAPSHOT_DIFF_18.md` | ? |
| `SNAPSHOT_MASK.md` | ? |
| `SNAPSHOT_REBUILD_ANALYSIS.md` | ? |
| `SNAPSHOT_REBUILD_RESULT.md` | ? |
| `STAGE1A1_MOBILE.md` | ? |
| `STAGE1A2_HOVER_PNGBTN.md` | ? |
| `STAGE1B_TYPOGRAPHY.md` | ? |
| `STAGE1C_A11Y_I18N.md` | ? |
| `STAGE2_HTML.md` | ? |
| `STAGE3_DIALOGS.md` | ? |
| `STAGE4_DATA.md` | ? |
| `STAGE4_SITEMAP.md` | ? |
| `STAGE5_CANONICAL_RSS.md` | ? |
| `STAGE5_LEGAL.md` | ? |
| `STAGE6_TEMPLATES.md` | ? |
| `STAGE7_SUP.md` | ? |
| `STAGE8A_MISC.md` | ? |
| `STAGE8B_SNAPSHOT_CLEANUP.md` | ? |
| `STICKY_RESTORE.md` | ? |
| `T1_SCALE_CHECK.md` | ? |
| `T1_T5_COMMIT.md` | ? |
| `T1_T5_SNAPSHOT_ANALYSIS.md` | ? |
| `TD_95_UPDATE.md` | ? |
| `TEST_UI_VERIFY.md` | ? |
| `TOKEN_SAVERS_INSTALL.md` | ? |
| `TRENDS_AUDIT.md` | ? |
| `UI_BUGS_v5.6.1.md` | ? |
| `UI_FIXES.md` | ? |
| `UI_FIXES_GRAPH_PERF.md` | ? |
| `USABILITY_AUDIT.md` | ? |
| `V1_CLEANUP.md` | ? |
| `V2_SINGLE_AGENT_SETUP.md` | ? |
| `V561_ARCHIVE.md` | ? |
| `V561_AUDITOR_SERENA.md` | ? |
| `V561_AUDIT_LAUNCH.md` | ? |
| `V561_CLOSE_DOCS.md` | ? |
| `V561_FINAL.md` | ? |
| `V561_GIGACHAT.md` | ? |
| `V561_MERGE_MAIN.md` | ? |
| `V561_Q14_RESTORE.md` | ? |
| `V561_SERENA_FINAL.md` | ? |
| `VENDOR_CLOSE.md` | ? |
| `VENDOR_FINAL.md` | ? |
| `VERSION_FIX_560.md` | ? |
| `VIS_CHART_VENDOR.md` | ? |
| `WORKTREE_MERGE.md` | ? |
| `audit_93_a_webkit45.md` | ? |
| `audit_93_b_sup131.md` | ? |
| `audit_93_c_pwa.md` | ? |
| `audit_93_d_safearea.md` | ? |
| `audit_93_e_orientation.md` | ? |
| `audit_A_cyberaudit.md` | ? |
| `audit_A_data-audit.md` | ? |
| `audit_A_docs-sync.md` | ? |
| `audit_A_legal-compliance.md` | ? |
| `audit_A_qa-deep-audit.md` | ? |
| `audit_B_mobile-deep.md` | ? |
| `audit_B_mobile_raw.md` | ? |
| `audit_C_marketing.md` | ? |
| `audit_C_product.md` | ? |
| `audit_C_visual-design.md` | ? |
| `audit_D_cwv.md` | ? |
| `audit_D_project.md` | ? |
| `audit_D_release.md` | ? |
| `audit_D_seo.md` | ? |
| `legal_questions_for_lawyer.md` | ? |

## Не перемещалось

- Подкаталоги `reports/`: `archive/`, `desktop-screens/`, `evidence/`, `i18n/`, `light/`,
  `light_after_accents/`, `mobile-screens/`, `ux/` — это исходники/скриншоты, не отчёты.
- Не-md артефакты верхнего уровня (json/png/txt, 63 файла) — данные и графики.
- Существующие `archive/v550/` (18) и `archive/v560/` (20) не тронуты.

## Проверки (STOP-условия)

- **Ни один файл не потерян:** 169 перемещено, 0 пропущено, удалений нет.
- **Источник для каждого типа аудита найден** — провалов нет.
- Код проекта, `tests/`, `docs/` не изменялись.

