all: pyflakes docs

run-debug-server:
	python3 -m httpkom.main --config configs/debug.cfg --host 127.0.0.1

docs: docs-html

docs-html:
	make -C docs html
	cp -r ./docs/_build/html/* ./gh-pages/html/

pyflakes:
	pyflakes ./httpkom

#test: pyflakes
#	py.test -v --maxfail 1 ./tests

.PHONY: all run-debug-server docs docs-html pyflakes
