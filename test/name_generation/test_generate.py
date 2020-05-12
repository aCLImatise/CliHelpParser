from acclimatise.name_generation import generate_name


def test_bwa_mem_t():
    name = list(generate_name("number of threads [1]"))
    assert len(name) < 5
    assert "number" in name
    assert "threads" in name


def test_bwa_mem_p():
    name = list(generate_name("smart pairing (ignoring in2.fq)"))
    assert len(name) == 2
    assert "smart" in name
    assert "pairing" in name


def test_bwa_mem_r():
    name = list(
        generate_name("read group header line such as '@RG\tID:foo\tSM:bar' [null]")
    )
    assert len(name) < 5
    assert "read" in name
    # assert 'header' in name


def test_bwa_mem_i():
    name = list(
        generate_name(
            "specify the mean, standard deviation (10% of the mean if absent), max (4 sigma from the mean if absent) and min of the insert size distribution. FR orientation only. [inferred]"
        )
    )
    assert len(name) < 5
    assert "specify" in name
    assert "mean" in name


def test_bedtools_coverage_d():
    name = list(
        generate_name(
            "Report the depth at each position in each A feature. Positions reported are one based. Each position and depth follow the complete A feature."
        )
    )
    assert len(name) < 5
    assert "report" in name
    assert "depth" in name


def test_bedtools_coverage_s():
    name = list(
        generate_name(
            "Require same strandedness. That is, only report hits in B that overlap A on the _same_ strand. By default, overlaps are reported without respect to strand"
        )
    )
    assert len(name) < 5
    assert "same" in name
    assert "strandedness" in name


def test_bedtools_coverage_g():
    name = list(
        generate_name(
            "Provide a genome file to enforce consistent chromosome sort order across input files. Only applies when used with -sorted option."
        )
    )
    assert len(name) < 5
    assert "genome" in name
    assert "file" in name
