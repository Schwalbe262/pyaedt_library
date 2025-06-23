 from pyaedt_module.model3d.core import Core
from pyaedt_module.model3d.transformer_winding import Transformer_winding
import math


def create_core_model(design):
    """Creates the 3D model of the core."""
    modeler = Core(design)
    
    core_params = {
        "w1": f"{design.w1}mm",
        "l1_leg": f"{design.l1}mm",
        "l1_top": f"{design.l1}mm",
        "l2": f"{design.l2}mm",
        "h1": f"{design.h1}mm",
        "mat": "power_ferrite",
        "coreloss": True
    }

    core = modeler.create_coretype_core(name="Core", **core_params)
    print("Core created successfully.")
    return core


def create_face(design):
    leg_left = design.modeler.create_rectangle(
        orientation = "XY",
        origin = ['-w1/2','-l2/2', '0'],
        sizes = ['w1','-l1']
    )
    leg_left.model = False
    leg_left.name = "leg_left"

    leg_right = design.modeler.create_rectangle(
        orientation = "XY",
        origin = ['-w1/2','l2/2', '0'],
        sizes = ['w1','l1']
    )
    leg_right.model = False
    leg_right.name = "leg_right"

    leg_top = design.modeler.create_rectangle(
        orientation = "XZ",
        origin = ['-w1/2', '0','h1/2'],
        sizes = ['l1', 'w1']
    )
    leg_top.model = False
    leg_top.name = "leg_top"

    leg_bottom = design.modeler.create_rectangle(
        orientation = "XZ",
        origin = ['-w1/2', '0','-h1/2'],
        sizes = ['-l1', 'w1']
    )
    leg_bottom.model = False
    leg_bottom.name = "leg_bottom"

    design.leg_left = leg_left
    design.leg_right = leg_right
    design.leg_top = leg_top
    design.leg_bottom = leg_bottom

    return leg_left, leg_right, leg_top, leg_bottom
    
    

def offset_calculation(coil_diameter, h1, height_ratio):
    """Calculates the z-offset for the winding."""
    plus = coil_diameter / 2
    minus = (h1 * height_ratio) - coil_diameter / 2
    offset = (plus + minus) / 2 - plus
    return offset

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
        "y": "l1 + 2*N1_space_l",
        "coil_diameter": "N1_coil_diameter",
        "coil_zgap": "N1_coil_zgap",
        "coil_layer_x_gap": "N1_layer_gap",
        "coil_layer_y_gap": "N1_layer_gap",
        "color": [255, 50, 50],
        "transparency": 0,
        "offset": ["0mm", "-(l1+l2)/2", f"{offset1}mm + {design.N1_offset}mm"],
        "terminal_position": "w1/2 + 150mm",
        "Num": 6
    }
    points1 = modeler.winding_points(**winding_params1)
    winding1 = modeler.create_polyline(name="winding1", points=points1, **winding_params1)
    winding1.material_name = "copper"
    print("Winding 'winding1' created successfully.")

    # --- Winding 2 ---
    offset2 = offset_calculation(
        design.N2_coil_diameter,
        design.h1,
        design.N2_height_ratio
    )
    winding_params2 = {
        "N": design.N2,
        "N_layer": design.N2_layer,
        "x": "w1 + 2*N2_space_w",
        "y": "l1 + 2*N2_space_l",
        "coil_diameter": "N2_coil_diameter",
        "coil_zgap": "N2_coil_zgap",
        "coil_layer_x_gap": "N2_layer_gap",
        "coil_layer_y_gap": "N2_layer_gap",
        "color": [50, 50, 255],
        "transparency": 0,
        "offset": ["0mm", "(l1+l2)/2", f"{offset2}mm + {design.N2_offset}mm"],
        "terminal_position": "w1/2 + 150mm",
        "Num": 6
    }
    points2 = modeler.winding_points(**winding_params2)
    winding2 = modeler.create_polyline(name="winding2", points=points2, **winding_params2)
    winding2.material_name = "copper"
    print("Winding 'winding2' created successfully.")   

    return winding1, winding2


def create_mold(design, name="mold", **kwargs):
    """
    Creates a mold that encapsulates the core and both windings by creating
    two separate mold halves and uniting them.
    """
    thermal_epoxy = design.materials.duplicate_material("Epoxy Resin-Typical","Epoxy Resin Thermal")
    thermal_epoxy.thermal_conductivity = design.thermal_conductivity
    material = kwargs.get("mat", "Epoxy Resin Thermal")
    mold_thick = "mold_thick"  # This should be a variable in the design

    # --- Create Mold for Winding 1 ---
    # Calculate the total thickness of the winding from the core outwards
    winding1_thickness_x = f"N1_space_w + ({design.N1_layer}-1)*N1_layer_gap + {design.N1_layer}*N1_coil_diameter"
    winding1_thickness_y = f"N1_space_l + ({design.N1_layer}-1)*N1_layer_gap + {design.N1_layer}*N1_coil_diameter"

    # Define origin and dimensions for the first mold half
    origin1 = [
        f"-(w1/2 + {winding1_thickness_x} + {mold_thick})",
        f"-(l1/2 + {winding1_thickness_y} + {mold_thick})",
        f"-(h1/2)"
    ]
    dimension1 = [
        f"2 * (w1/2 + {winding1_thickness_x} + {mold_thick})",
        f"2 * (l1/2 + {winding1_thickness_y} + {mold_thick})",
        f"h1"
    ]
    
    mold1 = design.modeler.create_box(
        origin=origin1,
        sizes=dimension1,
        name="mold1",
        material=material
    )
    mold1.move(['0mm', '-(l1+l2)/2', '0mm'])

    return mold1


