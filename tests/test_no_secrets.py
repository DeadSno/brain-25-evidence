"""Секреты не попадают в репозиторий (F-31, CYBER-P2-02).

Область — файлы, отслеживаемые git, потому что незакоммиченный черновик
никуда не утекает, а закоммиченный уезжает в историю навсегда.

Что уже замеряно и НЕ проверяется здесь, чтобы гейт не стал
ложнотревожным (это не «не заметили», это решение):

  * UUID вида 8-4-4-4-12 — 64 совпадения в `data/papers/papers_slim.json`.
    Это идентификаторы, а не ключи GigaChat Authorization Key, у которых
    та же длина и тот же разделитель. Проверять их шаблоном бессмысленно:
    гейт, дающий 64 ложных срабатывания, отключают целиком.
  * `{env:ИМЯ_ПЕРЕМЕННОЙ}` — ссылки на переменные окружения, их не 2,
    а почти все упоминания ключей в репозитории.
  * `${{ secrets.GITHUB_TOKEN }}` в `.github/workflows/watchdog.yml` —
    корректное обращение к секрету GitHub, а не его значение.
  * `meta name="google-site-verification"` — имя тега, не токен.

Остальное — проверяется. Список форм ниже взят из замеров по репозиторию
и покрывает провайдеров, которыми этот проект пользуется или уже
пользовался: OpenAI/Anthropic-совместимые ключи, GitHub, AWS, Google,
Slack, приватные ключи, JWT и GigaChat Authorization Key.

В конце — отрицательный пример: сканер обязан ловить подставной секрет.
Сканер, который ни на чём не срабатывает, опаснее отсутствующего гейта.
"""
import math
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

#: Куда не смотрим: бинарники и каталоги, которых нет в репозитории.
SKIP_PREFIX = (".git/", "node_modules/")
SKIP_SUFFIX = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".pdf",
               ".zip", ".gz", ".duckdb", ".woff", ".woff2", ".ttf")
#: Экраны и артефакты — большие бинарники, ключа там быть не может.
SKIP_DIR = ("tests/snapshots/", "reports/audits/_artifacts/")

#: Ссылки на переменные окружения и на секреты GitHub — не значения.
ENV_REF = re.compile(
    r"\{env:|\$\{|\$\(|process\.env|os\.environ|secrets\.|"
    r"getenv|ENV\[|env\[|%[A-Z_]+%",
    re.I)

# ── формы токенов провайдеров ──────────────────────────────────────────
VENDOR = {
    "openai": re.compile(r"\bsk-[A-Za-z0-9_\-]{20,}"),
    "github": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}"),
    "github_pat": re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}"),
    "aws_access_key_id": re.compile(r"\b(?:AKIA|ASIA|AGPA|AIDA|AROA)[0-9A-Z]{16}\b"),
    "google_api_key": re.compile(r"\bAIza[0-9A-Za-z_\-]{30,}"),
    "slack": re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}"),
    "stripe": re.compile(r"\b[sr]k_(?:live|test)_[A-Za-z0-9]{16,}"),
    "npm_token": re.compile(r"\bnpm_[A-Za-z0-9]{30,}"),
    "private_key": re.compile(
        r"-----BEGIN\s+(?:RSA\s+|EC\s+|DSA\s+|OPENSSH\s+|PGP\s+)?PRIVATE KEY-----"),
    "jwt": re.compile(r"\beyJ[A-Za-z0-9_\-]{10,}\.eyJ[A-Za-z0-9_\-]{10,}\."),
    # GigaChat: Authorization Key имеет вид 8-4-4-4-12 и выдаётся как
    # `Authorization: Bearer <ключ>`. Проверяем пару «заголовок + UUID»,
    # а не UUID сам по себе — см. исключения в докстринге.
    "gigachat_auth": re.compile(
        r"(?i)authorization\s*[:=]\s*[\"']?(?:bearer\s+)?"
        r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"),
}

