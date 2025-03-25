import math
import re
from collections import namedtuple

class Winding:

    def __init__(self, design) :

        self.design = design
        a = 1
        
    
    def __getattr__(self, name):

        return getattr(self.design, name)
    

    def _convert_unit(self, value, target_unit="mm"):

        unit_map = {
            "mm": 1,
            "cm": 10,
            "m": 1000,
            "um": 0.001
        }

        match = re.match(r"([-+]?\d*\.?\d+)([a-zA-Z]*)", str(value))
        
        if not match:
            raise ValueError(f"Invalid value format: {value}")

        num, unit = match.groups()
        num = float(num)

        if unit == "":
            unit = "mm"

        if unit not in unit_map or target_unit not in unit_map:
            raise ValueError(f"Unsupported unit: {unit} or {target_unit}")
        
        value_in_mm = num * unit_map[unit]
        converted_value = value_in_mm / unit_map[target_unit]

        return converted_value
    

    def create_polyline(self, name="winding", points=None, width=None, height=None, **kwargs):

        polyline_obj = self.design.modeler.create_polyline(points=points, name=name, xsection_type="Rectangle", xsection_width=f"{width}", xsection_height=f"{height}")
        polyline_obj.point_list = points
        
        return polyline_obj
    

    def create_via(self, name="via", center=[0,0,0], outer_R=None, inner_R=None, height=None, via_pad_R=None, via_pad_thick=None) :

        outer_cylinder = self.design.modeler.create_cylinder(orientation="Z", 
                                                             origin=[center[0], center[1], f"({center[2]})-({height}/2)"], 
                                                             radius=outer_R, height=height, name=name, material="copper", num_sides=12)

        if inner_R != None :
            inner_cylinder = self.design.modeler.create_cylinder(orientation="Z", 
                                                                 origin=[center[0], center[1], f"({center[2]})-({height}/2)"], 
                                                                 radius=inner_R, height=height, name=f"{name}_inner", material="copper", num_sides=12)
            self.design.modeler.subtract(blank_list = outer_cylinder, tool_list = inner_cylinder, keep_originals = False)

        if via_pad_R != None :

            upper_pad = self.design.modeler.create_cylinder(orientation="Z", 
                                                                 origin=[center[0], center[1], f"({center[2]})-({height}/2)"], 
                                                                 radius=via_pad_R, height=via_pad_thick, name=f"{name}_pad_u", material="copper", num_sides=12)
            lower_pad = self.design.modeler.create_cylinder(orientation="Z", 
                                                                 origin=[center[0], center[1], f"({center[2]})+({height}/2)-({via_pad_thick})"], 
                                                                 radius=via_pad_R, height=via_pad_thick, name=f"{name}_pad_l", material="copper", num_sides=12)
            
            outer_cylinder = self.design.model3d.unite(assignment=[outer_cylinder, upper_pad, lower_pad])

        
        return outer_cylinder



    def coil_points(self, turns=5, **kwargs):

        outer_x = kwargs.get("outer_x", "50mm")
        outer_y = kwargs.get("outer_y", "30mm")

        fillet = kwargs.get("fillet", "10mm")
        inner = kwargs.get("inner", "20mm")

        N = int(turns)

        fill_factor = kwargs.get("fill_factor", 0.8)

        outer_xx = f"({outer_x}-{fillet})"
        outer_yy = f"({outer_y}-{fillet})"


        width = f"({inner} * {fill_factor} / ({N}-1))"
        gap = f"(1-{fill_factor})/{fill_factor} * ({width})"
        wg = f"({width}) + ({gap})"

        theta1 = kwargs.get("theta1", "15*pi/180")
        theta2 = kwargs.get("theta2", "75*pi/180")

        points = []

        # inner의 값은 fillet*(1 / (1-tan(pi/8))) 보다 작아야 함



        for i in range(N) :

            points.append([f"({outer_xx}) - ({i})*({wg})*(1/tan({theta2})) - ({wg})", f"-({outer_y}) + ({i-1})*({wg})", 0])
            points.append([f"({outer_x}) - ({i})*({wg})", f"-({outer_yy}) + ({i})*({wg})*(tan({theta1}))", 0])
            points.append([f"({outer_x}) - ({i})*({wg})", f"({outer_yy}) - ({i})*({wg})*(tan({theta1}))", 0])
            points.append([f"({outer_xx}) - ({i})*({wg})*(1/tan({theta2}))", f"({outer_y}) - ({i})*({wg})", 0])

            points.append([f"-({outer_xx}) + ({i})*({wg})*(1/tan({theta2}))", f"({outer_y}) - ({i})*({wg})", 0])
            points.append([f"-({outer_x}) + ({i})*({wg})", f"({outer_yy}) - ({i})*({wg})*(tan({theta1}))", 0])
            points.append([f"-({outer_x}) + ({i})*({wg})", f"-({outer_yy}) + ({i})*({wg})*(tan({theta1}))", 0])
            points.append([f"-({outer_xx}) + ({i})*({wg})*(1/tan({theta2}))", f"-({outer_y}) + ({i})*({wg})", 0])


            if i == (N-1) :

                points.append([f"0", f"-({outer_y}) + ({i})*({wg})", 0])


        WindingResult = namedtuple("WindingResult", ["points", 
                                                     "outer_x", "outer_xx", "outer_y", "outer_yy", "fillet", "inner",
                                                     "width", "gap", "wg", "theta1", "theta2"])

        # fillet_coil 함수 마지막에:
        return WindingResult(points=points, 
                             outer_x=outer_x, outer_xx=outer_xx, outer_y=outer_y, outer_yy=outer_yy, fillet=fillet, inner=inner,
                             width=width, gap=gap, wg=wg, theta1=theta1, theta2=theta2)
        




    

    def create_winding(self, name="winding", **kwargs):

        outer_x = kwargs.get("outer_x", "50mm")
        outer_y = kwargs.get("outer_y", "30mm")

        outer_xx = kwargs.get("outer_x", "40mm")
        outer_yy = kwargs.get("outer_y", "20mm")

        N = int(kwargs.get("turns", "5"))

        inner = kwargs.get("inner", "20mm")

        fill_factor = kwargs.get("fill_factor", 0.8)


        width = f"({inner} * {fill_factor} / ({N}-1))"
        gap = f"(1-{fill_factor})/{fill_factor} * ({width})"
        wg = f"({width}) + ({gap})"

        c = f"sqrt({outer_xx}^2 + {outer_yy}^2) / 4"

        theta1 = f"atan(({outer_yy})/(({outer_x})-({c})))"
        theta2 = f"atan(({outer_y})/(({outer_xx})-({c})))"


        # theta1 = f"pi/8"
        # theta1 = f"pi/8 * 3"


        points = []



        for i in range(N) :

            # points.append([f"({outer_xx}) - ({i})*({wg})*(1/tan({theta2})) + ({wg})", f"-({outer_y}) + ({i})*({wg})", 0])
            points.append([f"({outer_xx}) - ({i})*({wg})*(1/tan({theta2})) + ({wg})", f"-({outer_y}) + ({i-1})*({wg})", 0])
            points.append([f"({outer_x}) - ({i})*({wg}) + ({wg})", f"-({outer_yy}) + ({i})*({wg})*(tan({theta1}))", 0])
            points.append([f"({outer_x}) - ({i})*({wg}) + ({wg})", f"({outer_yy}) - ({i})*({wg})*(tan({theta1}))", 0])
            points.append([f"({outer_xx}) - ({i})*({wg})*(1/tan({theta2})) + ({wg})", f"({outer_y}) - ({i})*({wg})", 0])

            points.append([f"-({outer_xx}) + ({i})*({wg})*(1/tan({theta2}))", f"({outer_y}) - ({i})*({wg})", 0])
            points.append([f"-({outer_x}) + ({i})*({wg})", f"({outer_yy}) - ({i})*({wg})*(tan({theta1}))", 0])
            points.append([f"-({outer_x}) + ({i})*({wg})", f"-({outer_yy}) + ({i})*({wg})*(tan({theta1}))", 0])
            points.append([f"-({outer_xx}) + ({i})*({wg})*(1/tan({theta2}))", f"-({outer_y}) + ({i})*({wg})", 0])


            # points.append([f"({outer_x}) - ({(i-1)})*({wg})", f"-({outer_yy}) + ({i})*({wg})*(tan({theta1}))", 0])
            # points.append([f"({outer_x}) - ({(i-1)})*({wg})", f"({outer_yy}) - ({i})*({wg})*(1/tan({theta1})) - ({i})*({wg})", 0])
            # points.append([f"({outer_xx}) - ({i})*({wg})*(1/tan({theta2})) - ({(i-1)})*({wg})", f"({outer_y}) - ({i})*({wg})", 0])



        self.design.modeler.create_polyline(points=points)
        




        # points = []



        # for i in range(N) :

        #     # points.append([f"({outer_xx}) - ({i})*({wg})*(1/tan({theta2})) + ({wg})", f"-({outer_y}) + ({i})*({wg})", 0])
        #     points.append([f"({outer_xx}) - ({i})*({wg}) + ({wg})", f"-({outer_y}) + ({i-1})*({wg})", 0])
        #     points.append([f"({outer_x}) - ({i})*({wg}) + ({wg})", f"-({outer_yy}) + ({i})*({wg})", 0])
        #     points.append([f"({outer_x}) - ({i})*({wg}) + ({wg})", f"({outer_yy}) - ({i})*({wg})", 0])
        #     points.append([f"({outer_xx}) - ({i})*({wg}) + ({wg})", f"({outer_y}) - ({i})*({wg})", 0])

        #     points.append([f"-({outer_xx}) + ({i})*({wg})", f"({outer_y}) - ({i})*({wg})", 0])
        #     points.append([f"-({outer_x}) + ({i})*({wg})", f"({outer_yy}) - ({i})*({wg})", 0])
        #     points.append([f"-({outer_x}) + ({i})*({wg})", f"-({outer_yy}) + ({i})*({wg})", 0])
        #     points.append([f"-({outer_xx}) + ({i})*({wg})", f"-({outer_y}) + ({i})*({wg})", 0])


        #     # points.append([f"({outer_x}) - ({(i-1)})*({wg})", f"-({outer_yy}) + ({i})*({wg})*(tan({theta1}))", 0])
        #     # points.append([f"({outer_x}) - ({(i-1)})*({wg})", f"({outer_yy}) - ({i})*({wg})*(1/tan({theta1})) - ({i})*({wg})", 0])
        #     # points.append([f"({outer_xx}) - ({i})*({wg})*(1/tan({theta2})) - ({(i-1)})*({wg})", f"({outer_y}) - ({i})*({wg})", 0])



        # self.design.modeler.create_polyline(points=points)



        points = []



        for i in range(N) :

            # points.append([f"({outer_xx}) - ({i})*({wg})*(1/tan({theta2})) + ({wg})", f"-({outer_y}) + ({i})*({wg})", 0])
            points.append([f"({outer_xx}) - ({i})*({wg})*(1/tan({theta2})) + ({wg})", f"-({outer_y}) + ({i-1})*({wg})", 0])
            points.append([f"({outer_x}) - ({i})*({wg}) + ({wg})", f"-({outer_yy}) + ({i})*({wg})*(tan({theta1}))", 0])
            points.append([f"({outer_x}) - ({i})*({wg}) + ({wg})", f"({outer_yy}) - ({i})*({wg})*(tan({theta1}))", 0])
            points.append([f"({outer_xx}) - ({i})*({wg})*(1/tan({theta2})) + ({wg})", f"({outer_y}) - ({i})*({wg})", 0])

            points.append([f"-({outer_xx}) + ({i})*({wg})*(1/tan({theta2}))", f"({outer_y}) - ({i})*({wg})", 0])
            points.append([f"-({outer_x}) + ({i})*({wg})", f"({outer_yy}) - ({i})*({wg})*(tan({theta1}))", 0])
            points.append([f"-({outer_x}) + ({i})*({wg})", f"-({outer_yy}) + ({i})*({wg})*(tan({theta1}))", 0])
            points.append([f"-({outer_xx}) + ({i})*({wg})*(1/tan({theta2}))", f"-({outer_y}) + ({i})*({wg})", 0])


            # points.append([f"({outer_x}) - ({(i-1)})*({wg})", f"-({outer_yy}) + ({i})*({wg})*(tan({theta1}))", 0])
            # points.append([f"({outer_x}) - ({(i-1)})*({wg})", f"({outer_yy}) - ({i})*({wg})*(1/tan({theta1})) - ({i})*({wg})", 0])
            # points.append([f"({outer_xx}) - ({i})*({wg})*(1/tan({theta2})) - ({(i-1)})*({wg})", f"({outer_y}) - ({i})*({wg})", 0])



        self.design.modeler.create_polyline(points=points)
        

        # points = []



        # for i in range(N) :

        #     # points.append([f"({outer_xx}) - ({i})*({wg})*(1/tan({theta2})) - ({(i-1)})*({wg})", f"-({outer_y}) + ({i})*({wg})", 0])
        #     points.append([f"({outer_x}) - ({(i-1)})*({wg})", f"-({outer_yy}) + ({i})*({wg})", 0])
        #     # points.append([f"({outer_x}) - ({(i-1)})*({wg})", f"({outer_yy}) - ({i})*({wg})*(1/tan({theta1})) - ({i})*({wg})", 0])
        #     # points.append([f"({outer_xx}) - ({i})*({wg})*(1/tan({theta2})) - ({(i-1)})*({wg})", f"({outer_y}) - ({i})*({wg})", 0])



        # self.design.modeler.create_polyline(points=points)




        
    

    # def create_winding(self, name="Tx", **kwargs):
    #     """
    #     Creates a winding structure with configurable parameters.
    #     """
    #     # 기본 변수 설정
    #     center_length = kwargs.get("center_length", "50mm")
    #     center_width = kwargs.get("center_width", "40mm")
    #     min_lw = kwargs.get("min_lw", "5mm")
    #     layer_gap_Tx = kwargs.get("layer_gap_Tx", "2mm")
    #     N_Tx = kwargs.get("N_Tx", 3)
    #     coil_width = kwargs.get("coil_width", "Tx_width")
    #     coil_height = kwargs.get("coil_height", "Tx_height")
        
    #     # 초기 포인트 설정
    #     temp = [[f'{center_length}/2', f'{center_width}/(2+{math.sqrt(2)})', 0]]
        
    #     # Winding 생성
    #     for i in range(N_Tx):
    #         for j in range(8):
    #             if j == 0:
    #                 temp.append([f'{center_length}/2+{i}*{layer_gap_Tx}',
    #                             f'-{center_width}/(2+{math.sqrt(2)})-{i}*{layer_gap_Tx}*{math.tan(math.pi/8)}', 0])
    #             elif j == 1:
    #                 temp.append([f'{center_length}/2-{min_lw}/(2+{math.sqrt(2)})+{i}*{layer_gap_Tx}*{math.tan(math.pi/8)}',
    #                             f'-{center_width}/2-{i}*{layer_gap_Tx}', 0])
    #             elif j == 2:
    #                 temp.append([f'-{center_length}/2+{min_lw}/(2+{math.sqrt(2)})-{i}*{layer_gap_Tx}*{math.tan(math.pi/8)}',
    #                             f'-{center_width}/2-{i}*{layer_gap_Tx}', 0])
    #             elif j == 3:
    #                 temp.append([f'-{center_length}/2-{i}*{layer_gap_Tx}',
    #                             f'-{center_width}/(2+{math.sqrt(2)})-{i}*{layer_gap_Tx}*{math.tan(math.pi/8)}', 0])
    #             elif j == 4:
    #                 temp.append([f'-{center_length}/2-{i}*{layer_gap_Tx}',
    #                             f'{center_width}/(2+{math.sqrt(2)})+{i}*{layer_gap_Tx}*{math.tan(math.pi/8)}', 0])
    #             elif j == 5:
    #                 temp.append([f'-{center_length}/2+{min_lw}/(2+{math.sqrt(2)})-{i}*{layer_gap_Tx}*{math.tan(math.pi/8)}',
    #                             f'{center_width}/2+{i}*{layer_gap_Tx}', 0])
    #             elif j == 6:
    #                 temp.append([f'{center_length}/2-{min_lw}/(2+{math.sqrt(2)})+{i}*{layer_gap_Tx}*{math.tan(math.pi/8)}+{layer_gap_Tx}*{math.sqrt(2)}',
    #                             f'{center_width}/2+{i}*{layer_gap_Tx}', 0])
    #             elif j == 7:
    #                 temp.append([f'{center_length}/2+{(i+1)}*{layer_gap_Tx}',
    #                             f'{center_width}/(2+{math.sqrt(2)})+{(i+1)}*{layer_gap_Tx}*{math.tan(math.pi/8)}', 0])

    #         if i == N_Tx - 1:
    #             temp.append([f'{center_length}/2+{(i+1)}*{layer_gap_Tx}',
    #                         f'{center_width}/(2+{math.sqrt(2)})+{(i+1)}*{layer_gap_Tx}*{math.tan(math.pi/8)}-0.2mm', 0])
        
    #     # 폴리라인 생성
    #     sorted_edges_Tx = self._create_polyline(points=temp, name=name, coil_width=coil_width, coil_height=coil_height)
        
    #     # winding 객체 색상 변경
    #     winding_obj = self.design.modeler.get_object_from_name(objname=name)
    #     winding_obj.color = (255, 0, 0)
        
    #     return winding_obj
