 import math

def calculate_coil_parameter(N, N_layer, h1, height_ratio, fill_factor):
    height = h1 * height_ratio
    effective_height = height * fill_factor

    if N_layer == 1:
        effective_N = N
    elif N_layer == 2:
        effective_N = math.ceil(N / 2)
    else:
        effective_N = N 

    if effective_N == 0:
        return 0, 0

    coil_diameter = effective_height / (effective_N + 1)
    
    if effective_N > 0:
        coil_z_gap = (height - effective_height) / effective_N
    else:
        coil_z_gap = 0

    return coil_diameter, coil_z_gap



def calculate_coil_offset(N, N_layer, h1, height_ratio, offset_ratio) :

    height = h1 * height_ratio
    offset = (h1 - height)/2 * offset_ratio

    return offset


def create_input_parameter(design) :

    N1 = design.get_random_value(lower=5, upper=10, resolution=1)
    N2 = N1
    N1_layer = design.get_random_value(lower=1, upper=2, resolution=1)
    N2_layer = design.get_random_value(lower=1, upper=2, resolution=1)

    per = design.get_random_value(lower=500, upper=30000, resolution=1)
    
    w1 = design.get_random_value(lower=100, upper=350, resolution=0.1)
    l1 = design.get_random_value(lower=15, upper=40, resolution=0.1)
    h1 = design.get_random_value(lower=50, upper=150, resolution=0.1)

    N1_height_ratio = design.get_random_value(lower=0.4, upper=0.95, resolution=0.01)
    N2_height_ratio = design.get_random_value(lower=0.4, upper=0.95, resolution=0.01)
    N1_fill_factor = design.get_random_value(lower=0.6, upper=0.95, resolution=0.01)
    N2_fill_factor = design.get_random_value(lower=0.6, upper=0.95, resolution=0.01)

    N1_coil_diameter, N1_coil_zgap = calculate_coil_parameter(N1, N1_layer, h1, N1_height_ratio, N1_fill_factor)
    N2_coil_diameter, N2_coil_zgap = calculate_coil_parameter(N2, N2_layer, h1, N2_height_ratio, N2_fill_factor)

    N1_space_w = design.get_random_value(lower=1, upper=30, resolution=0.1)
    N1_space_l = design.get_random_value(lower=1, upper=30, resolution=0.1)
    N2_space_w = design.get_random_value(lower=1, upper=30, resolution=0.1)
    N2_space_l = design.get_random_value(lower=1, upper=30, resolution=0.1)
    
    N1_layer_gap = design.get_random_value(lower=1, upper=10, resolution=0.1)
    N2_layer_gap = design.get_random_value(lower=1, upper=10, resolution=0.1)

    N1_offset_ratio = design.get_random_value(lower=-0.95, upper=0.95, resolution=0.01)
    N2_offset_ratio = design.get_random_value(lower=-0.95, upper=0.95, resolution=0.01)

    N1_offset = calculate_coil_offset(N1, N1_layer, h1, N1_height_ratio, N1_offset_ratio)
    N2_offset = calculate_coil_offset(N2, N2_layer, h1, N2_height_ratio, N2_offset_ratio)

    mold_thick = design.get_random_value(lower=10, upper=40, resolution=0.1)

    l2_gap = design.get_random_value(lower=5, upper=50, resolution=0.1)
    l2_lower = N1_layer*N1_coil_diameter + N2_layer*N2_coil_diameter + (N1_layer-1)*N1_layer_gap + (N2_layer-1)*N2_layer_gap + N1_space_l + N2_space_l + mold_thick
    l2 = l2_lower + l2_gap

    h1_gap = (h1 - h1*N1_height_ratio)/2 - abs(N1_offset)
    h2_gap = (h1 - h1*N2_height_ratio)/2 - abs(N2_offset)

    cold_plate_x = design.get_random_value(lower=0, upper=30, resolution=0.1)
    cold_plate_y = design.get_random_value(lower=0, upper=30, resolution=0.1)
    cold_plate_z1 = design.get_random_value(lower=10, upper=50, resolution=0.1)
    cold_plate_z2 = design.get_random_value(lower=0.1, upper=0.5, resolution=0.01)

    thermal_conductivity = design.get_random_value(lower=0.2, upper=2, resolution=0.01)
    

    input_parameter = {
        "N1": N1,
        "N2": N2,
        "N1_layer": N1_layer,
        "N2_layer": N2_layer,

        "per": per,

        "w1": w1,
        "l1": l1,
        "l2": l2,
        "l2_gap": l2_gap,
        "h1": h1,
        "h1_gap": h1_gap,
        "h2_gap": h2_gap,

        "N1_height_ratio": N1_height_ratio,
        "N1_fill_factor": N1_fill_factor,
        "N1_coil_diameter": N1_coil_diameter,
        "N1_coil_zgap": N1_coil_zgap,
        "N2_height_ratio": N2_height_ratio,
        "N2_fill_factor": N2_fill_factor,
        "N2_coil_diameter": N2_coil_diameter,
        "N2_coil_zgap": N2_coil_zgap,

        "N1_space_w": N1_space_w,
        "N1_space_l": N1_space_l,
        "N2_space_w": N2_space_w,
        "N2_space_l": N2_space_l,
        "N1_layer_gap": N1_layer_gap,
        "N2_layer_gap": N2_layer_gap,

        "N1_offset_ratio": N1_offset_ratio,
        "N2_offset_ratio": N2_offset_ratio,
        "N1_offset": N1_offset,
        "N2_offset": N2_offset,

        "cold_plate_x": cold_plate_x,
        "cold_plate_y": cold_plate_y,
        "cold_plate_z1": cold_plate_z1,
        "cold_plate_z2": cold_plate_z2,

        "mold_thick": mold_thick,
        "thermal_conductivity": thermal_conductivity
    }


    return input_parameter 





def set_design_variables(design, input_parameter):
    """
    주어진 파라미터 딕셔너리를 사용하여 Ansys 디자인 변수를 설정합니다.
    """
    units = {
        "w1": "mm", "l1": "mm", "l1_leg": "mm", "l1_top": "mm", "l2": "mm", "h1": "mm", "h1_gap": "mm", "h2_gap": "mm",
        "cold_plate_x": "mm", "cold_plate_y": "mm", "cold_plate_z1": "mm",
        "N1_coil_diameter": "mm", "N1_coil_zgap": "mm",
        "N2_coil_diameter": "mm", "N2_coil_zgap": "mm",
        "N1_space_x": "mm", "N1_space_y": "mm",
        "N2_space_x": "mm", "N2_space_y": "mm",
        "N1_space_w": "mm", "N1_space_l": "mm",
        "N2_space_w": "mm", "N2_space_l": "mm",
        "N1_layer_gap": "mm", "N2_layer_gap": "mm",
        "N1_offset": "mm", "N2_offset": "mm",
        "N1_height_ratio": "mm",
        "N2_height_ratio": "mm",
        "N1_fill_factor": "mm",
        "mold_thick": "mm"
    }

    for key, value in input_parameter.items():
        # Ansys 디자인에 변수를 설정합니다.
        unit = units.get(key, "")
        design.set_variable(variable_name=key, value=value, unit=unit)

    print("Ansys 디자인 변수가 설정되었습니다.")