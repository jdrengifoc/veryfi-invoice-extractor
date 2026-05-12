from pathlib import Path

ROOT: Path = Path(__file__).resolve().parents[2]

DATA_DIR: Path = ROOT / "data"
INPUTS_DIR: Path = DATA_DIR / "00-inputs"
VERYFI_OUTPUTS_DIR: Path = DATA_DIR / "01-veryfi_outputs"
RESULTS_DIR: Path = DATA_DIR / "02-results"
LOGS_DIR: Path = ROOT / "logs"

TESTS_DIR: Path = ROOT / "tests"
FIXTURES_DIR: Path = TESTS_DIR / "fixtures"
