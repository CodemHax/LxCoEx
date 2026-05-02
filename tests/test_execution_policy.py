import asyncio
import tempfile
import unittest
from unittest.mock import patch

from app.core.code_sanitizer import sanitize_code
from app.core.config import settings
from app.core.excute_engine import (
    _build_docker_create_command,
    execute_code,
    get_runtime,
    validate_execution_environment,
)
from app.core.execution_policy import (
    MAX_TIMEOUT_MS,
    get_source_filename,
    normalize_language,
    validate_stdin,
    validate_timeout,
)
from app.core.templates import get_template
from app.models.code_input_model import CodeInput


class ExecutionPolicyTests(unittest.TestCase):
    def test_language_aliases_are_normalized(self):
        self.assertEqual(normalize_language("js"), "javascript")
        self.assertEqual(normalize_language("TS"), "typescript")
        self.assertEqual(normalize_language("c++"), "cpp")
        self.assertEqual(normalize_language("golang"), "go")
        self.assertEqual(normalize_language("jva"), "java")

    def test_unknown_language_is_rejected(self):
        with self.assertRaises(ValueError):
            normalize_language("ruby")

    def test_timeout_limits_are_enforced(self):
        self.assertEqual(validate_timeout(3000), 3000)
        with self.assertRaises(ValueError):
            validate_timeout(MAX_TIMEOUT_MS + 1)

    def test_stdin_limits_are_enforced(self):
        self.assertEqual(validate_stdin("hello"), "hello")
        with self.assertRaises(ValueError):
            validate_stdin("x" * 10001)

    def test_template_uses_canonical_language(self):
        self.assertIn("console.log", get_template("js"))
        self.assertIn("public class Main", get_template("jva"))

    def test_model_validates_and_normalizes(self):
        model = CodeInput(code="console.log('ok')", language="node", timeout=1500, stdin=None)
        self.assertEqual(model.language, "javascript")
        self.assertEqual(model.timeout, 1500)
        self.assertEqual(model.stdin, "")

    def test_sanitizer_rejects_unsupported_languages(self):
        is_safe, message = sanitize_code("puts 'hi'", "ruby")
        self.assertFalse(is_safe)
        self.assertIn("Unsupported language", message)

    def test_source_filename_matches_language(self):
        self.assertEqual(get_source_filename("typescript"), "main.ts")
        self.assertEqual(get_source_filename("java"), "Main.java")

    def test_runtime_listing_uses_engine_metadata(self):
        runtimes = asyncio.run(get_runtime())
        python_runtime = next(runtime for runtime in runtimes if runtime["language"] == "python")
        self.assertEqual(python_runtime["version"], "sandbox")
        self.assertIn("available", python_runtime)
        self.assertIn("missing_commands", python_runtime)
        self.assertEqual(python_runtime["engine"], settings.EXECUTION_ENGINE)

    def test_local_python_execution_is_disabled_by_default(self):
        with patch.object(settings, "EXECUTION_ENGINE", "local"):
            with patch.object(settings, "EXECUTION_ALLOW_LOCAL", False):
                with self.assertRaises(RuntimeError):
                    asyncio.run(execute_code("print('ok')", "python", timeout=2000))

    def test_docker_command_uses_hardened_sandbox_flags(self):
        with tempfile.TemporaryDirectory():
            command = _build_docker_create_command("python", 3000)
        self.assertIn("create", command)
        self.assertIn("--network", command)
        self.assertIn("none", command)
        self.assertIn("--read-only", command)
        self.assertIn("--user", command)
        self.assertIn("--memory-swap", command)
        self.assertIn("--ulimit", command)
        self.assertIn("--tmpfs", command)
        self.assertIn(settings.EXECUTION_SANDBOX_IMAGE, command)

    def test_validate_execution_environment_rejects_non_docker_in_strict_mode(self):
        with patch.object(settings, "EXECUTION_REQUIRE_SANDBOX", True):
            with patch.object(settings, "EXECUTION_ENGINE", "local"):
                with self.assertRaises(RuntimeError):
                    validate_execution_environment()


if __name__ == "__main__":
    unittest.main()
