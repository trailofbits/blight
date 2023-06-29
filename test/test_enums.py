from blight import enums


def test_buildtool_cmd():
    # the cmd property is only used in `blight.cli`, so we test it exhaustively here
    assert enums.BuildTool.CC.cmd == "cc"
    assert enums.BuildTool.CXX.cmd == "c++"
    assert enums.BuildTool.CPP.cmd == "cpp"
    assert enums.BuildTool.LD.cmd == "ld"
    assert enums.BuildTool.AS.cmd == "as"
    assert enums.BuildTool.AR.cmd == "ar"
    assert enums.BuildTool.STRIP.cmd == "strip"
    assert enums.BuildTool.INSTALL.cmd == "install"


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


def test_enum_stringification():
    for tool in enums.BuildTool:
        assert str(tool) == tool.value

    for tool in enums.BlightTool:
        assert str(tool) == tool.value

    for family in enums.CompilerFamily:
        assert str(family) == family.name

    for stage in enums.CompilerStage:
        assert str(stage) == stage.name

    for lang in enums.Lang:
        assert str(lang) == lang.name

    for std in enums.Std:
        assert str(std) == std.name

    for opt in enums.OptLevel:
        assert str(opt) == opt.name

    for model in enums.CodeModel:
        assert str(model) == model.name

    for output in enums.OutputKind:
        assert str(output) == output.value

    for input in enums.InputKind:
        assert str(input) == input.value
