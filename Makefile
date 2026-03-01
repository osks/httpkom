all: pyflakes docs

clean:
	rm -rf dist
	rm -rf site

run-debug-server:
	python3 -m httpkom --config configs/debug.cfg --host 127.0.0.1

dist:
	rm -rf dist
	uv build

docs:
	uv run mkdocs build --strict

docs-serve:
	uv run mkdocs serve

tox:
	uvx tox

pyflakes:
	pyflakes ./httpkom

.PHONY: all clean run-debug-server dist docs docs-serve tox pyflakes
