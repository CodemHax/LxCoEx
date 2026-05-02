import re

from app.core.execution_policy import normalize_language

DANGEROUS_PATTERNS: dict[str, list[tuple[str, str]]] = {
    "python": [
        (r'\bimport\s+os\b', "Import of 'os' module is not allowed"),
        (r'\bfrom\s+os\s+import\b', "Import from 'os' module is not allowed"),
        (r'\bimport\s+subprocess\b', "Import of 'subprocess' module is not allowed"),
        (r'\bfrom\s+subprocess\s+import\b', "Import from 'subprocess' module is not allowed"),
        (r'\bimport\s+sys\b', "Import of 'sys' module is not allowed"),
        (r'\bfrom\s+sys\s+import\b', "Import from 'sys' module is not allowed"),
        (r'\bimport\s+shutil\b', "Import of 'shutil' module is not allowed"),
        (r'\bfrom\s+shutil\s+import\b', "Import from 'shutil' module is not allowed"),
        (r'\bimport\s+socket\b', "Import of 'socket' module is not allowed"),
        (r'\bfrom\s+socket\s+import\b', "Import from 'socket' module is not allowed"),
        (r'\bimport\s+ctypes\b', "Import of 'ctypes' module is not allowed"),
        (r'\bfrom\s+ctypes\s+import\b', "Import from 'ctypes' module is not allowed"),
        (r'\bimport\s+multiprocessing\b', "Import of 'multiprocessing' module is not allowed"),
        (r'\bfrom\s+multiprocessing\s+import\b', "Import from 'multiprocessing' module is not allowed"),
        
        (r'\beval\s*\(', "Use of 'eval()' is not allowed"),
        (r'\bexec\s*\(', "Use of 'exec()' is not allowed"),
        (r'\bcompile\s*\(', "Use of 'compile()' is not allowed"),
        (r'\b__import__\s*\(', "Use of '__import__()' is not allowed"),
        (r'\bgetattr\s*\(.+,\s*[\'\"](\system|popen|exec)', "Dangerous getattr usage detected"),
        
        (r'\bopen\s*\([^)]*[\'\"](\/etc|\/proc|\/sys|\/dev|C:\\|\/var)', "Access to system directories is not allowed"),
        
        (r'\bimport\s+requests\b', "Import of 'requests' module is not allowed"),
        (r'\bimport\s+urllib\b', "Import of 'urllib' module is not allowed"),
        (r'\bfrom\s+urllib\b', "Import from 'urllib' module is not allowed"),
        (r'\bimport\s+http\b', "Import of 'http' module is not allowed"),
        (r'\bfrom\s+http\b', "Import from 'http' module is not allowed"),
        
        (r'\\x[0-9a-fA-F]{2}', "Hex-encoded strings are not allowed"),
        (r'\bbase64\b', "Use of 'base64' encoding is not allowed"),
        (r'\bcodecs\b', "Use of 'codecs' module is not allowed"),
    ],
    
    "javascript": [
        (r'\brequire\s*\(\s*[\'"]child_process[\'"]\s*\)', "Use of 'child_process' is not allowed"),
        (r'\brequire\s*\(\s*[\'"]fs[\'"]\s*\)', "Use of 'fs' module is not allowed"),
        (r'\brequire\s*\(\s*[\'"]net[\'"]\s*\)', "Use of 'net' module is not allowed"),
        (r'\brequire\s*\(\s*[\'"]http[\'"]\s*\)', "Use of 'http' module is not allowed"),
        (r'\brequire\s*\(\s*[\'"]https[\'"]\s*\)', "Use of 'https' module is not allowed"),
        (r'\bprocess\.exit\b', "Use of 'process.exit' is not allowed"),
        (r'\bprocess\.env\b', "Access to 'process.env' is not allowed"),
        (r'\bprocess\.kill\b', "Use of 'process.kill' is not allowed"),
        
        (r'\beval\s*\(', "Use of 'eval()' is not allowed"),
        (r'\bFunction\s*\(', "Use of 'Function()' constructor is not allowed"),
        
        (r'import\s+.*\s+from\s+[\'"]child_process[\'"]', "Import from 'child_process' is not allowed"),
        (r'import\s+.*\s+from\s+[\'"]fs[\'"]', "Import from 'fs' is not allowed"),
    ],
    
    "go": [
        (r'import\s+[\"](os|os/exec)["\)]', "Import of 'os' or 'os/exec' package is not allowed"),
        (r'exec\.Command', "Use of 'exec.Command' is not allowed"),
        (r'syscall\.', "Use of 'syscall' package is not allowed"),
        
        (r'import\s+[\"\"]net[\"\"]', "Import of 'net' package is not allowed"),
        (r'import\s+[\"\"]net/http[\"\"]', "Import of 'net/http' package is not allowed"),
    ],
    
    "java": [
        (r'Runtime\.getRuntime\(\)', "Use of 'Runtime.getRuntime()' is not allowed"),
        (r'ProcessBuilder', "Use of 'ProcessBuilder' is not allowed"),
        (r'Process\s+\w+\s*=', "Creating Process objects is not allowed"),
        
        (r'Class\.forName', "Use of 'Class.forName' is not allowed"),
        (r'\.getDeclaredMethod', "Use of reflection methods is not allowed"),
        (r'\.invoke\s*\(', "Use of reflection invoke is not allowed"),
        
        (r'new\s+File\s*\(\s*[\"\'](\\/etc|\\/proc|\\/sys|C:\\\\)', "Access to system directories is not allowed"),
        
        (r'import\s+java\.net\.', "Import of 'java.net' package is not allowed"),
        (r'Socket\s*\(', "Use of Socket is not allowed"),
        (r'ServerSocket', "Use of ServerSocket is not allowed"),
    ],

    "c": [
        (r'system\s*\(', "Use of 'system()' is not allowed"),
        (r'exec\w*\s*\(', "Use of 'exec' family functions is not allowed"),
        (r'fork\s*\(', "Use of 'fork()' is not allowed"),
        (r'popen\s*\(', "Use of 'popen()' is not allowed"),
        (r'fopen\s*\([^,]+,\s*[\'"][aw+]+\w*[\'"]', "File write access is not allowed"),
        (r'remove\s*\(', "Use of 'remove()' is not allowed"),
        (r'rename\s*\(', "Use of 'rename()' is not allowed"),
        (r'#include\s*<stdlib\.h>', "Include of 'stdlib.h' might be restricted"),
        (r'#include\s*<unistd\.h>', "Include of 'unistd.h' is not allowed"),
    ],

    "cpp": [
        (r'system\s*\(', "Use of 'system()' is not allowed"),
        (r'exec\w*\s*\(', "Use of 'exec' family functions is not allowed"),
        (r'std::system', "Use of 'std::system' is not allowed"),
        (r'std::fstream\s+\w+\s*\(.+,\s*std::ios::(out|app|trunc)', "File write access is not allowed"),
        (r'std::ofstream', "Use of 'std::ofstream' is not allowed"),
        (r'filesystem::remove', "Use of 'filesystem::remove' is not allowed"),
        (r'filesystem::rename', "Use of 'filesystem::rename' is not allowed"),
        (r'#include\s*<cstdlib>', "Include of 'cstdlib' might be restricted"),
        (r'#include\s*<unistd\.h>', "Include of 'unistd.h' is not allowed"),
    ],

    "typescript": [
        (r'\brequire\s*\(\s*[\'"]child_process[\'"]\s*\)', "Use of 'child_process' is not allowed"),
        (r'\brequire\s*\(\s*[\'"]fs[\'"]\s*\)', "Use of 'fs' module is not allowed"),
        (r'\brequire\s*\(\s*[\'"]net[\'"]\s*\)', "Use of 'net' module is not allowed"),
        (r'\bprocess\.exit\b', "Use of 'process.exit' is not allowed"),
        (r'\bprocess\.env\b', "Access to 'process.env' is not allowed"),
        (r'import\s+.*\s+from\s+[\'"]child_process[\'"]', "Import from 'child_process' is not allowed"),
        (r'import\s+.*\s+from\s+[\'"]fs[\'"]', "Import from 'fs' is not allowed"),
        (r'import\s+.*\s+from\s+[\'"]net[\'"]', "Import from 'net' is not allowed"),
    ],
}

