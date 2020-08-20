from typing import List

from docker.utils.socket import consume_socket_output, demux_adaptor, frames_iter

from . import Executor


class DockerExecutor(Executor):
    """
    An executor that runs the commands on an already-running docker Container (not an Image!)
    """

    def __init__(self, container: "docker.models.containers.Container"):
        self.container = container

    def execute(self, command: List[str]) -> str:
        _, socket = self.container.exec_run(
            command, stdout=True, stderr=True, demux=True, socket=True
        )

        socket._sock.settimeout(5)
        gen = frames_iter(socket, tty=False)
        gen = (demux_adaptor(*frame) for frame in gen)

        stdout, stderr = consume_socket_output(gen, demux=True)
        return (stdout or stderr).decode()
