
LANGUAGE_ALIASES: dict[str, str] = {
    "py": "python",
    "python": "python",
    "python3": "python",
    "js": "javascript",
    "javascript": "javascript",
    "node": "javascript",
    "nodejs": "javascript",
    "java": "java",
    "jva": "java",
    "c": "c",
    "cc": "cpp",
    "cpp": "cpp",
    "c++": "cpp",
    "cxx": "cpp",
}

DEFAULT_TIMEOUT_MS = 3_000
MIN_TIMEOUT_MS = 100
MAX_TIMEOUT_MS = 10_000
MAX_STDIN_LENGTH = 10_000

FILE_NAMES: dict[str, str] = {
    "python": "main.py",
    "javascript": "main.js",
    "java": "Main.java",
    "c": "main.c",
    "cpp": "main.cpp",
}


def normalize_language(language: str) -> str:
    normalized = language.lower().strip()
    canonical = LANGUAGE_ALIASES.get(normalized)
    if not canonical:
        raise ValueError(f"Unsupported language: {language}")
    return canonical


def validate_timeout(timeout: float | int | None) -> int:
    if timeout is None:
        return DEFAULT_TIMEOUT_MS

    timeout_ms = int(timeout)
    if timeout_ms < MIN_TIMEOUT_MS or timeout_ms > MAX_TIMEOUT_MS:
        raise ValueError(
            f"Timeout must be between {MIN_TIMEOUT_MS} and {MAX_TIMEOUT_MS} milliseconds"
        )
    return timeout_ms


def validate_stdin(stdin: str | None) -> str:
    value = stdin or ""
    if len(value) > MAX_STDIN_LENGTH:
        raise ValueError(f"stdin exceeds maximum length of {MAX_STDIN_LENGTH} characters")
    return value


def get_source_filename(language: str) -> str:
    canonical = normalize_language(language)
    return FILE_NAMES[canonical]


def get_supported_languages() -> list[str]:
    return list(FILE_NAMES.keys())
