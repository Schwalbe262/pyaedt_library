from pyaedt_module.model3d.core import Core
from pyaedt_module.model3d.transformer_winding import Transformer_winding
from pyaedt_module.model3d.PCB_winding import PCB_winding
import math

import numpy as np






def create_one_turn(design, itr, N) :

    modeler = PCB_winding(design)

    winding = None
    connector = None

    points = []

    x_pos1, y_pos1, x_pos_angle1, y_pos_angle1, width1 = calculate_xy_pos(design, itr)
    x_pos2, y_pos2, x_pos_angle2, y_pos_angle2, width2 = calculate_xy_pos(design, itr+1)

    if itr == 0 :
        
        # points.append([x_pos1, -y_pos1, 0])
        points.append([x_pos1, 0, 0])
        points.append([x_pos1, y_pos_angle1, 0])
        points.append([x_pos_angle1, y_pos1, 0])
        points.append([-x_pos_angle1, y_pos1, 0])
        points.append([-x_pos1, y_pos_angle1, 0])
        points.append([-x_pos1, -y_pos_angle1, 0])
        points.append([-x_pos_angle1, -y_pos1, 0])
        points.append([-x_pos_angle1/2, -y_pos1, 0])

        winding_params = {
            "type": "Rectangle",
            "width": f"{width1}mm",
            "height": "thickness",
            "color": [255, 50, 50],
            "transparency": 0,
            "offset": ["0mm", "0mm", "0mm"],
        }

        winding = modeler.create_polyline(name="winding", points=points, **winding_params)

    elif itr != N-1 :

        x_pos_n, y_pos_n, x_pos_angle_n, y_pos_angle_n, width_n = calculate_xy_pos(design, itr-1) # itr-1번째 턴의 좌표

        points.append([x_pos_angle_n/2, -y_pos_n, 0])
        points.append([x_pos_angle_n, -y_pos_n, 0])
        points.append([x_pos1, -y_pos_angle1, 0])
        points.append([x_pos1, y_pos_angle1, 0])
        points.append([x_pos_angle1, y_pos1, 0])
        points.append([-x_pos_angle1, y_pos1, 0])
        points.append([-x_pos1, y_pos_angle1, 0])
        points.append([-x_pos1, -y_pos_angle1, 0])
        points.append([-x_pos_angle1, -y_pos1, 0])
        points.append([-x_pos_angle1/2, -y_pos1, 0])

        winding_params = {
            "type": "Rectangle",
            "width": f"{width1}mm",
            "height": "thickness",
            "color": [255, 50, 50],
            "transparency": 0,
            "offset": ["0mm", "0mm", "0mm"],
        }

        winding = modeler.create_polyline(name="winding", points=points, **winding_params)

    else :

        x_pos_n, y_pos_n, x_pos_angle_n, y_pos_angle_n, width_n = calculate_xy_pos(design, itr-1) # itr-1번째 턴의 좌표

        points.append([x_pos_angle_n/2, -y_pos_n, 0])
        points.append([x_pos_angle_n, -y_pos_n, 0])
        points.append([x_pos1, -y_pos_angle1, 0])
        points.append([x_pos1, y_pos_angle1, 0])
        points.append([x_pos_angle1, y_pos1, 0])
        points.append([-x_pos_angle1, y_pos1, 0])
        points.append([-x_pos1, y_pos_angle1, 0])
        points.append([-x_pos1, -y_pos_angle1, 0])
        points.append([-x_pos_angle1, -y_pos1, 0])
        points.append([-x_pos_angle1/2, -y_pos1, 0])

        winding_params = {
            "type": "Rectangle",
            "width": f"{width1}mm",
            "height": "thickness",
            "color": [255, 50, 50],
            "transparency": 0,
            "offset": ["0mm", "0mm", "0mm"],
        }

        winding = modeler.create_polyline(name="winding", points=points, **winding_params)





    points = []

    if itr != N-1 :

        points.append([0, -y_pos1, "-thickness/2"])
        points.append([0, -y_pos1, "thickness/2"])

        winding_params = {
            "type": "Isosceles Trapezoid",
            "orientation": "X",
            "top_width": f"{width2}mm", # right
            "width": f"{width1}mm", # left
            "height": f"{x_pos_angle1}mm",
            "color": [255, 50, 50],
            "transparency": 0,
            "offset": ["0mm", "0mm", "0mm"],
        }

        connector = modeler.create_polyline(name="winding", points=points, **winding_params)




    return winding, connector


    


