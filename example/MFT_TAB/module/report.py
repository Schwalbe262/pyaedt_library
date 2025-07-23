import numpy as np
import pandas as pd

def extract_data_from_last_line(filename):
    """
    Reads the last non-empty line from a file and extracts convergence data.
    """
    with open(filename, 'r') as file:
        lines = file.readlines()

    last_data_line = ""
    for line in reversed(lines):
        if line.strip():
            last_data_line = line
            break
    
    if not last_data_line:
        return None, None, None, None, None

    parts = last_data_line.split('|')
    pass_number = parts[0].strip()
    tetrahedra = parts[1].strip()
    total_energy = parts[2].strip()
    energy_error = parts[3].strip()
    delta_energy = parts[4].strip()

    return pass_number, tetrahedra, total_energy, energy_error, delta_energy


def get_input_parameter(design):
    """
    Gathers input parameters from the design object and returns them as a pandas DataFrame.
    """
    param_columns = [
            "N1", "N2", "N1_layer", "N2_layer", "frequency", "per", "w1", "l1_top", "l1_top_ratio", "l1_side", "l1_side_ratio", "l1_center", "l2", "l2_gap", "h1",
            "h1_gap", "h2_gap", "N1_height_ratio", "N1_fill_factor", "N1_coil_diameter",
            "N1_coil_zgap", "N2_height_ratio", "N2_fill_factor", "N2_coil_diameter",
            "N2_coil_zgap", "N1_space_w", "N1_space_l", "N2_space_w", "N2_space_l",
            "N1_layer_gap", "N2_layer_gap", "N1_offset_ratio", "N2_offset_ratio",
            "N1_offset", "N2_offset", "cold_plate_x", "cold_plate_y", "cold_plate_z1",
            "cold_plate_z2", "mold_thick", "thermal_conductivity"
        ]       
    
    input_data = {col: [getattr(design, col, None)] for col in param_columns}
    
    return pd.DataFrame(data=input_data)


def get_maxwell_magnetic_parameter(design, dir=None, mod="write", import_report=None, report_name="magnetic_report"):
    """
    Creates a report for magnetic parameters (Inductances, Coupling)
    and returns the data as a pandas DataFrame.
    """



    params = [
        ["Matrix.L(Tx_Winding,Tx_Winding)", f"L11", "uH"],
        ["Matrix.L(Rx1_Winding,Rx1_Winding)", f"L22", "uH"],
        ["Matrix.L(Rx2_Winding,Rx2_Winding)", f"L33", "uH"],
        ["Matrix.L(Tx_Winding,Rx1_Winding)", f"M12", "uH"],
        ["Matrix.L(Tx_Winding,Rx2_Winding)", f"M13", "uH"],
        ["Matrix.L(Rx_Winding1,Rx_Winding2)", f"M23", "uH"],
        ["abs(Matrix.CplCoef(Tx_Winding,Rx1_Winding))", f"k12", ""],
        ["abs(Matrix.CplCoef(Tx_Winding,Rx2_Winding))", f"k13", ""],
        ["abs(Matrix.CplCoef(Rx1_Winding,Rx2_Winding))", f"k23", ""],
        ["Matrix.L(Tx_Winding,Tx_Winding)*(abs(Matrix.CplCoef(Tx_Winding,Rx1_Winding))^2)", f"Lmt1", "uH"],
        ["Matrix.L(Tx_Winding,Tx_Winding)*(abs(Matrix.CplCoef(Tx_Winding,Rx2_Winding))^2)", f"Lmt2", "uH"],
        ["Matrix.L(Tx_Winding,Tx_Winding)*(1-abs(Matrix.CplCoef(Tx_Winding,Rx1_Winding))^2)", f"Llk12", "uH"],
        ["Matrix.L(Tx_Winding,Tx_Winding)*(1-abs(Matrix.CplCoef(Tx_Winding,Rx2_Winding))^2)", f"Llk13", "uH"],
        ["Matrix.L(Rx1_Winding,Rx1_Winding)*(1-abs(Matrix.CplCoef(Rx1_Winding,Tx_Winding))^2)", f"Llk21", "uH"],
        ["Matrix.L(Rx1_Winding,Rx1_Winding)*(1-abs(Matrix.CplCoef(Rx1_Winding,Tx_Winding))^2)", f"Llk23", "uH"],
        ["Matrix.L(Rx2_Winding,Rx2_Winding)*(1-abs(Matrix.CplCoef(Rx2_Winding,Tx_Winding))^2)", f"Llk31", "uH"],
        ["Matrix.L(Rx2_Winding,Rx2_Winding)*(1-abs(Matrix.CplCoef(Rx2_Winding,Tx_Winding))^2)", f"Llk32", "uH"],
    ]

    report, df = design.get_magnetic_parameter(dir=dir, parameters=params, mod=mod, import_report=import_report, report_name=report_name)

    return report, df



