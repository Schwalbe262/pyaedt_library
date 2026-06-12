"""Shared report export and unit-conversion helpers."""

import os
import re

import numpy as np
import pandas as pd


UNIT_FACTORS = {
    "pH": 1e-12,
    "nH": 1e-9,
    "uH": 1e-6,
    "mH": 1e-3,
    "H": 1.0,
    "nW": 1e-9,
    "uW": 1e-6,
    "mW": 1e-3,
    "W": 1.0,
    "kW": 1e3,
    "MW": 1e6,
    "GW": 1e9,
}


def normalize_unit(unit):
    if unit is None:
        return ""
    return str(unit).strip().replace("µ", "u").replace("μ", "u")


def unit_factor(unit):
    return UNIT_FACTORS.get(normalize_unit(unit), 1.0)


def unit_from_column(column_name):
    match = re.search(r"\[(.*?)\]", str(column_name))
    return normalize_unit(match.group(1) if match else "")


def convert_series_to_unit(series, source_unit, target_unit):
    target_unit = normalize_unit(target_unit)
    if not target_unit:
        return pd.to_numeric(series, errors="coerce")
    target_factor = unit_factor(target_unit)
    if target_factor == 0:
        return pd.to_numeric(series, errors="coerce")
    multiplier = unit_factor(source_unit) / target_factor
    return pd.to_numeric(series, errors="coerce").abs() * multiplier


def export_report_to_dataframe(app, directory, report_name, file_name):
    if directory is None:
        directory = os.getcwd()
    os.makedirs(directory, exist_ok=True)
    export_path = os.path.join(directory, f"{file_name}.csv")
    report_module = app.odesign.GetModule("ReportSetup")
    report_module.ExportToFile(report_name, export_path, False)
    return pd.read_csv(export_path)


def select_report_columns(data, expressions, names, units=None, *, add_missing=True, dropna=True):
    units = units or ["" for _ in names]
    output = pd.DataFrame(index=data.index)

    for expression, name, target_unit in zip(expressions, names, units):
        matched_column = next((col for col in data.columns if str(expression) in str(col)), None)
        if matched_column is None:
            if add_missing:
                output[name] = np.nan
            continue
        source_unit = unit_from_column(matched_column)
        output[name] = convert_series_to_unit(data[matched_column], source_unit, target_unit)

    if dropna:
        output.dropna(inplace=True)
    return output
