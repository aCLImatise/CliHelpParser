import select
import socket
import time
from select import select as original_select
from typing import List, Tuple
from unittest.mock import patch

from docker.utils.socket import consume_socket_output, demux_adaptor, frames_iter

from aclimatise.execution.help import CliHelpExecutor


def read_socket(sock, timeout: int = None) -> Tuple[bytes, bytes]:
    """
    Reads from a docker socket, and returns everything
    :param sock: Docker socket to read from
    :param timeout: Number of seconds after which we return all data collected
    :return: A tuple of stdout, stderr
    """
    start_time = time.time()
    out = [b"", b""]
    for frame in frames_iter(sock, tty=False):
        frame = demux_adaptor(*frame)

        # If we hit the timeout, return anyawy
        if time.time() >= start_time + timeout:
            return tuple(out)

        assert frame != (None, None)

        if frame[0] is not None:
            out[0] += frame[0]
        else:
            out[1] += frame[1]
    return tuple(out)


class DockerExecutor(CliHelpExecutor):
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
            # These are timeouts that define how long to wait while nothing is being output
            sock._sock.settimeout(self.timeout)
            with patch.object(
                select,
                "select",
                new=lambda rlist, wlist, xlist: original_select(
                    rlist, wlist, xlist, self.timeout
                ),
            ):
                stdout, stderr = read_socket(sock, timeout=self.timeout)
        except socket.timeout as e:
            return self.handle_timeout(e)

        return (stdout or stderr or b"").decode()