def calculate_xy_pos(design, itr) :

    x_pos = 0
    y_pos = 0

    x_init = design.x_init
    y_init = design.y_init
    width_init = design.width_init
    x_space_init = design.x_space_init
    y_space_init = design.y_space_init
    width_exp_rate = design.width_exp_rate
    x_space_exp_rate = design.x_space_exp_rate
    y_space_exp_rate = design.y_space_exp_rate
    x_focus_ratio = design.x_focus_ratio
    y_focus_ratio = design.y_focus_ratio
    x_angle_ratio = design.x_angle_ratio
    y_angle_ratio = design.y_angle_ratio

    for i in range(itr+1) :

        if i == 0 :
            x_pos = x_pos + x_init + width_init/2
            y_pos = y_pos + y_init + width_init/2
        else : 
            x_pos = x_pos + (width_init*math.exp(-(i-1)*width_exp_rate))/2 + (x_space_init*math.exp(-(i-1)*x_space_exp_rate)) + (width_init*math.exp(-i*width_exp_rate))/2
            y_pos = y_pos + (width_init*math.exp(-(i-1)*width_exp_rate))/2 + (y_space_init*math.exp(-(i-1)*y_space_exp_rate)) + (width_init*math.exp(-i*width_exp_rate))/2

    slope_FA = (y_init * (1 - y_focus_ratio)) / (x_init * (1 - x_focus_ratio) * x_angle_ratio)
    x_pos_angle = x_init * x_focus_ratio + (y_pos - y_init * y_focus_ratio) / slope_FA

    slope_FB = (y_init * (1 - y_focus_ratio) * y_angle_ratio) / (x_init * (1 - x_focus_ratio))
    y_pos_angle = y_init * y_focus_ratio + slope_FB * (x_pos - x_init * x_focus_ratio)

    width = width_init * math.exp(-itr*width_exp_rate)

    print(f"x_pos: {x_pos}, y_pos: {y_pos}, x_pos_angle: {x_pos_angle}, y_pos_angle: {y_pos_angle}, width: {width}")

    return x_pos, y_pos, x_pos_angle, y_pos_angle, width





