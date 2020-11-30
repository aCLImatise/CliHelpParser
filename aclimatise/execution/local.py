"""
Functions that relate to executing the programs of interest, in order to extract their help text
"""
import os
import pty
import signal
import subprocess
import sys
from typing import List

import psutil

from aclimatise.execution.help import CliHelpExecutor


def kill_proc_tree(pid, sig=signal.SIGTERM, include_parent=True):
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


class LocalExecutor(CliHelpExecutor):
    def __init__(self, popen_args: dict = {}, **kwargs):
        super().__init__(**kwargs)
        self.popen_args = popen_args

    def execute(self, command: List[str]) -> str:
        master, slave = pty.openpty()
        popen_kwargs = dict(
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=slave,
            encoding="utf-8",
        )
        popen_kwargs.update(self.popen_args)

        # This works a lot like subprocess.run, but we need access to the pid in order to kill the process tree, so use Popen
        with subprocess.Popen(command, **popen_kwargs) as process:
            try:
                stdout, stderr = process.communicate(timeout=self.timeout)
            except subprocess.TimeoutExpired as e:
                # Kill the entire process tree, because sometimes killing the parent isn't enough
                kill_proc_tree(
                    process.pid,
                    include_parent=True,
                    sig=signal.SIGKILL if sys.platform == "linux" else None,
                )
                process.communicate()
                return self.handle_timeout(e)
            finally:
                os.close(master)
                os.close(slave)

        return stdout or stderr
