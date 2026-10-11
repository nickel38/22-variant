"""XML-образ виртуальной файловой системы.

Данные после загрузки хранятся только в памяти.
"""

from __future__ import annotations

import base64
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import posixpath
import xml.etree.ElementTree as ElementTree


class VFSError(ValueError):
    """Ошибка чтения XML-образа или обращения к виртуальному пути."""


@dataclass
class Node:
    """Файл или каталог с метаданными и base64-содержимым файла."""

    directory: bool
    content: str = ""
    owner: str = "root"
    group: str = "root"
    modified: datetime = field(default_factory=datetime.now)

    def data(self) -> bytes:
        """Декодировать содержимое файла в байты."""
        if self.directory:
            raise VFSError("каталог не содержит данных")
        try:
            return base64.b64decode(self.content, validate=True)
        except (ValueError, TypeError) as error:
            raise VFSError("повреждённые base64-данные") from error


class VirtualFS:
    """Дерево узлов; исходный XML после загрузки не изменяется."""

    def __init__(self, name: str = "empty") -> None:
        """Создать пустой корневой каталог."""
        self.name = name
        self.nodes: dict[str, Node] = {"/": Node(directory=True)}

    @classmethod
    def load(cls, path: Path) -> "VirtualFS":
        """Загрузить и проверить XML, не распаковывая данные на диск."""
        try:
            document = ElementTree.parse(path)
        except FileNotFoundError as error:
            raise VFSError(f"VFS не найдена: {path}") from error
        except (OSError, ElementTree.ParseError) as error:
            raise VFSError(f"ошибка чтения XML VFS {path}: {error}") from error
        root = document.getroot()
        if root.tag != "vfs":
            raise VFSError("корневой элемент VFS должен быть <vfs>")
        name = root.attrib.get("name", path.stem).strip()
        if not name:
            raise VFSError("имя VFS не может быть пустым")
        filesystem = cls(name)
        for element in root:
            filesystem._load_element(element)
        return filesystem

    def _load_element(self, element: ElementTree.Element) -> None:
        """Добавить один XML-элемент и его родительские каталоги."""
        if element.tag not in {"directory", "file"}:
            raise VFSError(f"неизвестный элемент VFS: {element.tag}")
        raw_path = element.attrib.get("path")
        if raw_path is None:
            raise VFSError(f"у элемента {element.tag} отсутствует path")
        path = self._stored_path(raw_path, element.tag == "directory")
        owner = element.attrib.get("owner", "root")
        group = element.attrib.get("group", "root")
        self._check_identity(owner, "owner")
        self._check_identity(group, "group")
        self._ensure_parent(path)
        if path in self.nodes:
            raise VFSError(f"повторяющийся путь VFS: {path}")
        content = ""
        if element.tag == "file":
            if element.attrib.get("encoding", "base64") != "base64":
                raise VFSError("файлы VFS должны использовать encoding=base64")
            content = "".join(element.itertext()).strip()
            try:
                base64.b64decode(content, validate=True)
            except (ValueError, TypeError) as error:
                raise VFSError(f"неверные base64-данные файла: {path}") from error
        self.nodes[path] = Node(element.tag == "directory", content, owner, group)

    @staticmethod
    def _check_identity(value: str, label: str) -> None:
        """Проверить непустое имя владельца или группы."""
        if not value or any(char.isspace() for char in value):
            raise VFSError(f"некорректный {label} VFS")

    @staticmethod
    def _stored_path(raw_path: str, directory: bool) -> str:
        """Нормализовать абсолютный путь XML.

        Выход за корень запрещён.
        """
        if not raw_path or not raw_path.startswith("/"):
            raise VFSError(f"путь VFS должен быть абсолютным: {raw_path!r}")
        if "\\" in raw_path or "\x00" in raw_path:
            raise VFSError(f"недопустимый путь VFS: {raw_path!r}")
        parts = raw_path.split("/")
        if ".." in parts:
            raise VFSError(f"выход за корень VFS: {raw_path!r}")
        path = posixpath.normpath(raw_path)
        if path == "/" and not directory:
            raise VFSError("корень VFS должен быть каталогом")
        return path

    def _ensure_parent(self, path: str) -> None:
        """Создать отсутствующих родителей или обнаружить конфликт.

        Файл не может быть родителем другого узла.
        """
        parent = posixpath.dirname(path)
        if parent == "/":
            return
        self._ensure_parent(parent)
        existing = self.nodes.get(parent)
        if existing is not None:
            if not existing.directory:
                raise VFSError(f"файл используется как каталог: {parent}")
            return
        self.nodes[parent] = Node(directory=True)

    def resolve(self, path: str, cwd: str = "/") -> str:
        """Разрешить абсолютный или относительный путь внутри VFS."""
        if not path:
            raise VFSError("пустой путь")
        if not cwd.startswith("/"):
            raise VFSError("текущий путь должен быть абсолютным")
        combined = path if path.startswith("/") else posixpath.join(cwd, path)
        return "/" + posixpath.normpath(combined).lstrip("/")

    def get(self, path: str) -> Node:
        """Вернуть узел или сообщить о несуществующем пути."""
        try:
            return self.nodes[path]
        except KeyError as error:
            raise VFSError(f"путь не найден: {path}") from error

    def children(self, path: str) -> list[str]:
        """Вернуть отсортированные имена непосредственных детей.

        Путь должен указывать на каталог.
        """
        if not self.get(path).directory:
            raise VFSError(f"не каталог: {path}")
        return sorted(
            posixpath.basename(candidate)
            for candidate in self.nodes
            if candidate != "/" and posixpath.dirname(candidate) == path
        )

    def text(self, path: str) -> str:
        """Прочитать UTF-8 файл из памяти."""
        try:
            return self.get(path).data().decode("utf-8")
        except UnicodeError as error:
            raise VFSError(f"файл не является UTF-8 текстом: {path}") from error

