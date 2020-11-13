from blight import enums


def test_optlevel_predictates():
    assert enums.OptLevel.OSize.for_size()
    assert enums.OptLevel.OSizeZ.for_size()

    assert enums.OptLevel.O1.for_performance()
    assert enums.OptLevel.O2.for_performance()
    assert enums.OptLevel.O3.for_performance()
    assert enums.OptLevel.OFast.for_performance()

    assert enums.OptLevel.ODebug.for_debug()


def test_std_predicates_and_lang():
    for std in enums.Std:
        if std.is_cstd():
            assert std.lang() == enums.Lang.C
            assert not std.is_cxxstd()
        elif std.is_cxxstd():
            assert std.lang() == enums.Lang.Cxx
            assert not std.is_cstd()
        else:
            assert std.lang() == enums.Lang.Unknown
            assert std == enums.Std.Unknown
