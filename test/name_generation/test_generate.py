from acclimatise.model import EmptyFlagArg, Flag, Positional


def test_bwa_mem_t():
    flag = Flag(
        synonyms=["-t"], description="number of threads [1]", args=EmptyFlagArg()
    )
    name = [s.lower() for s in flag.generate_name()]
    assert len(name) < 5
    assert "number" in name
    assert "threads" in name


def test_bwa_mem_p():
    flag = Flag(
        synonyms=["-p"],
        description="smart pairing (ignoring in2.fq)",
        args=EmptyFlagArg(),
    )
    name = [s.lower() for s in flag.generate_name()]
    assert len(name) == 2
    assert "smart" in name
    assert "pairing" in name


def test_bwa_mem_r():
    flag = Flag(
        synonyms=["-R"],
        description="read group header line such as '@RG\tID:foo\tSM:bar' [null]",
        args=EmptyFlagArg(),
    )
    name = [s.lower() for s in flag.generate_name()]
    assert len(name) < 5
    assert "read" in name
    # assert 'header' in name


def test_bwa_mem_i():
    flag = Flag(
        synonyms=["-t"],
        description="specify the mean, standard deviation (10% of the mean if absent), max (4 sigma from the mean if absent) and min of the insert size distribution. FR orientation only. [inferred]",
        args=EmptyFlagArg(),
    )
    name = [s.lower() for s in flag.generate_name()]
    assert len(name) < 5
    assert "specify" in name
    assert "mean" in name


def test_bedtools_coverage_d():
    flag = Flag(
        synonyms=["-d"],
        description="Report the depth at each position in each A feature. Positions reported are one based. Each position and depth follow the complete A feature.",
        args=EmptyFlagArg(),
    )
    name = [s.lower() for s in flag.generate_name()]
    assert len(name) < 5
    assert "report" in name
    assert "depth" in name


def test_bedtools_coverage_s():
    flag = Flag(
        synonyms=["-s"],
        description="Require same strandedness. That is, only report hits in B that overlap A on the _same_ strand. By default, overlaps are reported without respect to strand",
        args=EmptyFlagArg(),
    )
    name = [s.lower() for s in flag.generate_name()]
    assert len(name) < 5
    assert "same" in name
    assert "strandedness" in name


def test_bedtools_coverage_g():
    flag = Flag(
        synonyms=["-g"],
        description="Provide a genome file to enforce consistent chromosome sort order across input files. Only applies when used with -sorted option.",
        args=EmptyFlagArg(),
    )
    name = [s.lower() for s in flag.generate_name()]
    assert len(name) < 5
    assert "genome" in name
    assert "file" in name
