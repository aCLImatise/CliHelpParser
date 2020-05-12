import tempfile
from itertools import product

import pytest
from pkg_resources import resource_filename

from acclimatise import WrapperGenerator, parse_help

from ..util import validate_cwl, validate_wdl


@pytest.mark.parametrize(
    ["file_data", "language_data"],
    list(
        product(
            [
                ["test_data/bedtools.txt", ["bedtools"]],
                ["test_data/bedtools_coverage.txt", ["bedtools", "coverage"]],
                ["test_data/bwa.txt", ["bwa"]],
                ["test_data/bwa_mem.txt", ["bwa", "mem"]],
                ["test_data/bwa_bwt2sa.txt", ["bwa", "bwt2sa"]],
                ["test_data/htseq_count.txt", ["htseq-count"]],
                ["test_data/pisces.txt", ["pisces"]],
                ["test_data/podchecker.txt", ["podchecker"]],
                ["test_data/samtools.txt", ["samtools"]],
            ],
            [["cwl", validate_cwl], ["wdl", validate_wdl]],
        )
    ),
)
def test_all(file_data, language_data):
    test_file, cmd = file_data
    language, validate = language_data
    with open(resource_filename("test", test_file)) as fp:
        help_text = fp.read()

    cmd = parse_help(cmd, help_text)
    converter = WrapperGenerator.choose_converter(language)()
    converted = converter.generate_wrapper(cmd)
    validate(converted)
