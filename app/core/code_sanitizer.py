import re
import ast

from app.core.execution_policy import normalize_language

DANGEROUS_PATTERNS: dict[str, list[tuple[str, str]]] = {
    "python": [
        (r'\bimport\s+(os|subprocess|sys|shutil|socket|ctypes|multiprocessing|importlib|builtins|pty|ptyprocess)\b', "Import of restricted module is not allowed"),
        (r'\bfrom\s+(os|subprocess|sys|shutil|socket|ctypes|multiprocessing|importlib|builtins|pty|ptyprocess)\s+import\b', "Import from restricted module is not allowed"),
        
        (r'\beval\s*\(', "Use of 'eval()' is not allowed"),
        (r'\bexec\s*\(', "Use of 'exec()' is not allowed"),
        (r'\bcompile\s*\(', "Use of 'compile()' is not allowed"),
        (r'\b__import__\s*\(', "Use of '__import__()' is not allowed"),
        (r'\bgetattr\s*\(.+,\s*[\'\"](\system|popen|exec)', "Dangerous getattr usage detected"),
        
        (r'\b__builtins__\b', "Direct access to __builtins__ is restricted"),
        (r'\b__class__\b', "Direct access to __class__ is restricted"),
        (r'\b__subclasses__\b', "Direct access to __subclasses__ is restricted"),
        (r'\b__mro__\b', "Direct access to __mro__ is restricted"),
        (r'\b__bases__\b', "Direct access to __bases__ is restricted"),
        (r'\bglobals\s*\(', "Use of 'globals()' is not allowed"),
        (r'\blocals\s*\(', "Use of 'locals()' is not allowed"),
        
        (r'\bopen\s*\([^)]*[\'\"](\/etc|\/proc|\/sys|\/dev|C:\\|\/var|\.\.)', "Access to system directories is not allowed"),
        
        (r'\bimport\s+(requests|urllib|http|ftplib|telnetlib)\b', "Import of network module is not allowed"),
        (r'\bfrom\s+(urllib|http|ftplib|telnetlib)\b', "Import from network module is not allowed"),
        
        (r'\\x[0-9a-fA-F]{2}', "Hex-encoded strings are not allowed"),
        (r'\bbase64\b', "Use of 'base64' encoding is not allowed"),
        (r'\bcodecs\b', "Use of 'codecs' module is not allowed"),
    ],
    
    "javascript": [
        (r'\brequire\s*\(\s*[\'"](child_process|fs|net|http|https|vm|cluster|worker_threads|module|tls|dgram|crypto)[\'"]\s*\)', "Use of restricted built-in module is not allowed"),
        (r'\bprocess\.exit\b', "Use of 'process.exit' is not allowed"),
        (r'\bprocess\.env\b', "Access to 'process.env' is not allowed"),
        (r'\bprocess\.kill\b', "Use of 'process.kill' is not allowed"),
        (r'\bprocess\.binding\b', "Use of 'process.binding' is not allowed"),
        (r'\bprocess\.mainModule\b', "Use of 'process.mainModule' is not allowed"),
        
        (r'\beval\s*\(', "Use of 'eval()' is not allowed"),
        (r'\bFunction\s*\(', "Use of 'Function()' constructor is not allowed"),
        (r'\bsetTimeout\s*\(\s*[\'"]', "String evaluation in setTimeout is not allowed"),
        (r'\bsetInterval\s*\(\s*[\'"]', "String evaluation in setInterval is not allowed"),
        
        (r'import\s+.*\s+from\s+[\'"](child_process|fs|net|http|https|vm|cluster|worker_threads|module|tls|dgram|crypto)[\'"]', "Import from restricted built-in module is not allowed"),
        (r'\bglobal\b\.', "Accessing restricted global properties is not allowed"),
        (r'\bglobalThis\b\.', "Accessing restricted globalThis properties is not allowed"),
    ],
    
    "go": [
        (r'import\s+[\"\'](os|os/exec|syscall|net|net/http|plugin|unsafe)[\"\']', "Import of restricted package is not allowed"),
        (r'import\s+\(\s*[\"\'](os|os/exec|syscall|net|net/http|plugin|unsafe)[\"\']', "Import of restricted package is not allowed"),
        (r'exec\.Command', "Use of 'exec.Command' is not allowed"),
        (r'syscall\.', "Use of 'syscall' package is not allowed"),
        (r'os\.OpenFile', "Use of 'os.OpenFile' is not allowed"),
        (r'os\.Remove', "Use of 'os.Remove' is not allowed"),
    ],
    
    "java": [
        (r'Runtime\.getRuntime\(\)', "Use of 'Runtime.getRuntime()' is not allowed"),
        (r'ProcessBuilder', "Use of 'ProcessBuilder' is not allowed"),
        (r'Process\s+\w+\s*=', "Creating Process objects is not allowed"),
        (r'System\.exit', "Use of 'System.exit()' is not allowed"),
        (r'System\.getenv', "Use of 'System.getenv()' is not allowed"),
        (r'System\.getProperties', "Use of 'System.getProperties()' is not allowed"),
        
        (r'Class\.forName', "Use of 'Class.forName' is not allowed"),
        (r'\.getDeclaredMethod', "Use of reflection methods is not allowed"),
        (r'\.invoke\s*\(', "Use of reflection invoke is not allowed"),
        (r'java\.lang\.reflect\.', "Use of reflection API is not allowed"),
        
        (r'new\s+File\s*\(\s*[\"\'](\\/etc|\\/proc|\\/sys|C:\\\\|\.\.)', "Access to system directories is not allowed"),
        (r'java\.nio\.file\.', "Use of 'java.nio.file' API is not allowed"),
        
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
        (r'#include\s*<sys/', "Include of system headers is not allowed"),
        (r'#include\s*<netinet/', "Include of network headers is not allowed"),
        (r'#include\s*<arpa/', "Include of network headers is not allowed"),
        (r'mmap\s*\(', "Use of 'mmap()' is not allowed"),
        (r'pthread_create\s*\(', "Use of 'pthread_create()' is not allowed"),
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
        (r'#include\s*<sys/', "Include of system headers is not allowed"),
        (r'#include\s*<netinet/', "Include of network headers is not allowed"),
        (r'#include\s*<arpa/', "Include of network headers is not allowed"),
        (r'mmap\s*\(', "Use of 'mmap()' is not allowed"),
        (r'pthread_create\s*\(', "Use of 'pthread_create()' is not allowed"),
    ],

    "typescript": [
        (r'\brequire\s*\(\s*[\'"](child_process|fs|net|http|https|vm|cluster|worker_threads|module|tls|dgram|crypto)[\'"]\s*\)', "Use of restricted built-in module is not allowed"),
        (r'\bprocess\.exit\b', "Use of 'process.exit' is not allowed"),
        (r'\bprocess\.env\b', "Access to 'process.env' is not allowed"),
        (r'\bprocess\.kill\b', "Use of 'process.kill' is not allowed"),
        (r'\bprocess\.binding\b', "Use of 'process.binding' is not allowed"),
        (r'\bprocess\.mainModule\b', "Use of 'process.mainModule' is not allowed"),
        
        (r'\beval\s*\(', "Use of 'eval()' is not allowed"),
        (r'\bFunction\s*\(', "Use of 'Function()' constructor is not allowed"),
        (r'\bsetTimeout\s*\(\s*[\'"]', "String evaluation in setTimeout is not allowed"),
        (r'\bsetInterval\s*\(\s*[\'"]', "String evaluation in setInterval is not allowed"),
        
        (r'import\s+.*\s+from\s+[\'"](child_process|fs|net|http|https|vm|cluster|worker_threads|module|tls|dgram|crypto)[\'"]', "Import from restricted built-in module is not allowed"),
        (r'\bglobal\b\.', "Accessing restricted global properties is not allowed"),
        (r'\bglobalThis\b\.', "Accessing restricted globalThis properties is not allowed"),
    ],
}

