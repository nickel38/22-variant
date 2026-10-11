"""Проверки REPL, парсера и обработки ошибок первого этапа."""

import os
import unittest

from src.shell import CommandError, Shell, parse_command


class ParserTests(unittest.TestCase):
    """Проверить кавычки, переменные и синтаксические ошибки."""

    def test_environment_variables(self) -> None:
        """Переменная окружения раскрывается внутри аргумента."""
        old_value = os.environ.get("PRACTICE_NAME")
        os.environ["PRACTICE_NAME"] = "demo value"
        self.addCleanup(self._restore, old_value)
        self.assertEqual(parse_command('ls "$PRACTICE_NAME"'),
                         ["ls", "demo value"])

    def _restore(self, old_value: str | None) -> None:
        """Восстановить переменную после теста."""
        if old_value is None:
            os.environ.pop("PRACTICE_NAME", None)
        else:
            os.environ["PRACTICE_NAME"] = old_value

    def test_quotes_and_invalid_syntax(self) -> None:
        """Кавычки сохраняют пробелы, незакрытая кавычка ошибочна."""
        self.assertEqual(parse_command('cd "Мои документы"'),
                         ["cd", "Мои документы"])
        with self.assertRaises(CommandError):
            parse_command('cd "без конца')


class ShellTests(unittest.TestCase):
    """Проверить prompt, заглушки, exit и неизвестные команды."""

    def setUp(self) -> None:
        """Создать отдельное состояние оболочки."""
        self.shell = Shell()

    def test_prompt_uses_real_identity(self) -> None:
        """В prompt присутствуют имя пользователя и hostname ОС."""
        prompt = self.shell.prompt()
        self.assertIn(self.shell.username, prompt)
        self.assertIn(self.shell.hostname, prompt)
        self.assertTrue(prompt.endswith(":~$"))

    def test_stubs_and_exit(self) -> None:
        """ls/cd показывают аргументы, exit завершает REPL."""
        self.assertIn("a b", self.shell.execute("ls a b").output)
        self.assertIn("путь", self.shell.execute("cd путь").output)
        self.assertTrue(self.shell.execute("exit").should_exit)

    def test_errors(self) -> None:
        """Неизвестная команда и аргумент exit дают ошибки."""
        for line in ("unknown", "exit now"):
            with self.subTest(line=line):
                with self.assertRaises(CommandError):
                    self.shell.execute(line)


if __name__ == "__main__":
    unittest.main()

