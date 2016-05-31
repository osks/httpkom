all: pyflakes docs

run-debug-server-py2:
	HTTPKOM_SETTINGS=../configs/debug.cfg python2 ./runserver.py

run-debug-server-py3:
	HTTPKOM_SETTINGS=../configs/debug.cfg python3 ./runserver.py

docs: docs-html

docs-html:
	make -C docs html
	cp -r ./docs/_build/html/* ./gh-pages/html/

pyflakes:
	pyflakes ./httpkom

#test: pyflakes
#	py.test -v --maxfail 1 ./tests

.PHONY: all run-debug-server-py2 run-debug-server-py3 docs docs-html pyflakes
