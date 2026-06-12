"""Small runtime helpers for MFT simulation scripts."""

import os
from pathlib import Path

import pandas as pd
from filelock import FileLock


def create_simulation_name(counter_file="simulation_num.txt", prefix="simulation"):
    counter_path = Path(counter_file)
    counter_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = counter_path.with_suffix(counter_path.suffix + ".lock")
    with FileLock(str(lock_path)):
        if not counter_path.exists():
            counter_path.write_text("1", encoding="utf-8")
        content = counter_path.read_text(encoding="utf-8").strip() or "1"
        number = int(content)
        counter_path.write_text(str(number + 1), encoding="utf-8")
    return f"{prefix}{number}", number


def save_results_to_csv(results_df, filename="simulation_results.csv"):
    results_df = pd.DataFrame(results_df)
    lock_path = f"{filename}.lock"
    with FileLock(lock_path):
        file_exists = os.path.isfile(filename)
        results_df.to_csv(filename, mode="a", header=not file_exists, index=False)
    return filename


def save_geometry_views(design, output_dir, prefix="model", orientations=None, enable_pyvista_snapshot=False):
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    saved_files = []
    orientations = orientations or ["isometric", "top", "front", "right", "left", "bottom", "back"]

    for orientation in orientations:
        out_file = output_path / f"{prefix}_{orientation}.jpg"
        try:
            if hasattr(design, "post") and hasattr(design.post, "export_model_picture"):
                design.post.export_model_picture(
                    full_name=str(out_file),
                    show_axis=True,
                    show_grid=False,
                    show_ruler=False,
                    show_region=False,
                    orientation=orientation,
                )
                if out_file.exists():
                    saved_files.append(str(out_file))
        except Exception as exc:
            print(f"[WARN] export_model_picture failed ({orientation}): {exc}")

    if enable_pyvista_snapshot:
        pyvista_path = output_path / f"{prefix}_pyvista.png"
        try:
            if hasattr(design, "plot"):
                design.plot(show=False, output_file=str(pyvista_path))
                if pyvista_path.exists():
                    saved_files.append(str(pyvista_path))
        except Exception as exc:
            print(f"[WARN] design.plot failed: {exc}")

    names_path = output_path / f"{prefix}_objects.txt"
    try:
        modeler = getattr(design, "modeler", None)
        if modeler is not None:
            names = list(getattr(modeler, "object_names", []))
            names_path.write_text("\n".join(names), encoding="utf-8")
            saved_files.append(str(names_path))
    except Exception as exc:
        print(f"[WARN] failed to write object list: {exc}")

    return saved_files
