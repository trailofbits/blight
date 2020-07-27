from blight import enums


def test_optlevel_predictates():
    assert enums.OptLevel.OSize.for_size()
    assert enums.OptLevel.OSizeZ.for_size()

    assert enums.OptLevel.O1.for_performance()
    assert enums.OptLevel.O2.for_performance()
    assert enums.OptLevel.O3.for_performance()
    assert enums.OptLevel.OFast.for_performance()

    assert enums.OptLevel.ODebug.for_debug()
