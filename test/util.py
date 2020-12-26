import logging
import os
import shutil
import subprocess
import tempfile
from io import StringIO
from itertools import chain
from pathlib import Path
from textwrap import dedent
from typing import Callable, List, Optional

import attr
import cwl_utils.parser_v1_1 as parser
import pytest
from cwl_utils.parser_v1_0 import DockerRequirement
from cwltool.load_tool import fetch_document, resolve_and_validate_document
from WDL import Error, parse_document

from aclimatise import Command, Flag, WrapperGenerator, cli_types
from aclimatise.model import CliArgument
from aclimatise.name_generation import NameGenerationError
from aclimatise.yaml import yaml

logging.getLogger("cwltool").setLevel(30)


def skip_not_installed(executable: str):
    """
    Returns a pytest decorator to skip the test if the given executable is not in the path
    """
    return pytest.mark.skipif(
        not shutil.which(executable), reason="{} is not installed".format(executable)
    )


@attr.s(auto_attribs=True, frozen=True)
class HelpText:
    path: str
    """Path to the test data file"""
    cmd: List[str]
    """command-line used to generate this Command"""
    positional: Optional[int] = None
    """Number of positional args"""
    named: Optional[int] = None
    """Number of named args"""
    subcommands: Optional[int] = None
    """Number of subcommands"""
    outputs: Optional[int] = None
    """Number of outputs"""
    output_assertions: List[Callable[[CliArgument], bool]] = attr.ib(factory=list)
    """
    A list of assertions that must return True for at least one output
    """
    assertions: List[Callable[[Command], bool]] = attr.ib(factory=list)
    """
    A list of assertions that must return True if the command passed. Used for misc
    assertions that don't fit into the above fields
    """

    def run_assertions(self, cmd: Command, explore=False):
        """
        Run all assertions against the Command that was parsed
        """
        if explore:
            # If we are exploring, we have distinguished between positionals and
            # subcommands, so can make separate assertions
            if self.positional is not None:
                assert len(cmd.positional) == self.positional
            if self.subcommands is not None:
                assert len(cmd.subcommands) == self.subcommands
        else:
            # If we are not exploring, we haven't distinguished between positionals and
            # subcommands, so we have to combine them
            if self.positional is not None:
                assert len(cmd.positional) == self.positional + self.subcommands

        if self.named is not None:
            assert len(cmd.named) == self.named
        if self.outputs is not None:
            assert len(cmd.outputs) == self.outputs
        if self.output_assertions is not None:
            for assertion in self.output_assertions:
                assert any([assertion(out) for out in cmd.outputs])

        for assertion in self.assertions:
            assert assertion(cmd)

        # Check the converters work
        convert_validate(cmd, explore=explore)


