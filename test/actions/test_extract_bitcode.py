import os

from blight.actions import BitcodeExtract
from blight.tool import CC


def test_extract_bitcode_output(tmp_path):
    bitcode_extract = BitcodeExtract({})
    cc = CC(["-o", (tmp_path / "foo").__str__(), "test/fixtures/foo.c"])

    bitcode_extract.before_run(cc)
    assert (tmp_path / "foo.bc").exists()


def test_extract_bitcode_no_specified_output(tmp_path):
    bitcode_extract = BitcodeExtract({})
    cwd = os.getcwd()
    cc = CC([cwd + "/test/fixtures/foo.c"])

    os.chdir(tmp_path)
    bitcode_extract.before_run(cc)
    os.chdir(cwd)
    assert (tmp_path / "a.out.bc").exists()


def test_extract_bitcode_unknown_lang(tmp_path):
    bitcode_extract = BitcodeExtract({})
    cc = CC(["-x", "-unknownlanguage", "-Werror", "-o", (tmp_path / "foo").__str__()])

    bitcode_extract.before_run(cc)
    assert not (tmp_path / "foo.bc").exists()


def test_extract_bitcode_gen_flags(tmp_path):
    os.environ.update(
        {
            "LLVM_BITCODE_GENERATION_FLAGS": "-flto",
        }
    )
    bitcode_extract = BitcodeExtract({})
    cc = CC(["-o", (tmp_path / "foo").__str__(), "test/fixtures/foo.c"])

    bitcode_extract.before_run(cc)
    assert (tmp_path / "foo.bc").exists()
