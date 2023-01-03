ALL_PY_SRCS := $(shell find src -name '*.py') \
	$(shell find test -name '*.py')

.PHONY: all
all:
	@echo "Run my targets individually!"

.PHONY: dev
dev:
	test -d env || python -m venv env
	. env/bin/activate && \
		pip install --upgrade pip setuptools && \
		pip install -e .[dev]

.PHONY: lint
lint:
	. env/bin/activate && \
		black $(ALL_PY_SRCS) && \
		isort $(ALL_PY_SRCS) && \
		flake8 $(ALL_PY_SRCS) && \
		mypy src && \
		git diff --exit-code

.PHONY: test
test:
	. env/bin/activate && \
		pytest --cov=blight test/ && \
		python -m coverage report -m --fail-under 100

.PHONY: doc
doc:
	. env/bin/activate && \
		PYTHONWARNINGS='error::UserWarning' pdoc --force --html blight

.PHONY: package
package:
	. env/bin/activate && \
		python -m build && \
		twine upload --repository pypi dist/*

.PHONY: edit
edit:
	$(EDITOR) $(ALL_PY_SRCS)
