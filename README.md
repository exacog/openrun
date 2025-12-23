# OpenRun

A flexible, LLM-agnostic engine for orchestrating AI agents and complex conversational automation behind the firewall.

## Development

This project uses [uv](https://docs.astral.sh/uv/) for dependency management.

### Prerequisites

Install uv if you haven't already:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Setup

Clone the repository and install dependencies:

```bash
git clone https://github.com/exacog/openrun.git
cd openrun
uv sync
```

This will create a virtual environment and install all dependencies (including dev dependencies).

### Running Tests

```bash
uv run pytest
```

### Linting & Formatting

Check for linting issues:

```bash
uv run ruff check .
```

Auto-fix linting issues:

```bash
uv run ruff check . --fix
```

Format code:

```bash
uv run ruff format .
```

### Building

```bash
uv build
```

This will create distribution files in the `dist/` directory.
