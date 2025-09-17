import math
import re
from collections import namedtuple

class PCB_winding:

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