def create_cold_plate(design):
    """
    Creates top and bottom cold plates with subtractions for the core,
    based on the logic from the reference script but adapted for
    parametric string-based expressions.
    """
    modeler = design.modeler

    # --- Cold Plate Top ---
    origin_z_top = "(l1 + h1/2 - l1*cold_plate_z2)"
    dims_z_top = "(cold_plate_z1 + l1*cold_plate_z2)"

    origin_top = [f"-(w1/2) - cold_plate_x", f"-(2*l1 + l2)/2 - cold_plate_y", origin_z_top]
    dims_top = [f"w1 + 2*cold_plate_x", f"(2*l1 + l2) + 2*cold_plate_y", dims_z_top]

    cold_plate_top = modeler.create_box(origin_top, dims_top, name="cold_plate_top", material="Aluminum")

    origin_sub_top = ["-w1/2", "-(2*l1 + l2)/2", origin_z_top]
    dims_sub_top = ["w1", "(2*l1 + l2)", "l1*cold_plate_z2"]

    cold_plate_top_sub = modeler.create_box(origin_sub_top, dims_sub_top, name="cold_plate_top_sub", material="Aluminum")

    modeler.subtract([cold_plate_top.name], [cold_plate_top_sub.name], keep_originals=False)
    cold_plate_top.transparency = 0.5
    print("Top cold plate created successfully.")

    # --- Cold Plate Bottom (Corrected Logic) ---
    origin_z_bot = "-(l1 + h1/2 + cold_plate_z1)"
    dims_z_bot = "(cold_plate_z1 + l1*cold_plate_z2)" # Height is positive

    origin_bot = [f"-(w1/2) - cold_plate_x", f"-(2*l1 + l2)/2 - cold_plate_y", origin_z_bot]
    dims_bot = [f"w1 + 2*cold_plate_x", f"(2*l1 + l2) + 2*cold_plate_y", dims_z_bot]
    
    cold_plate_bottom = modeler.create_box(origin_bot, dims_bot, name="cold_plate_bottom", material="Aluminum")
    
    origin_z_sub_bot = "-(l1 + h1/2)"
    dims_z_sub_bot = "l1*cold_plate_z2"

    origin_sub_bot = ["-w1/2", "-(2*l1 + l2)/2", origin_z_sub_bot]
    dims_sub_bot = ["w1", "(2*l1 + l2)", dims_z_sub_bot]

    cold_plate_bottom_sub = modeler.create_box(origin_sub_bot, dims_sub_bot, name="cold_plate_bottom_sub", material="Aluminum")
    
    modeler.subtract([cold_plate_bottom.name], [cold_plate_bottom_sub.name], keep_originals=False)
    cold_plate_bottom.transparency = 0.5
    print("Bottom cold plate created successfully.")

    return cold_plate_top, cold_plate_bottom

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
    freq = design.freq

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
        assignment=[design.winding1.name, design.winding2.name],
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

def assign_excitations(design, winding1, winding2):
    """Assigns coils, windings, and matrix from terminal faces."""
    tx_face_start, tx_face_end = _find_terminal_faces(winding1)
    rx_face_start, rx_face_end = _find_terminal_faces(winding2)

    # Assign coil terminals
    tx_term_in = design.assign_coil(tx_face_start.id, conductors_number=1, polarity="Positive", name="Tx_in")
    tx_term_out = design.assign_coil(tx_face_end.id, conductors_number=1, polarity="Negative", name="Tx_out")
    rx_term_in = design.assign_coil(rx_face_start.id, conductors_number=1, polarity="Positive", name="Rx_in")
    rx_term_out = design.assign_coil(rx_face_end.id, conductors_number=1, polarity="Negative", name="Rx_out")
    
    # Assign windings
    tx_winding = design.assign_winding(
        assignment=[], 
        winding_type="Current", 
        is_solid=True, 
        current=f"{130*math.sqrt(2)}A",
        name="Tx_Winding"
    )
    rx_winding = design.assign_winding(
        assignment=[], 
        winding_type="Current", 
        is_solid=True, 
        current=f"{130*math.sqrt(2)}A",
        name="Rx_Winding"
    )
    
    # Add coils to windings
    design.add_winding_coils(tx_winding.name, [tx_term_in.name, tx_term_out.name])
    design.add_winding_coils(rx_winding.name, [rx_term_in.name, rx_term_out.name])

    # Assign matrix
    design.assign_matrix(matrix_name="Matrix", assignment=["Tx_Winding", "Rx_Winding"])
    print("Excitations assigned successfully.")

    return tx_winding, rx_winding