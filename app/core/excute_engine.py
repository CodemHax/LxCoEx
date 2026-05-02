import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from app.core.config import settings
from app.core.execution_policy import (
    get_source_filename,
    get_supported_languages,
    normalize_language,
    validate_stdin,
    validate_timeout,
)
from app.models.runtime_model import RuntimeInfo, RuntimeSpec


RUNTIME_SPECS: dict[str, RuntimeSpec] = {
    "python":     RuntimeSpec(language="python",     runtime="CPython",    aliases=("py", "python3")),
    "javascript": RuntimeSpec(language="javascript", runtime="Node.js",    aliases=("js", "node", "nodejs")),
    "typescript": RuntimeSpec(language="typescript", runtime="TypeScript", aliases=("ts",)),
    "go":         RuntimeSpec(language="go",         runtime="Go",         aliases=("golang",)),
    "java":       RuntimeSpec(language="java",       runtime="OpenJDK",    aliases=("jva",)),
    "c":          RuntimeSpec(language="c",          runtime="GCC"),
    "cpp":        RuntimeSpec(language="cpp",        runtime="G++",        aliases=("c++", "cc", "cxx")),
}


def docker_available() -> bool:
    return shutil.which(settings.EXECUTION_DOCKER_BINARY) is not None


def sandbox_image_present() -> bool:
    if not docker_available():
        return False
    try:
        result = subprocess.run(
            [settings.EXECUTION_DOCKER_BINARY, "image", "inspect", settings.EXECUTION_SANDBOX_IMAGE],
            capture_output=True,
            timeout=15,
        )
        return result.returncode == 0
    except Exception:
        return False


def build_docker_create_command(language: str, timeout_ms: int) -> list[str]:
    source_name = get_source_filename(language)
    return [
        settings.EXECUTION_DOCKER_BINARY, "create",
        "--interactive",
        "--network", "none",
        "--read-only",
        "--user", f"{settings.EXECUTION_SANDBOX_UID}:{settings.EXECUTION_SANDBOX_GID}",
        "--workdir", "/workspace",
        "--cap-drop", "ALL",
        "--security-opt", "no-new-privileges:true",
        "--pids-limit", str(settings.EXECUTION_SANDBOX_PIDS_LIMIT),
        "--memory", settings.EXECUTION_SANDBOX_MEMORY,
        "--memory-swap", settings.EXECUTION_SANDBOX_MEMORY_SWAP,
        "--cpus", str(settings.EXECUTION_SANDBOX_CPUS),
        "--ulimit", f"nofile={settings.EXECUTION_SANDBOX_NOFILE}:{settings.EXECUTION_SANDBOX_NOFILE}",
        "--ulimit", f"fsize={settings.EXECUTION_SANDBOX_FSIZE}:{settings.EXECUTION_SANDBOX_FSIZE}",
        "--tmpfs", f"/tmp:rw,noexec,nosuid,size={settings.EXECUTION_SANDBOX_TMP_SIZE}",
        "--tmpfs", f"/input:rw,noexec,nosuid,size={settings.EXECUTION_SANDBOX_INPUT_SIZE}",
        "--tmpfs", f"/workspace:rw,exec,nosuid,size={settings.EXECUTION_SANDBOX_WORKSPACE_SIZE}",
        settings.EXECUTION_SANDBOX_IMAGE,
        "python", "/sandbox/runner.py",
        "--language", language,
        "--source", f"/input/{source_name}",
        "--timeout-ms", str(timeout_ms),
        "--compile-timeout-ms", str(settings.EXECUTION_COMPILE_TIMEOUT_MS),
    ]


def run_docker(command: list[str], cwd: Path, stdin: str = "", timeout_ms: int = 15_000) -> dict:
    try:
        proc = subprocess.run(
            command,
            input=stdin.encode("utf-8"),
            capture_output=True,
            cwd=str(cwd),
            timeout=timeout_ms / 1000,
        )
        stdout = proc.stdout.decode("utf-8", errors="replace")
        stderr = proc.stderr.decode("utf-8", errors="replace")
        return {"stdout": stdout, "stderr": stderr, "code": proc.returncode}
    except subprocess.TimeoutExpired:
        return {"stdout": "", "stderr": f"Docker command timed out after {timeout_ms} ms", "code": -1}
    except FileNotFoundError:
        return {"stdout": "", "stderr": f"Docker binary not found: {settings.EXECUTION_DOCKER_BINARY}", "code": 127}


