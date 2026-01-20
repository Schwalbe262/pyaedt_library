import math
import re
from collections import namedtuple
import time

class Transformer_winding:

    def __init__(self, design) :
        self.design = design
    
    def __getattr__(self, name):
        return getattr(self.design, name)
    

    def _convert_unit(self, value, target_unit="mm"):
        """
        주어진 값을 다른 단위로 변환합니다.
        
        Parameters:
            value (str): 변환할 값 (예: "10mm", "1cm")
            target_unit (str): 변환할 단위 ("mm", "cm", "m", "um")
            
        Returns:
            float: 변환된 값
        """
        unit_map = {
            "mm": 1,
            "cm": 10,
            "m": 1000,
            "um": 0.001
        }


    def create_polyline(self, name="winding", points=None, **kwargs):
        """
        폴리라인을 생성합니다.
        
        Parameters:
            name (str): 폴리라인의 이름
            points (list): 폴리라인의 점들
            
        Returns:
            object: 생성된 폴리라인 객체
        """

        x_section_type = kwargs.get("type", "Circle") # Rectangle, Circle
        if x_section_type == "Circle" :
            orientation = kwargs.get("orientation", "Auto")
            xsection_topwidth = kwargs.get("top_width", "0mm")
            xsection_width = kwargs.get("coil_diameter", "5mm")
            xsection_height = kwargs.get("height", "0mm")
        elif x_section_type == "Rectangle" :
            orientation = kwargs.get("orientation", "Auto")
            xsection_topwidth = kwargs.get("top_width", "0mm")
            xsection_width = kwargs.get("width", "5mm")
            xsection_height = kwargs.get("height", "0.5mm")
        elif x_section_type == "Isosceles Trapezoid" :
            orientation = kwargs.get("orientation", "Auto")
            xsection_topwidth = kwargs.get("top_width", "3mm")
            xsection_width = kwargs.get("width", "5mm")
            xsection_height = kwargs.get("height", "0.5mm")
        else :
            raise ValueError(f"Invalid x_section_type: {x_section_type}")
        
        color = kwargs.get("color", None)
        transparency = kwargs.get("transparency", None)
        xsection_num_seg = kwargs.get("Num", 6)
        
        
        if points is None :
            raise ValueError("points is None")

        polyline_obj = self.design.modeler.create_polyline(
            points=points, name=name, xsection_orient=orientation,
            xsection_type=x_section_type, xsection_width=xsection_width, xsection_height=xsection_height, xsection_num_seg=xsection_num_seg, xsection_topwidth=xsection_topwidth)
        polyline_obj.point_list = points

        if color is not None :
            polyline_obj.color = color
        if transparency is not None :
            polyline_obj.transparency = transparency

        return polyline_obj
    


    def winding_points(self, **kwargs) :

        """
        사용 예시

        winding_params1 = {
            "N" : sim1.N1,
            "N_layer" : sim1.N1_layer,
            "x" : "w1 + 2*N1_space_w",
            "y" : "l1 + 2*N1_space_l",
            "coil_diameter" : "N1_coil_diameter",
            "coil_zgap" : "N1_coil_zgap",
            "coil_layer_x_gap" : "N1_layer_gap",
            "coil_layer_y_gap" : "N1_layer_gap",
            "color" : [255, 50, 50],
            "transparency" : 0,
            "offset" : ["0mm", "-(l1+l2)/2", f"{offset1}mm"]
        }
        points1 = sim1.winding_points(name="winding1", **winding_params1)

        
        """

        """
        예시

        modeler = Transformer_winding(simulation.design)
        winding_point = modeler.winding_points(**kwargs)
        winding = modeler.create_polyline(name=name, points=winding_point,**kwargs)

        """

        raw_N = kwargs.get("N", 10)
        raw_N_layer = kwargs.get("N_layer", 1)

        # N과 N_layer는 Python 로직(range, if)에 사용되므로 정수여야 합니다.
        # 문자열로 들어올 경우, 정수로 변환을 시도하고, 실패하면 디자인 변수로 간주하여 값을 가져옵니다.
        try:
            N = int(raw_N)
        except (ValueError, TypeError):
            # get_variable_value가 반환하는 값은 문자열일 수 있으므로, 숫자 타입으로 변환합니다.
            N = int(float(self.design.get_variable_value(raw_N)))

        try:
            N_layer = int(raw_N_layer)
        except (ValueError, TypeError):
            N_layer = int(float(self.design.get_variable_value(raw_N_layer)))

        x = kwargs.get("x", "100mm")
        y = kwargs.get("y", "20mm")
        coil_diameter = kwargs.get("coil_diameter", "10mm")
        coil_zgap = kwargs.get("coil_zgap", "1mm")
        coil_layer_x_gap = kwargs.get("coil_layer_x_gap", "1mm")
        coil_layer_y_gap = kwargs.get("coil_layer_y_gap", "1mm")

        clock_wise = kwargs.get("clock_wise", True)

        terminal = kwargs.get("terminal", True)
        terminal_position = kwargs.get("terminal_position", None)
        if terminal_position is None :
            terminal_length = kwargs.get("terminal_length", "30mm")
            terminal = False
        

        # offset을 x, y, z 각 축에 대한 리스트로 처리합니다.
        offset = kwargs.get("offset", ["0mm", "0mm", "0mm"])
        offset_x, offset_y, offset_z = offset[0], offset[1], offset[2]


        points = []

        
        if clock_wise :
            # --- 레이어 1 좌표 변수 ---
            pos_x1 = f"({x})/2 + ({coil_diameter})/2"
            neg_x1 = f"-({x})/2 - ({coil_diameter})/2"
            pos_y1 = f"({y})/2 + ({coil_diameter})/2"
            neg_y1 = f"-({y})/2 - ({coil_diameter})/2"

            if N_layer == 1 :
                for i in range(N) :
                    z_base = f"-({i})*(({coil_diameter}) + ({coil_zgap}))"
                    z_start = f"{z_base} + ({offset_z})"
                    z_end = f"-({i+1})*(({coil_diameter}) + ({coil_zgap})) + ({offset_z})"

                    # 각 좌표에 오프셋 적용
                    px1_off = f"{pos_x1} + ({offset_x})"
                    nx1_off = f"{neg_x1} + ({offset_x})"
                    py1_off = f"{pos_y1} + ({offset_y})"
                    ny1_off = f"{neg_y1} + ({offset_y})"

                    if terminal and i == 0 :
                        if terminal_position is not None :
                            points.append([f"{terminal_position}", ny1_off, z_start])
                        else :
                            points.append([f"{px1_off} + {terminal_length}", ny1_off, z_start])
                    
                    points.append([px1_off, ny1_off, z_start])
                    points.append([nx1_off, ny1_off, z_start])
                    points.append([nx1_off, py1_off, z_start])
                    points.append([px1_off, py1_off, z_end])

                    if terminal and i == N-1 :
                        if terminal_position is not None :
                            points.append([f"{terminal_position}", py1_off, z_end])
                        else :
                            points.append([f"{px1_off} + {terminal_length}", py1_off, z_end])
                            
            if N_layer == 2 :
                # --- 레이어 2 좌표 변수 ---
                x2 = f"({x})/2 + ({coil_diameter}) + ({coil_layer_x_gap})"
                y2 = f"({y})/2 + ({coil_diameter}) + ({coil_layer_y_gap})"
                pos_x2 = f"({x2}) + ({coil_diameter})/2"
                neg_x2 = f"-({x2}) - ({coil_diameter})/2"
                pos_y2 = f"({y2}) + ({coil_diameter})/2"
                neg_y2 = f"-({y2}) - ({coil_diameter})/2"

                n1 = math.ceil(N / 2) # 첫 번째 레이어의 턴 수

                for i in range(N):
                    # --- Z 좌표 계산 ---
                    if i < n1: # 레이어 1 (내려가는 중)
                        z_index_start = i
                        z_index_end = i + 1
                    else: # 레이어 2 (올라오는 중)
                        z_index_start = n1 - (i - n1)
                        z_index_end = z_index_start - 1
                    
                    z_base_start = f"-({z_index_start})*(({coil_diameter}) + ({coil_zgap}))"
                    z_base_end = f"-({z_index_end})*(({coil_diameter}) + ({coil_zgap}))"
                    z_start = f"{z_base_start} + ({offset_z})"
                    z_end = f"{z_base_end} + ({offset_z})"

                    # 각 좌표에 오프셋 적용
                    px1_off = f"{pos_x1} + ({offset_x})"
                    nx1_off = f"{neg_x1} + ({offset_x})"
                    py1_off = f"{pos_y1} + ({offset_y})"
                    ny1_off = f"{neg_y1} + ({offset_y})"
                    px2_off = f"{pos_x2} + ({offset_x})"
                    nx2_off = f"{neg_x2} + ({offset_x})"
                    py2_off = f"{pos_y2} + ({offset_y})"
                    ny2_off = f"{neg_y2} + ({offset_y})"


                    # --- X, Y 좌표 및 포인트 추가 ---
                    if i < n1: # 레이어 1
                        if terminal and i == 0:
                            if terminal_position is not None :
                                points.append([f"{terminal_position}", ny1_off, z_start])
                            else :
                                points.append([f"{px1_off} + {terminal_length}", ny1_off, z_start])
                        points.append([px1_off, ny1_off, z_start])
                        points.append([nx1_off, ny1_off, z_start])
                        points.append([nx1_off, py1_off, z_start])
                        points.append([px1_off, py1_off, z_end])
                    elif i == n1: # 레이어 2의 시작 (전이 구간)
                        # 요청하신대로, 올라오는 구간의 첫 포인트는 pos_x1, neg_y2를 사용합니다.
                        points.append([px1_off, ny2_off, z_start]) # 전이 포인트
                        points.append([nx2_off, ny2_off, z_start])
                        points.append([nx2_off, py2_off, z_start])
                        points.append([px2_off, py2_off, z_end])
                    else: # 레이어 2의 나머지
                        points.append([px2_off, ny2_off, z_start])
                        points.append([nx2_off, ny2_off, z_start])
                        points.append([nx2_off, py2_off, z_start])
                        points.append([px2_off, py2_off, z_end])

                        if terminal and i == N-1 :
                            if terminal_position is not None :
                                points.append([f"{terminal_position}", py2_off, z_end])
                            else :
                                points.append([f"{px2_off} + {terminal_length}", py2_off, z_end])

                        

        return points


    def foil_winding(self, name, **kwargs) :

        """
        사용 예시

        winding_params1 = {
            "N" : sim1.N1,
            "N_layer" : sim1.N1_layer,
            "x" : "w1 + 2*N1_space_w",
            "y" : "l1 + 2*N1_space_l",
            "coil_diameter" : "N1_coil_diameter",
            "coil_zgap" : "N1_coil_zgap",
            "coil_layer_x_gap" : "N1_layer_gap",
            "coil_layer_y_gap" : "N1_layer_gap",
            "color" : [255, 50, 50],
            "transparency" : 0,
            "offset" : ["0mm", "-(l1+l2)/2", f"{offset1}mm"]
        }
        points1 = sim1.winding_points(name="winding1", **winding_params1)

        
        """

        """
        예시

        modeler = Transformer_winding(simulation.design)
        winding_point = modeler.winding_points(**kwargs)
        winding = modeler.create_polyline(name=name, points=winding_point,**kwargs)

        """

        raw_N = kwargs.get("N", 10)
        raw_NN = kwargs.get("NN", 2)

        # N과 N_layer는 Python 로직(range, if)에 사용되므로 정수여야 합니다.
        # 문자열로 들어올 경우, 정수로 변환을 시도하고, 실패하면 디자인 변수로 간주하여 값을 가져옵니다.
        try:
            N = int(raw_N)
        except (ValueError, TypeError):
            # get_variable_value가 반환하는 값은 문자열일 수 있으므로, 숫자 타입으로 변환합니다.
            N = int(float(self.design.get_variable_value(raw_N)))

        try:
            NN = int(raw_NN)
        except (ValueError, TypeError):
            NN = int(float(self.design.get_variable_value(raw_NN)))

        if NN == 0 :
            NN = 10000

        x_pos = kwargs.get("x_pos", "100mm")
        y_pos = kwargs.get("y_pos", "100mm")
        inner = kwargs.get("inner", "1mm")
        outer = kwargs.get("outer", "3mm")
        width = kwargs.get("width", "10mm")
        height = kwargs.get("height", "10mm")
        terminal_length = kwargs.get("terminal_length", "30mm")
        terminal_width = kwargs.get("terminal_width", "10mm")
        material = kwargs.get("material", "copper")

        # x = "x_pos"
        # y = "y_pos"
        # inner = "(width+inner)"
        # outer = "(width+outer)"

        x = x_pos
        y = y_pos
        inner = f'({width} + {inner})'
        outer = f'({width} + {outer})'


        points = []
        points_terminal1 = []
        points_terminal2 = []

        Ns = 0
        NNs = 0

        for i in range(N) :
            
            if i == 0 : # start point
                points.append([f'{x}', f'0mm', f'0mm'])
                points_terminal1.append([f'{x}', f'0mm', f'0mm - ({height})/2'])
                points_terminal1.append([f'{x}', f'0mm', f'0mm + ({height})/2+({terminal_length})'])

            points.append([f'{x} - {Ns}*{inner} - {NNs}*{outer}', f'-{y} + {Ns}*{inner} + {NNs}*{outer}', f'0mm'])
            points.append([f'-{x} + {Ns}*{inner} + {NNs}*{outer}', f'-{y} + {Ns}*{inner} + {NNs}*{outer}', f'0mm'])
            points.append([f'-{x} + {Ns}*{inner} + {NNs}*{outer}', f'{y} - {Ns}*{inner} - {NNs}*{outer}', f'0mm'])

            if i % NN != 0 :
                points.append([f'{x} - {Ns+1}*{inner} - {NNs}*{outer}', f'{y} - {Ns}*{inner} - {NNs}*{outer}', f'0mm'])
                if i == N-1 :
                    points.append([f'{x} - {Ns+1}*{inner} - {NNs}*{outer}', f'0mm', f'0mm'])
                    points_terminal2.append([f'{x} - {Ns+1}*{inner} - {NNs}*{outer}', f'0mm', f'0mm - ({height})/2'])
                    points_terminal2.append([f'{x} - {Ns+1}*{inner} - {NNs}*{outer}', f'0mm', f'0mm + ({height})/2+({terminal_length})'])
                Ns = Ns+1
            else :
                points.append([f'{x} - {Ns}*{inner} - {NNs+1}*{outer}', f'{y} - {Ns}*{inner} - {NNs}*{outer}', f'0mm'])
                if i == N-1 : # end point
                    points.append([f'{x} - {Ns}*{inner} - {NNs+1}*{outer}', f'0mm', f'0mm'])
                    points_terminal2.append([f'{x} - {Ns}*{inner} - {NNs+1}*{outer}', f'0mm', f'0mm - ({height})/2'])
                    points_terminal2.append([f'{x} - {Ns}*{inner} - {NNs+1}*{outer}', f'0mm', f'0mm + ({height})/2+({terminal_length})'])
                NNs = NNs+1



        orientation = "Auto"
        x_section_type = "Rectangle"
        xsection_width = width
        xsection_height = height
        xsection_num_seg = 0
        xsection_topwidth = "0mm"

        polyline_obj = self.design.modeler.create_polyline(
                    points=points, name=name, xsection_orient=orientation,
                    xsection_type=x_section_type, xsection_width=xsection_width, xsection_height=xsection_height, xsection_num_seg=xsection_num_seg, xsection_topwidth=xsection_topwidth)

        polyline_obj.color = [255, 0, 0]
        polyline_obj.transparency = 0


        xsection_width = terminal_width
        xsection_height = width

        polyline_obj1 = self.design.modeler.create_polyline(
                    points=points_terminal1, name=name + "_terminal_in", xsection_orient=orientation,
                    xsection_type=x_section_type, xsection_width=xsection_width, xsection_height=xsection_height, xsection_num_seg=xsection_num_seg, xsection_topwidth=xsection_topwidth)

        polyline_obj2 = self.design.modeler.create_polyline(
                    points=points_terminal2, name=name + "_terminal_out", xsection_orient=orientation,
                    xsection_type=x_section_type, xsection_width=xsection_width, xsection_height=xsection_height, xsection_num_seg=xsection_num_seg, xsection_topwidth=xsection_topwidth)

        polyline_obj.unite([polyline_obj1, polyline_obj2])

        polyline_obj.material_name = material


        return polyline_obj