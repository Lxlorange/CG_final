from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(args: list[str]) -> None:
    print("+", " ".join(args))
    subprocess.run(args, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Postprocess multi-scene formal experiments.")
    parser.add_argument("--scenes", nargs="+", default=["lego", "materials", "drums"])
    parser.add_argument("--methods", nargs="+", default=["nerfacto", "splatfacto"])
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--traditional-resolution", type=int, default=96)
    parser.add_argument("--skip-traditional", action="store_true")
    parser.add_argument("--lpips", action="store_true")
    parser.add_argument("--lpips-device", default="cpu")
    args = parser.parse_args()

    scripts = ROOT / "scripts"
    for scene in args.scenes:
        run([
            sys.executable,
            str(scripts / "prepare_nerf_synthetic_eval.py"),
            "--scene",
            scene,
            "--max-views",
            str(args.limit),
            "--copy-mode",
            "composite",
        ])

        if not args.skip_traditional:
            run([
                sys.executable,
                str(scripts / "traditional_visual_hull.py"),
                "--scene",
                scene,
                "--resolution",
                str(args.traditional_resolution),
                "--limit",
                str(args.limit),
            ])

        for method in args.methods:
            raw_dir = ROOT / "outputs" / "formal" / scene / "raw_renders" / method
            dst_dir = ROOT / "outputs" / "formal" / scene / method
            if raw_dir.exists():
                run([
                    sys.executable,
                    str(scripts / "normalize_nerfstudio_renders.py"),
                    "--src-dir",
                    str(raw_dir),
                    "--dst-dir",
                    str(dst_dir),
                    "--limit",
                    str(args.limit),
                ])
            if dst_dir.exists():
                cmd = [
                    sys.executable,
                    str(scripts / "evaluate_folder.py"),
                    "--pred-dir",
                    str(dst_dir),
                    "--method",
                    method,
                    "--gt-dir",
                    str(ROOT / "outputs" / "formal" / scene / "gt"),
                    "--limit",
                    str(args.limit),
                ]
                if args.lpips:
                    cmd.extend(["--lpips", "--lpips-device", args.lpips_device])
                run(cmd)

        run([
            sys.executable,
            str(scripts / "make_formal_summary.py"),
            "--scene",
            scene,
            "--max-views",
            "8",
        ])


if __name__ == "__main__":
    main()
