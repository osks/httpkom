all: docs

run-debug-server:
	HTTPKOM_SETTINGS=../configs/debug.cfg ./runserver.py

docs: docs-html

docs-html:
	make -C docs html


.PHONY: all run-debug-server docs docs-html
