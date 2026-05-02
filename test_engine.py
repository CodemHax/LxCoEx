"""
test_engine.py — Integration tests for the LiCoEx Docker sandbox engine.
Requires Docker to be running and the licoex-sandbox image to be built.

Build the image first:
    docker build -f Dockerfile.sandbox -t licoex-sandbox:latest .

Run tests:
    python test_engine.py
"""

import asyncio
import os

from app.core.excute_engine import (
    docker_available,
    execute_code,
    get_runtime,
    sandbox_image_present,
)


def check_prerequisites() -> bool:
    if not docker_available():
        print("SKIPPED — Docker is not available on this machine.")
        return False
    if not sandbox_image_present():
        print("SKIPPED — licoex-sandbox image not found. Run: docker build -f Dockerfile.sandbox -t licoex-sandbox:latest .")
        return False
    return True


async def test_python_hello():
    print("\n=== Test: Python hello world ===")
    result = await execute_code('print("Hello from sandbox!")', "python")
    print(f"  result: {result}")
    assert not result["error"], f"Unexpected error: {result['message']}"
    assert "Hello from sandbox!" in result["run"]["stdout"]
    assert result["engine"] == "docker"
    print("  PASSED")


async def test_python_stdin():
    print("\n=== Test: Python stdin ===")
    code = "import sys\nname = sys.stdin.readline().strip()\nprint('Hello, ' + name + '!')"
    result = await execute_code(code, "python", stdin="World")
    print(f"  result: {result}")
    assert "Hello, World!" in result["run"]["stdout"]
    print("  PASSED")


async def test_python_syntax_error():
    print("\n=== Test: Python syntax error ===")
    result = await execute_code("def broken(\nprint('oops')", "python")
    print(f"  result: {result}")
    assert result["error"]
    assert result["run"]["code"] != 0
    print("  PASSED")


async def test_timeout_enforcement():
    print("\n=== Test: Timeout enforcement ===")
    result = await execute_code("while True: pass", "python", timeout=500)
    print(f"  result: {result}")
    assert result["error"]
    print("  PASSED")


async def test_network_blocked():
    print("\n=== Test: Network blocked ===")
    code = "import urllib.request\nurllib.request.urlopen('http://example.com')"
    result = await execute_code(code, "python")
    print(f"  result: {result}")
    assert result["error"], "Expected network to be blocked in sandbox"
    print("  PASSED")


async def test_get_runtime():
    print("\n=== Test: get_runtime ===")
    runtimes = await get_runtime()
    print(f"  Found {len(runtimes)} runtimes")
    for r in runtimes:
        print(f"  - {r.language} ({r.engine})")
    assert len(runtimes) > 0
    assert all(r.engine == "docker" for r in runtimes)
    print("  PASSED")


async def main():
    print("Running LiCoEx Docker sandbox tests...")
    if not check_prerequisites():
        return

    tests = [
        test_python_hello,
        test_python_stdin,
        test_python_syntax_error,
        test_timeout_enforcement,
        test_network_blocked,
        test_get_runtime,
    ]

    passed = failed = 0
    for test_fn in tests:
        try:
            await test_fn()
            passed += 1
        except AssertionError as e:
            print(f"  FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"  ERROR: {e}")
            failed += 1

    print(f"\n{'='*40}")
    print(f"  Results: {passed} passed | {failed} failed")
    print(f"{'='*40}\n")
    return failed == 0


if __name__ == "__main__":
    ok = asyncio.run(main())
    raise SystemExit(0 if ok else 1)