all_tests = [
    pytest.param(
        HelpText(
            path="test_data/bowtie2_build.txt",
            cmd=["bowtie2-build"],
            positional=2,
            named=19,
            subcommands=0,
            outputs=0,
        ),
    ),
    pytest.param(
        HelpText(
            path="test_data/typeHLA.txt",
            cmd=["typeHLA.js"],
            positional=1,  # filek
            named=209,  # 208 flags with descriptions, and also "-e"
            subcommands=2,  # shell and d8
            outputs=0,
        ),
    ),
    pytest.param(
        HelpText(
            path="test_data/samtools_pl.txt",
            cmd=["samtools.pl"],
            positional=0,
            named=0,
            subcommands=3,
            outputs=0,
        ),
    ),
    pytest.param(
        HelpText(
            path="test_data/samtools_bedcov.txt",
            cmd=["samtools", "bedcov"],
            positional=2,
            named=4,
            subcommands=0,
            outputs=0,
        ),
    ),
    pytest.param(
        HelpText(
            path="test_data/gth.txt",
            cmd=["gth"],
            positional=0,
            named=37,
            subcommands=0,
            # Actually this has several outputs, but because the help doesn't like argument it's hard to detect this
            # outputs=1,
        ),
    ),
    pytest.param(
        HelpText(
            path="test_data/bedtools_closest.txt",
            cmd=["bedtools", "closest"],
            positional=0,
            named=29,
            subcommands=0,
            outputs=0,
        ),
    ),
    pytest.param(
        HelpText(
            path="test_data/bedtools_spacing.txt",
            cmd=["bedtools", "spacing"],
            positional=0,
            named=5,
            subcommands=0,
            outputs=0,
        ),
    ),
    pytest.param(
        HelpText(
            path="test_data/samtools_quickcheck.txt",
            cmd=["samtools", "quickcheck"],
            positional=1,
            named=2,
            subcommands=0,
            outputs=0,
        ),
    ),
    pytest.param(
        HelpText(
            path="test_data/bedtools_subtract.txt",
            cmd=["bedtools", "subtract"],
            positional=0,
            named=20,
            subcommands=0,
            outputs=0,
        ),
    ),
    pytest.param(
        HelpText(
            path="test_data/bedtools_window.txt",
            cmd=["bedtools", "window"],
            positional=0,
            named=15,
            subcommands=0,
            outputs=0,
        ),
    ),
    pytest.param(
        HelpText(
            path="test_data/samtools_dict.txt",
            cmd=["samtools", "dict"],
            positional=1,
            named=5,
            subcommands=0,
            # outputs=1,
        ),
    ),
    pytest.param(
        HelpText(
            path="test_data/bwa_index.txt",
            cmd=["bwa", "index"],
            positional=1,
            named=4,
            subcommands=0,
            outputs=0,
        ),
    ),
    pytest.param(
        HelpText(
            path="test_data/bedtools_multiinter.txt",
            cmd=["bedtools", "multiinter"],
            positional=0,
            named=8,
            subcommands=0,
            outputs=0,
        ),
    ),
    pytest.param(
        HelpText(
            path="test_data/bedtools_coverage.txt",
            cmd=["bedtools", "coverage"],
            positional=0,
            named=20,
            subcommands=0,
            outputs=0,
        ),
    ),
    pytest.param(
        HelpText(
            path="test_data/bwa_mem.txt",
            cmd=["bwa", "mem"],
            positional=3,
            named=36,
            subcommands=0,
            outputs=1,  # -o
        ),
    ),
    pytest.param(
        HelpText(
            path="test_data/bwa_bwt2sa.txt",
            cmd=["bwa", "bwt2sa"],
            named=1,
            positional=2,
            subcommands=0,
            outputs=0,
        ),
    ),
    pytest.param(
        HelpText(
            path="test_data/bwa_bwtupdate.txt",
            cmd=["bwa", "bwtupdate"],
            named=0,
            positional=1,
            subcommands=0,
            outputs=0,
        ),
    ),
    pytest.param(
        HelpText(
            path="test_data/htseq_count.txt",
            cmd=["htseq-count"],
            named=20,
            positional=2,
            subcommands=0,
            # outputs=1,  # Should actually be 2: -c and -o, but we're currently failing -o
            # output_assertions=[
            #     lambda out: "-c" in out.synonyms,
            #     # lambda out: '-o' in out.synonyms,
            # ],
        ),
    ),
    pytest.param(
        HelpText(
            path="test_data/bedtools.txt",
            cmd=["bedtools"],
            positional=0,
            named=1,
            subcommands=43,
            outputs=0,
        ),
    ),
    pytest.param(
        HelpText(
            path="test_data/pisces.txt",
            cmd=["pisces"],
            named=57,
            positional=0,
            subcommands=0,
            outputs=1,
            output_assertions=[
                lambda out: "--outfolder" in out.synonyms
                and out.get_type() == cli_types.CliDir(output=True)
            ],
        ),
    ),
    pytest.param(
        HelpText(
            path="test_data/podchecker.txt",
            cmd=["podchecker"],
            named=2,
            positional=1,
            subcommands=0,
            outputs=0,
        ),
    ),
    pytest.param(
        HelpText(
            path="test_data/bwa.txt",
            cmd=["bwa"],
            named=0,
            positional=0,
            subcommands=14,
            outputs=0,
        ),
    ),
    pytest.param(
        HelpText(
            path="test_data/samtools.txt",
            cmd=["samtools"],
            positional=0,
            named=0,
            subcommands=29,
            outputs=0,
        ),
    ),
    pytest.param(
        HelpText(
            path="test_data/bedtools_random.txt",
            cmd=["bedtools", "random"],
            positional=0,
            named=4,
            subcommands=0,
            outputs=0,
        ),
    ),
    # These last two are really strange, maybe I'll support them eventually
    pytest.param(
        HelpText(
            path="test_data/dinosaur.txt",
            cmd=["dinosaur"],
            positional=0,
            named=24,
            subcommands=0,
        ),
        marks=pytest.mark.xfail,
    ),
    pytest.param(
        HelpText(
            path="test_data/mauve.txt",
            cmd=["mauveAligner"],
            positional=2,
            named=30,
            subcommands=0,
        ),
        marks=pytest.mark.xfail,
    ),
]

