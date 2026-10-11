"""Проверки изменения владельцев только в памяти."""

import tempfile
import unittest
from pathlib import Path

from src.shell import CommandError, Shell
from src.vfs import VirtualFS


class ChownTests(unittest.TestCase):
    """Проверить обычный и рекурсивный режимы chown."""

    def setUp(self) -> None:
        """Загрузить образ и запомнить исходный XML."""
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.image = Path(self.temp.name) / "fs.xml"
        self.image.write_text(
            '<vfs><directory path="/docs" owner="old" group="old" />'
            '<file path="/docs/a" owner="old" group="old">QQ==</file>'
            '<file path="/top" owner="top" group="top">Qg==</file></vfs>',
            encoding="utf-8",
        )
        self.before = self.image.read_bytes()
        self.shell = Shell(vfs=VirtualFS.load(self.image))

    def test_single_and_partial_owner(self) -> None:
        """OWNER:GROUP меняет обе части, OWNER только владельца."""
        self.shell.execute("chown alice:staff /top")
        node = self.shell.vfs.get("/top")
        self.assertEqual((node.owner, node.group), ("alice", "staff"))
        self.shell.execute("chown bob /top")
        self.assertEqual((node.owner, node.group), ("bob", "staff"))

    def test_recursive_and_source_unchanged(self) -> None:
        """Ключ -R меняет дерево, исходный XML на диске не меняется."""
        self.shell.execute("chown -R alice:dev /docs")
        for path in ("/docs", "/docs/a"):
            node = self.shell.vfs.get(path)
            self.assertEqual((node.owner, node.group), ("alice", "dev"))
        self.assertEqual(self.image.read_bytes(), self.before)

    def test_invalid_arguments(self) -> None:
        """Пустые спецификации и ключи отклоняются.

        Отсутствующие пути также должны давать ошибку.
        """
        for line in ("chown", "chown : /top", "chown a:b:c /top",
                     "chown -x alice /top", "chown alice /missing"):
            with self.subTest(line=line):
                with self.assertRaises(CommandError):
                    self.shell.execute(line)


if __name__ == "__main__":
    unittest.main()

