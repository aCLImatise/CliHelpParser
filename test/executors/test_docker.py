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
