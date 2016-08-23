all: pyflakes docs

run-debug-server-py2:
	python2 -m httpkom.main --config ../configs/debug.cfg

run-debug-server-py3:
	python3 -m httpkom.main --config ../configs/debug.cfg

docs: docs-html

docs-html:
	make -C docs html
	cp -r ./docs/_build/html/* ./gh-pages/html/

pyflakes:
	pyflakes ./httpkom

#test: pyflakes
#	py.test -v --maxfail 1 ./tests

.PHONY: all run-debug-server-py2 run-debug-server-py3 docs docs-html pyflakes
