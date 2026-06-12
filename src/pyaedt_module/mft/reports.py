"""MFT report presets."""

import pandas as pd


INPUT_PARAMETER_COLUMNS = [
    "N1",
    "N2",
    "N1_layer",
    "N2_layer",
    "frequency",
    "per",
    "w1",
    "l1_top",
    "l1_top_ratio",
    "l1_side",
    "l1_side_ratio",
    "l1_center",
    "l2",
    "l2_gap",
    "h1",
    "h1_gap",
    "h2_gap",
    "N1_height_ratio",
    "N1_fill_factor",
    "N1_coil_diameter",
    "N1_coil_zgap",
    "N2_height_ratio",
    "N2_fill_factor",
    "N2_coil_diameter",
    "N2_coil_zgap",
    "N1_space_w",
    "N1_space_l",
    "N2_space_w",
    "N2_space_l",
    "N1_layer_gap",
    "N2_layer_gap",
    "N1_offset_ratio",
    "N2_offset_ratio",
    "N1_offset",
    "N2_offset",
    "cold_plate_x",
    "cold_plate_y",
    "cold_plate_z1",
    "cold_plate_z2",
    "mold_thick",
    "thermal_conductivity",
    "winding_thermal_ratio",
    "wind_speed",
]


def extract_data_from_last_line(filename):
    with open(filename, "r") as file:
        lines = file.readlines()
    last_data_line = next((line for line in reversed(lines) if line.strip()), "")
    if not last_data_line:
        return None, None, None, None, None
    parts = [part.strip() for part in last_data_line.split("|")]
    parts.extend([None] * (5 - len(parts)))
    return parts[:5]


def get_input_parameter(design):
    input_data = {column: [getattr(design, column, None)] for column in INPUT_PARAMETER_COLUMNS}
    return pd.DataFrame(data=input_data)


def get_maxwell_magnetic_parameter(
    design,
    dir=None,
    mod="write",
    import_report=None,
    report_name="magnetic_report",
    file_name="magnetic_report",
    parameters=None,
):
    params = parameters or [
        ["Matrix.L(Tx_Winding,Tx_Winding)", "L11", "uH"],
        ["Matrix.L(Rx1_Winding,Rx1_Winding)", "L22", "uH"],
        ["Matrix.L(Rx2_Winding,Rx2_Winding)", "L33", "uH"],
        ["Matrix.L(Tx_Winding,Rx1_Winding)", "M12", "uH"],
        ["Matrix.L(Tx_Winding,Rx2_Winding)", "M13", "uH"],
        ["Matrix.L(Rx_Winding1,Rx_Winding2)", "M23", "uH"],
        ["abs(Matrix.CplCoef(Tx_Winding,Rx1_Winding))", "k12", ""],
        ["abs(Matrix.CplCoef(Tx_Winding,Rx2_Winding))", "k13", ""],
        ["abs(Matrix.CplCoef(Rx1_Winding,Rx2_Winding))", "k23", ""],
        ["Matrix.L(Tx_Winding,Tx_Winding)*(abs(Matrix.CplCoef(Tx_Winding,Rx1_Winding))^2)", "Lmt1", "uH"],
        ["Matrix.L(Tx_Winding,Tx_Winding)*(abs(Matrix.CplCoef(Tx_Winding,Rx2_Winding))^2)", "Lmt2", "uH"],
        ["Matrix.L(Tx_Winding,Tx_Winding)*(1-abs(Matrix.CplCoef(Tx_Winding,Rx1_Winding))^2)", "Llk12", "uH"],
        ["Matrix.L(Tx_Winding,Tx_Winding)*(1-abs(Matrix.CplCoef(Tx_Winding,Rx2_Winding))^2)", "Llk13", "uH"],
        ["Matrix.L(Rx1_Winding,Rx1_Winding)*(1-abs(Matrix.CplCoef(Rx1_Winding,Tx_Winding))^2)", "Llk21", "uH"],
        ["Matrix.L(Rx1_Winding,Rx1_Winding)*(1-abs(Matrix.CplCoef(Rx1_Winding,Rx2_Winding))^2)", "Llk23", "uH"],
        ["Matrix.L(Rx2_Winding,Rx2_Winding)*(1-abs(Matrix.CplCoef(Rx2_Winding,Tx_Winding))^2)", "Llk31", "uH"],
        ["Matrix.L(Rx2_Winding,Rx2_Winding)*(1-abs(Matrix.CplCoef(Rx2_Winding,Rx1_Winding))^2)", "Llk32", "uH"],
    ]
    return design.get_magnetic_parameter(
        dir=dir,
        parameters=params,
        mod=mod,
        import_report=import_report,
        report_name=report_name,
        file_name=file_name,
    )


