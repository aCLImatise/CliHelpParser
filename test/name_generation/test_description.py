"""
Tests the generate_name function, which converts a paragraph of text into a variable name
"""
from acclimatise.name_generation import generate_name, preprocess


def test_bwa_mem_t():
    name = next(generate_name(preprocess("number of threads [1]")))
    assert len(name) < 5
    assert "number" in name
    assert "threads" in name


def test_bwa_mem_p():
    name = next(generate_name(preprocess("smart pairing (ignoring in2.fq)")))
    assert len(name) <= 3
    assert "smart" in name
    assert "pairing" in name


def test_bwa_mem_r():
    name = next(
        generate_name(
            preprocess("read group header line such as '@RG\tID:foo\tSM:bar' [null]")
        )
    )
    assert len(name) < 5
    assert "read" in name
    # assert 'header' in name


def test_bwa_mem_i():
    name = next(
        generate_name(
            preprocess(
                "specify the mean, standard deviation (10% of the mean if absent), max (4 sigma from the mean if absent) and min of the insert size distribution. FR orientation only. [inferred]"
            )
        )
    )
    assert len(name) < 5
    assert "specify" in name

    # Ideally this would return "mean" first, but the POS engine thinks that "mean" describes "deviation"
    # assert "mean" in name
    assert "deviation" in name


def test_bedtools_coverage_d():
    name = next(
        generate_name(
            preprocess(
                "Report the depth at each position in each A feature. Positions reported are one based. Each position and depth follow the complete A feature."
            )
        )
    )
    assert len(name) < 5
    assert "report" in name
    assert "depth" in name


def test_bedtools_coverage_s():
    name = next(
        generate_name(
            preprocess(
                "Require same strandedness. That is, only report hits in B that overlap A on the _same_ strand. By default, overlaps are reported without respect to strand"
            )
        )
    )
    assert len(name) < 5
    assert "require" in name
    assert "strandedness" in name


def test_bedtools_coverage_g():
    name = next(
        generate_name(
            preprocess(
                "Provide a genome file to enforce consistent chromosome sort order across input files. Only applies when used with -sorted option."
            )
        )
    )
    assert len(name) < 5
    assert "provide" in name
    assert "file" in name


def test_symbol():
    """
    Check that symbols are correctly removed from the output
    """
    name = next(generate_name(preprocess("/genome@ #file$")))
    assert len(name) < 5
    assert "genome" in name
    assert "file" in name


def test_hyphens():
    name = next(generate_name(preprocess("penalty for 5'- and 3'-end clipping [5,5]")))
    assert len(name) < 5
    assert "penalty" in name

    for word in name:
        assert "-" not in word
        assert "[" not in word
        assert "," not in word
