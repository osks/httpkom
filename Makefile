all: pyflakes docs

run-debug-server:
	HTTPKOM_SETTINGS=../configs/debug.cfg ./runserver.py

docs: docs-html

docs-html:
	make -C docs html
	cp -r ./docs/_build/html/* ./gh-pages/html/

pyflakes:
	pyflakes ./httpkom
	pyflakes ./pylyskomrpc

test: pyflakes
	py.test --maxfail 1 ./tests

.PHONY: all run-debug-server docs docs-html pyflakes test
