.PHONY: all fmt test changelog

all: fmt test

fmt:
	ruff format
	ruff check --select I --fix
qa:
	ruff check
	ty check
	

test:
	pytest

run:
	python euemastobot.py

changelog:
	git-cliff -o CHANGELOG.md
