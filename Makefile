.PHONY: help install dev build test clean deploy

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install all dependencies
	@echo "Installing backend dependencies..."
	cd backend && python -m pip install -r requirements.txt
	@echo "Installing frontend dependencies..."
	cd frontend && npm install
	@echo "Dependencies installed!"

dev: ## Start development environment
	@echo "Starting development environment..."
	docker-compose up --build

dev-bg: ## Start development environment in background
	@echo "Starting development environment in background..."
	docker-compose up --build -d

stop: ## Stop development environment
	@echo "Stopping development environment..."
	docker-compose down

logs: ## View logs
	docker-compose logs -f

backend-dev: ## Start backend only in development mode
	cd backend && uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

frontend-dev: ## Start frontend only in development mode
	cd frontend && npm run dev

test: ## Run all tests
	@echo "Running backend tests..."
	cd backend && python -m pytest tests/ -v
	@echo "Running frontend tests..."
	cd frontend && npm test

test-backend: ## Run backend tests only
	cd backend && python -m pytest tests/ -v

test-frontend: ## Run frontend tests only
	cd frontend && npm test

lint: ## Run linting
	@echo "Linting backend..."
	cd backend && black src/ tests/ --check
	cd backend && flake8 src/ tests/
	@echo "Linting frontend..."
	cd frontend && npm run lint

format: ## Format code
	@echo "Formatting backend..."
	cd backend && black src/ tests/
	@echo "Formatting frontend..."
	cd frontend && npm run format

build: ## Build production images
	@echo "Building production images..."
	docker-compose -f docker-compose.prod.yml build

deploy: ## Deploy to production
	@echo "Deploying to production..."
	docker-compose -f docker-compose.prod.yml up -d

clean: ## Clean up containers and volumes
	@echo "Cleaning up..."
	docker-compose down -v --rmi all --remove-orphans
	docker system prune -f

db-migrate: ## Run database migrations
	@echo "Running database migrations..."
	cd backend && python -m alembic upgrade head

db-seed: ## Seed database with test data
	@echo "Seeding database..."
	cd backend && python -m src.utils.seed_data

db-backup: ## Backup database
	@echo "Creating database backup..."
	docker-compose exec db pg_dump -U postgres bylaw_db > backups/backup_$(shell date +%Y%m%d_%H%M%S).sql

db-restore: ## Restore database (set BACKUP_FILE variable)
	@echo "Restoring database from $(BACKUP_FILE)..."
	docker-compose exec -T db psql -U postgres bylaw_db < $(BACKUP_FILE)

scrape-test: ## Run a test scraping job
	@echo "Running test scraping job..."
	cd backend && python -m src.scrapers.test_scraper

monitor: ## Open monitoring dashboard
	@echo "Opening monitoring dashboard..."
	open http://localhost:8000/docs

setup: ## Complete project setup
	@echo "Setting up bylaw-db project..."
	@echo "1. Creating environment files..."
	cp .env.example .env
	cp backend/.env.example backend/.env
	cp frontend/.env.example frontend/.env
	@echo "2. Installing dependencies..."
	$(MAKE) install
	@echo "3. Starting development environment..."
	$(MAKE) dev-bg
	@echo "4. Waiting for services to start..."
	sleep 30
	@echo "5. Running migrations..."
	$(MAKE) db-migrate
	@echo "6. Seeding database..."
	$(MAKE) db-seed
	@echo ""
	@echo "Setup complete! Access the application at:"
	@echo "  Frontend: http://localhost:3000"
	@echo "  Backend API: http://localhost:8000"
	@echo "  API Docs: http://localhost:8000/docs"
	@echo ""
	@echo "To stop the environment: make stop"