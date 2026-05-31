# LiCoEx – Live Code Executor

LiCoEx is a modern, web‑based code execution platform that lets you write, run, and share code snippets in multiple programming languages, with a polished UI and safe, sandboxed backend.

![LiCoEx](https://img.shields.io/badge/LiCoEx-Code%20Executor-00b8a3)
![Python](https://img.shields.io/badge/Python-3.11+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green)
![Monaco](https://img.shields.io/badge/Editor-Monaco-0078d4)
![License](https://img.shields.io/badge/License-GPLv3-yellow)

---

## Features

- **Multi-language support** – Python, JavaScript, Java, C, and C++
- **Queued & sync execution** – Run code via a queue or wait for immediate results
- **Code sharing** – Generate shareable URLs for snippets 
- **Language templates** – Starter templates for each language
- **Hardened sandbox** – Containerized execution with no network, non-root user, read-only rootfs, and resource limits
- **Security layer** – Code sanitizer to block obvious dangerous operations before sandbox execution
- **Rate limiting** – Protects the API from abuse
- **Monaco Editor** – VS Code's editor engine with syntax highlighting, IntelliSense, multi-cursor, find & replace, and smooth animations
- **Dark / light theme** – Toggleable UI theme (`vs-dark` / `vs` Monaco themes)
- **Local Persistence** – Code is automatically saved to local storage (Ctrl+S / Cmd+S)
- **AI error explanation** – Enhanced AI‑based explanations for errors (now more robust and handles multiple response formats)

---

## Tech Stack

### Backend

| Technology   | Purpose                                      |
|-------------|----------------------------------------------|
| **FastAPI** | Modern async Python web framework            |
| **Local Runtime Engine** | In-house compile/run pipeline     |
| **MongoDB** | Store shared code snippets                   |
| **Redis**   | Job queue, caching, and rate limiting        |
| **Motor**   | Async MongoDB driver                         |
| **Pydantic** / **pydantic-settings** | Data models & config management |
| **Uvicorn** | ASGI server                                  |

### Frontend

| Technology          | Purpose                                  |
|---------------------|------------------------------------------|
| **HTML5 / CSS3**    | Structure and styling                   |
| **JavaScript (ES6+)** | Client‑side logic                     |
| **Monaco Editor**   | VS Code's editor engine — syntax highlighting, IntelliSense, multi-cursor, find & replace |
| **Puter.js**        | AI‑powered error explanations            |

---

## Project Structure

```text
LiCoEx/
├── app/
│   ├── api/
│   │   ├── deps.py                # Dependency injection helpers
│   │   └── v1/
│   │       ├── excuter_endpoint.py  # Code execution endpoints
│   │       └── snippet_endpoint.py  # Code sharing endpoints
│   ├── core/
│   │   ├── code_sanitizer.py      # Security: code validation
│   │   ├── config.py              # Application settings
│   │   ├── exceptions.py          # Custom exceptions
│   │   ├── excute_engine.py       # Local execution engine
│   │   ├── rate_limit.py          # Rate limiting dependency
│   │   └── templates.py           # Code templates
│   ├── crud/
│   │   └── snippet_crud.py        # Snippet DB operations
│   ├── db/
│   │   ├── mongo.py               # MongoDB connection
│   │   └── redis.py               # Redis connection
│   ├── models/
│   │   ├── code_input_model.py    # Request models
│   │   └── snippet_model.py       # Snippet models
│   ├── services/
│   │   ├── execution_queue.py     # Job queue management
│   │   └── logger.py              # Logging config
│   └── main.py                    # FastAPI app entrypoint
├── frontend/
│   ├── css/
│   │   └── style.css              # UI styles
│   ├── js/
│   │   └── app.js                 # Frontend logic
│   └── index.html                 # Main page
├── .env                           # Environment variables (local)
├── Dockerfile                     # App container image
├── docker-compose.yml             # App + Mongo + Redis stack
├── requirements.txt               # Python dependencies
├── .dockerignore
├── .gitignore
└── README.md
```

---

## API Endpoints

### Code Execution

| Method | Endpoint                     | Description                     |
|--------|------------------------------|---------------------------------|
| `POST` | `/api/v1/core/execute`       | Queue code for execution        |
| `POST` | `/api/v1/core/execute-sync`  | Execute code and wait for result|
| `GET`  | `/api/v1/core/job/{job_id}`  | Get job status / result         |
| `GET`  | `/api/v1/core/queue/status`  | Get queue length / status       |
| `GET`  | `/api/v1/core/get-runtimes`  | List local runtime availability |

### Templates

| Method | Endpoint                             | Description                 |
|--------|--------------------------------------|-----------------------------|
| `GET`  | `/api/v1/core/template/{language}`   | Get template for a language |
| `GET`  | `/api/v1/core/templates`             | Get all templates           |

### Code Sharing

| Method | Endpoint                         | Description                 |
|--------|----------------------------------|-----------------------------|
| `POST` | `/api/v1/snippet/share`          | Create a shareable snippet  |
| `GET`  | `/api/v1/snippet/{snippet_id}`   | Get snippet by ID           |

---

## Installation

### Prerequisites

- Python **3.11+**
- **MongoDB**
- **Redis**
- **Node.js** (optional, only if you want to work on frontend tooling)

### Quick Start with Docker

```bash
# Clone the repository
git clone https://github.com/yourusername/LiCoEx.git
cd LiCoEx

# Build the sandbox image used for isolated executions
docker build -f Dockerfile.sandbox -t licoex-sandbox:latest .

# Start the full stack (app + MongoDB + Redis)
docker-compose up -d

# App will be available at:
# http://localhost:8000
```

### Manual Setup

1. **Clone the repository**

   ```bash
   git clone https://github.com/yourusername/LiCoEx.git
   cd LiCoEx
   ```

2. **Create and activate a virtual environment**

   ```bash
   python -m venv venv

   # Windows
   venv\Scripts\activate

   # Linux / macOS
   source venv/bin/activate
   ```

3. **Install dependencies**

   Using `requirements.txt`:

   ```bash
   pip install -r requirements.txt
   ```

   Or minimal manual install:

   ```bash
   pip install fastapi uvicorn motor redis pydantic-settings
   ```

4. **Configure environment variables**

   Create a `.env` file in the project root:

   ```env
   PROJECT_NAME=LiCoEx_API
   API_V1_STR=/api/v1
   MONGODB_URL=mongodb://localhost:27017
   MONGODB_DB_NAME=licoex_db
   REDIS_URL=redis://127.0.0.1:6379
   EXECUTION_ENGINE=docker
   EXECUTION_ALLOW_LOCAL=false
   EXECUTION_REQUIRE_SANDBOX=true
   EXECUTION_SANDBOX_IMAGE=licoex-sandbox:latest
   ```

5. **Start MongoDB and Redis**

   ```bash
   # Start MongoDB
   mongod

   # Start Redis
   redis-server
   ```

6. **Build the sandbox image**

   ```bash
   docker build -f Dockerfile.sandbox -t licoex-sandbox:latest .
   ```

7. **Run the application**

   ```bash
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```

   The app now fails closed at startup if Docker or the sandbox image is missing.

8. **Open in your browser**

   ```text
   http://127.0.0.1:8000
   ```

---

## Supported Languages

| Language    | Runtime (example) | Typical Extension |
|-------------|-------------------|-------------------|
| Python      | 3.x               | `.py`             |
| JavaScript  | Node.js           | `.js`             |
| Java        | Latest            | `.java`           |
| C           | GCC               | `.c`              |
| C++         | G++               | `.cpp`            |

> Exact runtime availability comes from the local machine or container. You can query it via `/api/v1/core/get-runtimes`.

---

## Security Features

User code is passed through a sanitizer before execution to reduce risk.

> Important: this project now prefers one Docker sandbox per request. Each run uses a fresh container, disables network access, drops Linux capabilities, applies CPU/memory/pid limits, and removes the container after completion.

### Python

Blocks e.g.:

- Dangerous modules: `os`, `subprocess`, `sys`, `shutil`, `socket`, `ctypes`, `multiprocessing`
- Dynamic execution: `eval()`, `exec()`, `compile()`, `__import__()`
- Certain file and system access patterns
- Network and encoding modules like `requests`, `urllib`, `http`, `base64`, `codecs`

### JavaScript

Restrictions include:

- Node core modules: `child_process`, `fs`, `net`, `http`, `https`
- Dynamic execution: `eval()`, `Function()` constructor
- `process.env`, `process.exit`, `process.kill`

### Other Languages

The sanitizer also checks for dangerous patterns such as:

- System calls (`system()`, `exec*`, `fork()`, `popen()`)
- Raw socket / network operations
- Unsafe file IO (e.g. arbitrary writes, deletes, renames)
- Potentially dangerous headers / packages (e.g. `unistd.h`, `sys/socket.h`)

> The goal is to minimize what user code can do to the underlying system while still allowing most algorithmic / competitive‑programming style code.

---

## Rate Limiting

Rate limiting is implemented using Redis and the `RateLimiter` dependency.

- **Code execution endpoints**: up to **10** requests per **60 seconds** per IP
- **Code sharing endpoints**: up to **5** requests per **60 seconds** per IP

If the limit is exceeded, the API returns `429 Too Many Requests`.

---

## Configuration

These settings live in `app/core/config.py` and can be overridden via environment variables or `.env`.

| Variable        | Default value                 | Description                |
|-----------------|-------------------------------|----------------------------|
| `PROJECT_NAME`  | `LiCoEx API`                  | Application name          |
| `API_V1_STR`    | `/api/v1`                     | API version prefix        |
| `MONGODB_URL`   | `mongodb://localhost:27017`   | MongoDB connection URL    |
| `MONGODB_DB_NAME` | `licoex_db`                 | MongoDB database name     |
| `REDIS_URL`     | `redis://localhost:6379`      | Redis connection URL      |
| `EXECUTION_ENGINE` | `docker`                   | `docker` for sandboxed execution, `local` for fallback |
| `EXECUTION_SANDBOX_IMAGE` | `licoex-sandbox:latest` | Sandbox container image |
| `EXECUTION_DOCKER_BINARY` | `docker`            | Docker CLI binary path   |
| `EXECUTION_SANDBOX_MEMORY` | `256m`             | Memory limit per sandbox |
| `EXECUTION_SANDBOX_CPUS` | `1.0`                | CPU limit per sandbox    |
| `EXECUTION_SANDBOX_PIDS_LIMIT` | `64`           | Process limit per sandbox |

---

## Development

### Running in Development Mode

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### API Documentation

FastAPI auto‑generates interactive docs:

- Swagger UI: <http://127.0.0.1:8000/docs>
- ReDoc: <http://127.0.0.1:8000/redoc>

---

## Contributing

1. Fork this repository
2. Create a feature branch:
   ```bash
   git checkout -b feature/my-feature
   ```
3. Commit your changes:
   ```bash
   git commit -m "Add my feature"
   ```
4. Push the branch:
   ```bash
   git push origin feature/my-feature
   ```
5. Open a Pull Request on GitHub

---

## License

This project is licensed under the **MIT License**. See the [`LICENSE`](LICENSE) file for details.

---

## Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) – Web framework
- [Monaco Editor](https://microsoft.github.io/monaco-editor/) – VS Code's in‑browser code editor engine
- [Puter.js](https://puter.com/) – AI / assistant integration
