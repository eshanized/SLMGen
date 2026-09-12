# SLMGEN Makefile
# Author: Eshan Roy <eshanized@proton.me>
# License: MIT

VENV := libslmgen/.venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
UVICORN := $(VENV)/bin/uvicorn

.PHONY: all install install-backend install-frontend dev dev-backend dev-frontend build run test test-backend test-frontend lint clean help venv

# Default target
all: help

# Create Python virtual environment
venv: $(VENV)/bin/activate

$(VENV)/bin/activate:
	@echo "🐍 Creating Python virtual environment..."
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip -q
	@echo "✅ Virtual environment ready at $(VENV)"

# Install all dependencies
install: install-backend install-frontend

install-backend: venv
	@echo "📦 Installing backend dependencies..."
	$(PIP) install -r libslmgen/requirements.txt -q
	@echo "✅ Backend ready"

install-frontend:
	@echo "📦 Installing frontend dependencies..."
	cd slmgenui && npm install --silent
	@echo "✅ Frontend ready"

# Development servers
dev: 
	@echo "🚀 Starting both servers..."
	@make -j2 dev-backend dev-frontend

dev-backend: venv
	@echo "🐍 Starting backend on http://localhost:8000"
	cd libslmgen && ../$(UVICORN) app.main:app --reload --port 8000

dev-frontend:
	@echo "⚡ Starting frontend on http://localhost:3000"
	cd slmgenui && npm run dev

# Production build
build:
	@echo "🔨 Building frontend..."
	cd slmgenui && npm run build
	@echo "✅ Build complete"

# Run complete project (production mode)
run: install build
	@echo "🚀 Starting SLMGEN..."
	@echo "   Backend:  http://localhost:8000"
	@echo "   Frontend: http://localhost:3000"
	@make -j2 run-backend run-frontend

run-backend: venv
	cd libslmgen && ../$(UVICORN) app.main:app --host 0.0.0.0 --port 8000

run-frontend:
	cd slmgenui && npm run start

# Tests
test: test-backend test-frontend

test-backend: venv
	@echo "🧪 Running backend test suite..."
	cd libslmgen && ../$(PYTHON) -m pytest tests/

test-frontend:
	@echo "🧪 Running frontend type-check & lint..."
	cd slmgenui && npm run lint

# Lint and type check
lint: venv
	@echo "🔍 Checking Python syntax & tests..."
	cd libslmgen && ../$(PYTHON) -m py_compile app/main.py app/models.py app/config.py app/session_store.py \
		core/ingest.py core/quality.py core/analyzer.py core/recommender.py core/notebook.py \
		app/routers/upload.py app/routers/analyze.py app/routers/recommend.py app/routers/generate.py
	@echo "🔍 Checking TypeScript & ESLint..."
	cd slmgenui && npm run lint
	@echo "✅ All checks passed"

# Clean build artifacts
clean:
	@echo "🧹 Cleaning..."
	rm -rf slmgenui/.next slmgenui/node_modules/.cache
	rm -rf libslmgen/uploads/*.jsonl libslmgen/uploads/*.ipynb
	rm -rf libslmgen/__pycache__ libslmgen/**/__pycache__
	rm -rf $(VENV)
	@echo "✅ Clean"

# Help
help:
	@echo ""
	@echo "🚀 SLMGEN - Fine-tune SLMs in Minutes"
	@echo ""
	@echo "Usage: make <target>"
	@echo ""
	@echo "Targets:"
	@echo "  venv             Create Python virtual environment"
	@echo "  install          Install all dependencies"
	@echo "  install-backend  Install Python dependencies (with venv)"
	@echo "  install-frontend Install Node.js dependencies"
	@echo "  dev              Run both servers (parallel, dev mode)"
	@echo "  dev-backend      Run FastAPI backend only (dev mode)"
	@echo "  dev-frontend     Run Next.js frontend only (dev mode)"
	@echo "  run              Run complete project (production)"
	@echo "  build            Production build frontend"
	@echo "  test             Run all backend and frontend tests"
	@echo "  lint             Check code quality"
	@echo "  clean            Remove build artifacts and venv"
	@echo "  help             Show this message"
	@echo ""
