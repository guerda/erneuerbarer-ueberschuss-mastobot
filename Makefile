.PHONY: all fmt qa deps test run changelog

all: fmt test qa deps

fmt:
	ruff format
	ruff check --select I --fix
qa:
	ruff check
	ty check

deps:
	pip-audit

test:
	pytest

run:
	python euemastobot.py

changelog:
	git-cliff -o CHANGELOG.md
