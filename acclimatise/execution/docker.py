from typing import List

from docker.utils.socket import consume_socket_output, demux_adaptor, frames_iter

from . import Executor


class DockerExecutor(Executor):
    """
    An executor that runs the commands on an already-running docker Container (not an Image!)
    """

    def __init__(self, container: "docker.models.containers.Container"):
        self.container = container

    @staticmethod
    def frames(socket):
        for frame in frames_iter(socket, tty=False):
            yield demux_adaptor(*frame)

    def execute(self, command: List[str]) -> str:
        resp = self.container.client.api.exec_create(
            self.id,
            command,
            stdout=True,
            stderr=True,
            stdin=False,
            tty=False,
            privileged=False,
            user="",
            environment=None,
            workdir=None,
        )

        res = self.container.client._post_json(
            self.container.client._url("/exec/{0}/start", resp["Id"]),
            headers={"Connection": "Upgrade", "Upgrade": "tcp"},
            data={"Tty": False, "Detach": False},
            stream=True,
            timeout=5,
        )
        print(res)
