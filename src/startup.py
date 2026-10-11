"""Исполнение стартовых скриптов эмулятора."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from .shell import CommandError, Shell

Writer = Callable[[str, str], None]


@dataclass(frozen=True)
class StartupResult:
    """Результат чтения и исполнения стартового файла."""

    failed: bool = False
    should_exit: bool = False


def _read_lines(path: Path, write: Writer) -> list[str] | None:
    """Прочитать UTF-8 файл и сообщить об ошибке чтения."""
    try:
        return path.read_text(encoding="utf-8-sig").splitlines()
    except (OSError, UnicodeError) as error:
        write(f"Ошибка чтения стартового скрипта {path}: {error}", "error")
        return None


def run_startup(path: Path, shell: Shell, write: Writer) -> StartupResult:
    """Показать диалог скрипта и остановиться после первой ошибки."""
    lines = _read_lines(path, write)
    if lines is None:
        return StartupResult(failed=True)
    write(f"Стартовый скрипт: {path}", "info")
    for number, line in enumerate(lines, start=1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        write(f"{shell.prompt()} {line}", "input")
        try:
            result = shell.execute(line)
        except CommandError as error:
            write(f"Ошибка в строке {number}: {error}", "error")
            write("Выполнение скрипта остановлено.", "error")
            return StartupResult(failed=True)
        if result.output:
            write(result.output, "output")
        if result.should_exit:
            return StartupResult(should_exit=True)
    write("Стартовый скрипт завершён.", "info")
    return StartupResult()

