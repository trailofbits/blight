VENV := env
VENV_EXISTS := $(VENV)/pyvenv.cfg

ALL_PY_SRCS := $(shell find src -name '*.py') \
	$(shell find test -name '*.py')

.PHONY: all
all:
	@echo "Run my targets individually!"

$(VENV)/pyvenv.cfg: pyproject.toml
	python -m venv env
	. $(VENV)/bin/activate && \
		pip install --upgrade pip setuptools && \
		pip install -e .[dev]

.PHONY: dev
dev: $(VENV)/pyvenv.cfg

.PHONY: lint
lint: $(VENV_EXISTS)
	. $(VENV)/bin/activate && \
		black --check $(ALL_PY_SRCS) && \
		isort --check $(ALL_PY_SRCS) && \
		flake8 $(ALL_PY_SRCS) && \
		mypy src

.PHONY: test
test:
	. $(VENV)/bin/activate && \
		pytest --cov=blight test/ && \
		python -m coverage report -m --fail-under 100

.PHONY: doc
doc:
	. $(VENV)/bin/activate && \
		PYTHONWARNINGS='error::UserWarning' pdoc --force --html blight

.PHONY: package
package:
	. $(VENV)/bin/activate && \
		python -m build && \
		twine upload --repository pypi dist/*

.PHONY: edit
edit:
	$(EDITOR) $(ALL_PY_SRCS)
