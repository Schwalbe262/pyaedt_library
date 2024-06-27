import pyaedt
from pyaedt import Desktop
import os
import shutil
import math

from pyaedt import Maxwell3d

class Model3D:

    def __init__(self, design):
        self.design = design


    # radiation boundary
    def create_region(self, x_p=100, x_n=100, y_p=100, y_n=100, z_p=100, z_n=100) :

        # region = self.design.modeler.create_air_region(x_pos=x_pos, y_pos=y_pos, z_pos=z_pos, x_neg=x_neg, y_neg=y_neg, z_neg=z_neg)
        region = self.design.modeler.create_air_region(x_pos=x_p, x_neg=y_n, y_pos=x_n, y_neg=z_p, z_pos=y_p, z_neg=z_n)

        region_face = self.design.modeler.get_object_faces("Region")
        region_face
        self.design.assign_radiation(assignment=region_face, radiation_name="Radiation")
        self.design.assign_material(obj= region, mat="vacuum")

        return region



    def create_coretype_core(self, name="core", **kwargs) :

        # variable setting
        core_w1 = kwargs.get("w1", "60mm") # core_w1
        core_l1_leg = kwargs.get("l1_leg", "25mm") # core_l1_leg
        core_l1_top = kwargs.get("l1_top", "25mm") # core_l1_top
        core_l2 = kwargs.get("l2", "80mm") # core_l2
        core_h1 = kwargs.get("h1", "80mm") # core_h1

        material = kwargs.get("mat", "ferrite")
        coreloss = kwargs.get("coreloss", False)

        # make core (main part)
        origin = [f"-({core_w1})/2", f"-(2*{core_l1_leg} + {core_l2})/2", f"-(2*{core_l1_top} + {core_h1})/2"]
        dimension = [f"({core_w1})", f"(2*{core_l1_leg} + {core_l2})", f"(2*{core_l1_top} + {core_h1})"]
        core_base = self.design.modeler.create_box(
            origin = origin,
            sizes = dimension,
            name = name,
            material = material
        )

        # make core (sub part)
        origin = [f"-({core_w1})/2", f"-({core_l2})/2", f"-({core_h1})/2"]
        dimension = [f"({core_w1})", f"({core_l2})", f"({core_h1})"]
        core_sub = self.design.modeler.create_box(
            origin = origin,
            sizes = dimension,
            name = f'{name}_sub',
            material = material
        )


        # subtract core
        blank_list = [core_base.name]
        tool_list = [core_sub.name]

        self.design.modeler.subtract(
            blank_list = blank_list,
            tool_list = tool_list,
            keep_originals = False
        )

        core_base.transparency = 0

        # fillet
        # if kwargs['fillet'] == True :
        #     fillet_edge = [edge for edge in core_base.edges if edge.midpoint[0] == 0]

        if coreloss == True :
            self.design.set_core_losses(assignment=core_base, core_loss_on_field=True)

        return core_base
    


    def create_cold_plate(self, type="core_type", name="cold_plate", pos="both", **kwargs) :

        # variable setting
        core_w1 = kwargs.get("w1", "60mm") # core_w1
        core_l1_leg = kwargs.get("l1_leg", "25mm") # core_l1_leg
        core_l1_top = kwargs.get("l1_top", "25mm") # core_l1_top
        core_l2 = kwargs.get("l2", "80mm") # core_l2
        core_h1 = kwargs.get("h1", "80mm") # core_h1

        cold_plate_x = kwargs.get("cold_plate_x", "20mm") # cold plate skirt size (x axis)
        cold_plate_y = kwargs.get("cold_plate_y", "20mm") # cold plate skirt size (y axis)
        cold_plate_z1 = kwargs.get("cold_plate_z1", "15mm") # cold plate base thick
        cold_plate_z2 = kwargs.get("cold_plate_z2", "0.2") # cold plate skirt size (thick)


        material = kwargs.get("mat", "aluminum")

        # make cold plate (main part)
        origin = [
            f"-({core_w1})/2 - ({cold_plate_x})", 
            f"-({core_l1_leg}) - ({core_l2})/2 - ({cold_plate_y})", 
            f"({core_l1_top}) + ({core_h1})/2 - ({core_l1_top})*({cold_plate_z2})"
            ]
        
        dimension = [
            f"({core_w1}) + 2*({cold_plate_x})", 
            f"2*({core_l1_leg}) + ({core_l2}) + 2*({cold_plate_y})", 
            f"({cold_plate_z1}) + ({core_l1_top})*({cold_plate_z2})"]
        
        cold_plate_base = self.design.modeler.create_box(
            origin = origin,
            sizes = dimension,
            name = name,
            material = material
        )

        # make cold plate (sub part)
        origin = [
            f"-({core_w1})/2", 
            f"-({core_l1_leg}) - ({core_l2})/2", 
            f"({core_l1_top}) + ({core_h1})/2 - ({core_l1_top})*({cold_plate_z2})"
            ]
        
        dimension = [
            f"({core_w1})", 
            f"2*({core_l1_leg}) + ({core_l2})", 
            f"({core_l1_top})*({cold_plate_z2})"]
        
        cold_plate_sub = self.design.modeler.create_box(
            origin = origin,
            sizes = dimension,
            name = name + "_sub",
            material = material
        )

        blank_list = [cold_plate_base.name]
        tool_list = [cold_plate_sub.name]
        self.design.modeler.subtract(blank_list, tool_list, keep_originals=False)

        cold_plate_object = []



        if pos == "both" :
            
            cold_plate_base.name += "_top"
            cold_plate_object.append(cold_plate_base)

            self.design.modeler.copy(cold_plate_object)
            copy_object_name = self.design.modeler.paste()
            copy_object = self.find_object(copy_object_name)
            copy_object.name = cold_plate_base.name.replace("_top", "") + "_bottom"
            copy_object.mirror(position = [0, 0, 0], vector = [0, 0, -1])
            cold_plate_object.append(copy_object)

        if pos == "top" :

            cold_plate_object.append(cold_plate_base)

        if pos == "bottom" :

            cold_plate_object.mirror(position = [0, 0, 0], vector = [0, 0, -1])
            cold_plate_object.append(cold_plate_base)
            

        return cold_plate_object



    def create_winding(self, name="winding", turns=6, layer=1, **kwargs) :


        # default variable setting
        core_x = kwargs.get("core_x", "100mm") # core_w1
        core_y = kwargs.get("core_y", "20mm") # core_l1_leg
        space_x = kwargs.get("space_x", "10mm")
        space_y = kwargs.get("space_y", "10mm")
        space_z = kwargs.get("space_z", "3mm")
        coil_width = kwargs.get("coil_width", "5mm")

        layer_gap = kwargs.get("layer_gap", "2mm")

        if layer == 1 : 
            polyline, seg_type = self._single_winding(turns=turns, **kwargs)
        elif layer == 2 :
            polyline, seg_type = self._dual_winding(turns=turns, **kwargs)


        winding = self.design.modeler.create_polyline(
            points=polyline, 
            segment_type=seg_type, 
            name=name,
            material = "copper",
            xsection_type = "Circle",
            xsection_width = coil_width,
            xsection_num_seg = 6)
        
        if layer == 1:
            winding.move(["0mm", "0mm", f"({turns}/2) * ({space_z}+{coil_width})"])

        if layer == 2:
            winding.move(["0mm", "0mm", f"({round(turns)/2}/2) * ({space_z}+{coil_width})"])
        
        return winding




    def find_object(self, obj_list) :

        new_obj_list = []

        for obj in obj_list :

            obj_name = obj if isinstance(obj, str) else obj.name # convert object to name
            new_obj_list.append(self.design.modeler.get_object_from_name(obj_name)) # get object from name

        if len(new_obj_list) == 1:
            return new_obj_list[0]

        return new_obj_list


    def _dual_winding(self, turns, **kwargs) :

        polyline = []
        seg_type = []

        last = 0

        # default variable setting
        core_x = kwargs.get("core_x", "100mm") # core_w1
        core_y = kwargs.get("core_y", "20mm") # core_l1_leg
        space_x = kwargs.get("space_x", "10mm")
        space_y = kwargs.get("space_y", "10mm")
        space_z = kwargs.get("space_z", "3mm")
        coil_width = kwargs.get("coil_width", "5mm")

        layer_gap = kwargs.get("layer_gap", "2mm")

        # terminal
        polyline.append([
            f'({core_x}/2 + {space_x} + {coil_width}/2 + 100mm)',
            f'-({core_y}/2 + {space_y} + {coil_width}/2)',
            f'0*({space_z}+{coil_width})'
        ])

        # inner layer
        for itr in range(math.ceil(turns/2)) :

            last = itr

            polyline.append([
                f'(({core_x})/2 + ({space_x}) + 0.5*({coil_width}))',
                f'-(({core_y})/2 + ({space_y}) + 0.5*({coil_width}))',
                f'-(({itr})+0)*(({space_z})+({coil_width}))'
            ])
            seg_type.append("Line")

            polyline.append([
                f'-(({core_x})/2 + ({space_x}) + 0.5*({coil_width}))',
                f'-(({core_y})/2 + ({space_y}) + 0.5*({coil_width}))',
                f'-(({itr})+0.5)*(({space_z})+({coil_width}))'
            ])
            seg_type.append("Line")

            polyline.append([
                f'-(({core_x})/2 + ({space_x}) + 0.5*({coil_width}))',
                f'(({core_y})/2 + ({space_y}) + 0.5*({coil_width}))',
                f'-(({itr})+0.5)*(({space_z})+({coil_width}))'
            ])
            seg_type.append("Line")

            polyline.append([
                f'(({core_x})/2 + ({space_x}) + 0.5*({coil_width}))',
                f'(({core_y})/2 + ({space_y}) + 0.5*({coil_width}))',
                f'-(({itr})+1.0)*(({space_z})+({coil_width}))'
            ])
            seg_type.append("Line") 

        # outer layer
        for itr in range(math.floor(turns/2)):

            print(itr)

            if itr == 0 :
                polyline.append([
                    f'(({core_x})/2 + ({space_x}) + 0.5*({coil_width}))',
                    f'-(({core_y})/2 + ({space_y}) + 1.5*({coil_width}) + ({layer_gap}))',
                    f'-(({last})-({itr})+1.0)*(({space_z})+({coil_width}))'
                ])
                seg_type.append("Line")
            else:
                polyline.append([
                    f'(({core_x})/2 + ({space_x}) + 1.5*({coil_width}) + ({layer_gap}))',
                    f'-(({core_y})/2 + ({space_y}) + 1.5*({coil_width}) + ({layer_gap}))',
                    f'-(({last})-({itr})+1.0)*(({space_z})+({coil_width}))'
                ])
                seg_type.append("Line")

            polyline.append([
                f'-(({core_x})/2 + ({space_x}) + 1.5*({coil_width}) + ({layer_gap}))',
                f'-(({core_y})/2 + ({space_y}) + 1.5*({coil_width}) + ({layer_gap}))',
                f'-(({last})-({itr})+0.5)*(({space_z})+({coil_width}))'
            ])
            seg_type.append("Line")

            polyline.append([
                f'-(({core_x})/2 + ({space_x}) + 1.5*({coil_width}) + ({layer_gap}))',
                f'(({core_y})/2 + ({space_y}) + 1.5*({coil_width}) + ({layer_gap}))',
                f'-(({last})-({itr})+0.5)*(({space_z})+({coil_width}))'
            ])
            seg_type.append("Line")

            polyline.append([
                f'(({core_x})/2 + ({space_x}) + 1.5*({coil_width}) + ({layer_gap}))',
                f'(({core_y})/2 + ({space_y}) + 1.5*({coil_width}) + ({layer_gap}))',
                f'-(({last})-({itr})+0.0)*(({space_z})+({coil_width}))'
            ])
            seg_type.append("Line")

            if itr == turns - math.ceil(turns/2) - 1 :
                polyline.append([
                    f'(({core_x})/2 + ({space_x}) + 1.5*({coil_width}) + ({layer_gap}))',
                    f'-(({core_y})/2 + ({space_y}) - 0.5*({coil_width}) - ({layer_gap}))',
                    f'-(({last})-({itr})+0.0)*(({space_z})+({coil_width}))'
                ])
                seg_type.append("Line")

                polyline.append([
                    f'({core_x}/2 + {space_x} + {coil_width}/2 + 100mm)',
                    f'-(({core_y})/2 + ({space_y}) - 0.5*({coil_width}) - ({layer_gap}))',
                    f'-(({last})-({itr})+0.0)*(({space_z})+({coil_width}))'
                ])
                seg_type.append("Line")


        return polyline, seg_type





    def _single_winding(self, turns, **kwargs) :

        polyline = []
        seg_type = []

        # default variable setting
        core_x = kwargs.get("core_x", "100mm") # core_w1
        core_y = kwargs.get("core_y", "20mm") # core_l1_leg
        space_x = kwargs.get("space_x", "10mm")
        space_y = kwargs.get("space_y", "10mm")
        space_z = kwargs.get("space_z", "3mm")
        coil_width = kwargs.get("coil_width", "5mm")


        # test_points = [["0mm", "0mm", "0mm"], ["100mm", "20mm", "0mm"],
        #        ["71mm", "71mm", "0mm"], ["0mm", "100mm", "0mm"]]

        # P1 = design1.modeler.create_polyline(test_points,name="PL_line_segments")
        # P2 = design1.modeler.create_polyline(test_points,segment_type=["Line", "Arc"],name="PL_line_plus_arc")

        # terminal
        polyline.append([
            f'({core_x}/2 + {space_x} + {coil_width}/2 + 100mm)',
            f'-({core_y}/2 + {space_y} + {coil_width}/2)',
            f'0*({space_z}+{coil_width})'
        ])
        # seg_type.append("Line")


        for itr in range(turns) :

            polyline.append([
                f'({core_x}/2 + {space_x} + {coil_width}/2)',
                f'-({core_y}/2 + {space_y} + {coil_width}/2)',
                f'-({itr}+0)*({space_z}+{coil_width})'
            ])
            seg_type.append("Line")

            polyline.append([
                f'-({core_x}/2 + {space_x} + {coil_width}/2)',
                f'-({core_y}/2 + {space_y} + {coil_width}/2)',
                f'-({itr}+0.5)*({space_z}+{coil_width})'
            ])
            seg_type.append("Line")

            polyline.append([
                f'-({core_x}/2 + {space_x} + {coil_width}/2)',
                f'({core_y}/2 + {space_y} + {coil_width}/2)',
                f'-({itr}+0.5)*({space_z}+{coil_width})'
            ])
            seg_type.append("Line")

            polyline.append([
                f'({core_x}/2 + {space_x} + {coil_width}/2)',
                f'({core_y}/2 + {space_y} + {coil_width}/2)',
                f'-({itr}+1.0)*({space_z}+{coil_width})'
            ])
            seg_type.append("Line")

            polyline.append([
                f'({core_x}/2 + {space_x} + {coil_width}/2)',
                f'-({core_y}/2 + {space_y} + {coil_width}/2)',
                f'-({itr}+1.0)*({space_z}+{coil_width})'
            ])
            seg_type.append("Line")

        # end terminal

        polyline.append([
            f'({core_x}/2 + {space_x} + {coil_width}/2 + 100mm)',
            f'-({core_y}/2 + {space_y} + {coil_width}/2)',
            f'-{turns}*({space_z}+{coil_width})'
        ])
        seg_type.append("Line")



        return polyline, seg_type





    



    

    






