from test.util import skip_not_installed

from aclimatise.execution.man import ManPageExecutor


@skip_not_installed("git")
@skip_not_installed("man")
def test_git():
    cmd = ManPageExecutor(max_length=99999).explore(
        ["git"],
    )
    assert len(cmd.positional) > 20


@skip_not_installed("git")
@skip_not_installed("ls")
def test_ls():
    cmd = ManPageExecutor().explore(
        ["ls"],
    )
    assert {"-A", "--almost-all", "-1", "--context"} <= cmd.all_synonyms
