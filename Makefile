.PHONY: run test-archive install

PYTHON ?= python3

install:
	$(PYTHON) -m pip install -r requirements.txt

run:
	$(PYTHON) flask_app.py

# Rebuild archive from SQL dumps and print sanity-check output.
test-archive:
	$(PYTHON) scripts/test_archive.py
