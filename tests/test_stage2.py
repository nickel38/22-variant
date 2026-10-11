"""Проверки конфигурации и стартовых сценариев второго этапа."""

import tempfile
import unittest
from pathlib import Path

from src.config import Config, parse_config
from src.shell import Shell
from src.startup import run_startup


class ConfigTests(unittest.TestCase):
    """Проверить параметры командной строки и conf-dump."""

    def test_paths_and_defaults(self) -> None:
        """Пути сохраняются, а значения по умолчанию отображаются."""
        config = parse_config(["--vfs", "a.xml", "--startup", "run.txt"])
        self.assertEqual(config, Config(Path("a.xml"), Path("run.txt")))
        self.assertIn("vfs=a.xml", config.describe())
        self.assertIn("startup=run.txt", config.describe())

    def test_conf_dump_command(self) -> None:
        """Служебная команда возвращает все заданные ключи."""
        result = Shell({"vfs": "a.xml", "startup": "run.txt"}).execute(
            "conf-dump"
        )
        self.assertEqual(result.output, "vfs=a.xml\nstartup=run.txt")


class StartupTests(unittest.TestCase):
    """Проверить диалог, остановку на ошибке и exit."""

    def setUp(self) -> None:
        """Создать временный стартовый файл и буфер сообщений."""
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "startup.txt"
        self.messages: list[tuple[str, str]] = []

    def write(self, text: str, tag: str) -> None:
        """Сохранить сообщение вместо печати в терминал."""
        self.messages.append((text, tag))

    def test_first_error_stops_script(self) -> None:
        """Команда после первой ошибки не выполняется."""
        self.path.write_text("ls\nunknown\nls after\n", encoding="utf-8")
        result = run_startup(self.path, Shell(), self.write)
        text = "\n".join(message for message, _ in self.messages)
        self.assertTrue(result.failed)
        self.assertIn("Выполнение скрипта остановлено", text)
        self.assertNotIn("after", text)

    def test_exit_stops_successfully(self) -> None:
        """Команда exit завершает сценарий без ошибки."""
        self.path.write_text("ls\nexit\nunknown\n", encoding="utf-8")
        result = run_startup(self.path, Shell(), self.write)
        self.assertTrue(result.should_exit)
        self.assertFalse(result.failed)

    def test_missing_file_is_reported(self) -> None:
        """Отсутствующий стартовый файл возвращает ошибку."""
        result = run_startup(self.path, Shell(), self.write)
        self.assertTrue(result.failed)
        self.assertEqual(self.messages[-1][1], "error")


if __name__ == "__main__":
    unittest.main()

