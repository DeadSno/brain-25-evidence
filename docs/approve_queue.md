# APPROVE-ОЧЕРЕДЬ кандидатов Hedges' g (цикл 4)

> g из абстрактов мета-анализов PubMed (esearch+efetch). В data.json
> НЕ записывается, пока владелец не пометит «ок» в этой таблице.
> |extract_g − PRIOR_G| ≤ 0.1 → колонка «приор совпал» = да.

| добавка | pmid | год | g | CI | исход | сниппет | приор ±0.1 совпал? | владелец |
|---|---|---|---|---|---|---|---|---|
| Кофеин | [42228847](https://pubmed.ncbi.nlm.nih.gov/42228847/) | 2026 | +0.21 | 0.14..0.27 | strength | `An ergogenic effect of caffeinated chewing gum was found for muscular strength (SMD = 0.21; 95% confidence interval [CI]` | ? | ок: outcome strength ✓, форма специфическая (жевательная резинка) |
| Кофеин | [42208612](https://pubmed.ncbi.nlm.nih.gov/42208612/) | 2026 | +0.21 | 0.11..0.29 | performance | `rgogenic effect of caffeine supplementation on cycling performance for females (standardized mean difference = 0.21; 95%` | ? | нет: ложный PMID (МА про омега-3) |
| Кофеин | [41374083](https://pubmed.ncbi.nlm.nih.gov/41374083/) | 2025 | -0.31 | -0.45..-0.17 | power | `95% confidence interval [CI] -0.62, -0.06), followed by moderate-dose capsules (SMD = -0.31; 95% CI: -0.45, -0.17) and m` | ? | нет: инверсия направления (время = обратная шкала) |
