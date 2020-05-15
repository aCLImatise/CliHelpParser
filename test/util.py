import tempfile
from io import StringIO
from pathlib import Path
from textwrap import dedent
from typing import List

import cwl_utils.parser_v1_1 as parser
from cwltool.load_tool import fetch_document, resolve_and_validate_document
from dataclasses import dataclass
from WDL import parse_document

from acclimatise.yaml import yaml


@dataclass
class HelpText:
    path: str
    cmd: List[str]
    positional: int
    named: int


all_tests = [
    HelpText(path="test_data/bedtools.txt", cmd=["bedtools"], positional=43, named=1),
    HelpText(
        path="test_data/bedtools_coverage.txt",
        cmd=["bedtools", "coverage"],
        positional=0,
        named=18,
    ),
    HelpText(path="test_data/bwa.txt", cmd=["bwa"], named=0, positional=14),
    HelpText(path="test_data/bwa_mem.txt", cmd=["bwa", "mem"], positional=3, named=32),
    HelpText(
        path="test_data/bwa_bwt2sa.txt", cmd=["bwa", "bwt2sa"], named=1, positional=2
    ),
    HelpText(
        path="test_data/bwa_bwtupdate.txt",
        cmd=["bwa", "bwtupdate"],
        named=0,
        positional=1,
    ),
    HelpText(
        path="test_data/htseq_count.txt", cmd=["htseq-count"], named=14, positional=2
    ),
    HelpText(path="test_data/pisces.txt", cmd=["pisces"], named=57, positional=0),
    HelpText(
        path="test_data/podchecker.txt", cmd=["podchecker"], named=2, positional=1
    ),
    HelpText(path="test_data/samtools.txt", cmd=["samtools"], positional=28, named=0),
]


def validate_cwl(cwl: str):
    parsed = yaml.load(cwl)
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        tmpfile = tmpdir / parsed["id"]
        tmpfile.write_text(cwl)
        loading_context, workflowobj, uri = fetch_document(str(tmpfile))
        resolve_and_validate_document(loading_context, workflowobj, uri)


def validate_wdl(wdl: str):
    return parse_document(wdl)
