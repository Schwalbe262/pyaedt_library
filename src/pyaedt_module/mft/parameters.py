"""MFT parameter generation, validation, and AEDT variable helpers."""

import numpy as np
import pandas as pd


DEFAULT_PARAMETER_COLUMNS = [
    "N1",
    "N2",
    "N1_main",
    "N1_side",
    "N2_main",
    "N2_side",
    "w1",
    "l1",
    "l2",
    "h1",
    "cc_w2c_space_x",
    "w2c_w1c_space_x",
    "w1c_w2s_space_x",
    "w2s_w1s_space_x",
    "w1s_cs_space_x",
    "cc_w2c_space_y",
    "w2c_w1c_space_y",
    "cs_w1s_space_y",
    "w1s_w2s_space_y",
    "window_ratio",
    "wh1",
    "wh2",
    "wff1",
    "wff2",
]

DEFAULT_UNITS = {
    "w1": "mm",
    "l1": "mm",
    "l2": "mm",
    "h1": "mm",
    "cc_w2c_space_x": "mm",
    "w2c_w1c_space_x": "mm",
    "w1c_w2s_space_x": "mm",
    "w2s_w1s_space_x": "mm",
    "w1s_cs_space_x": "mm",
    "cc_w2c_space_y": "mm",
    "w2c_w1c_space_y": "mm",
    "cs_w1s_space_y": "mm",
    "w1s_w2s_space_y": "mm",
    "w1c_space_z": "mm",
    "w2c_space_z": "mm",
}


def get_random_value(lower=None, upper=None, resolution=None, rng=None):
    rng = rng or np.random
    if isinstance(resolution, float):
        resolution_text = f"{resolution:.16f}".rstrip("0").rstrip(".")
        precision = len(resolution_text.split(".")[-1]) if "." in resolution_text else 0
    else:
        precision = 0

    possible_values = np.arange(lower, upper + resolution * 0.5, resolution)
    if len(possible_values) == 0:
        possible_values = np.array([upper])
    elif abs(possible_values[-1] - upper) > 1e-8 and np.abs(possible_values - upper).min() > 1e-8:
        possible_values = np.unique(np.append(possible_values, upper))

    if hasattr(rng, "choice"):
        chosen = rng.choice(possible_values)
    else:
        chosen = np.random.choice(possible_values)
    value = round(float(chosen), precision)
    return int(value) if resolution in (1, 1.0) else float(value)


def _coerce_parameter_frame(param_list):
    if isinstance(param_list, pd.DataFrame):
        return param_list.copy()
    if isinstance(param_list, (list, tuple)) and param_list:
        first = param_list[0]
        if not isinstance(first, (list, tuple, dict, pd.Series)):
            param_list = [param_list]
    return pd.DataFrame(param_list, columns=DEFAULT_PARAMETER_COLUMNS)


def create_input_parameter(param_list=None, rng=None):
    if param_list is not None:
        param_df = _coerce_parameter_frame(param_list)
        if param_df.shape[1] != len(DEFAULT_PARAMETER_COLUMNS):
            raise ValueError(
                f"Input list must have exactly {len(DEFAULT_PARAMETER_COLUMNS)} elements, "
                f"but got {param_df.shape[1]}."
            )
        return param_df

    rng = rng or np.random
    n1 = get_random_value(5, 10, 1, rng=rng)
    n2 = n1 * 10
    n1_side = round(n1 * get_random_value(0, 0.5, 0.01, rng=rng))
    n1_main = n1 - n1_side
    n2_side = round(n2 * get_random_value(0, 0.8, 0.01, rng=rng))
    n2_main = n2 - n2_side

    w1 = get_random_value(200, 800, 1, rng=rng)
    l1 = get_random_value(40, 100, 1, rng=rng)
    total_length = get_random_value(500, 1200, 1, rng=rng)
    l2 = (total_length - 4 * l1) / 2
    total_height = get_random_value(500, 1000, 1, rng=rng)
    h1 = total_height - 2 * l1

    values = [
        n1,
        n2,
        n1_main,
        n1_side,
        n2_main,
        n2_side,
        w1,
        l1,
        l2,
        h1,
        get_random_value(10, 50, 0.1, rng=rng),
        get_random_value(10, 50, 0.1, rng=rng),
        get_random_value(10, 100, 0.1, rng=rng),
        get_random_value(10, 50, 0.1, rng=rng),
        get_random_value(10, 50, 0.1, rng=rng),
        get_random_value(10, 50, 0.1, rng=rng),
        get_random_value(10, 50, 0.1, rng=rng),
        get_random_value(10, 50, 0.1, rng=rng),
        get_random_value(10, 50, 0.1, rng=rng),
        get_random_value(0.3, 0.7, 0.01, rng=rng),
        get_random_value(0.8, 0.95, 0.01, rng=rng),
        get_random_value(0.5, 0.95, 0.01, rng=rng),
        get_random_value(0.4, 0.8, 0.01, rng=rng),
        get_random_value(0.4, 0.75, 0.01, rng=rng),
    ]
    return pd.DataFrame([values], columns=DEFAULT_PARAMETER_COLUMNS)


