import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_DIR = ROOT / "example"
RUN_SCRIPTS = sorted(EXAMPLE_DIR.glob("*/run_simulation.py"))
CONTROLLERS = sorted(EXAMPLE_DIR.glob("*/controller.py"))
PERSONAL_PATH_PATTERNS = ("Y:/git", "NEC_5950X1", "/gpfs/home")


def test_run_simulation_entrypoints_do_not_use_personal_absolute_paths():
    assert RUN_SCRIPTS
    for script in RUN_SCRIPTS:
        text = script.read_text(encoding="utf-8")
        for pattern in PERSONAL_PATH_PATTERNS:
            assert pattern not in text, f"{script} contains personal path pattern {pattern}"
        assert 'Path(__file__).resolve().parents[2] / "src"' in text


def test_controllers_have_explicit_action_and_execute_flags():
    assert CONTROLLERS
    for controller in CONTROLLERS:
        text = controller.read_text(encoding="utf-8")
        for flag in ("--execute", "--submit", "--kill-existing", "--clean"):
            assert flag in text, f"{controller} does not expose {flag}"
        assert '["rm", "-rf"' not in text
        assert "rm -rf" not in text
        assert "while True" not in text


def test_controllers_default_to_noop():
    for controller in CONTROLLERS:
        result = subprocess.run(
            [sys.executable, str(controller)],
            cwd=controller.parent,
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0, result.stderr
        assert "No controller actions selected" in result.stdout
        assert all(not line.startswith("RUN:") for line in result.stdout.splitlines())
        assert "DRY-RUN:" not in result.stdout


def test_controller_submit_without_execute_is_dry_run():
    for controller in CONTROLLERS:
        result = subprocess.run(
            [
                sys.executable,
                str(controller),
                "--submit",
                "--iterations",
                "1",
                "--submit-delay",
                "0",
                "--status-delay",
                "0",
            ],
            cwd=controller.parent,
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0, result.stderr
        assert "DRY-RUN: sbatch simulation1.sh" in result.stdout
        assert "DRY-RUN: sbatch simulation2.sh" in result.stdout
        assert all(not line.startswith("RUN:") for line in result.stdout.splitlines())
