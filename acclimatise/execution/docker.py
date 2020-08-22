import select
import socket
from select import select as original_select
from typing import List
from unittest.mock import patch

from docker.utils.socket import consume_socket_output, demux_adaptor, frames_iter

from . import Executor


class DockerExecutor(Executor):
    """
    An executor that runs the commands on an already-running docker Container (not an Image!)
    """

    def __init__(self, container: "docker.models.containers.Container", **kwargs):
        super().__init__(**kwargs)
        self.container = container

    def execute(self, command: List[str]) -> str:
        _, sock = self.container.exec_run(
            command, stdout=True, stderr=True, demux=True, socket=True
        )
        try:
            sock._sock.settimeout(self.timeout)

            with patch.object(
                select,
                "select",
                new=lambda rlist, wlist, xlist: original_select(
                    rlist, wlist, xlist, self.timeout
                ),
            ):
                gen = (demux_adaptor(*frame) for frame in frames_iter(sock, tty=False))
                stdout, stderr = consume_socket_output(gen, demux=True)
        except socket.timeout as e:
            return self.handle_timeout(e)

        return (stdout or stderr).decode()
