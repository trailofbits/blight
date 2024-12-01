from blight.actions import EmbedCommands
from blight.tool import CC


def test_embed_bitcode():
    embed_bitcode = EmbedCommands({})
    cc1 = CC(["-o", "foo"])
    embed_bitcode.before_run(cc1)
    cc2 = CC(["foo.S"])
    embed_bitcode.before_run(cc2)