def build_error_result(language: str, message: str) -> dict:
    stub = {"stdout": "", "stderr": message, "code": 1}
    return {
        "language": language,
        "version": "sandbox",
        "engine": "docker",
        "error": True,
        "message": message,
        "compile": stub,
        "run": stub,
    }


async def execute_code(code: str, language: str, timeout: int = 3000, stdin: str = "") -> dict:
    import asyncio

    language = normalize_language(language)
    timeout  = validate_timeout(timeout)
    stdin    = validate_stdin(stdin)

    if not docker_available():
        return build_error_result(language, f"Docker binary not found: {settings.EXECUTION_DOCKER_BINARY}")
    if not sandbox_image_present():
        return build_error_result(language, f"Sandbox image not found: {settings.EXECUTION_SANDBOX_IMAGE}")

    return await asyncio.to_thread(_execute_docker_sync, code, language, timeout, stdin)


def _execute_docker_sync(code: str, language: str, timeout_ms: int, stdin: str) -> dict:
    source_dir = Path(tempfile.mkdtemp(prefix=f"licoex-input-{language}-", dir=settings.EXECUTION_TMP_DIR))
    source_path = source_dir / get_source_filename(language)
    source_path.write_text(code, encoding="utf-8")
    container_id = ""

    try:
        create = run_docker(build_docker_create_command(language, timeout_ms), cwd=source_dir)
        if create["code"] != 0:
            msg = create["stderr"].strip() or "Failed to create sandbox container"
            return build_error_result(language, msg)
        container_id = create["stdout"].strip()

        copy = run_docker(
            [settings.EXECUTION_DOCKER_BINARY, "cp", str(source_path), f"{container_id}:/input/{source_path.name}"],
            cwd=source_dir,
        )
        if copy["code"] != 0:
            msg = copy["stderr"].strip() or "Failed to copy source into container"
            return build_error_result(language, msg)

        run = run_docker(
            [settings.EXECUTION_DOCKER_BINARY, "start", "--attach", "--interactive", container_id],
            cwd=source_dir,
            stdin=stdin,
            timeout_ms=timeout_ms + settings.EXECUTION_COMPILE_TIMEOUT_MS + 5_000,
        )

        if run["code"] != 0:
            msg = run["stderr"].strip() or "Sandbox container failed"
            return build_error_result(language, msg)

        try:
            payload = json.loads(run["stdout"] or "{}")
        except json.JSONDecodeError:
            return build_error_result(language, "Sandbox returned invalid JSON output")

        payload["engine"] = "docker"
        return payload

    finally:
        if container_id:
            run_docker([settings.EXECUTION_DOCKER_BINARY, "rm", "-f", container_id], cwd=source_dir)
        import shutil as _shutil
        _shutil.rmtree(source_dir, ignore_errors=True)


async def execute_code_from_file(file_content: bytes, language: str, timeout: int = 3000) -> dict:
    return await execute_code(file_content.decode("utf-8"), language, timeout=timeout)


async def get_runtime() -> list[RuntimeInfo]:
    docker_ok = docker_available()
    image_ok = sandbox_image_present() if docker_ok else False
    available = docker_ok and image_ok
    missing = []
    if not docker_ok:
        missing.append(settings.EXECUTION_DOCKER_BINARY)
    elif not image_ok:
        missing.append(settings.EXECUTION_SANDBOX_IMAGE)

    supported = get_supported_languages()
    return [
        RuntimeInfo(
            language=spec.language,
            version="sandbox",
            aliases=list(spec.aliases),
            runtime=spec.runtime,
            available=available,
            missing_commands=missing,
            engine="docker",
        )
        for spec in RUNTIME_SPECS.values()
        if spec.language in supported
    ]


def validate_execution_environment() -> None:
    if not docker_available():
        raise RuntimeError(f"Docker binary not found: {settings.EXECUTION_DOCKER_BINARY}")
    if not sandbox_image_present():
        raise RuntimeError(f"Sandbox image not found: {settings.EXECUTION_SANDBOX_IMAGE}")
