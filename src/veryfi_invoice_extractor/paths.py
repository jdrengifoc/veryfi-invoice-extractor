from pathlib import Path

ROOT: Path = Path(__file__).resolve().parents[2]

DATA_DIR: Path = ROOT / "data"
INPUTS_DIR: Path = DATA_DIR / "inputs"
VERYFI_OUTPUTS_DIR: Path = DATA_DIR / "veryfi_outputs"
RESULTS_DIR: Path = DATA_DIR / "results"

TESTS_DIR: Path = ROOT / "tests"
FIXTURES_DIR: Path = TESTS_DIR / "fixtures"
