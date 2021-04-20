import hashlib
import os
from pathlib import Path

from blight.actions import BitcodeExtract
from blight.tool import CC


def test_extract_bitcode_output(tmp_path):
    bitcode_extract = BitcodeExtract({"store": tmp_path.__str__()})
    foo_path = "test/fixtures/foo.c"
    cc = CC(["-o", "foo", foo_path])

    bitcode_extract.before_run(cc)
    content_hash = hashlib.sha256(Path(foo_path).read_bytes()).hexdigest()
    assert (tmp_path / (content_hash + ".bc")).exists()


def test_extract_bitcode_no_specified_output(tmp_path):
    bitcode_extract = BitcodeExtract({"store": tmp_path.__str__()})
    foo_path = "test/fixtures/foo.c"
    cc = CC([foo_path])

    bitcode_extract.before_run(cc)
    content_hash = hashlib.sha256(Path(foo_path).read_bytes()).hexdigest()
    assert (tmp_path / (content_hash + ".bc")).exists()


def test_extract_bitcode_wrong_stage(tmp_path):
    bitcode_extract = BitcodeExtract({"store": tmp_path.__str__()})
    foo_path = "test/fixtures/foo.c"
    cc = CC(["-o", "foo", "-S", foo_path])

    bitcode_extract.before_run(cc)
    assert not os.listdir(tmp_path)


def test_extract_bitcode_no_store(tmp_path):
    bitcode_extract = BitcodeExtract({})
    foo_path = "test/fixtures/foo.c"
    cc = CC(["-o", "foo", foo_path])

    bitcode_extract.before_run(cc)
    assert not os.listdir(tmp_path)


def test_extract_bitcode_gen_flags(tmp_path):
    bitcode_extract = BitcodeExtract({"store": tmp_path.__str__(), "llvm-bitcode-flags": "-flto"})
    foo_path = "test/fixtures/foo.c"
    cc = CC(["-o", "foo", foo_path])

    bitcode_extract.before_run(cc)
    content_hash = hashlib.sha256(Path(foo_path).read_bytes()).hexdigest()
    assert (tmp_path / (content_hash + ".bc")).exists()
