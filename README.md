canker
======

![CI](https://github.com/trailofbits/canker/workflows/CI/badge.svg)

`canker` is a catch-all compile tool wrapper.

## Usage

```bash
$ pip3 install canker
$ eval $(canker-env --guess-wrapped)
$ export CANKER_ACTIONS="Record"
$ export CANKER_ACTION_RECORD="output=/tmp/demo.jsonl"
$ cd /your/project && make
$ cat /tmp/demo.jsonl
```

## Goals

* Wrapping `CC`, `CXX`, `CPP`, `LD`, and `AS`.
* Providing a visitor-style API for each of the above, pre- and post-execution.
* Providing a nice set of default actions.
* Being as non-invasive as possible.

## Anti-goals

* Using `LD_PRELOAD` to capture every `exec` in a build system,
a la [Bear](https://github.com/rizsotto/Bear).
* Supporting `cl.exe`.
* Detailed support for non C/C++ languages.
* Parsing arguments that are passed via `@file`.

## Contributing a new action

New canker actions are easy to write. For example, the following prints a message before every `ld`
invocation:

```python
# src/canker/actions/printld.py

from canker.action import LDAction


class PrintLD(LDAction):
    def before_run(self, tool):
        print(f"ld was run with: {tool.args}")
```

```python
# src/canker/actions/__init__.py

# bring PrintLD into canker.actions so that `CANKER_ACTIONS` can find it
from printld import PrintLD  # noqa: F401
```

```bash
$ eval $(canker-env --guess-wrapped)
$ export CANKER_ACTIONS="PrintLD"
$ make
```

Check out canker's [API documentation](https://trailofbits.github.io/canker) for more details,
including the kinds of available actions.

## The name?

My phone autocorrected "CMake" to "canker" once.

Canker is cognate with cancer, which is appropriate for both build systems and tools
that instrument build systems (like canker does).
