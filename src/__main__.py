"""Точка входа консольного эмулятора."""

from __future__ import annotations

import sys

from .config import parse_config
from .shell import CommandError, Shell
from .startup import run_startup
from .vfs import VFSError, VirtualFS


def run_repl(shell: Shell) -> int:
    """Запустить интерактивный REPL до `exit`, EOF или прерывания."""
    print(
        "Эмулятор оболочки, этап 1. Команды: ls, cd, exit."
    )
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


def _write(text: str, tag: str) -> None:
    """Вывести сообщение стартового скрипта с учётом его типа."""
    stream = sys.stderr if tag == "error" else sys.stdout
    print(text, file=stream)


def main(arguments: list[str] | None = None) -> int:
    """Разобрать конфигурацию, выполнить скрипт и запустить REPL."""
    config = parse_config(arguments)
    print("Конфигурация запуска:")
    print(config.describe())
    try:
        filesystem = (VirtualFS.load(config.vfs_path)
                      if config.vfs_path else VirtualFS())
    except VFSError as error:
        print(f"Ошибка загрузки VFS: {error}", file=sys.stderr)
        return 1
    shell = Shell(config.as_dict(), filesystem)
    if config.startup_path is not None:
        result = run_startup(config.startup_path, shell, _write)
        if result.failed:
            return 1
        if result.should_exit or not sys.stdin.isatty():
            return 0
    return run_repl(shell)


if __name__ == "__main__":
    raise SystemExit(main())

