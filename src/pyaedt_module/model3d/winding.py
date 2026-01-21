import math
import re
from collections import namedtuple

class Winding:

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
        """
        폴리라인을 생성합니다.
        
        Parameters:
            name (str): 폴리라인의 이름
            points (list): 폴리라인의 점들
            width (str): 폴리라인의 너비
            height (str): 폴리라인의 높이
            
        Returns:
            object: 생성된 폴리라인 객체
        """
        polyline_obj = self.design.modeler.create_polyline(points=points, name=name, xsection_type="Rectangle", xsection_width=f"{width}", xsection_height=f"{height}")
        polyline_obj.point_list = points
        
        return polyline_obj
    

    def create_via(self, name="via", center=[0,0,0], outer_R=None, inner_R=None, height=None, via_pad_R=None, via_pad_thick=None) :
        """
        비아를 생성합니다.
        
        Parameters:
            name (str): 비아의 이름
            center (list): 비아의 중심 좌표
            outer_R (str): 비아의 외부 반지름
            inner_R (str): 비아의 내부 반지름
            height (str): 비아의 높이
            via_pad_R (str): 비아 패드의 반지름
            via_pad_thick (str): 비아 패드의 두께
            
        Returns:
            object: 생성된 비아 객체
        """
        outer_cylinder = self.design.modeler.create_cylinder(orientation="Z", 
                                                             origin=[center[0], center[1], f"({center[2]})-(({height})/2)"], 
                                                             radius=outer_R, height=height, name=name, material="copper", num_sides=12)

        if inner_R != None :
            inner_cylinder = self.design.modeler.create_cylinder(orientation="Z", 
                                                                 origin=[center[0], center[1], f"({center[2]})-(({height})/2)"], 
                                                                 radius=inner_R, height=height, name=f"{name}_inner", material="copper", num_sides=12)
            self.design.modeler.subtract(blank_list = outer_cylinder, tool_list = inner_cylinder, keep_originals = False)

        if via_pad_R != None :

            upper_pad = self.design.modeler.create_cylinder(orientation="Z", 
                                                                 origin=[center[0], center[1], f"({center[2]})+(({height})/2)-({via_pad_thick})"], 
                                                                 radius=via_pad_R, height=via_pad_thick, name=f"{name}_pad_u", material="copper", num_sides=12)
            lower_pad = self.design.modeler.create_cylinder(orientation="Z", 
                                                                 origin=[center[0], center[1], f"({center[2]})-(({height})/2)"], 
                                                                 radius=via_pad_R, height=via_pad_thick, name=f"{name}_pad_l", material="copper", num_sides=12)
            
            outer_cylinder = self.design.model3d.unite(assignment=[outer_cylinder, upper_pad, lower_pad])

        
        return outer_cylinder



    def coil_points(self, turns=5, **kwargs):
        """
        코일의 점들을 생성합니다.
        
        Parameters:
            turns (int): 코일의 턴 수
            **kwargs:
                outer_x (str): 코일의 외부 x 크기
                outer_y (str): 코일의 외부 y 크기
                fillet (str): 코일의 필릿 크기
                inner (str): 코일의 내부 크기
                fill_factor (float): 코일의 채움 계수
                theta1 (str): 코일의 각도 1
                theta2 (str): 코일의 각도 2
                turns_sub (int) : 빼낼 턴 수 (default: 0)

        Returns:
            namedtuple: 코일의 점들과 관련 파라미터들
        """
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

        turns_sub = kwargs.get("turns_sub", 0)


        points = []

        for i in range(turns_sub, N):

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

        return WindingResult(points=points, 
                             outer_x=outer_x, outer_xx=outer_xx, outer_y=outer_y, outer_yy=outer_yy, fillet=fillet, inner=inner,
                             width=width, gap=gap, wg=wg, theta1=theta1, theta2=theta2)
        
    def create_winding(self, name="winding", **kwargs):
        """
        와인딩을 생성합니다.
        
        Parameters:
            name (str): 와인딩의 이름
            **kwargs:
                outer_x (str): 와인딩의 외부 x 크기
                outer_y (str): 와인딩의 외부 y 크기
                outer_xx (str): 와인딩의 내부 x 크기
                outer_yy (str): 와인딩의 내부 y 크기
                turns (int): 와인딩의 턴 수
                inner (str): 와인딩의 내부 크기
                fill_factor (float): 와인딩의 채움 계수
                
        Returns:
            object: 생성된 와인딩 객체
        """
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

        points = []

        for i in range(N) :

            points.append([f"({outer_xx}) - ({i})*({wg})*(1/tan({theta2})) + ({wg})", f"-({outer_y}) + ({i-1})*({wg})", 0])
            points.append([f"({outer_x}) - ({i})*({wg}) + ({wg})", f"-({outer_yy}) + ({i})*({wg})*(tan({theta1}))", 0])
            points.append([f"({outer_x}) - ({i})*({wg}) + ({wg})", f"({outer_yy}) - ({i})*({wg})*(tan({theta1}))", 0])
            points.append([f"({outer_xx}) - ({i})*({wg})*(1/tan({theta2})) + ({wg})", f"({outer_y}) - ({i})*({wg})", 0])

            points.append([f"-({outer_xx}) + ({i})*({wg})*(1/tan({theta2}))", f"({outer_y}) - ({i})*({wg})", 0])
            points.append([f"-({outer_x}) + ({i})*({wg})", f"({outer_yy}) - ({i})*({wg})*(tan({theta1}))", 0])
            points.append([f"-({outer_x}) + ({i})*({wg})", f"-({outer_yy}) + ({i})*({wg})*(tan({theta1}))", 0])
            points.append([f"-({outer_xx}) + ({i})*({wg})*(1/tan({theta2}))", f"-({outer_y}) + ({i})*({wg})", 0])

        self.design.modeler.create_polyline(points=points)
