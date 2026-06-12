# Examples

This directory contains runnable examples and older reference notebooks.

## Supported PyAEDT 1.0.1 examples

The supported execution path is the `run_simulation.py` file in each example
directory. These scripts are covered by the no-solve AEDT smoke runner:

```powershell
python -m pip install -e .
python tools/smoke_examples_pyaedt_1_0_1.py --version 261
```

The smoke runner imports each `Simulation` class, creates the AEDT project and
Maxwell design, builds geometry, assigns mesh/excitations, exports snapshots,
and then releases Desktop. It does not solve.

## Legacy/reference notebooks

Notebook files (`*.ipynb`) are kept as historical references. They may contain
stale code snippets, old local paths, or pre-1.0 PyAEDT usage. Use
`run_simulation.py` and the smoke tools as the current source of truth.

## Slurm controllers

`controller.py` files are operational helpers for cluster runs. They default to
a no-op dry run. Use action flags to preview work, and add `--execute` only when
the selected actions should actually run:

```powershell
python controller.py --submit --iterations 1
python controller.py --submit --iterations 1 --execute
```

Available action flags are `--submit`, `--kill-existing`, and `--clean`.
Cleanup is limited to contents under the example's own `simulation/` directory.
