import pandas as pd
import pytest

from pyaedt_module.solver._reports import normalize_unit, select_report_columns


def test_select_report_columns_converts_common_units():
    data = pd.DataFrame(
        {
            "Matrix.L(Tx,Tx) [mH]": [0.002],
            "Loss [mW]": [2500],
            "abs(k)": [0.42],
        }
    )
    result = select_report_columns(
        data,
        ["Matrix.L(Tx,Tx)", "Loss", "abs(k)"],
        ["L_uH", "Loss_W", "k"],
        ["uH", "W", ""],
    )
    assert result["L_uH"].iloc[0] == pytest.approx(2.0)
    assert result["Loss_W"].iloc[0] == pytest.approx(2.5)
    assert result["k"].iloc[0] == pytest.approx(0.42)


def test_normalize_unit_handles_micro_symbols():
    assert normalize_unit("µH") == "uH"
    assert normalize_unit("μW") == "uW"
    assert normalize_unit(None) == ""