def create_all_windings(design):
    """
    Creates both primary and secondary windings based on simulation parameters.
    """
    modeler = Transformer_winding(design)

    # --- Winding 1 ---
    offset1 = offset_calculation(
        design.N1_coil_diameter,
        design.h1,
        design.N1_height_ratio
    )
    winding_params1 = {
        "N": design.N1,
        "N_layer": design.N1_layer,
        "x": "w1 + 2*N1_space_w",
        "y": "l1_center + 2*N1_space_l",
        "coil_diameter": "N1_coil_diameter",
        "coil_zgap": "N1_coil_zgap",
        "coil_layer_x_gap": "N1_layer_gap",
        "coil_layer_y_gap": "N1_layer_gap",
        "color": [255, 50, 50],
        "transparency": 0,
        "offset": ["0mm", "0mm", f"{offset1}mm + ({design.N1_offset}mm)"],
        # "terminal_position": "w1/2 + 150mm",
        "Num": 6
    }
    points1 = modeler.winding_points(**winding_params1)
    first_point = points1[0].copy()
    first_point[2] = "h1/2 + N1_coil_diameter/2"
    last_point = points1[-1].copy() 
    last_point[2] = "-h1/2 - N1_coil_diameter/2"
    points1 = [first_point] + points1 + [last_point]
    first_point = points1[0].copy()
    first_point[0] = "w1/2 + 200mm"
    last_point = points1[-1].copy() 
    last_point[0] = "w1/2 + 200mm"
    points1 = [first_point] + points1 + [last_point]
    
    winding1 = modeler.create_polyline(name="winding1", points=points1, **winding_params1)
    winding1.material_name = "copper"
    print("Winding 'winding1' created successfully.")

    # --- Winding 2 ---
    offset2 = offset_calculation(
        design.N2_coil_diameter,
        design.h1/2,
        design.N2_height_ratio
    )
    winding_params2 = {
        "N": design.N2,
        "N_layer": design.N2_layer,
        "x": "w1 + 2*N2_space_w + " +
             "2*N1_space_w + 2*N1_layer * (N1_coil_diameter) + 2*(N1_layer - 1) * N1_layer_gap + 2*mold_thick",
        "y": "l1_center + 2*N2_space_l + " +
             "2*N1_space_l + 2*N1_layer * (N1_coil_diameter) + 2*(N1_layer - 1) * N1_layer_gap + 2*mold_thick",
        "coil_diameter": "N2_coil_diameter",
        "coil_zgap": "N2_coil_zgap",
        "coil_layer_x_gap": "N2_layer_gap",
        "coil_layer_y_gap": "N2_layer_gap",
        "color": [50, 50, 255],
        "transparency": 0,
        "offset": ["0mm", "0mm", f"h1/4 + {offset2}mm + ({design.N2_offset}mm)"],
        "terminal_position": "w1/2 + 200mm",
        "Num": 6
    }
    points2 = modeler.winding_points(**winding_params2)
    winding2 = modeler.create_polyline(name="winding2", points=points2, **winding_params2)
    winding2.material_name = "copper"
    print("Winding 'winding2' created successfully.")   

    # --- Winding 3 ---
    offset2 = offset_calculation(
        design.N2_coil_diameter,
        design.h1/2,
        design.N2_height_ratio
    )
    winding_params3 = {
        "N": design.N2,
        "N_layer": design.N2_layer,
        "x": "w1 + 2*N2_space_w + " +
             "2*N1_space_w + 2*N1_layer * (N1_coil_diameter) + 2*(N1_layer - 1) * N1_layer_gap + 2*mold_thick",
        "y": "l1_center + 2*N2_space_l + " +
             "2*N1_space_l + 2*N1_layer * (N1_coil_diameter) + 2*(N1_layer - 1) * N1_layer_gap + 2*mold_thick",
        "coil_diameter": "N2_coil_diameter",
        "coil_zgap": "N2_coil_zgap",
        "coil_layer_x_gap": "N2_layer_gap",
        "coil_layer_y_gap": "N2_layer_gap",
        "color": [50, 50, 255],
        "transparency": 0,
        "offset": ["0mm", "0mm", f"-h1/4 + {offset2}mm + ({design.N2_offset}mm)"],
        "terminal_position": "w1/2 + 200mm",
        "Num": 6
    }
    points3 = modeler.winding_points(**winding_params3)
    winding3 = modeler.create_polyline(name="winding3", points=points3, **winding_params3)
    winding3.material_name = "copper"
    print("Winding 'winding3' created successfully.")   


    return winding1, winding2, winding3




def create_air(design) :
    """Creates the air region and assigns a radiation boundary."""
    # create air
    air_region = design.modeler.create_air_region(x_pos=0.0, y_pos=100.0, z_pos=100.0, x_neg=50.0, y_neg=100.0, z_neg=100.0, is_percentage=True)

    # assign radiation boundary
    design.assign_radiation(assignment=[air_region.name], radiation="Radiation")
    print("Air region and radiation boundary created successfully.")

    return air_region

def assign_meshing(design):
    """Assigns mesh operations to the core and windings."""
    freq = design.frequency

    mu0 = 4 * math.pi * 1e-7
    mu_copper = mu0 
    sigma_copper = 58000000
    omega = 2 * math.pi * freq
    skin_depth = math.sqrt(2 / (omega * mu_copper * sigma_copper)) * 1e3 # in mm

    length_mesh = design.mesh.assign_length_mesh(
        assignment=[design.core.name],
        inside_selection=False,
        maximum_length="100mm",
        name="core_mesh"
    )

    skin_depth_mesh = design.mesh.assign_skin_depth(
        assignment=[design.winding1.name, design.winding2.name, design.winding3.name],
        skin_depth=f'{skin_depth}mm',
        triangulation_max_length='50mm',
        layers_number="2",
        name="winding_skin_depth"
    )
    print("Mesh operations assigned successfully.")

    return length_mesh, skin_depth_mesh

