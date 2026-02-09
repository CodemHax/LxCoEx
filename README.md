# LiCoEx - Live Code Executor

A modern, web-based code execution platform that allows users to write, run, and share code snippets in multiple programming languages.

![LiCoEx](https://img.shields.io/badge/LiCoEx-Code%20Executor-00b8a3)
![Python](https://img.shields.io/badge/Python-3.11+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## Features

- **Multi-Language Support**: Execute code in Python, JavaScript, TypeScript, Go, Java, C, and C++
- **Real-time Execution**: Queue-based code execution with status tracking
- **Code Sharing**: Share code snippets via unique URLs
- **Code Templates**: Pre-built templates for each supported language
- **Security**: Built-in code sanitizer to prevent malicious code execution
- **Rate Limiting**: Protection against API abuse
- **Dark/Light Theme**: Toggle between dark and light modes
- **AI Error Explanation**: Get AI-powered explanations for code errors (via Puter.js)

## Tech Stack

### Backend
| Technology | Purpose |
|------------|---------|
| **FastAPI** | Modern async Python web framework |
| **Pyston** | Code execution engine (Piston API client) |
| **MongoDB** | Database for storing code snippets |
| **Redis** | Job queue and rate limiting |
| **Motor** | Async MongoDB driver |
| **Pydantic** | Data validation and settings management |
| **Uvicorn** | ASGI server |

### Frontend
| Technology | Purpose |
|------------|---------|
| **HTML5/CSS3** | Structure and styling |
| **JavaScript (ES6+)** | Client-side logic |
| **CodeMirror** | Code editor with syntax highlighting |
| **Puter.js** | AI-powered error explanations |

## Project Structure

```
LiCoEx/
├── app/
│   ├── api/
│   │   ├── deps.py              # Dependency injection
│   │   └── v1/
│   │       ├── excuter_endpoint.py   # Code execution endpoints
│   │       └── snippet_endpoint.py   # Code sharing endpoints
│   ├── core/
│   │   ├── code_sanitizer.py    # Security: code validation
│   │   ├── config.py            # Application settings
│   │   ├── exceptions.py        # Custom exceptions
│   │   ├── excute_engine.py     # Pyston execution wrapper
│   │   ├── rate_limit.py        # Rate limiting middleware
│   │   └── templates.py         # Code templates
│   ├── crud/
│   │   └── snippet_crud.py      # Snippet database operations
│   ├── db/
│   │   ├── mongo.py             # MongoDB connection
│   │   └── redis.py             # Redis connection
│   ├── models/
│   │   ├── code_input_model.py  # Request models
│   │   └── snippet_model.py     # Snippet models
│   ├── services/
│   │   ├── execution_queue.py   # Job queue management
│   │   └── logger.py            # Logging configuration
│   └── main.py                  # Application entry point
├── frontend/
│   ├── css/
│   │   └── style.css            # Styles
│   ├── js/
│   │   └── app.js               # Frontend logic
│   └── index.html               # Main page
├── .env                         # Environment variables
├── .gitignore
└── README.md
```

## API Endpoints

### Code Execution

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/core/execute` | Queue code for execution |
| `POST` | `/api/v1/core/execute-sync` | Execute code and wait for result |
| `GET` | `/api/v1/core/job/{job_id}` | Get job status/result |
| `GET` | `/api/v1/core/queue/status` | Get queue status |
| `GET` | `/api/v1/core/get-runtimes` | List supported languages |

### Templates

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/core/template/{language}` | Get template for language |
| `GET` | `/api/v1/core/templates` | Get all templates |

### Code Sharing

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/snippet/share` | Create shareable snippet |
| `GET` | `/api/v1/snippet/{snippet_id}` | Get snippet by ID |

## Installation

### Prerequisites

- Python 3.11+
- MongoDB
- Redis
- Node.js (optional, for frontend development)

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/LiCoEx.git
   cd LiCoEx
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install fastapi uvicorn motor redis pyston pydantic-settings
   ```

4. **Configure environment variables**
   
   Create a `.env` file:
   ```env
   PROJECT_NAME=LiCoEx_API
   API_V1_STR=/api/v1
   MONGODB_URL=mongodb://localhost:27017
   MONGODB_DB_NAME=licoex_db
   REDIS_URL=redis://127.0.0.1:6379
   ```

5. **Start MongoDB and Redis**
   ```bash
   # Start MongoDB
   mongod
   
   # Start Redis
   redis-server
   ```

6. **Run the application**
   ```bash
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```

7. **Open in browser**
   ```
   http://127.0.0.1:8000
   ```

## Supported Languages

| Language | Version | File Extension |
|----------|---------|----------------|
| Python | 3.x | `.py` |
| JavaScript | Node.js | `.js` |
| TypeScript | Latest | `.ts` |
| Go | Latest | `.go` |
| Java | Latest | `.java` |
| C | GCC | `.c` |
| C++ | G++ | `.cpp` |

## Security Features

The code sanitizer blocks potentially dangerous operations:

### Python
- `os`, `subprocess`, `sys`, `shutil` modules
- `eval()`, `exec()`, `compile()` functions
- Network modules (`requests`, `urllib`, `socket`)

### JavaScript/TypeScript
- `child_process`, `fs`, `net` modules
- `eval()`, `Function()` constructor
- `process.env`, `process.exit`

### Other Languages
- System calls and process execution
- File system write operations
- Network operations

## Rate Limiting

- **Code Execution**: 10 requests per 60 seconds
- **Code Sharing**: 5 requests per 60 seconds

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `PROJECT_NAME` | `LiCoEx API` | Application name |
| `API_V1_STR` | `/api/v1` | API version prefix |
| `MONGODB_URL` | `mongodb://localhost:27017` | MongoDB connection URL |
| `MONGODB_DB_NAME` | `licoex_db` | Database name |
| `REDIS_URL` | `redis://localhost:6379` | Redis connection URL |

## Development

### Running in Development Mode
```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### API Documentation
FastAPI provides automatic API documentation:
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Piston](https://github.com/engineer-man/piston) - Code execution engine
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [CodeMirror](https://codemirror.net/) - Code editor
- [Puter.js](https://puter.com/) - AI capabilities

