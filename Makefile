# Optionally overriden by the user, if they're using a virtual environment manager.
VENV ?= env
VENV_EXISTS := $(VENV)/pyvenv.cfg

# On Windows, venv scripts/shims are under `Scripts` instead of `bin`.
VENV_BIN := $(VENV)/bin
ifeq ($(OS),Windows_NT)
	VENV_BIN := $(VENV)/Scripts
endif

# Optionally overridden by the user/CI, to limit the installation to a specific
# subset of development dependencies.
BLIGHT_EXTRA := dev

ALL_PY_SRCS := $(shell find src -name '*.py') \
	$(shell find test -name '*.py')

.PHONY: all
all:
	@echo "Run my targets individually!"

$(VENV)/pyvenv.cfg: pyproject.toml
	python -m venv env
	. $(VENV_BIN)/activate && \
		pip install --upgrade pip setuptools && \
		pip install -e .[$(BLIGHT_EXTRA)]

.PHONY: dev
dev: $(VENV)/pyvenv.cfg

.PHONY: lint
lint: $(VENV_EXISTS)
	. $(VENV_BIN)/activate && \
		black --check $(ALL_PY_SRCS) && \
		ruff $(ALL_PY_SRCS) && \
		mypy src

.PHONY: format
format: $(VENV_EXISTS)
	. $(VENV_BIN)/activate && \
		ruff --fix $(ALL_PY_SRCS) && \
		black $(ALL_PY_SRCS)

.PHONY: test
test: $(VENV_EXISTS)
	. $(VENV_BIN)/activate && \
		pytest --cov=blight test/ && \
		python -m coverage report -m --fail-under 100

.PHONY: doc
doc: $(VENV_EXISTS)
	. $(VENV_BIN)/activate && \
		PYTHONWARNINGS='error::UserWarning' pdoc --force --html blight

.PHONY: package
package: $(VENV_EXISTS)
	. $(VENV_BIN)/activate && \
		python -m build && \
		twine upload --repository pypi dist/*

.PHONY: edit
edit:
	$(EDITOR) $(ALL_PY_SRCS)
