def test_single_flag(parser):

    txt = """
    --use_strict (enforce strict mode)
          type: bool  default: false
      """

    result = parser.flag_block.parseString(txt)[0]
    assert "type: bool" in result.description


def test_multiple_flags(parser):

    txt = """
    --use_strict (enforce strict mode)
          type: bool  default: false
    --es5_readonly (activate correct semantics for inheriting readonliness)
          type: bool  default: true
      """

    result = parser.flag_block.setDebug().parseString(txt)
    assert len(result) == 2
