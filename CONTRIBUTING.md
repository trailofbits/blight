# Contributing to `blight`

Thank you for your interest in contributing to `blight`!

The information below will help you set up a local development environment,
as well as performing common development tasks.

- [Requirements](#requirements)
- [Development steps](#development-steps)
  - [Linting](#linting)
  - [Testing](#testing)
  - [Documentation](#documentation)
- [Contributing a new action](#contributing-a-new-action)

## Requirements

`blight`'s only requirement is Python 3.8 or newer.

Development and testing is actively performed on macOS and Linux, but Windows
and other supported platforms that are supported by Python should also work.

If you're on a system that has GNU Make, you can use the convenience targets
included in the Makefile that comes in the `blight` repository detailed below.
But this isn't required; all steps can be done without Make.

## Development steps

First, clone this repository:

```bash
git clone https://github.com/trailofbits/blight
cd blight
```

Then, use one of the `Makefile` targets to run a task. The first time this is
run, this will also set up the local development virtual environment, and will
install `blight` as an editable package into this environment.

Any changes you make to the `src/blight` source tree will take effect
immediately in the virtual environment.

### Linting

This repository uses [trunk.io](https://trunk.io) and the `trunk` CLI for
linting.

If you don't already have `trunk`, you can download it with one of the
following:

```bash
# macOS (Homebrew Cask)
brew install trunk-io

# all platforms
curl https://get.trunk.io -fsSL | bash
```

Once installed, you can run `trunk check` and `trunk fmt` for all linting
and auto-formatting, or use the Makefile:

```bash
# run all linters
make lint

# run all auto-formatters
make format
```

By default, only modified files are checked.

### Testing

You can run the tests locally with:

```bash
make test
```

You can also filter by a pattern (uses `pytest -k`):

```bash
make test TESTS=test_audit_dry_run
```

To test a specific file:

```bash
make test T=path/to/file.py
```

`blight` has a [`pytest`](https://docs.pytest.org/)-based unit test suite,
including code coverage with [`coverage.py`](https://coverage.readthedocs.io/).

### Documentation

If you're running Python 3.7 or newer, you can run the documentation build locally:

```bash
make doc
```

`blight` uses [`pdoc`](https://github.com/mitmproxy/pdoc) to generate HTML
documentation for its public Python APIs.

Live documentation for the `master` branch is hosted
[here](https://trailofbits.github.io/blight/).

## Contributing a new action

New blight actions are easy to write. For example, the following prints a
message before every `ld` invocation:

```python
# src/blight/actions/printld.py

from blight.action import LDAction


class PrintLD(LDAction):
    def before_run(self, tool):
        print(f"ld was run with: {tool.args}")
```

```python
# src/blight/actions/__init__.py

# bring PrintLD into blight.actions so that `BLIGHT_ACTIONS` can find it
from printld import PrintLD  # noqa: F401
```

```bash
eval $(blight-env --guess-wrapped)
export BLIGHT_ACTIONS="PrintLD"
make
```

Check out blight's [API documentation](https://trailofbits.github.io/blight)
for more details, including the kinds of available actions.