# ── общая форма: ключ/пароль/токен, присвоенный строкой ─────────────────
CREDENTIAL_KEY = re.compile(
    r"(?i)(?:[\"']?)(api[_-]?key|apikey|secret|secret[_-]?key|password|passwd|"
    r"auth[_-]?token|access[_-]?token|bearer)[\"']?\s*[:=]\s*[\"']([^\"'\n]{12,})[\"']")
#: Значения, которые не являются секретом, хотя и выглядят как строка.
PLACEHOLDER = re.compile(
    r"(?i)^(?:x{3,}|\*{3,}|\.{3,}|-+|_+|changeme|placeholder|redacted|"
    r"your[_-]?\w+|example|dummy|test[_-]?\w*|<[^>]+>|todo|\$\{.*\}|"
    r"\{\{.*\}\}|%s|%d|none|null|true|false)$")
#: Строки с пробелами — это фразы и предложения, а не токены.
HAS_SPACE = re.compile(r"\s")


def _entropy(s: str) -> float:
    if not s:
        return 0.0
    counts: dict[str, int] = {}
    for ch in s:
        counts[ch] = counts.get(ch, 0) + 1
    n = len(s)
    return -sum((c / n) * math.log2(c / n) for c in counts.values())


def _is_secret_like(value: str) -> bool:
    """Отсеивает фразы, плейсхолдеры и подстановки."""
    v = value.strip()
    if not v or PLACEHOLDER.match(v):
        return False
    if HAS_SPACE.search(v) and len(v) < 40:
        return False
    if ENV_REF.search(v):
        return False
    if len(v) < 12:
        return False
    # Токен обязан быть смешанным: только цифры или только буквы — это
    # идентификатор, версия или дата, а не ключ.
    has_digit = any(c.isdigit() for c in v)
    has_alpha = any(c.isalpha() for c in v)
    if not (has_digit and has_alpha):
        return False
    return _entropy(v) >= 3.0


def scan_text(text: str) -> list[tuple[str, str]]:
    """-> [(правило, совпадение)] по одному тексту. Точка входа для тестов."""
    found: list[tuple[str, str]] = []
    for rule, rx in VENDOR.items():
        for m in rx.finditer(text):
            found.append((rule, m.group(0)))
    for m in CREDENTIAL_KEY.finditer(text):
        value = m.group(2)
        if _is_secret_like(value):
            found.append(("credential_literal", value))
    return found


def _tracked_text_files() -> list[Path]:
    out = subprocess.run(
        ["git", "ls-files", "-z"], cwd=ROOT, capture_output=True,
        text=True, encoding="utf-8", errors="replace",
    ).stdout
    paths = []
    for raw in out.split("\0"):
        if not raw:
            continue
        if raw.startswith(SKIP_PREFIX) or raw.startswith(SKIP_DIR):
            continue
        if raw.lower().endswith(SKIP_SUFFIX):
            continue
        if raw.replace("\\", "/") == Path(__file__).relative_to(ROOT).as_posix():
            # Сканер исключает себя. Здесь лежат УЧЕБНЫЕ образцы: ключ
            # формата GigaChat и UUID, на которых проверяется, что сканер
            # срабатывает на настоящем секрете и молчит на безобидном.
            # Без исключения гейт всегда падал бы на самом себе — и
            # вердикт «секрет в репозитории» указывал бы на файл гейта,
            # а не на утечку. Проверка живости сканера от этого не
            # слабеет: она по-прежнему требует, чтобы ЭТИ образцы были
            # пойманы и чтобы UUID остался тихим.
            continue
        p = ROOT / raw
        if not p.is_file():
            continue
        try:
            p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue           # бинарник — пропускаем
        paths.append(p)
    return paths


def test_tracked_text_files_are_readable():
    """Страховка гейта: если файлы не нашлись, сканировать нечего.

    Без этой проверки пустой список молча дал бы «утечек нет».
    """
    files = _tracked_text_files()
    assert len(files) > 500, (
        f"git вернул всего {len(files)} текстовых файлов — гейт был бы "
        f"зелёным вхолостую. Проверь, что запуск из корня репозитория."
    )


