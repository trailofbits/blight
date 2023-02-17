# blight

![CI](https://github.com/trailofbits/blight/workflows/CI/badge.svg)
[![PyPI version](https://badge.fury.io/py/blight.svg)](https://badge.fury.io/py/blight)
[![Downloads](https://pepy.tech/badge/blight)](https://pepy.tech/project/blight)

`blight` is a framework for wrapping and instrumenting build tools and build
systems. It contains:

1. A collection of high-fidelity models for various common build tools (e.g.
   the C and C++ compilers, the standard linker, the preprocessor, etc.);
1. A variety of "actions" that can be run on each build tool or specific
   classes of tools (e.g. "whenever the build system invokes `$CC`, add this
   flag");
1. Command-line wrappers (`blight-env` and `blight-exec`) for instrumenting
   builds.

- [Installation](#installation)
- [Usage](#usage)
- [Quickstart](#quickstart)
- [Cookbook](#cookbook)
- [Goals](#goals)
- [Anti-goals](#anti-goals)
- [Contributing](#contributing)

## Installation

`blight` is available on PyPI and is installable via `pip`:

```bash
python -m pip install blight
```

Python 3.7 or newer is required.

## Usage

`blight` comes with two main entrypoints:

- `blight-exec`: directly execute a command within a `blight`-instrumented
  environment
- `blight-env`: write a `sh`-compatible environment definition to `stdout`,
  which the shell or other tools can consume to enter a `blight`-instrumented
  environment

In most cases, you'll probably want `blight-exec`. `blight-env` can be thought
of as the "advanced" or "plumbing" interface.

<!-- @begin-blight-exec-help@ -->

```text
Usage: blight-exec [OPTIONS] TARGET [ARGS]...

Options:
  --guess-wrapped      Attempt to guess the appropriate programs to wrap
  --swizzle-path       Wrap via PATH swizzling
  --stub STUB          Stub a command out while swizzling
  --shim SHIM          Add a custom shim while swizzling
  --action ACTION      Enable an action
  --journal-path PATH  The path to use for action journaling
  --help               Show this message and exit.
```

<!-- @end-blight-exec-help@ -->

<!-- @begin-blight-env-help@ -->

```text
Usage: blight-env [OPTIONS]

Options:
  --guess-wrapped  Attempt to guess the appropriate programs to wrap
  --swizzle-path   Wrap via PATH swizzling
  --stub TEXT      Stub a command out while swizzling
  --shim TEXT      Add a custom shim while swizzling
  --unset          Unset the tool variables instead of setting them
  --help           Show this message and exit.
```

<!-- @end-blight-env-help@ -->

## Quickstart

The easiest way to get started with `blight` is to use `blight-exec` with
`--guess-wrapped` and `--swizzle-path`. These flags tell `blight` to configure
the environment with some common-sense defaults:

- `--guess-wrapped`: guess the appropriate underlying tools to invoke from
  the current `PATH` and other runtime environment;
- `--swizzle-path`: rewrite the `PATH` to put some common build tool shims
  first, e.g. redirecting `cc` to `blight-cc`.

For example, the following will run `cc -v` under `blight`'s instrumentation,
with the [`Demo`](https://trailofbits.github.io/blight/blight/actions/demo.html)
action:

```bash
blight-exec --action Demo --swizzle-path --guess-wrapped -- cc -v
```

which should produce something like:

```console
[demo] before-run: /usr/bin/cc
Apple clang version 14.0.0 (clang-1400.0.29.202)
Target: x86_64-apple-darwin22.2.0
Thread model: posix
InstalledDir: /Library/Developer/CommandLineTools/usr/bin
[demo] after-run: /usr/bin/cc
```

We can also see the effect of `--swizzle-path` by running `which cc` under
`blight`, and observing that it points to a temporary shim rather than the
normal `cc` location:

```bash
$ blight-exec --swizzle-path --guess-wrapped -- which cc
/var/folders/zj/hy934vnj5xs68zv6w4b_f6s40000gn/T/tmp5uahp6tg@blight-swizzle@/cc

$ which cc
/usr/bin/cc
```

All the `Demo` action does is print a message before and after each tool run,
allowing you to diagnose when a tool is or isn't correctly instrumented.
See the [actions documentation below](#enabling-actions) for information on
using and configuring more interesting actions.

## Cookbook

### Running `blight` against a `make`-based build

Most `make`-based builds use `$(CC)`, `$(CXX)`, etc., which means that they
should work out of the box with `blight-exec`:

```bash
blight-exec --guess-wrapped -- make
```

In some cases, poorly written builds may hard-code `cc`, `clang`, `gcc`, etc.
rather than using their symbolic counterparts. For these, you can use
`--swizzle-path` to interpose shims that redirect those hardcoded tool
invocations back to `blight`'s wrappers:

```bash
blight-exec --guess-wrapped --swizzle-path -- make
```

See [Taming an uncooperative build with shims and stubs](#taming-an-uncooperative-build-with-shims-and-stubs)
for more advanced techniques for dealing with poorly written build systems.

### Enabling actions

Actions are where `blight` really shines: they allow you to run arbitrary Python
code before and after each build tool invocation.

`blight` comes with built-in actions, which are
[documented here](https://trailofbits.github.io/blight/blight/actions.html).
See each action's Python module for its documentation.

Actions can be enabled in two different ways:

- With the `--action` flag, which can be passed multiple times. For example,
  `--action SkipStrip --action Record` enables both the
  [`SkipStrip`](https://trailofbits.github.io/blight/blight/actions/skip_strip.html)
  and [`Record`](https://trailofbits.github.io/blight/blight/actions/record.html)
  actions.

- With the `BLIGHT_ACTIONS` environment variable, which can take multiple
  actions delimited by `:`. For example, `BLIGHT_ACTIONS=SkipStrip:Record`
  is equivalent to `--action SkipStrip --action Record`.

Actions are run in the order of specification with duplicates removed, meaning
that `BLIGHT_ACTIONS=Foo:Bar:Foo` is equivalent to `BLIGHT_ACTIONS=Foo:Bar`
but **not** `BLIGHT_ACTIONS=Bar:Foo`. This is important if actions have side
effects, which they may (such as modifying the tool's flags).

#### Action configuration

Some actions accept or require additional configuration, which is passed
through the `BLIGHT_ACTION_{ACTION}` environment variable in `key=value`
format, where `{ACTION}` is the uppercased name of the action.

For example, to configure `Record`'s output file:

```bash
BLIGHT_ACTION_RECORD="output=/tmp/output.jsonl"
```

#### Action outputs

There are two ways to get output from actions under `blight`:

- Many actions support an `output` configuration value, which should be a
  filename to write to. This allows each action to write its own output
  file.
- `blight` supports a "journaling" mode, in which all action outputs
  are written to a single file, keyed by action name.

The "journaling" mode is generally encouraged over individual outputs,
and can be enabled with either `BLIGHT_JOURNAL_PATH=/path/to/output.jsonl`
in the environment or `blight-exec --journal-path /path/to/output.jsonl`.

### Configuring an environment with `blight-env`

`blight-env` behaves exactly the same as `blight-exec`, except that it
stops before actually executing anything. You can use it to set up an
environment for use across multiple build system runs.

By default, `blight-env` will just export the appropriate environment
for replacing `CC`, etc., with their `blight` wrappers:

```bash
$ blight-env
export CC=blight-cc
export CXX=blight-c++
export CPP=blight-cpp
export LD=blight-ld
export AS=blight-as
export AR=blight-ar
export STRIP=blight-strip
export INSTALL=blight-install
```

`--guess-wrapped` augments this by adding a best-guess underlying tool for
each wrapper:

```bash
$ blight-env --guess-wrapped
export BLIGHT_WRAPPED_CC=/usr/bin/cc
export BLIGHT_WRAPPED_CXX=/usr/bin/c++
export BLIGHT_WRAPPED_CPP=/usr/bin/cpp
export BLIGHT_WRAPPED_LD=/usr/bin/ld
export BLIGHT_WRAPPED_AS=/usr/bin/as
export BLIGHT_WRAPPED_AR=/usr/bin/ar
export BLIGHT_WRAPPED_STRIP=/usr/bin/strip
export BLIGHT_WRAPPED_INSTALL=/usr/bin/install
export CC=blight-cc
export CXX=blight-c++
export CPP=blight-cpp
export LD=blight-ld
export AS=blight-as
export AR=blight-ar
export STRIP=blight-strip
export INSTALL=blight-install
```

`--guess-wrapped` also respects `CC`, etc. in the environment:

```bash
$ CC=/some/custom/cc blight-env --guess-wrapped
export BLIGHT_WRAPPED_CC=/some/custom/cc
export BLIGHT_WRAPPED_CXX=/usr/bin/c++
export BLIGHT_WRAPPED_CPP=/usr/bin/cpp
export BLIGHT_WRAPPED_LD=/usr/bin/ld
export BLIGHT_WRAPPED_AS=/usr/bin/as
export BLIGHT_WRAPPED_AR=/usr/bin/ar
export BLIGHT_WRAPPED_STRIP=/usr/bin/strip
export BLIGHT_WRAPPED_INSTALL=/usr/bin/install
export CC=blight-cc
export CXX=blight-c++
export CPP=blight-cpp
export LD=blight-ld
export AS=blight-as
export AR=blight-ar
export STRIP=blight-strip
export INSTALL=blight-install
```

`--swizzle-path` further modifies the environment by rewriting `PATH`:

```bash
$ blight-env --guess-wrapped-swizzle-path
export BLIGHT_WRAPPED_CC=/usr/bin/cc
export BLIGHT_WRAPPED_CXX=/usr/bin/c++
export BLIGHT_WRAPPED_CPP=/usr/bin/cpp
export BLIGHT_WRAPPED_LD=/usr/bin/ld
export BLIGHT_WRAPPED_AS=/usr/bin/as
export BLIGHT_WRAPPED_AR=/usr/bin/ar
export BLIGHT_WRAPPED_STRIP=/usr/bin/strip
export BLIGHT_WRAPPED_INSTALL=/usr/bin/install
export PATH='/var/folders/zj/hy934vnj5xs68zv6w4b_f6s40000gn/T/tmpxh5ryu22@blight-swizzle@:/bin:/usr/bin:/usr/local/bin'
export CC=blight-cc
export CXX=blight-c++
export CPP=blight-cpp
export LD=blight-ld
export AS=blight-as
export AR=blight-ar
export STRIP=blight-strip
export INSTALL=blight-install
```

The swizzled addition can be identified by its `@blight-swizzle@` directory name.

### Taming an uncooperative build with shims and stubs

Sometimes build systems need more coaxing than just `--guess-wrapped` and
`--swizzle-path`. Common examples include:

- Hard-coding a particular tool or tool version rather than using the symbolic
  name (e.g. `clang-7 example.c` instead of `$(CC) example.c`);
- Running lots of "junk" commands that can be suppressed (e.g. lots of `echo`
  invocations)

You can use _shims_ and _stubs_ to smooth out these cases:

- _shims_ replace a command with a build tool that `blight` knows about, e.g.
  `clang-3.8` with `cc`.
- _stubs_ replace a command with an invocation of `true`, meaning that it
  does nothing and never fails.

Shims are specified with `--shim cmd:tool`, while stubs are specified with
`--stub cmd`. Both require `--swizzle-path`, since the `PATH` must be rewritten
to inject additional commands.

For example, to instrument a build system that hardcodes `tcc` everywhere
and that spews way too much output with `echo`:

```bash
blight-exec --guess-wrapped --swizzle-path --shim tcc:cc --stub echo -- make
```

## Goals

- Wrapping `CC`, `CXX`, `CPP`, `LD`, `AS`, `AR`, `STRIP`, and `INSTALL`.
- Providing a visitor-style API for each of the above, pre- and post-execution.
- Providing a nice set of default actions.
- Being as non-invasive as possible.

## Anti-goals

- Using `LD_PRELOAD` to capture every `exec` in a build system,
  a la [Bear](https://github.com/rizsotto/Bear).
- Supporting `cl.exe`.
- Detailed support for non C/C++ languages.

## Contributing

Check out our [CONTRIBUTING.md](./CONTRIBUTING.md)!
