.PHONY: help install test run clean

help:
	@echo "Available commands:"
	@echo "  make install   - Install dependencies"
	@echo "  make test      - Run tests"
	@echo "  make run       - Run the application"
	@echo "  make clean     - Clean up temporary files"

install:
	pip install -r requirements.txt

test:
	python -m pytest

run:
	python main.py

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
