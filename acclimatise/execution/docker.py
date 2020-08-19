from typing import List

from . import Executor


class DockerExecutor(Executor):
    """
    An executor that runs the commands on an already-running docker Container (not an Image!)
    """

    def __init__(self, container: "docker.models.containers.Container"):
        self.container = container

    def execute(self, command: List[str]) -> str:
        # Note: the timeout for the command can't be set on the exec command directly, it has to be set on the client
        # when created
        exit_code, (stdout, stderr) = self.container.exec_run(
            command, stdout=True, stderr=True, demux=True
        )
        out = stdout or stderr
        return out.decode()
