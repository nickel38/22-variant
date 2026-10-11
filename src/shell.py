"""Разбор команд и минимальное состояние REPL."""

from __future__ import annotations

import os
import re
import shlex
from dataclasses import dataclass


class CommandError(ValueError):
    """Ошибка синтаксиса или выполнения команды."""


@dataclass(frozen=True)
class CommandResult:
    """Результат команды и признак завершения REPL."""

    output: str = ""
    should_exit: bool = False


def expand_variables(value: str) -> str:
    """Раскрыть `$NAME` и `${NAME}` значениями окружения ОС."""
    pattern = re.compile(r"\$(?:\{([A-Za-z_][A-Za-z0-9_]*)\}|"
                         r"([A-Za-z_][A-Za-z0-9_]*))")

    def replace(match: re.Match[str]) -> str:
        """Вернуть значение одной переменной или пустую строку."""
        name = match.group(1) or match.group(2)
        return os.environ.get(name, "")

    return pattern.sub(replace, value)


def parse_command(line: str) -> list[str]:
    """Разобрать команду с кавычками и раскрытием переменных."""
    try:
        tokens = shlex.split(line, comments=False, posix=True)
    except ValueError as error:
        raise CommandError("ошибка кавычек или экранирования") from error
    return [expand_variables(token) for token in tokens]


class Shell:
    """Состояние прототипа оболочки с командами-заглушками."""

    def __init__(self) -> None:
        """Сохранить имя пользователя и узла реальной ОС."""
        self.username = os.environ.get("USER", "user")
        self.hostname = os.uname().nodename

    def prompt(self) -> str:
        """Сформировать приглашение на основе реальных данных ОС."""
        return f"{self.username}@{self.hostname}:~$"

    def execute(self, line: str) -> CommandResult:
        """Выполнить команду первого этапа или сообщить об ошибке."""
        tokens = parse_command(line)
        if not tokens:
            return CommandResult()
        command, *arguments = tokens
        if command == "exit":
            if arguments:
                raise CommandError("использование: exit")
            return CommandResult("Завершение работы.", should_exit=True)
        if command not in {"ls", "cd"}:
            raise CommandError(f"неизвестная команда: {command}")
        details = " ".join(arguments) or "(без аргументов)"
        return CommandResult(f"{command}: {details}")

