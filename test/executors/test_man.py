from test.util import skip_not_installed

from aclimatise.execution.man import ManPageExecutor


@skip_not_installed("git")
def test_git():
    cmd = ManPageExecutor(max_length=99999).explore(
        ["git"],
    )
    assert len(cmd.subcommands) > 20
