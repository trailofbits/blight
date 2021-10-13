from blight.actions import EmbedBitcode
from blight.tool import CC


def test_embed_bitcode():
    embed_bitcode = EmbedBitcode({})
    cc = CC(["-o", "foo"])
    embed_bitcode.before_run(cc)

    assert cc.args[0] == "-fembed-bitcode"