def get_maxwell_calculator_parameter(
    design,
    dir=None,
    mod="write",
    import_report=None,
    report_name="calculator_report",
    file_name="calculator_report",
    parameters=None,
):
    params = parameters or [
        [design.winding1, "P_winding1", "EMLoss"],
        [design.winding2, "P_winding2", "EMLoss"],
        [design.winding3, "P_winding3", "EMLoss"],
        [design.core, "P_Core", "CoreLoss"],
        [design.leg_left, "B_mean_leg_left", "B_mean"],
        [design.leg_right, "B_mean_leg_right", "B_mean"],
        [design.leg_center, "B_mean_leg_center", "B_mean"],
        [design.leg_top_left, "B_mean_leg_top_left", "B_mean"],
        [design.leg_top_right, "B_mean_leg_top_right", "B_mean"],
        [design.leg_bottom_left, "B_mean_leg_bottom_left", "B_mean"],
        [design.leg_bottom_right, "B_mean_leg_bottom_right", "B_mean"],
    ]
    return design.get_calculator_parameter(
        dir=dir,
        parameters=params,
        mod=mod,
        import_report=import_report,
        report_name=report_name,
        file_name=file_name,
    )


def get_icepak_calculator_parameter(
    design,
    dir=None,
    mod="write",
    import_report=None,
    report_name="thermal_report",
    file_name="thermal_report",
    parameters=None,
):
    params = parameters or [
        [design.core, "Temp_max_core", "Temp_max"],
        [design.core, "Temp_mean_core", "Temp_mean"],
        [design.winding1, "Temp_max_winding1", "Temp_max"],
        [design.winding1, "Temp_mean_winding1", "Temp_mean"],
        [design.winding2, "Temp_max_winding2", "Temp_max"],
        [design.winding2, "Temp_mean_winding2", "Temp_mean"],
        [design.winding3, "Temp_max_winding3", "Temp_max"],
        [design.winding3, "Temp_mean_winding3", "Temp_mean"],
        [design.leg_left, "Temp_max_leg_left", "Temp_max"],
        [design.leg_right, "Temp_max_leg_right", "Temp_max"],
        [design.leg_center, "Temp_max_leg_center", "Temp_max"],
        [design.leg_top_left, "Temp_max_leg_top_left", "Temp_max"],
        [design.leg_top_right, "Temp_max_leg_top_right", "Temp_max"],
        [design.leg_bottom_left, "Temp_max_leg_bottom_left", "Temp_max"],
        [design.leg_bottom_right, "Temp_max_leg_bottom_right", "Temp_max"],
        [design.leg_left, "Temp_mean_leg_left", "Temp_mean"],
        [design.leg_right, "Temp_mean_leg_right", "Temp_mean"],
        [design.leg_center, "Temp_mean_leg_center", "Temp_mean"],
        [design.leg_top_left, "Temp_mean_leg_top_left", "Temp_mean"],
        [design.leg_top_right, "Temp_mean_leg_top_right", "Temp_mean"],
        [design.leg_bottom_left, "Temp_mean_leg_bottom_left", "Temp_mean"],
        [design.leg_bottom_right, "Temp_mean_leg_bottom_right", "Temp_mean"],
    ]
    return design.get_calculator_parameter(
        dir=dir,
        parameters=params,
        mod=mod,
        import_report=import_report,
        report_name=report_name,
        file_name=file_name,
    )


def get_convergence_report(design, setup_name="Setup1"):
    report_path = design.export_convergence(setup=setup_name)
    pass_num, tetra, energy, error, delta = extract_data_from_last_line(report_path)
    return pd.DataFrame(
        data={
            "Pass Number": [pass_num],
            "Tetrahedra": [tetra],
            "Total Energy": [energy],
            "Energy Error": [error],
            "Delta Energy": [delta],
        }
    )
