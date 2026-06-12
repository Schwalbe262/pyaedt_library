"""Run no-solve AEDT smoke checks for bundled examples.

The example ``main()`` functions run full Maxwell/Icepak solves. This runner
imports their ``Simulation`` classes and executes only the setup/modeling steps
needed to verify PyAEDT 1.0.1 compatibility.
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import re
import sys
import tempfile
import traceback
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from pyaedt_module.core import pyDesktop
from pyaedt_module.mft.runner import save_geometry_views


@dataclass(frozen=True)
class ExampleConfig:
    name: str
    script: Path
    steps: tuple[str, ...]
    use_test_parameters: bool = False


EXAMPLES = {
    "MFT_Maxwell_Icepak": ExampleConfig(
        name="MFT_Maxwell_Icepak",
        script=ROOT / "example" / "MFT_Maxwell_Icepak" / "run_simulation.py",
        steps=(
            "create_design",
            "create_input_parameter",
            "set_variable",
            "set_maxwell_analysis",
            "create_core",
            "create_face",
            "create_windings",
            "create_mold",
            "create_cold_plate",
            "create_air",
            "assign_meshing",
            "assign_excitations",
        ),
    ),
    "MFT_TAB": ExampleConfig(
        name="MFT_TAB",
        script=ROOT / "example" / "MFT_TAB" / "run_simulation.py",
        steps=(
            "create_design",
            "create_input_parameter",
            "set_variable",
            "set_maxwell_analysis",
            "create_core",
            "create_face",
            "create_windings",
            "create_mold",
            "create_cold_plate",
            "create_air",
            "assign_meshing",
            "assign_excitations",
        ),
        use_test_parameters=True,
    ),
    "MFT_TAB_natrual_convection": ExampleConfig(
        name="MFT_TAB_natrual_convection",
        script=ROOT / "example" / "MFT_TAB_natrual_convection" / "run_simulation.py",
        steps=(
            "create_design",
            "create_input_parameter",
            "set_variable",
            "set_maxwell_analysis",
            "create_core",
            "create_face",
            "create_windings",
            "create_air",
            "assign_meshing",
            "assign_excitations",
        ),
    ),
    "MFT_TAB_natural_convection_v2": ExampleConfig(
        name="MFT_TAB_natural_convection_v2",
        script=ROOT / "example" / "MFT_TAB_natural_convection_v2" / "run_simulation.py",
        steps=(
            "create_design",
            "create_input_parameter",
            "set_variable",
            "set_maxwell_analysis",
            "create_core",
            "create_face",
            "create_windings",
            "create_air",
            "assign_meshing",
            "assign_excitations",
        ),
    ),
    "Uniform_field_WPT_coil": ExampleConfig(
        name="Uniform_field_WPT_coil",
        script=ROOT / "example" / "Uniform_field_WPT_coil" / "run_simulation.py",
        steps=(
            "create_design",
            "create_input_parameter",
            "set_variable",
            "set_maxwell_analysis",
            "create_one_turn",
        ),
    ),
}


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default="261", help="AEDT version, for example 261 or 2026.1")
    parser.add_argument("--non-graphical", action="store_true", default=(os.name != "nt"))
    parser.add_argument("--example", action="append", choices=sorted(EXAMPLES), help="Example name to run.")
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


def clear_example_modules():
    for key in list(sys.modules):
        if key == "module" or key.startswith("module.") or key.startswith("_example_smoke_"):
            del sys.modules[key]


def import_example(config: ExampleConfig) -> ModuleType:
    clear_example_modules()
    example_dir = str(config.script.parent)
    sys.path.insert(0, example_dir)
    try:
        spec = importlib.util.spec_from_file_location(f"_example_smoke_{config.name}", config.script)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"Could not load {config.script}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        try:
            sys.path.remove(example_dir)
        except ValueError:
            pass


def patch_desktop_factory(module: ModuleType, version, non_graphical):
    def desktop_factory(*args, **kwargs):
        if kwargs.get("version") is None:
            kwargs["version"] = version
        kwargs["non_graphical"] = non_graphical
        kwargs.setdefault("new_desktop", True)
        kwargs["close_on_exit"] = False
        return pyDesktop(*args, **kwargs)

    module.pyDesktop = desktop_factory


def call_step(simulation, step):
    if step == "create_design":
        return simulation.create_design("SST_MFT")
    if step == "create_face":
        return simulation.create_face(simulation.maxwell_design)
    if step == "set_variable":
        return simulation.set_variable(simulation.input_parameters)

    result = getattr(simulation, step)()
    if step == "create_input_parameter":
        simulation.input_parameters = result
    return result


def release_desktop(simulation):
    desktop = getattr(simulation, "desktop", None)
    if desktop is None:
        return
    try:
        desktop.release(close_projects=True, close_on_exit=True)
    except Exception:
        try:
            desktop.release_desktop(close_projects=True, close_on_exit=True)
        except Exception as exc:
            print(f"[WARN] desktop release failed: {exc}")


def run_example(config: ExampleConfig, args, output_root: Path):
    print(f"\n=== {config.name} ===")
    module = import_example(config)
    patch_desktop_factory(module, args.version, args.non_graphical)

    work_dir = output_root / config.name / "work"
    snapshot_dir = output_root / config.name / "snapshots"
    work_dir.mkdir(parents=True, exist_ok=True)

    previous_cwd = Path.cwd()
    simulation = None
    try:
        os.chdir(work_dir)
        simulation = module.Simulation()
        simulation.test = config.use_test_parameters

        for step in config.steps:
            print(f"[{config.name}] {step}")
            call_step(simulation, step)

        design = getattr(simulation, "maxwell_design", None)
        saved = save_geometry_views(
            design,
            snapshot_dir,
            prefix=config.name,
            orientations=["isometric", "top"],
        )
        object_count = len(getattr(getattr(design, "modeler", None), "object_names", []))
        print(f"[PASS] {config.name}: objects={object_count}, saved={saved}")
        return True, None
    except Exception as exc:
        details = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        print(f"[FAIL] {config.name}: {exc}")
        print(details)
        return False, details
    finally:
        if simulation is not None:
            release_desktop(simulation)
        os.chdir(previous_cwd)


def main():
    args = parse_args()
    configure_ansys_environment(args.version)
    try:
        from ansys.aedt.core import settings

        settings.skip_license_check = True
        settings.wait_for_license = False
    except Exception:
        pass

    output_root = Path(args.output_dir) if args.output_dir else Path(tempfile.mkdtemp(prefix="pyaedt_101_examples_"))
    output_root.mkdir(parents=True, exist_ok=True)

    selected = args.example or sorted(EXAMPLES)
    failures = {}
    for name in selected:
        ok, details = run_example(EXAMPLES[name], args, output_root)
        if not ok:
            failures[name] = details

    print(f"\nOutput directory: {output_root}")
    if failures:
        print(f"Failed examples: {', '.join(failures)}")
        return 1
    print("All selected examples passed no-solve smoke checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
