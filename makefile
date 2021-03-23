.PHONY: all update

all:
	@echo "Hello $(LOGNAME)"
	@echo "Try 'make help'"


# target: help - Display callable targets.
help:
	@egrep "^# target:" [Mm]akefile


# target: update - Update pip venv packages
update:
	pipenv update
	pipenv lock -r > requirements.txt
	pipenv lock -r --dev-only > requirements-dev.txt


# target: lock - Lock the pipenv requirements.txt
lock:
	pipenv lock -r > requirements.txt
	pipenv lock -r --dev-only > requirements-dev.txt
