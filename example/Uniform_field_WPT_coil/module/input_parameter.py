# Uniform field WPT coil

import math


def calculate_coil_xy(N, x_init, y_init, x_space_init, y_space_init, width_init, x_space_exp_rate, y_space_exp_rate, width_exp_rate):

    x_final = 0
    y_final = 0

    for i in range(N) :

        if i == 0 :
            x_final = x_final + x_init + width_init/2
            y_final = y_final + y_init + width_init/2
        else :
            x_final = x_final + (width_init*math.exp(-(i-1)*width_exp_rate))/2 + (x_space_init*math.exp(-(i-1)*x_space_exp_rate)) + (width_init*math.exp(-i*width_exp_rate))/2
            y_final = y_final + (width_init*math.exp(-(i-1)*width_exp_rate))/2 + (y_space_init*math.exp(-(i-1)*y_space_exp_rate)) + (width_init*math.exp(-i*width_exp_rate))/2

    return x_final, y_final


def create_input_parameter(design, param_list=None):
    
    # manual input (for test)
    if param_list is not None:
        keys = [
            "N", "x_init", "y_init", "x_final", "y_final", "x_space_init_ratio", "y_space_init_ratio", "x_space_init", "y_space_init", "width_init_ratio", "width_init", 
            "x_focus_ratio", "y_focus_ratio", "x_angle_ratio", "y_angle_ratio", "x_space_exp_rate", "y_space_exp_rate", "width_exp_rate", "thickness", "PCB_core_thickness"
        ]
        
        if len(param_list) != len(keys):
            raise ValueError(f"Input list must have exactly {len(keys)} elements, but got {len(param_list)}.")

        input_parameter = dict(zip(keys, param_list))

        return input_parameter

    N = design.get_random_value(lower=3, upper=10, resolution=1)

    x_init = design.get_random_value(lower=10, upper=50, resolution=0.1)
    y_init_ratio = design.get_random_value(lower=0.5, upper=1, resolution=0.01)
    y_init = design.get_random_value(lower=10, upper=50, resolution=0.1)

    x_space_init_ratio = design.get_random_value(lower=0.1, upper=0.25, resolution=0.01)
    y_space_init_ratio = design.get_random_value(lower=0.1, upper=0.25, resolution=0.01)
    x_space_init = x_init * x_space_init_ratio
    y_space_init = y_init * y_space_init_ratio

    width_init_ratio = design.get_random_value(lower=0.05, upper=0.2, resolution=0.01)
    width_init = x_init * width_init_ratio

    x_focus_ratio = design.get_random_value(lower=0.3, upper=0.8, resolution=0.01)
    y_focus_ratio = design.get_random_value(lower=0.3, upper=0.8, resolution=0.01)

    x_angle_ratio = design.get_random_value(lower=0.3, upper=0.7, resolution=0.01)
    y_angle_ratio = design.get_random_value(lower=0.3, upper=0.7, resolution=0.01)

    x_space_exp_rate = design.get_random_value(lower=0.1, upper=0.5, resolution=0.01)
    y_space_exp_rate = design.get_random_value(lower=0.1, upper=0.5, resolution=0.01)
    width_exp_rate = design.get_random_value(lower=0, upper=0.35, resolution=0.01)

    x_final, y_final = calculate_coil_xy(N, x_init, y_init, x_space_init, y_space_init, width_init, x_space_exp_rate, y_space_exp_rate, width_exp_rate)

    thickness = 35 * design.get_random_value(lower=0.25, upper=3, resolution=0.01) # copper thick (unit:oz)
    PCB_core_thickness = design.get_random_value(lower=30, upper=200, resolution=0.1) # PCB core (unit:um)




    input_parameter = {
        "N" : N,
        "x_init" : x_init,
        "y_init" : y_init,
        "x_final" : x_final,
        "y_final" : y_final,
        "x_space_init_ratio" : x_space_init_ratio,
        "y_space_init_ratio" : y_space_init_ratio,
        "x_space_init" : x_space_init,
        "y_space_init" : y_space_init,
        "width_init_ratio" : width_init_ratio,
        "width_init" : width_init,
        "x_focus_ratio" : x_focus_ratio,
        "y_focus_ratio" : y_focus_ratio,
        "x_angle_ratio" : x_angle_ratio,
        "y_angle_ratio" : y_angle_ratio,
        "x_space_exp_rate" : x_space_exp_rate,
        "y_space_exp_rate" : y_space_exp_rate,
        "width_exp_rate" : width_exp_rate,
        "thickness" : thickness,
        "PCB_core_thickness" : PCB_core_thickness,
    }


    return input_parameter 





def set_design_variables(design, input_parameter):
    """
    주어진 파라미터 딕셔너리를 사용하여 Ansys 디자인 변수를 설정합니다.
    """
    units = {
        "x_init": "mm", "y_init": "mm", "x_final": "mm", "y_final": "mm", "x_space_init": "mm", "y_space_init": "mm", "width_init": "mm",
        "thickness": "um", "PCB_core_thickness": "um"
    }

    for key, value in input_parameter.items():
        # Ansys 디자인에 변수를 설정합니다.
        unit = units.get(key, "")
        design.set_variable(variable_name=key, value=value, unit=unit)

    print("Ansys 디자인 변수가 설정되었습니다.")