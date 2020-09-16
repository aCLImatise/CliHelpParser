from aclimatise.execution.local import LocalExecutor

from ..util import skip_not_installed


@skip_not_installed("bwa")
def test_local(bwamem_help):
    exec = LocalExecutor()
    output = exec.execute(["bwa", "mem"])
    assert output == bwamem_help
