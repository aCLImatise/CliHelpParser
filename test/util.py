import tempfile
from io import StringIO
from pathlib import Path
from textwrap import dedent

import cwl_utils.parser_v1_1 as parser
from cwltool.load_tool import fetch_document, resolve_and_validate_document
from WDL import parse_document

from acclimatise.yaml import yaml


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
