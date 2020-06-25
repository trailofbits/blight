canker
======

`canker` is a catch-all compile-tool wrapper.

## Usage

```bash
$ pip3 install canker
$ eval $(canker-env --guess-wrapped)
$ export CANKER_ACTIONS="Record"
$ export CANKER_ACTION_RECORD_FILE=/tmp/demo.jsonl
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

## The name?

My phone autocorrected "CMake" to "canker" once.

Canker is cognate with cancer, which is appropriate for both build systems and tools
that instrument build systems (like canker does).
