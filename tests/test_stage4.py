"""Проверки основных команд работы с VFS."""

import base64
import tempfile
import unittest
from pathlib import Path

from src.shell import CommandError, Shell
from src.vfs import VirtualFS


class CommandTests(unittest.TestCase):
    """Проверить ls, cd, uptime и who."""

    def setUp(self) -> None:
        """Создать образ с файлами и оболочку."""
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        image = Path(self.temp.name) / "fs.xml"
        payload = base64.b64encode(b"hello").decode()
        image.write_text(
            '<vfs name="test"><directory path="/docs" '
            'owner="alice" group="dev" />'
            f'<file path="/docs/a.txt">{payload}</file>'
            '</vfs>',
            encoding="utf-8",
        )
        self.shell = Shell(vfs=VirtualFS.load(image))

    def test_ls_modes(self) -> None:
        """Обычный и длинный режимы ls показывают VFS."""
        self.assertEqual(self.shell.execute("ls").output, "docs/")
        long_output = self.shell.execute("ls -l /").output
        self.assertIn("d alice dev docs/", long_output)
        self.assertIn("a.txt", self.shell.execute("ls /docs").output)

    def test_cd_and_prompt(self) -> None:
        """cd меняет cwd, принимает .. и отклоняет файл."""
        self.shell.execute("cd /docs")
        self.assertTrue(self.shell.prompt().endswith(":/docs$"))
        self.shell.execute("cd ..")
        self.assertEqual(self.shell.cwd, "/")
        with self.assertRaises(CommandError):
            self.shell.execute("cd /docs/a.txt")

    def test_system_commands(self) -> None:
        """uptime и who возвращают данные текущего процесса и ОС."""
        self.assertRegex(self.shell.execute("uptime").output, r"^up \d+ минут")
        self.assertIn(self.shell.username, self.shell.execute("who").output)
        with self.assertRaises(CommandError):
            self.shell.execute("uptime now")

    def test_path_and_option_errors(self) -> None:
        """Ошибки пути и неизвестные ключи не меняют состояние."""
        with self.assertRaises(CommandError):
            self.shell.execute("ls --bad")
        with self.assertRaises(CommandError):
            self.shell.execute("ls /missing")
        self.assertEqual(self.shell.cwd, "/")


if __name__ == "__main__":
    unittest.main()