MAX_CODE_LENGTH = 50000

MAX_CODE_LINES = 1000


def sanitize_code(code: str, language: str) -> tuple[bool, str]:
    try:
        language = normalize_language(language)
    except ValueError as exc:
        return False, str(exc)
    
    if len(code) > MAX_CODE_LENGTH:
        return False, f"Code exceeds maximum length of {MAX_CODE_LENGTH} characters"
    
    line_count = code.count('\n') + 1
    if line_count > MAX_CODE_LINES:
        return False, f"Code exceeds maximum of {MAX_CODE_LINES} lines"
    
    if '\x00' in code:
        return False, "Null bytes detected in code"
    blocked_modules = get_blocked_modules(language)
    for module in blocked_modules:
        if re.search(r'\b' + re.escape(module) + r'\b', code):
            return False, f"Security violation: Module '{module}' is blocked"
            
    blocked_functions = get_blocked_functions(language)
    for func in blocked_functions:
        base_func = func.replace('()', '')
        if re.search(r'\b' + re.escape(base_func) + r'\b', code):
            return False, f"Security violation: Function '{func}' is blocked"

    patterns = DANGEROUS_PATTERNS.get(language, [])
    
    backtick_safe_languages = {"javascript", "typescript"}
    
    common_patterns = [
        (r'rm\s+-rf\s+/', "Shell command 'rm -rf' detected"),
        (r'chmod\s+777', "Dangerous chmod command detected"),
        (r'curl\s+.*\|.*sh', "Piped curl to shell detected"),
        (r'wget\s+.*\|.*sh', "Piped wget to shell detected"),
        (r'\$\(.*\)', "Shell command substitution detected"),
    ]
    
    if language not in backtick_safe_languages:
        common_patterns.append((r'`[^`]+`', "Backtick command execution detected"))
    
    all_patterns = patterns + common_patterns
    
    for pattern, message in all_patterns:
        if re.search(pattern, code, re.IGNORECASE | re.MULTILINE):
            return False, f"Security violation: {message}"
    
    return True, "Code passed security check"




