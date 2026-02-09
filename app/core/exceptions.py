class CodeExecutionError(Exception):
    message = "Code execution error"
    status_code = 400


class SecurityError(Exception):
    message = "Security violation"
    status_code = 400


class JobNotFoundError(Exception):
    message = "Job not found"
    status_code = 404
