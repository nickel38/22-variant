"""Параметры запуска эмулятора."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Config:
    """Пути к образу VFS и стартовому скрипту."""

    vfs_path: Path | None = None
    startup_path: Path | None = None

    def as_dict(self) -> dict[str, str]:
        """Вернуть параметры в формате ключ-значение."""
        return {
            "vfs": str(self.vfs_path or "<не задан>") ,
            "startup": str(self.startup_path or "<не задан>"),
        }

    def describe(self) -> str:
        """Сформировать отладочный вывод всех параметров."""
        return "\n".join(f"{key}={value}" for key, value in self.as_dict().items())


def parse_config(arguments: list[str] | None = None) -> Config:
    """Разобрать параметры командной строки."""
    parser = argparse.ArgumentParser(
        description="Эмулятор оболочки, практическая работа №1, вариант 22.",
    )
    parser.add_argument("--vfs", type=Path, metavar="PATH",
                        help="путь к XML-образу VFS")
    parser.add_argument("--startup", type=Path, metavar="PATH",
                        help="путь к стартовому скрипту")
    options = parser.parse_args(arguments)
    return Config(options.vfs, options.startup)

