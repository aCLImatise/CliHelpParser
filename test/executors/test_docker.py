import pytest

import docker
from acclimatise.execution.docker import DockerExecutor


def test_docker(bwamem_help):
    client = docker.from_env()
    container = client.containers.run(
        "biocontainers/bwa:v0.7.17_cv1", entrypoint=["sleep", "999999999"], detach=True,
    )

    exec = DockerExecutor(container)
    output = exec.execute(["bwa", "mem"])
    assert output == bwamem_help
    container.kill()


@pytest.mark.timeout(360)
def test_docker_kill():
    """
    Test that the DockerExecutor can kill the command if it times out
    """
    client = docker.from_env(timeout=99999)
    container = client.containers.run(
        "ubuntu:latest", entrypoint=["sleep", "999999999"], detach=True,
    )

    exec = DockerExecutor(container)
    output = exec.execute(["sleep", "999999"])
    container.kill()
    assert output == ""
