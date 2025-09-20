#!/bin/bash
# Development script for Requirements Generator

# Add uv to PATH
export PATH="$HOME/.local/bin:$PATH"

# Function to show usage
show_usage() {
    echo "Usage: ./scripts/dev.sh [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  install     Install dependencies"
    echo "  dev         Start development server"
    echo "  test        Run tests"
    echo "  lint        Run code quality checks"
    echo "  format      Format code with black and isort"
    echo "  migrate     Run database migrations"
    echo "  makemigrations  Create new migration"
    echo "  reset-db    Reset database"
    echo "  worker      Start Celery worker"
    echo "  shell       Start Python shell with project context"
    echo "  clean       Clean cache and temporary files"
    echo ""
}

case "$1" in
    install)
        echo "Installing dependencies with uv..."
        uv sync --extra dev
        ;;
    dev)
        echo "Starting development server..."
        uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
        ;;
    test)
        echo "Running tests..."
        uv run pytest "$@"
        ;;
    lint)
        echo "Running code quality checks..."
        uv run black --check src tests
        uv run isort --check src tests
        uv run flake8 src tests
        uv run mypy src
        uv run bandit -r src
        ;;
    format)
        echo "Formatting code..."
        uv run black src tests
        uv run isort src tests
        ;;
    migrate)
        echo "Running database migrations..."
        uv run alembic upgrade head
        ;;
    makemigrations)
        echo "Creating new migration..."
        shift
        if [ -z "$1" ]; then
            echo "Usage: ./scripts/dev.sh makemigrations <migration_message>"
            exit 1
        fi
        uv run alembic revision --autogenerate -m "$*"
        ;;
    reset-db)
        echo "⚠️ Resetting database..."
        rm -f requirements.db
        uv run alembic upgrade head
        ;;
    worker)
        echo "Starting Celery worker..."
        uv run celery -A src.shared.tasks worker --loglevel=info
        ;;
    shell)
        echo "Starting Python shell..."
        uv run python
        ;;
    clean)
        echo "Cleaning cache and temporary files..."
        find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
        find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
        find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
        find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
        rm -rf htmlcov/ .coverage coverage.xml
        echo "Cache cleaned!"
        ;;
    *)
        show_usage
        exit 1
        ;;
esac