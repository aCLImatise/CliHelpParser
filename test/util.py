import subprocess
from declivity.parser import CliParser
import pytest
from textwrap import dedent

def process_help_section(help):
    """
    Does some preprocessing on a help text segment to facilitate testing
    """
    help = help.strip('\n')
    return dedent(help)

def get_help(cmd):
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return (proc.stdout or proc.stderr).decode('utf_8')

