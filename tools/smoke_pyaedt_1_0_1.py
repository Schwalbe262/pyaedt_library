"""AEDT smoke test for PyAEDT 1.0.1 compatibility.

This script intentionally stops after model creation and snapshot export. It
does not solve the design.
"""

import argparse
import os
import re
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from pyaedt_module.core import pyDesktop
from pyaedt_module.mft.modeling import create_coil, create_core
from pyaedt_module.mft.runner import save_geometry_views


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default="261", help="AEDT version, for example 261 or 2026.1")
    parser.add_argument("--non-graphical", action="store_true", default=(os.name != "nt"))
    parser.add_argument("--no-solve", action="store_true", help="Kept for explicit CLI documentation.")
    parser.add_argument("--output-dir", default=None)
    return parser.parse_args()


def configure_ansys_environment(version):
    version_text = str(version)
    match = re.search(r"(\d{3})", version_text)
    if match:
        suffix = match.group(1)
    elif "2026.1" in version_text:
        suffix = "261"
    else:
        return

    if os.environ.get(f"ANSYSEM_ROOT{suffix}"):
        return

    candidates = [
        Path(f"C:/Program Files/ANSYS Inc/v{suffix}/AnsysEM"),
        Path(f"C:/Program Files/AnsysEM/v{suffix}/Win64"),
    ]
    for candidate in candidates:
        if candidate.exists():
            os.environ[f"ANSYSEM_ROOT{suffix}"] = str(candidate)
            os.environ.setdefault(f"AWP_ROOT{suffix}", str(candidate.parent))
            os.environ["PATH"] = f"{candidate};{os.environ.get('PATH', '')}"
            return


def main():
    args = parse_args()
    configure_ansys_environment(args.version)
    try:
        from ansys.aedt.core import settings

        settings.skip_license_check = True
        settings.wait_for_license = False
    except Exception:
        pass

    output_dir = Path(args.output_dir) if args.output_dir else Path(tempfile.mkdtemp(prefix="pyaedt_101_smoke_"))
    project_dir = output_dir / "project"
    project_name = "pyaedt_101_smoke"
    desktop = None

    try:
        desktop = pyDesktop(
            version=args.version,
            non_graphical=args.non_graphical,
            close_on_exit=False,
            new_desktop=True,
        )
        project = desktop.create_project(path=str(project_dir), name=project_name)
        design = project.create_design(name="maxwell_smoke", solver="maxwell3d", solution="AC Magnetic")
        design.set_variables(
            {
                "w1": 200,
                "l1": 40,
                "l2": 300,
                "h1": 300,
            },
            units={"w1": "mm", "l1": "mm", "l2": "mm", "h1": "mm"},
        )
        create_core(design, name="core", core_material="ferrite")
        create_coil(
            design=design,
            name="Tx",
            window_height=120,
            window_length=80,
            window_layer=1,
            N_input=3,
            width_fill_factor=0.6,
            space_length=120,
            space_width=80,
            shape="rectangle",
            color=[255, 10, 10],
        )
        saved = save_geometry_views(design, output_dir / "snapshots", prefix="smoke", orientations=["isometric", "top"])
        print(f"Smoke project: {project.aedt_path}")
        print(f"Saved files: {saved}")
        return 0
    finally:
        if desktop is not None:
            desktop.release(close_projects=True, close_on_exit=True)


if __name__ == "__main__":
    raise SystemExit(main())