all_tests_lookup = {tuple(param.values[0].cmd): param.values[0] for param in all_tests}

all_ids = [" ".join(case.values[0].cmd) for case in all_tests]


def convert_validate(cmd: Command, lang: str = None, explore=True):
    """
    Converts the command into one or all formats, and then validates that they worked
    """
    if lang:
        conv = WrapperGenerator.choose_converter(lang)()
        with tempfile.TemporaryDirectory() as tempd:
            for path, subcommand in conv.generate_tree(cmd, Path(tempd)):
                content = path.read_text()
                validators[lang](content, subcommand, explore=explore)
    else:
        for lang in ("cwl", "wdl", "yml"):
            convert_validate(cmd, lang, explore=explore)


def validate_cwl(cwl: str, cmd: Command = None, explore: bool = True):
    parsed = yaml.load(cwl)
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        tmpfile = tmpdir / parsed["id"]
        tmpfile.write_text(cwl)

        # cwltool doesn't have an official Python API, so run it as a subprocess
        subprocess.run(["cwltool", "--validate", tmpfile])

        # We don't want this to be an actual field hierarchy
        path = Path(parsed["id"])
        assert len(path.parts) == 1

        if cmd:
            assert len(parsed["inputs"]) == len(cmd.positional) + len(cmd.named)
            # We should have all the official outputs, plus stdout
            assert len(parsed["outputs"]) == len(cmd.outputs) + 1


def validate_wdl(wdl: str, cmd: Command = None, explore=True):
    """
    :param explore: If true, we're in explore mode, and we should ignore subcommands
    """
    try:
        doc = parse_document(wdl)
    except Error.SyntaxError as e:
        print(wdl)
        raise e

    task = doc.tasks[0]

    # task.inputs might be None
    cmd_input_names = {inp.name for inp in task.inputs or []}
    # Verify that every parameter has been documented
    wdl_input_names = {meta for meta in task.parameter_meta.keys()}
    assert cmd_input_names == wdl_input_names

    # wdl_input_descriptions = {meta for meta in doc.tasks[0].parameter_meta.values()}
    # cmd_input_descriptions = {arg.description for arg in [*cmd.subcommands, *cmd.named, *cmd.positional]}
    # assert wdl_input_descriptions == cmd_input_descriptions, wdl_input_descriptions ^ cmd_input_descriptions

    # Check that the generated WDL has the correct parameter meta fields
    if cmd:
        cmd_names = [arg.full_name() for arg in [*cmd.named, *cmd.positional]]
        target = len(cmd.named) + len(cmd.positional)
        # If we're not in explore mode, subcommands will be parsed as inputs
        if not explore:
            target += len(cmd.subcommands)
        assert len(task.parameter_meta) == target, "{} vs {}".format(
            task.parameter_meta.keys(), cmd_names
        )
        # We should have all the official outputs, plus stdout
        assert len(task.outputs) == len(cmd.outputs) + 1


def validate_yml(yml: str, cmd: Command = None, explore=True):
    stream = StringIO(yml)
    yaml.load(stream)


def ensure_conda():
    """
    Ensures we're in a conda env, and that the PATH is correctly set
    """
    if "CONDA_PREFIX" not in os.environ:
        raise Exception("Must be in a conda environment")
    bin = os.path.join(os.environ["CONDA_PREFIX"], "bin")
    os.environ["PATH"] = bin + os.pathsep + os.environ["PATH"]


validators = dict(cwl=validate_cwl, wdl=validate_wdl, yml=validate_yml)
