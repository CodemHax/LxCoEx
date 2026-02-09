from pyston import PystonClient, File


async def get_runtime():
    client = PystonClient()
    runtimes = await client.runtimes()
    await client.close_session()
    return [
        {
            "language": runtime.language,
            "version": runtime.version,
            "aliases": runtime.aliases,
            "runtime": runtime.runtime
        } for runtime in runtimes
    ]


async def execute_code(code: str, language: str, timeout: int = 3000, stdin: str = None):
    client = PystonClient()
    output = await client.execute(language, [File(code)], run_timeout=timeout, stdin=stdin)
    await client.close_session()
    return output.raw_json


async def execute_code_from_file(file_content: bytes, language: str, timeout: int = 3000):
    client = PystonClient()
    code_str = file_content.decode('utf-8')
    pyston_file = File(code_str)
    output = await client.execute(language, [pyston_file], run_timeout=timeout)
    await client.close_session()
    return output.raw_json



