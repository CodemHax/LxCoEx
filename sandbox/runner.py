import argparse
import json
import os
import queue
import shutil
import subprocess
import sys
import threading
from pathlib import Path

MAX_OUTPUT_BYTES = 32768


def exe_name(base_name: str) -> str:
    return f"{base_name}.exe" if os.name == "nt" else base_name


def python_run(workspace: Path, source: Path) -> list[str]:
    return ["python", source.name]


def node_run(workspace: Path, source: Path) -> list[str]:
    return ["node", source.name]


def typescript_compile(workspace: Path, source: Path) -> list[str]:
    return ["tsc", source.name, "--target", "es2020", "--module", "commonjs", "--outDir", "dist"]


def typescript_run(workspace: Path, source: Path) -> list[str]:
    return ["node", str(Path("dist") / "main.js")]


def go_run(workspace: Path, source: Path) -> list[str]:
    return ["go", "run", source.name]


def java_compile(workspace: Path, source: Path) -> list[str]:
    return ["javac", source.name]


def java_run(workspace: Path, source: Path) -> list[str]:
    return ["java", "-cp", ".", "Main"]


def c_compile(workspace: Path, source: Path) -> list[str]:
    return ["gcc", source.name, "-O2", "-o", exe_name("program")]


def cpp_compile(workspace: Path, source: Path) -> list[str]:
    return ["g++", source.name, "-O2", "-std=c++17", "-o", exe_name("program")]


def native_run(workspace: Path, source: Path) -> list[str]:
    return [str(workspace / exe_name("program"))]


LANGUAGE_SPECS = {
    "python": {
        "compile": None,
        "run": python_run,
    },
    "javascript": {
        "compile": None,
        "run": node_run,
    },
    "typescript": {
        "compile": typescript_compile,
        "run": typescript_run,
    },
    "go": {
        "compile": None,
        "run": go_run,
    },
    "java": {
        "compile": java_compile,
        "run": java_run,
    },
    "c": {
        "compile": c_compile,
        "run": native_run,
    },
    "cpp": {
        "compile": cpp_compile,
        "run": native_run,
    },
}


def read_stream(stream, limit: int, result_queue: queue.Queue, stream_name: str) -> None:
    chunks: list[bytes] = []
    total = 0
    truncated = False
    try:
        while True:
            chunk = stream.read(4096)
            if not chunk:
                break
            if total < limit:
                remaining = limit - total
                chunks.append(chunk[:remaining])
                total += min(len(chunk), remaining)
            if total >= limit:
                truncated = True
    finally:
        stream.close()
        result_queue.put((stream_name, b"".join(chunks), truncated))


def run_command(command: list[str], cwd: Path, stdin: str = "", timeout_ms: int = 3000) -> dict:
    try:
        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(cwd),
        )
    except FileNotFoundError:
        return {
            "stdout": "",
            "stderr": f"Required runtime command not found: {command[0]}",
            "code": 127,
        }

    result_queue: queue.Queue = queue.Queue()
    stdout_thread = threading.Thread(
        target=read_stream,
        args=(process.stdout, MAX_OUTPUT_BYTES, result_queue, "stdout"),
        daemon=True,
    )
    stderr_thread = threading.Thread(
        target=read_stream,
        args=(process.stderr, MAX_OUTPUT_BYTES, result_queue, "stderr"),
        daemon=True,
    )
    stdout_thread.start()
    stderr_thread.start()

    if process.stdin is not None:
        process.stdin.write(stdin.encode("utf-8"))
        process.stdin.close()

    try:
        code = process.wait(timeout=timeout_ms / 1000)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()
        return {
            "stdout": "",
            "stderr": f"Execution timed out after {timeout_ms} ms",
            "code": -1,
        }

    stdout_thread.join()
    stderr_thread.join()

    stdout = b""
    stderr = b""
    stdout_truncated = False
    stderr_truncated = False
    while not result_queue.empty():
        stream_name, data, truncated = result_queue.get()
        if stream_name == "stdout":
            stdout = data
            stdout_truncated = truncated
        else:
            stderr = data
            stderr_truncated = truncated

    stdout_text = stdout.decode("utf-8", errors="replace")
    stderr_text = stderr.decode("utf-8", errors="replace")
    if stdout_truncated:
        stdout_text += "\n[output truncated]"
    if stderr_truncated:
        stderr_text += "\n[output truncated]"

    return {
        "stdout": stdout_text,
        "stderr": stderr_text,
        "code": code,
    }


def build_result(language: str, error: bool, message: str, compile_result: dict, run_result: dict) -> dict:
    return {
        "language": language,
        "version": "sandbox",
        "error": error,
        "message": message,
        "compile": compile_result,
        "run": run_result,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--language", required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--timeout-ms", type=int, required=True)
    parser.add_argument("--compile-timeout-ms", type=int, required=True)
    args = parser.parse_args()

    if args.language not in LANGUAGE_SPECS:
        print(
            json.dumps(
                build_result(
                    language=args.language,
                    error=True,
                    message=f"Unsupported language: {args.language}",
                    compile_result={"stdout": "", "stderr": "", "code": 1},
                    run_result={"stdout": "", "stderr": "", "code": 1},
                )
            )
        )
        return 1

    source = Path(args.source)
    workspace = Path("/workspace")
    workspace.mkdir(parents=True, exist_ok=True)
    sandbox_source = workspace / source.name
    shutil.copy2(source, sandbox_source)
    stdin_data = sys.stdin.read()
    spec = LANGUAGE_SPECS[args.language]
    compile_result = {"stdout": "", "stderr": "", "code": 0}

    if spec["compile"] is not None:
        compile_result = run_command(spec["compile"](workspace, sandbox_source), workspace, timeout_ms=args.compile_timeout_ms)
        if compile_result["code"] != 0:
            print(
                json.dumps(
                    build_result(
                        language=args.language,
                        error=True,
                        message="Compilation failed",
                        compile_result=compile_result,
                        run_result={"stdout": "", "stderr": "", "code": 1},
                    )
                )
            )
            return 0

    run_result = run_command(spec["run"](workspace, sandbox_source), workspace, stdin=stdin_data, timeout_ms=args.timeout_ms)
    print(
        json.dumps(
            build_result(
                language=args.language,
                error=run_result["code"] != 0,
                message="Execution completed" if run_result["code"] == 0 else "Execution failed",
                compile_result=compile_result,
                run_result=run_result,
            )
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