MAX_CODE_LENGTH = 50000
MAX_CODE_LINES = 1000

def check_python_ast(code: str) -> tuple[bool, str]:
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return False, f"Syntax Error: {str(e)}"
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in get_blocked_modules("python"):
                    return False, f"AST Security violation: Import of '{alias.name}' is blocked"
        elif isinstance(node, ast.ImportFrom):
            if node.module in get_blocked_modules("python"):
                return False, f"AST Security violation: Import from '{node.module}' is blocked"
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                if node.func.id in get_blocked_functions("python"):
                    return False, f"AST Security violation: Call to '{node.func.id}' is blocked"
            elif isinstance(node.func, ast.Attribute):
                if node.func.attr in ["system", "popen", "spawn"]:
                    return False, f"AST Security violation: Call to attribute '{node.func.attr}' is blocked"
        elif isinstance(node, ast.Attribute):
            if node.attr in ["__builtins__", "__class__", "__subclasses__", "__mro__", "__bases__"]:
                return False, f"AST Security violation: Access to attribute '{node.attr}' is restricted"
    return True, ""

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

    if language == "python":
        is_safe, msg = check_python_ast(code)
        if not is_safe:
            return False, msg

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
                       "multiprocessing", "requests", "urllib", "http", "importlib", "builtins", "pty", "ftplib", "telnetlib", "urllib2"],
        "javascript": ["child_process", "fs", "net", "http", "https", "vm", "cluster", "worker_threads", "module", "tls", "dgram", "crypto"],
        "typescript": ["child_process", "fs", "net", "http", "https", "vm", "cluster", "worker_threads", "module", "tls", "dgram", "crypto"],
        "go":         ["os", "os/exec", "syscall", "net", "net/http", "plugin", "unsafe"],
        "java":       ["java.lang.Runtime", "java.lang.ProcessBuilder", "java.net", "java.lang.reflect", "java.nio.file", "java.io.File"],
        "c":          ["stdlib.h", "unistd.h", "sys/socket.h", "arpa/inet.h", "sys/types.h", "sys/wait.h", "netinet/in.h"],
        "cpp":        ["cstdlib", "unistd.h", "sys/socket.h", "arpa/inet.h", "fstream", "sys/types.h", "sys/wait.h", "netinet/in.h"],
    }
    try:
        language = normalize_language(language)
    except ValueError:
        return []
    return blocked.get(language, [])

def get_blocked_functions(language: str) -> list[str]:
    blocked = {
        "python":     ["eval()", "exec()", "compile()", "__import__()", "globals()", "locals()", "getattr()", "setattr()", "delattr()", "memoryview()"],
        "javascript": ["eval()", "Function()"],
        "typescript": ["eval()", "Function()"],
        "go":         ["exec.Command()"],
        "java":       ["Runtime.getRuntime()", "ProcessBuilder", "Class.forName()", "System.exit()", "System.getenv()"],
        "c":          ["system()", "exec()", "fork()", "popen()", "mmap()", "pthread_create()"],
        "cpp":        ["system()", "exec()", "fork()", "popen()", "mmap()", "pthread_create()"],
    }
    try:
        language = normalize_language(language)
    except ValueError:
        return []
    return blocked.get(language, [])
