install:
	poetry install

lint:
	poetry run flake8
	poetry run black --check --diff .
	poetry run isort --check-only .
	poetry run ocdc --check

format:
	poetry run isort .
	poetry run black .
	poetry run ocdc

test:
	poetry run mypy ocdc/ tests/
	poetry run coverage run -m pytest --failed-first -vv
	poetry run coverage report
	poetry run coverage html
