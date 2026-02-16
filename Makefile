.PHONY: all fmt test changelog

all: fmt test

fmt:
	ruff format
	ruff check --fix

test:
	pytest

run:
	python euemastobot.py

changelog:
	git-cliff -o CHANGELOG.md
