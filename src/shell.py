"""Разбор команд и минимальное состояние REPL."""

from __future__ import annotations

import os
import re
import shlex
from datetime import datetime
from dataclasses import dataclass
import posixpath
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .vfs import VirtualFS

from .vfs import VFSError


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

    def __init__(self, configuration: dict[str, str] | None = None,
                 vfs: "VirtualFS | None" = None) -> None:
        """Сохранить имя пользователя и узла реальной ОС."""
        self.username = os.environ.get("USER", "user")
        self.hostname = os.uname().nodename
        self.configuration = configuration or {}
        self.vfs = vfs
        self.cwd = "/"
        self.started = time.monotonic()
        self.login_time = datetime.now()

    def prompt(self) -> str:
        """Сформировать приглашение на основе реальных данных ОС."""
        display_path = "~" if self.cwd == "/" else self.cwd
        return f"{self.username}@{self.hostname}:{display_path}$"

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
        if command == "conf-dump":
            if arguments:
                raise CommandError("использование: conf-dump")
            return CommandResult(self._dump_configuration())
        if command == "ls":
            return self._ls(arguments)
        if command == "cd":
            return self._cd(arguments)
        if command == "uptime":
            return self._uptime(arguments)
        if command == "who":
            return self._who(arguments)
        raise CommandError(f"неизвестная команда: {command}")

    def _ls(self, arguments: list[str]) -> CommandResult:
        """Вывести содержимое каталогов или сведения о файлах."""
        if self.vfs is None:
            details = " ".join(arguments) or "(без аргументов)"
            return CommandResult(f"ls: {details}")
        long_format, paths = self._ls_options(arguments)
        paths = paths or ["."]
        sections: list[str] = []
        for path in paths:
            sections.append(self._list_path(path, long_format, len(paths) > 1))
        return CommandResult("\n".join(section for section in sections if section))

    @staticmethod
    def _ls_options(arguments: list[str]) -> tuple[bool, list[str]]:
        """Разобрать поддерживаемые ключи ls."""
        long_format = False
        paths: list[str] = []
        for argument in arguments:
            if argument in {"-l", "--long"}:
                long_format = True
            elif argument.startswith("-"):
                raise CommandError(f"неизвестный ключ ls: {argument}")
            else:
                paths.append(argument)
        return long_format, paths

    def _list_path(self, raw_path: str, long_format: bool,
                   show_header: bool) -> str:
        """Сформировать вывод одного пути ls."""
        path, node = self._node(raw_path)
        if not node.directory:
            return self._entry(path, posixpath.basename(path), node, long_format)
        names = self.vfs.children(path)
        lines = [self._entry(
            posixpath.join(path, name), name, self.vfs.get(
                posixpath.join(path, name)
            ), long_format
        ) for name in names]
        if show_header:
            return "\n".join([f"{raw_path}:", *lines])
        return "\n".join(lines)

    @staticmethod
    def _entry(path: str, name: str, node: object, long_format: bool) -> str:
        """Отформатировать одну запись ls."""
        directory = getattr(node, "directory")
        shown_name = name + "/" if directory else name
        if not long_format:
            return shown_name
        marker = "d" if directory else "-"
        return f"{marker} {getattr(node, 'owner')} {getattr(node, 'group')} " \
               f"{shown_name}"

    def _cd(self, arguments: list[str]) -> CommandResult:
        """Перейти в каталог VFS и обновить prompt."""
        if self.vfs is None:
            details = " ".join(arguments) or "(без аргументов)"
            return CommandResult(f"cd: {details}")
        if len(arguments) > 1:
            raise CommandError("использование: cd [путь]")
        raw_path = arguments[0] if arguments else "/"
        path, node = self._node(raw_path)
        if not node.directory:
            raise CommandError(f"cd: не каталог: {raw_path}")
        self.cwd = path
        return CommandResult()

    def _uptime(self, arguments: list[str]) -> CommandResult:
        """Показать время работы текущего процесса-эмулятора."""
        if arguments:
            raise CommandError("использование: uptime")
        seconds = max(0, int(time.monotonic() - self.started))
        minutes, remainder = divmod(seconds, 60)
        return CommandResult(f"up {minutes} минут, {remainder} секунд")

    def _who(self, arguments: list[str]) -> CommandResult:
        """Показать текущего пользователя и время запуска оболочки."""
        if arguments:
            raise CommandError("использование: who")
        timestamp = self.login_time.strftime("%Y-%m-%d %H:%M")
        return CommandResult(f"{self.username} pts/0 {timestamp}")

    def _node(self, raw_path: str) -> tuple[str, object]:
        """Разрешить путь и преобразовать ошибку VFS в ошибку команды."""
        try:
            path = self.vfs.resolve(raw_path, self.cwd)
            return path, self.vfs.get(path)
        except VFSError as error:
            raise CommandError(str(error)) from error

    def _dump_configuration(self) -> str:
        """Сериализовать параметры запуска в формате ключ-значение."""
        if not self.configuration:
            return "Конфигурация не задана."
        return "\n".join(
            f"{key}={value}" for key, value in self.configuration.items()
        )

