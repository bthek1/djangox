.PHONY: help pull-deploy push-deploy makemigrations migrate runserver createsuperuser collectstatic test install-nginx uninstall-nginx install-gunicorn uninstall-gunicorn

# Makefile

help:			## Show this help.
	@echo "Available commands:"
	@echo "For more information, see the README.md file."
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'


up: ## Start the project
	docker compose up -d

down: ## Stop the project
	docker compose down

build:  ## Build the project
	docker compose build

restart: down up ## Restart the project

logs: ## Show logs
	docker compose logs -f

shell: up ## Execute a shell in the web container
	docker compose exec web bash

makemigrations: up ## Make migrations
	docker compose exec web python manage.py makemigrations

migrate: makemigrations ## Apply migrations
	docker compose exec web python manage.py migrate

runserver: migrate  ## Run the Django development server
	docker compose exec web python manage.py runserver 0.0.0.0:8002

stopserver: ## Stop the Django development server
	docker compose exec web pkill -f "manage.py runserver"
	
superuser: ## Create a superuser
	docker compose exec web python manage.py createsuperuser --no-input

collectstatic: ## Collect static files
	docker compose exec web python manage.py collectstatic --noinput

test: ## Run tests
	docker compose exec web pytest

flush: ## Flush the database (delete all data!) 
	docker compose exec web python manage.py flush

clean_cache: ## Clear all cache in Django project
	@echo "Deleting all cache in Django project..."
	docker compose exec web find . -path "*/__pycache__" -exec rm -rf {} +
	docker compose exec web find . -name "*.pyc" -delete
	docker compose exec web find . -name "*.pyo" -delete
	@echo "Cache cleared successfully."

journal: ## View all relevant logs
	docker compose logs -f --tail=50 web db

rm-migrations: ## Remove all migration files
	@read -p "Delete ALL migrations? [y/N] " confirm; \
	if [ "$$confirm" != "y" ] && [ "$$confirm" != "Y" ]; then \
		exit 1; \
	fi
	docker compose exec web find . -path "*/migrations/0*.py" -delete
	docker compose exec web find . -path "*/migrations/0*.py" -delete
	@echo "Deleted all migrations. Run 'make migrate' to recreate them."
	
backup: ## Backup the database
	mkdir -p backups
	docker compose exec web python manage.py dumpdata --indent 2 > backups/db_backup_$(shell date +%Y%m%d_%H%M%S).json
	@echo "Backup completed and saved in the backups folder."


restore: ## Restore the database from the latest or specified backup
	@latest_backup=$$(ls -t ./backups/db_backup_*.json 2>/dev/null | head -n 1); \
	if [ -z "$$latest_backup" ]; then \
		echo "Error: No backup files found in the backups directory."; \
		exit 1; \
	fi; \
	read -p "Enter the backup file to restore (default: $$latest_backup): " backup_file; \
	backup_file=$${backup_file:-$$latest_backup}; \
	if [ ! -f "$$backup_file" ]; then \
		echo "Error: Backup file '$$backup_file' not found."; \
		exit 1; \
	fi; \
	echo "Restoring database from backup: $$backup_file"; \
	docker compose exec web python manage.py loaddata "$$backup_file"; \
	echo "Database restored from backup."
