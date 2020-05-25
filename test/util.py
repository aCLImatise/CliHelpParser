import tempfile
from io import StringIO
from pathlib import Path
from textwrap import dedent
from typing import List

import cwl_utils.parser_v1_1 as parser
import pytest
from cwltool.load_tool import fetch_document, resolve_and_validate_document
from dataclasses import dataclass
from WDL import parse_document

from acclimatise import Command, WrapperGenerator
from acclimatise.yaml import yaml


@dataclass
class HelpText:
    path: str
    cmd: List[str]
    positional: int
    named: int
    subcommands: int


all_tests = [
    HelpText(
        path="test_data/bedtools.txt",
        cmd=["bedtools"],
        positional=0,
        named=1,
        subcommands=43,
    ),
    HelpText(
        path="test_data/bedtools_coverage.txt",
        cmd=["bedtools", "coverage"],
        positional=0,
        named=18,
        subcommands=0,
    ),
    HelpText(
        path="test_data/bwa.txt", cmd=["bwa"], named=0, positional=0, subcommands=14
    ),
    HelpText(
        path="test_data/bwa_mem.txt",
        cmd=["bwa", "mem"],
        positional=3,
        named=32,
        subcommands=0,
    ),
    HelpText(
        path="test_data/bwa_bwt2sa.txt",
        cmd=["bwa", "bwt2sa"],
        named=1,
        positional=2,
        subcommands=0,
    ),
    HelpText(
        path="test_data/bwa_bwtupdate.txt",
        cmd=["bwa", "bwtupdate"],
        named=0,
        positional=1,
        subcommands=0,
    ),
    HelpText(
        path="test_data/htseq_count.txt",
        cmd=["htseq-count"],
        named=14,
        positional=2,
        subcommands=0,
    ),
    HelpText(
        path="test_data/pisces.txt",
        cmd=["pisces"],
        named=57,
        positional=0,
        subcommands=0,
    ),
    HelpText(
        path="test_data/podchecker.txt",
        cmd=["podchecker"],
        named=2,
        positional=1,
        subcommands=0,
    ),
    HelpText(
        path="test_data/samtools.txt",
        cmd=["samtools"],
        positional=0,
        named=0,
        subcommands=28,
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


def convert_validate(cmd: Command, lang: str = None):
    """
    Converts the command into one or all formats, and then validates that they worked
    """
    if lang:
        conv = WrapperGenerator.choose_converter(lang)()
        with tempfile.TemporaryDirectory() as tempd:
            for path in conv.generate_tree(cmd, tempd):
                content = path.read_text()
                validators[lang](content, cmd)
    else:
        for lang in ("cwl", "wdl", "yml"):
            convert_validate(cmd, lang)


def validate_cwl(cwl: str, cmd: Command = None):
    parsed = yaml.load(cwl)
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        tmpfile = tmpdir / parsed["id"]
        tmpfile.write_text(cwl)
        loading_context, workflowobj, uri = fetch_document(str(tmpfile))
        resolve_and_validate_document(loading_context, workflowobj, uri)


def validate_wdl(wdl: str, cmd: Command = None):
    doc = parse_document(wdl)

    # Verify that every parameter has been documented
    cmd_input_names = {inp.name for inp in doc.tasks[0].inputs}
    wdl_input_names = {meta for meta in doc.tasks[0].parameter_meta.keys()}
    assert cmd_input_names == wdl_input_names

    # wdl_input_descriptions = {meta for meta in doc.tasks[0].parameter_meta.values()}
    # cmd_input_descriptions = {arg.description for arg in [*cmd.subcommands, *cmd.named, *cmd.positional]}
    # assert wdl_input_descriptions == cmd_input_descriptions, wdl_input_descriptions ^ cmd_input_descriptions

    # Check that the generated WDL has the correct parameter meta fields
    if cmd:
        assert len(doc.tasks[0].parameter_meta) == len(cmd.subcommands) + len(
            cmd.named
        ) + len(cmd.positional)


def validate_yml(yml: str, cmd: Command = None):
    stream = StringIO(yml)
    yaml.load(stream)


validators = dict(cwl=validate_cwl, wdl=validate_wdl, yml=validate_yml)
