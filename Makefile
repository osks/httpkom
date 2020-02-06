all: pyflakes docs

clean:
	rm -rf dist
	rm -rf docs/_build
	rm -rf gh-pages

run-debug-server:
	python3 -m httpkom --config configs/debug.cfg --host 127.0.0.1

dist:
	rm -rf dist
	python3 setup.py sdist

docs: docs-html

docs-html:
	make -C docs html
	mkdir -p gh-pages/html
	cp -r ./docs/_build/html/* ./gh-pages/html/

pyflakes:
	pyflakes ./httpkom

.PHONY: all clean run-debug-server dist docs docs-html pyflakes
