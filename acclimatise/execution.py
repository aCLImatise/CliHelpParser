"""
Functions that relate to executing the programs of interest, in order to extract their help text
"""
import os
import pty
import signal
import subprocess
import sys
import typing

import psutil


def kill_proc_tree(
    pid, sig=signal.SIGTERM, include_parent=True, timeout=None, on_terminate=None
):
    """
    Kill a process tree (including grandchildren) with signal "sig" and return a (gone, still_alive) tuple.
    "on_terminate", if specified, is a callabck function which is called as soon as a child terminates.

    Taken from https://psutil.readthedocs.io/en/latest/#kill-process-tree
    """
    assert pid != os.getpid(), "won't kill myself"
    parent = psutil.Process(pid)
    children = parent.children(recursive=True)
    if include_parent:
        children.append(parent)
    for p in children:
        p.send_signal(sig)


def execute_cmd(help_cmd: typing.List[str], timeout: int = 5, **kwargs) -> str:
    """
    Execute a command defined by a list of arguments, and return the result as a string
    """
    master, slave = pty.openpty()
    popen_kwargs = dict(
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=slave, encoding="utf-8"
    )
    popen_kwargs.update(kwargs)

    # This works a lot like subprocess.run, but we need access to the pid in order to kill the process tree, so use Popen
    with subprocess.Popen(help_cmd, **popen_kwargs) as process:
        try:
            stdout, stderr = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired as e:
            # Kill the entire process tree, because sometimes killing the parent isn't enough
            kill_proc_tree(
                process.pid,
                include_parent=True,
                sig=signal.SIGKILL if sys.platform == "linux" else None,
            )
            process.communicate()
            return ""
        finally:
            os.close(master)
            os.close(slave)

    return stdout or stderr
