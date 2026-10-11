"""Проверки XML VFS, base64 и работы только в памяти."""

import base64
from pathlib import Path
import tempfile
import unittest

from src.vfs import VFSError, VirtualFS


class VFSTests(unittest.TestCase):
    """Проверить загрузку, пути, типы узлов и ошибки формата."""

    def setUp(self) -> None:
        """Подготовить временный каталог с XML-файлом."""
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "image.xml"

    def write(self, content: str) -> VirtualFS:
        """Записать XML и загрузить его в память."""
        self.path.write_text(content, encoding="utf-8")
        return VirtualFS.load(self.path)

    def test_empty_and_nested_files(self) -> None:
        """Пустой, вложенный и двоичный файл корректно читаются."""
        fs = self.write(
            '<vfs name="demo"><file path="/a/b.txt">'
            f'{base64.b64encode("Текст".encode()).decode()}'
            '</file><file path="/raw.bin">AP+A</file></vfs>'
        )
        self.assertEqual(fs.name, "demo")
        self.assertEqual(fs.children("/"), ["a", "raw.bin"])
        self.assertEqual(fs.text("/a/b.txt"), "Текст")
        self.assertEqual(fs.get("/raw.bin").data(), bytes([0, 255, 128]))

    def test_paths_and_metadata(self) -> None:
        """Относительный путь разрешается от cwd.

        Метаданные владельца сохраняются.
        """
        fs = self.write(
            '<vfs><directory path="/docs" owner="alice" group="dev" />'
            '</vfs>'
        )
        node = fs.get(fs.resolve("..", "/docs/sub"))
        self.assertEqual((node.owner, node.group), ("alice", "dev"))
        self.assertEqual(fs.resolve("../../", "/"), "/")

    def test_invalid_sources(self) -> None:
        """Отсутствующий и повреждённый XML отклоняются.

        Небезопасные пути также должны приводить к ошибке.
        """
        with self.assertRaises(VFSError):
            VirtualFS.load(self.path)
        for content in (
            "<broken>",
            "<root />",
            '<vfs><file path="../outside">QQ==</file></vfs>',
            '<vfs><file path="/bad">%%% </file></vfs>',
        ):
            with self.subTest(content=content):
                with self.assertRaises(VFSError):
                    self.write(content)

    def test_conflicts_and_operations(self) -> None:
        """Конфликты узлов и операции с неверным типом дают ошибки."""
        cases = (
            '<vfs><file path="/x">QQ==</file><file path="/x">Qg==</file></vfs>',
            '<vfs><file path="/x">QQ==</file><file path="/x/y">Qg==</file></vfs>',
        )
        for content in cases:
            with self.assertRaises(VFSError):
                self.write(content)
        fs = self.write('<vfs><file path="/x">QQ==</file></vfs>')
        with self.assertRaises(VFSError):
            fs.children("/x")


if __name__ == "__main__":
    unittest.main()