def get_blocked_modules(language: str) -> list[str]:
    blocked = {
        "python":     ["os", "subprocess", "sys", "shutil", "socket", "ctypes",
                       "multiprocessing", "requests", "urllib", "http"],
        "javascript": ["child_process", "fs", "net", "http", "https"],
        "typescript": ["child_process", "fs", "net", "http", "https"],
        "go":         ["os", "os/exec", "syscall", "net", "net/http"],
        "java":       ["java.lang.Runtime", "java.lang.ProcessBuilder", "java.net"],
        "c":          ["stdlib.h", "unistd.h", "sys/socket.h", "arpa/inet.h"],
        "cpp":        ["cstdlib", "unistd.h", "sys/socket.h", "arpa/inet.h", "fstream"],
    }
    try:
        language = normalize_language(language)
    except ValueError:
        return []
    return blocked.get(language, [])


def get_blocked_functions(language: str) -> list[str]:
    blocked = {
        "python":     ["eval()", "exec()", "compile()", "__import__()"],
        "javascript": ["eval()", "Function()"],
        "typescript": ["eval()", "Function()"],
        "go":         ["exec.Command()"],
        "java":       ["Runtime.getRuntime()", "ProcessBuilder", "Class.forName()"],
        "c":          ["system()", "exec()", "fork()", "popen()"],
        "cpp":        ["system()", "exec()", "fork()", "popen()"],
    }
    try:
        language = normalize_language(language)
    except ValueError:
        return []
    return blocked.get(language, [])




