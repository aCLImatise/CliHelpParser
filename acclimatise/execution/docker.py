from typing import List

from docker.utils.socket import consume_socket_output, demux_adaptor, frames_iter


import errno
import os
from select import select as original_select
import select
import socket as pysocket
import struct

import six

from . import Executor
from unittest.mock import patch


class DockerExecutor(Executor):
    """
    An executor that runs the commands on an already-running docker Container (not an Image!)
    """

    def __init__(self, container: "docker.models.containers.Container"):
        self.container = container

    def execute(self, command: List[str], timeout: int=10) -> str:
        _, socket = self.container.exec_run(
            command, stdout=True, stderr=True, demux=True, socket=True
        )
        socket._sock.settimeout(timeout)

        with patch.object(select, 'select', new=lambda rlist, wlist, xlist: original_select(rlist, wlist, xlist, timeout)):
            gen = (demux_adaptor(*frame) for frame in frames_iter(socket, tty=False))
            stdout, stderr = consume_socket_output(gen, demux=True)
        return (stdout or stderr).decode()
