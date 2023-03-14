.PHONY: all update

all:
	@echo "Hello $(LOGNAME)"
	@echo "Try 'make help'"


# target: help - Display callable targets.
help:
	@grep -E "^# target:" [Mm]akefile


# target: update - Update pip packages
update:
	rm -f requirements.txt requirements-dev.txt requirements-test.txt
	pip-compile -q --output-file=requirements.txt --resolver=backtracking pyproject.toml
	pip-compile -q --extra=dev --output-file=requirements-dev.txt --resolver=backtracking pyproject.toml
	pip-compile -q --extra=test --output-file=requirements-test.txt --resolver=backtracking pyproject.toml
	pip-sync requirements-dev.txt
