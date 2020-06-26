ALL_PY_SRCS := $(shell find src -name '*.py') \
	$(shell find test -name '*.py')

.PHONY: all
all:
	@echo "Run my targets individually!"

.PHONY: dev
dev:
	test -d env || python3 -m venv env
	. env/bin/activate && pip install -e .[dev]

.PHONY: lint
.ONESHELL:
lint:
	. env/bin/activate
	black $(ALL_PY_SRCS)
	isort $(ALL_PY_SRCS)
	flake8 $(ALL_PY_SRCS)
	git diff --exit-code

.PHONY: test
.ONESHELL:
test:
	. env/bin/activate
	pytest --cov=canker test/
	python -m coverage report -m --fail-under 100

.PHONY: doc
.ONESHELL:
doc:
	. env/bin/activate
	PYTHONWARNINGS='error::UserWarning' pdoc --force --html canker

.PHONY: package
.ONESHELL:
package:
	. env/bin/activate
	python3 setup.py sdist
	twine upload --repository pypi dist/*

.PHONY: edit
edit:
	$(EDITOR) $(ALL_PY_SRCS)