def get_maxwell_calculator_parameter(design, dir=None, mod="write", import_report=None, report_name="calculator_report"):
    """
    Creates a report for various calculator quantities (losses, fields).
    """
    params = [
        [design.winding1, f"P_winding1", "EMLoss"],
        [design.winding2, f"P_winding2", "EMLoss"],
        [design.winding3, f"P_winding3", "EMLoss"],
        [design.core, f"P_Core", "CoreLoss"],
        [design.leg_left, f"B_mean_leg_left", "B_mean"],
        [design.leg_right, f"B_mean_leg_right", "B_mean"],
        [design.leg_center, f"B_mean_leg_center", "B_mean"],
        [design.leg_top_left, f"B_mean_leg_top_left", "B_mean"],
        [design.leg_top_right, f"B_mean_leg_top_right", "B_mean"],
        [design.leg_bottom_left, f"B_mean_leg_bottom_left", "B_mean"],
        [design.leg_bottom_right, f"B_mean_leg_bottom_right", "B_mean"],
    ]

    report, df = design.get_calculator_parameter(dir=dir, parameters=params, mod=mod, import_report=import_report, report_name=report_name)

    return report, df


def get_icepak_calculator_parameter(design, dir=None, mod="write", import_report=None):
    """
    Creates a report for various calculator quantities (losses, fields).
    """
    params = [
        [design.core, f"Temp_max_core", "Temp_max"],
        [design.core, f"Temp_mean_core", "Temp_mean"],
        [design.winding1, f"Temp_max_winding1", "Temp_max"],
        [design.winding1, f"Temp_mean_winding1", "Temp_mean"],
        [design.winding2, f"Temp_max_winding2", "Temp_max"],
        [design.winding2, f"Temp_mean_winding2", "Temp_mean"],
        [design.winding3, f"Temp_max_winding3", "Temp_max"],
        [design.winding3, f"Temp_mean_winding3", "Temp_mean"],
        [design.leg_left, f"Temp_max_leg_left", "Temp_max"],
        [design.leg_right, f"Temp_max_leg_right", "Temp_max"],
        [design.leg_center, f"Temp_max_leg_center", "Temp_max"],
        [design.leg_top_left, f"Temp_max_leg_top_left", "Temp_max"],
        [design.leg_top_right, f"Temp_max_leg_top_right", "Temp_max"],
        [design.leg_bottom_left, f"Temp_max_leg_bottom_left", "Temp_max"],
        [design.leg_bottom_right, f"Temp_max_leg_bottom_right", "Temp_max"],
        [design.leg_left, f"Temp_mean_leg_left", "Temp_mean"],
        [design.leg_right, f"Temp_mean_leg_right", "Temp_mean"],
        [design.leg_center, f"Temp_mean_leg_center", "Temp_mean"],
        [design.leg_top_left, f"Temp_mean_leg_top_left", "Temp_mean"],
        [design.leg_top_right, f"Temp_mean_leg_top_right", "Temp_mean"],
        [design.leg_bottom_left, f"Temp_mean_leg_bottom_left", "Temp_mean"],
        [design.leg_bottom_right, f"Temp_mean_leg_bottom_right", "Temp_mean"],
    ]

    # Icepak does not have a frequency sweep, so we expect a single row of results.
    # The get_calculator_parameter function should be adapted to handle this.
    report, df = design.get_calculator_parameter(dir=dir, parameters=params, mod=mod, import_report=import_report)

    return report, df
    

def get_convergence_report(design, setup_name="Setup1"):
    """
    Exports the convergence report, extracts data from the last analysis pass,
    and returns it as a pandas DataFrame.
    """
    report_path = design.export_convergence(setup=setup_name)
    pass_num, tetra, energy, error, delta = extract_data_from_last_line(report_path)
    
    columns = {
        'Pass Number': pass_num,
        'Tetrahedra': tetra,
        'Total Energy': energy,
        'Energy Error': error,
        'Delta Energy': delta
    }
    
    new_columns = {k: [v] for k, v in columns.items()}
        
    return pd.DataFrame(data=new_columns) 