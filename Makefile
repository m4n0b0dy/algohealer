install-playwright:
	poetry run playwright install

run:
	poetry run python lib/exec/main.py

format:
	black .

shell:
	poetry shell

pre-commit:
	pre-commit run --all-files
