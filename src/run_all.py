"""Run the full pipeline: extraction, then every table and figure."""
import shutil
import subprocess
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent
ROOT = SRC.parent
STEPS = ["extract_data.py", "q1_inventory.py", "q2_growth.py", "q3_discounts.py"]


def main():
    """Run extraction and all three analyses, then copy the figures.

    Args:
        None.

    Returns:
        None. Stops with an error if any step fails.
    """
    for step in STEPS:
        print(f"== {step}", flush=True)
        subprocess.run([sys.executable, str(SRC / step)], cwd=SRC if step != "extract_data.py" else ROOT,
                       check=True)
    # The webpage in docs/ serves its own copy of the figures (GitHub Pages root = docs/).
    shutil.copytree(ROOT / "outputs" / "figures", ROOT / "docs" / "figures", dirs_exist_ok=True)


if __name__ == "__main__":
    main()
