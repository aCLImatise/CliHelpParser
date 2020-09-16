import docker
import pytest

from aclimatise.execution.docker import DockerExecutor


def test_docker(bwamem_help):
    client = docker.from_env()
    container = client.containers.run(
        "biocontainers/bwa:v0.7.17_cv1",
        entrypoint=["sleep", "999999999"],
        detach=True,
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
        "ubuntu:latest",
        entrypoint=["sleep", "999999999"],
        detach=True,
    )

    exec = DockerExecutor(container)
    output = exec.execute(["sleep", "999999"])
    container.kill()
    assert output == ""


def test_no_output():
    # Check that it doesn't crash when no output is received

    client = docker.from_env()
    container = client.containers.run(
        "quay.io/biocontainers/gadem:1.3.1--h516909a_2",
        entrypoint=["sleep", "9999999"],
        detach=True,
    )
    exec = DockerExecutor(container)
    output = exec.execute(["gadem"])
    container.kill()
    assert output is not None


@pytest.mark.timeout(360)
def test_infinite_output():
    """
    Test that the DockerExecutor can kill the command if it's constantly producing output
    """
    client = docker.from_env(timeout=99999)
    container = client.containers.run(
        "ubuntu:latest",
        entrypoint=["sleep", "999999999"],
        detach=True,
    )

    exec = DockerExecutor(container)
    output = exec.execute(["yes"])
    container.kill()
    assert output.startswith("y")
