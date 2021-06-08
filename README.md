blight
======

![CI](https://github.com/trailofbits/blight/workflows/CI/badge.svg)

`blight` is a framework for wrapping and instrumenting build tools.

## Usage

```bash
$ pip3 install blight
$ eval $(blight-env --guess-wrapped)
$ export BLIGHT_ACTIONS="Record"
$ export BLIGHT_ACTION_RECORD="output=/tmp/demo.jsonl"
$ cd /your/project && make
$ cat /tmp/demo.jsonl
```

## Goals

* Wrapping `CC`, `CXX`, `CPP`, `LD`, `AS`, `AR`, `STRIP`, and `INSTALL`.
* Providing a visitor-style API for each of the above, pre- and post-execution.
* Providing a nice set of default actions.
* Being as non-invasive as possible.

## Anti-goals

* Using `LD_PRELOAD` to capture every `exec` in a build system,
a la [Bear](https://github.com/rizsotto/Bear).
* Supporting `cl.exe`.
* Detailed support for non C/C++ languages.

## Contributing a new action

New blight actions are easy to write. For example, the following prints a message before every `ld`
invocation:

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
$ eval $(blight-env --guess-wrapped)
$ export BLIGHT_ACTIONS="PrintLD"
$ make
```

Check out blight's [API documentation](https://trailofbits.github.io/blight) for more details,
including the kinds of available actions.

## The name?

Build systems and tools that instrument build systems are a blight on my productivity.
