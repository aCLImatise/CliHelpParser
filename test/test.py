import subprocess
from declivity.parser import parse


def get_help(cmd):
    proc = subprocess.run(cmd, capture_output=True)
    return (proc.stdout or proc.stderr).decode('utf_8')

def test_bwa_segmented_options():
    parsed = parse("""
    Scoring options:

       -A INT        score for a sequence match, which scales options -TdBOELU unless overridden [1]
       -B INT        penalty for a mismatch [4]
       -O INT[,INT]  gap open penalties for deletions and insertions [6,6]
       -E INT[,INT]  gap extension penalty; a gap of size k cost '{-O} + {-E}*k' [1,1]
       -L INT[,INT]  penalty for 5'- and 3'-end clipping [5,5]
       -U INT        penalty for an unpaired read pair [17]

       -x STR        read type. Setting -x changes multiple parameters unless overriden [null]
                     pacbio: -k17 -W40 -r10 -A1 -B1 -O1 -E1 -L0  (PacBio reads to ref)
                     ont2d: -k14 -W20 -r10 -A1 -B1 -O1 -E1 -L0  (Oxford Nanopore 2D-reads to ref)
                     intractg: -B9 -O16 -L5  (intra-species contigs to ref)
    """)
    print(parsed)

def test_bwa_str():
    parsed = parse("""
       -t INT        number of threads [1]
       -k INT        minimum seed length [19]
       -w INT        band width for banded alignment [100]
       -d INT        off-diagonal X-dropoff [100]
       -r FLOAT      look for internal seeds inside a seed longer than {-k} * FLOAT [1.5]
       -y INT        seed occurrence for the 3rd round seeding [20]
       -c INT        skip seeds with more than INT occurrences [500]
       -D FLOAT      drop chains shorter than FLOAT fraction of the longest overlapping chain [0.50]
       -W INT        discard a chain if seeded bases shorter than INT [0]
       -m INT        perform at most INT rounds of mate rescues for each read [50]
       -S            skip mate rescue
       -P            skip pairing; mate rescue performed unless -S also in use
    """)
    # There are 12 total arguments
    assert len(parsed) == 12

    # Each flag should have a list of flags and a description
    for flag in parsed:
        assert isinstance(flag['flags'], list)
        assert isinstance(flag['description'], str)

    # There should be two flags without an argument
    assert len([p for p in parsed if p['metavar'] is None]) == 2


def test_bwa():
    parse(get_help(['bwa', 'mem']))


def test_samtools():
    parse(get_help(['samtools', 'view', '--help']))
