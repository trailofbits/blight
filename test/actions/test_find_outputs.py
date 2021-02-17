import hashlib
import json

from blight.actions import FindOutputs
from blight.actions.find_outputs import OutputKind
from blight.tool import CC


def test_find_outputs(tmp_path):
    output = tmp_path / "outputs.jsonl"

    find_outputs = FindOutputs({"output": output})
    cc = CC(["-o", "foo", "foo.c"])
    find_outputs.before_run(cc)
    find_outputs.after_run(cc)

    outputs = json.loads(output.read_text())["outputs"]
    assert outputs == [
        {
            "kind": OutputKind.Executable.value,
            "path": str(cc.cwd / "foo"),
            "store_path": None,
        }
    ]


def test_find_outputs_multiple(tmp_path):
    fake_cs = [tmp_path / fake_c for fake_c in ["foo.c", "bar.c", "baz.c"]]
    [fake_c.touch() for fake_c in fake_cs]

    output = tmp_path / "outputs.jsonl"

    find_outputs = FindOutputs({"output": output})
    cc = CC(["-c", *[str(fake_c) for fake_c in fake_cs]])
    find_outputs.before_run(cc)
    find_outputs.after_run(cc)

    outputs = json.loads(output.read_text())["outputs"]
    assert outputs == [
        {
            "kind": OutputKind.Object.value,
            "path": str(cc.cwd / fake_c.with_suffix(".o").name),
            "store_path": None,
        }
        for fake_c in fake_cs
    ]


def test_find_outputs_handles_a_out(tmp_path):
    output = tmp_path / "outputs.jsonl"

    find_outputs = FindOutputs({"output": output})
    cc = CC(["foo.c"])
    find_outputs.before_run(cc)
    find_outputs.after_run(cc)

    outputs = json.loads(output.read_text())["outputs"]
    assert outputs == [
        {
            "kind": OutputKind.Executable.value,
            "path": str(cc.cwd / "a.out"),
            "store_path": None,
        }
    ]


def test_find_outputs_store(tmp_path):
    output = tmp_path / "outputs.jsonl"
    store = tmp_path / "store"
    contents = b"not a real object file"
    contents_digest = hashlib.sha256(contents).hexdigest()
    dummy_foo_o = tmp_path / "foo.o"
    dummy_foo_o_store = store / f"{dummy_foo_o.name}-{contents_digest}"

    find_outputs = FindOutputs({"output": output, "store": store})
    cc = CC(["-c", "foo.c", "-o", str(dummy_foo_o)])
    find_outputs.before_run(cc)
    # Pretend to be the compiler: write some junk to dummy_foo_o
    dummy_foo_o.write_bytes(contents)
    find_outputs.after_run(cc)

    outputs = json.loads(output.read_text())["outputs"]
    assert outputs == [
        {
            "kind": OutputKind.Object.value,
            "path": str(dummy_foo_o),
            "store_path": str(dummy_foo_o_store),
        }
    ]


def test_find_outputs_store_output_does_not_exist(tmp_path):
    output = tmp_path / "outputs.jsonl"
    store = tmp_path / "store"
    dummy_foo_o = tmp_path / "foo.o"

    find_outputs = FindOutputs({"output": output, "store": store})
    cc = CC(["-c", "foo.c", "-o", str(dummy_foo_o)])
    find_outputs.before_run(cc)
    find_outputs.after_run(cc)

    outputs = json.loads(output.read_text())["outputs"]
    assert outputs == [
        {
            "kind": OutputKind.Object.value,
            "path": str(dummy_foo_o),
            "store_path": None,
        }
    ]
