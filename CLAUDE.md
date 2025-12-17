# CLAUDE.md - Context & Guidelines

## 🚀 Common Commands

### Server Management
- **Start Web Server**: `python run.py serve` (Default port: 8080)
- **Start with Custom Port**: `python run.py serve --port 8089`

### Analysis Tasks
- **Run All Analysis**: `python run.py analyze --type all`
- **Run Uncommented Function Analysis**: `python run.py analyze --type uncommented`
- **Run Duplicate Code Analysis**: `python run.py analyze --type duplicate`

### Weekly Reports
- **Generate Report**: `python run.py weekly --entity-id <ID> --workspace-id <ID>`
- **Fetch Duplicate Data**: `python run.py fetch-duplicate`

### Development
- **Install Dependencies**: `pip install -r requirements.txt`

## 🛠 Technology Stack
- **Backend**: Python 3.10+, Flask, APScheduler
- **AI/LLM**: ZhipuAI (GLM-4.5-Flash)
- **Frontend**: HTML5, Vanilla JS, CSS3 (Glassmorphism)
- **Data**: JSON based storage (in `output/`)

## 🏗 Architecture Overview
- **Entry Point**: `run.py` (CLI & Server starter)
- **API Application**: `src/api/app.py` (Flask factory)
- **Agent Core**: `src/agent/`
  - `service.py`: Main conversation loop & state management
  - `tools.py`: Tool registry for LLM function calling
  - `prompts.py`: System prompts and context management
- **Core Logic**: `src/core/`
  - `generators/`: Report generation (ZhipuAI integration)
  - `analyzers/`: Data processing
  - `fetchers/`: Data collection
- **Templates**: `templates/base.html` (Main layout with Chat Widget)

## 📝 Coding Guidelines
- **Python**: Follow PEP 8. Use type hints (`typing`) where possible.
- **Logging**: Use `src.utils.LoggerFactory` instead of `print`.
- **Error Handling**: Use `try/except` blocks and log errors with tracebacks.
- **Paths**: Use `pathlib.Path` for file system operations.
- **Frontend**: Keep JS and CSS separate in `static/`. Use BEM naming for CSS classes if complex.