def _find_terminal_faces(winding_obj):
    """
    Finds the two terminal faces of a winding object based on their position.
    It assumes the terminal faces are those with the maximum x-coordinate.
    Returns the upper face and the lower face.
    """
    if not winding_obj.faces:
        raise ValueError(f"Winding object {winding_obj.name} has no faces.")

    # Find the maximum absolute x-position among all face centers
    max_x_pos = 0
    for face in winding_obj.faces:
        if abs(face.center[0]) > max_x_pos:
            max_x_pos = abs(face.center[0])
    
    # Collect faces that are at the maximum x-position
    terminal_faces = []
    for face in winding_obj.faces:
        if abs(abs(face.center[0]) - max_x_pos) < 1e-4: # Using a small tolerance
            terminal_faces.append(face)

    if len(terminal_faces) != 2:
        centers = [f.center for f in terminal_faces]
        raise Exception(
            f"Expected 2 terminal faces for {winding_obj.name}, but found {len(terminal_faces)}. "
            f"Face centers: {centers}"
        )

    # Sort faces by Z-coordinate to find upper and lower faces
    sorted_faces = sorted(terminal_faces, key=lambda f: f.center[2], reverse=True)
    upper_face = sorted_faces[0]
    lower_face = sorted_faces[1]
    
    return upper_face, lower_face

def assign_excitations(design, winding1, winding2, winding3):
    """Assigns coils, windings, and matrix from terminal faces."""
    tx_face_start, tx_face_end = _find_terminal_faces(winding1)
    rx_face_start1, rx_face_end1 = _find_terminal_faces(winding2)
    rx_face_start2, rx_face_end2 = _find_terminal_faces(winding3)

    # Assign coil terminals
    tx_term_in = design.assign_coil(tx_face_start.id, conductors_number=1, polarity="Positive", name="Tx_in")
    tx_term_out = design.assign_coil(tx_face_end.id, conductors_number=1, polarity="Negative", name="Tx_out")
    rx_term_in1 = design.assign_coil(rx_face_start1.id, conductors_number=1, polarity="Positive", name="Rx1_in")
    rx_term_out1 = design.assign_coil(rx_face_end1.id, conductors_number=1, polarity="Negative", name="Rx1_out")
    rx_term_in2 = design.assign_coil(rx_face_start2.id, conductors_number=1, polarity="Positive", name="Rx2_in")
    rx_term_out2 = design.assign_coil(rx_face_end2.id, conductors_number=1, polarity="Negative", name="Rx2_out")
    
    # Assign windings
    tx_winding = design.assign_winding(
        assignment=[], 
        winding_type="Current", 
        is_solid=True, 
        current=f"{600*math.sqrt(2)}A",
        name="Tx_Winding"
    )
    rx_winding1 = design.assign_winding(
        assignment=[], 
        winding_type="Current", 
        is_solid=True, 
        current=f"{300*math.sqrt(2)}A",
        name="Rx1_Winding"
    )

    rx_winding2 = design.assign_winding(
        assignment=[], 
        winding_type="Current", 
        is_solid=True, 
        current=f"{300*math.sqrt(2)}A",
        name="Rx2_Winding"
    )
    
    # Add coils to windings
    design.add_winding_coils(tx_winding.name, [tx_term_in.name, tx_term_out.name])
    design.add_winding_coils(rx_winding1.name, [rx_term_in1.name, rx_term_out1.name])
    design.add_winding_coils(rx_winding2.name, [rx_term_in2.name, rx_term_out2.name])

    # Assign matrix
    design.assign_matrix(matrix_name="Matrix", assignment=["Tx_Winding", "Rx1_Winding", "Rx2_Winding"])
    print("Excitations assigned successfully.")

    return tx_winding, rx_winding1, rx_winding2