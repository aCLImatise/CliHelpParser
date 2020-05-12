from acclimatise.model import EmptyFlagArg, Flag, SimpleFlagArg


def test_bwt2sa_i():
    arg = Flag(synonyms=["-i"], description="", args=SimpleFlagArg(name="32"))
    # 32 isn't a valid variable name, so the only option here is to use the letter i
    assert arg.variable_name == ["i"]
