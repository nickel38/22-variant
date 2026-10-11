"""Точка входа консольного эмулятора."""

from __future__ import annotations

import sys

from .shell import CommandError, Shell


def run_repl(shell: Shell) -> int:
    """Запустить интерактивный REPL до `exit`, EOF или прерывания."""
    print("Эмулятор оболочки, этап 1. Команды: ls, cd, exit.")
    while True:
        try:
            line = input(f"{shell.prompt()} ")
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        try:
            result = shell.execute(line)
        except CommandError as error:
            print(f"Ошибка: {error}", file=sys.stderr)
            continue
        if result.output:
            print(result.output)
        if result.should_exit:
            return 0


def main() -> int:
    """Создать оболочку и передать управление REPL."""
    return run_repl(Shell())


if __name__ == "__main__":
    raise SystemExit(main())

