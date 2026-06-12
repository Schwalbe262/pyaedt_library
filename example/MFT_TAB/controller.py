"""Safe Slurm controller for this example.

The default mode is a no-op. Select actions with flags, and add ``--execute``
only when those actions should run on the host.
"""

import argparse
import getpass
import shutil
import subprocess
import time
from pathlib import Path


EXAMPLE_DIR = Path(__file__).resolve().parent
SIMULATION_DIR = EXAMPLE_DIR / "simulation"
JOB_SCRIPTS = ("simulation1.sh", "simulation2.sh")
DEFAULT_INTERVAL_SECONDS = 6 * 3600


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true", help="Run selected actions. Without this, print dry-run output.")
    parser.add_argument("--submit", action="store_true", help="Submit simulation1.sh and simulation2.sh jobs.")
    parser.add_argument("--kill-existing", action="store_true", help="Cancel existing Slurm jobs for --user.")
    parser.add_argument("--clean", action="store_true", help="Remove contents under this example's simulation directory.")
    parser.add_argument("--iterations", type=int, default=10, help="Number of times to submit each job script.")
    parser.add_argument("--cycles", type=int, default=1, help="Number of cycles to run. Use 0 to loop forever.")
    parser.add_argument("--interval-seconds", type=int, default=DEFAULT_INTERVAL_SECONDS)
    parser.add_argument("--submit-delay", type=int, default=60)
    parser.add_argument("--status-delay", type=int, default=5)
    parser.add_argument("--user", default=getpass.getuser())
    return parser.parse_args(argv)


def run_command(command, execute):
    action = "RUN" if execute else "DRY-RUN"
    print(f"{action}: {' '.join(command)}")
    if execute:
        subprocess.run(command, cwd=EXAMPLE_DIR, check=True)


def maybe_sleep(seconds, execute):
    if seconds <= 0:
        return
    if execute:
        time.sleep(seconds)
    else:
        print(f"DRY-RUN: sleep {seconds}s")


def clean_simulation_dir(execute):
    if not SIMULATION_DIR.exists():
        print(f"No simulation directory: {SIMULATION_DIR}")
        return

    simulation_root = SIMULATION_DIR.resolve()
    for child in SIMULATION_DIR.iterdir():
        target = child.resolve()
        if simulation_root not in target.parents:
            raise RuntimeError(f"Refusing to remove path outside simulation directory: {target}")

        if execute:
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()
            print(f"REMOVED: {target}")
        else:
            print(f"DRY-RUN: remove {target}")


def submit_jobs(args):
    for script in JOB_SCRIPTS:
        if not (EXAMPLE_DIR / script).exists():
            print(f"SKIP: {script} does not exist")
            continue

        for index in range(args.iterations):
            print(f"Submit {script}: {index + 1}/{args.iterations}")
            run_command(["sbatch", script], args.execute)
            maybe_sleep(args.status_delay, args.execute)
            run_command(["squeue", "-u", args.user], args.execute)
            maybe_sleep(args.submit_delay, args.execute)


def run_cycle(args):
    if args.kill_existing:
        run_command(["scancel", "-u", args.user, "--signal=kill"], args.execute)
    if args.clean:
        clean_simulation_dir(args.execute)
    if args.submit:
        submit_jobs(args)


def main(argv=None):
    args = parse_args(argv)
    if not (args.kill_existing or args.clean or args.submit):
        print("No controller actions selected. Add --submit, --kill-existing, or --clean.")
        print("Add --execute only when selected actions should run on the host.")
        return 0

    cycle = 0
    while args.cycles == 0 or cycle < args.cycles:
        run_cycle(args)
        cycle += 1
        if args.cycles == 0 or cycle < args.cycles:
            maybe_sleep(args.interval_seconds, args.execute)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