def _safe_gap(total, item, count):
    gaps = count - 1
    if gaps <= 0:
        return 0
    return (total - item * count) / gaps


def derive_parameters(input_df):
    inp = input_df.copy()
    row = inp.iloc[0]

    nwl_x = (
        row["l2"]
        - row["cc_w2c_space_x"]
        - row["w2c_w1c_space_x"]
        - row["w1c_w2s_space_x"]
        - row["w2s_w1s_space_x"]
        - row["w1s_cs_space_x"]
    )
    inp["nwl_x"] = [nwl_x]

    n1_main = row["N1_main"]
    n1_side = row["N1_side"]
    n2_main = row["N2_main"]
    n2_side = row["N2_side"]
    n1_total = n1_main + n1_side
    n2_total = n2_main + n2_side

    nwl1 = nwl_x * row["window_ratio"]
    nwl2 = nwl_x - nwl1
    cw1 = (nwl1 * row["wff1"]) / n1_total if n1_total else 0
    cw2 = (nwl2 * row["wff2"]) / n2_total if n2_total else 0
    inp["cw1"] = [cw1]
    inp["cw2"] = [cw2]

    coil_gap_layer1 = _safe_gap(nwl1, cw1, n1_total)
    coil_gap_layer2 = _safe_gap(nwl2, cw2, n2_total)
    inp["coil_gap_layer1"] = [coil_gap_layer1]
    inp["coil_gap_layer2"] = [coil_gap_layer2]

    nwl1_main = cw1 * n1_main + coil_gap_layer1 * max(n1_main - 1, 0)
    nwl1_side = cw1 * n1_side + coil_gap_layer1 * max(n1_side - 1, 0)
    nwl2_main = cw2 * n2_main + coil_gap_layer2 * max(n2_main - 1, 0)
    nwl2_side = cw2 * n2_side + coil_gap_layer2 * max(n2_side - 1, 0)
    inp["nwl1_main"] = [nwl1_main]
    inp["nwl1_side"] = [nwl1_side]
    inp["nwl2_main"] = [nwl2_main]
    inp["nwl2_side"] = [nwl2_side]

    nwh1 = row["h1"] * row["wh1"]
    nwh2 = row["h1"] * row["wh2"]
    inp["nwh1"] = [nwh1]
    inp["nwh2"] = [nwh2]
    inp["h_gap1"] = [(row["h1"] - nwh1) / 2]
    inp["h_gap2"] = [(row["h1"] - nwh2) / 2]

    inp["wff1_main"] = [0 if n1_main == 0 else cw1 * n1_main / max(nwl1_main, 1e-12)]
    inp["wff1_side"] = [0 if n1_side == 0 else cw1 * n1_side / max(nwl1_side, 1e-12)]
    inp["wff2_main"] = [0 if n2_main == 0 else cw2 * n2_main / max(nwl2_main, 1e-12)]
    inp["wff2_side"] = [0 if n2_side == 0 else cw2 * n2_side / max(nwl2_side, 1e-12)]

    sl2_main_x = 2 * row["l1"] + 2 * row["cc_w2c_space_x"]
    sl2_main_y = row["w1"] + 2 * row["cc_w2c_space_y"]
    sl1_main_x = sl2_main_x + 2 * nwl2_main + 2 * row["w2c_w1c_space_x"]
    sl1_main_y = sl2_main_y + 2 * nwl2_main + 2 * row["w2c_w1c_space_y"]
    sl1_side_x = row["l1"] + 2 * row["w1s_cs_space_x"]
    sl1_side_y = row["w1"] + 2 * row["cs_w1s_space_y"]
    sl2_side_x = sl1_side_x + 2 * nwl1_side + 2 * row["w2s_w1s_space_x"]
    sl2_side_y = sl1_side_y + 2 * nwl1_side + 2 * row["w1s_w2s_space_y"]

    inp["sl2_main_x"] = [sl2_main_x]
    inp["sl2_main_y"] = [sl2_main_y]
    inp["sl1_main_x"] = [sl1_main_x]
    inp["sl1_main_y"] = [sl1_main_y]
    inp["sl1_side_x"] = [sl1_side_x]
    inp["sl1_side_y"] = [sl1_side_y]
    inp["sl2_side_x"] = [sl2_side_x]
    inp["sl2_side_y"] = [sl2_side_y]

    return inp


def validation_check(input_df):
    derived = derive_parameters(input_df)
    row = derived.iloc[0]
    valid = True
    valid = valid and row["nwl1_main"] >= 0 and row["nwl2_main"] >= 0
    valid = valid and row["nwh1"] >= 0 and row["nwh2"] >= 0
    valid = valid and 1.0 <= row["cw1"] <= 10
    valid = valid and row["cw2"] >= 0.6
    valid = valid and row["coil_gap_layer1"] >= 0.3
    valid = valid and row["coil_gap_layer2"] >= 0.3
    return bool(valid), derived


def set_design_variables(design, input_parameter, units=None):
    units = {**DEFAULT_UNITS, **(units or {})}
    row = input_parameter.iloc[0] if isinstance(input_parameter, pd.DataFrame) else input_parameter
    for key, value in row.items():
        unit = units.get(key, "")
        design.set_variable(variable_name=key, value=value, unit=unit)