def test_no_secrets_in_repository():
    """Ни одного значения секрета в отслеживаемых файлах."""
    files = _tracked_text_files()
    hits: list[str] = []
    for p in files:
        for rule, match in scan_text(p.read_text(encoding="utf-8")):
            rel = p.relative_to(ROOT).as_posix()
            hits.append("%s :: %s :: %s" % (rule, rel, match[:24]))
    assert not hits, "похожи на секреты:\n  " + "\n  ".join(sorted(hits)[:40])


def test_no_gigachat_authorization_key():
    """Ключ GigaChat в репозиторий не попадал — намеренно.

    Решение владельца от 07.10.2026: ключ был прислан в чат и НЕ записан
    в конфиг, потому что это означало бы положить секрет в открытый
    репозиторий. Гейт держит это решение, а не просто проверяет строку.
    """
    offenders = []
    for p in _tracked_text_files():
        text = p.read_text(encoding="utf-8")
        for m in re.finditer(
            r"(?i)authorization\s*[:=]\s*[\"']?(?:bearer\s+)?"
            r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})",
            text,
        ):
            offenders.append("%s :: %s" % (p.relative_to(ROOT).as_posix(),
                                          m.group(1)[:12]))
    assert not offenders, "ключ GigaChat в репозитории: %s" % offenders


def test_env_references_are_not_secrets():
    """Ссылки на переменные окружения — не утечка. Это не «зелёный вхолостую»."""
    sample = (
        '"apiKey": "{env:OPENROUTER_API_KEY}"\n'
        'token = os.environ["GITHUB_TOKEN"]\n'
        'key: ${{ secrets.GITHUB_TOKEN }}\n'
    )
    assert scan_text(sample) == [], (
        "сканер считает ссылку на переменную окружения секретом — "
        "тогда гейт придётся отключить целиком"
    )


def test_placeholder_values_are_not_secrets():
    sample = (
        'api_key = "xxxxxxxxxxxxxxxx"\n'
        'password = "your-password-here"\n'
        'secret = "<REDACTED>"\n'
        'token = "${GITHUB_TOKEN}"\n'
    )
    assert scan_text(sample) == [], "сканер ловит плейсхолдеры"


def test_scanner_catches_real_secrets():
    """Отрицательный пример: сканер обязан срабатывать. Иначе он мёртв."""
    samples = {
        "openai": "OPENAI_API_KEY = 'sk-abcdefghijklmnopqrstuvwxyz0123456789'",
        "github": "token: ghp_abcdefghijklmnopqrstuvwxyz0123456789",
        "aws": 'AWS_ACCESS_KEY_ID = "AKIAIOSFODNN7EXAMPLE"',
        "google": 'k: "AIzaSyA1234567890abcdefghijklmnopqrstuv"',
        "slack": 'SLACK="xoxb-123456789012-abcdefghijklmno"',
        "private_key": "-----BEGIN RSA PRIVATE KEY-----",
        "jwt": "t=eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.ab",
        "gigachat": "Authorization: Bearer 12345678-1234-1234-1234-123456789012",
        "literal": 'db = {"password": "Xy7!kQ2mLp9wZ4tRv"}',
    }
    misses = [name for name, text in samples.items() if not scan_text(text)]
    assert not misses, ("сканер промустил: {misses}. Сменить шаблон проверки.")


def test_uuid_is_not_a_secret():
    """Зафиксированное исключение — как измерение, а не как догадка.

    64 таких идентификатора лежат в data/papers/papers_slim.json. Если
    когда-нибудь понадобится их проверять, это делается по списку полей
    данных, а не по форме строки.
    """
    assert scan_text('"id": "a314704f-dd72-4295-9ec0-3cdcda7bd826"') == []
