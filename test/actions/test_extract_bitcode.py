import os

from blight.actions import BitcodeExtract
from blight.tool import CC


def test_extract_bitcode_output(tmp_path):
    bitcode_extract = BitcodeExtract({"store": tmp_path.__str__()})
    cc = CC(["-o", "foo", "test/fixtures/foo.c"])

    bitcode_extract.before_run(cc)
    assert (tmp_path / "foo.bc").exists()


def test_extract_bitcode_no_specified_output(tmp_path):
    bitcode_extract = BitcodeExtract({"store": tmp_path.__str__()})
    cc = CC(["test/fixtures/foo.c"])

    bitcode_extract.before_run(cc)
    assert (tmp_path / "foo.bc").exists()


def test_extract_bitcode_unknown_lang(tmp_path):
    bitcode_extract = BitcodeExtract({"store": tmp_path.__str__()})
    cc = CC(["-x", "-unknownlanguage", "-Werror"])

    bitcode_extract.before_run(cc)
    assert not (tmp_path / "foo.bc").exists()


def test_extract_bitcode_gen_flags(tmp_path):
    os.environ.update(
        {
            "LLVM_BITCODE_GENERATION_FLAGS": "-flto",
        }
    )
    bitcode_extract = BitcodeExtract({"store": tmp_path.__str__()})
    cc = CC(["-o", "foo", "test/fixtures/foo.c"])

    bitcode_extract.before_run(cc)
    assert (tmp_path / "foo.bc").exists()
