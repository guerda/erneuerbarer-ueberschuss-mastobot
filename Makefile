.PHONY: all fmt test changelog

all: fmt test

fmt:
	ruff format
	uv run ruff check --select I --fix

test:
	pytest

run:
	python euemastobot.py

changelog:
	git-cliff -o CHANGELOG.md
