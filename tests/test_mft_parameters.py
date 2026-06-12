import pandas as pd

from pyaedt_module.mft.parameters import (
    DEFAULT_PARAMETER_COLUMNS,
    create_input_parameter,
    set_design_variables,
    validation_check,
)


class FakeDesign:
    def __init__(self):
        self.calls = []

    def set_variable(self, variable_name=None, value=None, unit=""):
        self.calls.append((variable_name, value, unit))


def valid_parameter_frame():
    values = [
        20,
        100,
        20,
        0,
        100,
        0,
        200,
        40,
        500,
        500,
        10,
        10,
        10,
        10,
        10,
        10,
        10,
        10,
        10,
        0.5,
        0.9,
        0.9,
        0.5,
        0.5,
    ]
    return pd.DataFrame([values], columns=DEFAULT_PARAMETER_COLUMNS)


def test_create_input_parameter_accepts_flat_row():
    df = create_input_parameter(valid_parameter_frame().iloc[0].tolist())
    assert list(df.columns) == DEFAULT_PARAMETER_COLUMNS
    assert len(df) == 1


def test_validation_check_returns_derived_columns():
    result, derived = validation_check(valid_parameter_frame())
    assert result is True
    assert {"nwl_x", "cw1", "cw2", "sl1_main_x"}.issubset(derived.columns)


def test_set_design_variables_applies_units():
    design = FakeDesign()
    set_design_variables(design, valid_parameter_frame()[["w1", "N1"]])
    assert ("w1", 200, "mm") in design.calls
    assert ("N1", 20, "") in design.calls
