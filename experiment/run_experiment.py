from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parent
SCRIPTS = ROOT / "scripts"


def run(script: str) -> None:
    path = SCRIPTS / script
    print(f"\n[run] {path}")
    subprocess.run([sys.executable, str(path)], check=True)


def main() -> None:
    run("generate_dataset.py")
    run("traditional_point_splat.py")
    run("neural_ray_field.py")
    run("make_summary.py")
    print("\nDone. See experiment/outputs/summary/metrics.csv and comparison.png")


if __name__ == "__main__":
    main()
