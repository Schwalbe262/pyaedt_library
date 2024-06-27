import pyaedt
from pyaedt import Desktop
import os
import shutil
import math

from pyaedt import Maxwell3d

# from .variable import Variable

class Excitation:

    def __init__(self, design, desktop):
        self.design = design
        self.desktop = desktop

    def _find_terminal_face(self, winding_obj) :

        terminal_face = []

        # find maximum x position of winding object
        max_x_pos = max(abs(face.center[0]) for face in winding_obj.faces)

        # append terminal face to array
        for face in winding_obj.faces :
            if abs(abs(face.center[0]) - max_x_pos) <= 0.0001:
                    terminal_face.append(face)

        # sort (upper, lower)
        if abs(terminal_face[0].center[2] - terminal_face[1].center[2]) <= 1 : # 2 layer case
            ter_u, ter_l = sorted(terminal_face, key=lambda x : x.center[2], reverse=False)
        else :
            ter_u, ter_l = sorted(terminal_face, key=lambda x : x.center[2], reverse=True)

        return ter_u, ter_l



    def assign_winding_coil(self, winding_obj, ter_name=["ter_in", "ter_out"], winding_name="Winding", rms_current=100, polarity="positive"):
        
        ter_in, ter_out = self._find_terminal_face(winding_obj)

        if polarity == "positive":
            self.design.assign_coil(ter_in, conductor_number=1, polarity="Positive", name=ter_name[0])
            self.design.assign_coil(ter_out, conductor_number=1, polarity="Negative", name=ter_name[1])
        elif polarity == "negative":
            self.design.assign_coil(ter_in, conductor_number=1, polarity="Negative", name=ter_name[0])
            self.design.assign_coil(ter_out, conductor_number=1, polarity="Positive", name=ter_name[1])

        winding = self.design.assign_winding(coil_terminals=[], winding_type="Current", is_solid=True, current_value=f"{rms_current} * sqrt(2)A", name=winding_name)
        self.design.add_winding_coils(winding.name, coil_names=[ter_name[0], ter_name[1]])

        return winding
    


    def set_power_ferrite(self, cm=3, x=1.5, y=2.5, per=1000) :
        
        power_ferrite = self.design.materials.duplicate_material("ferrite","power_ferrite")
        power_ferrite.set_power_ferrite_coreloss(cm=cm, x=x, y=y)
        power_ferrite.permeability = per

        return power_ferrite



    # EM loss excitation for icepak
    def assign_EM_loss(self, name="EMLoss", objects=None, design=None, frequency=None, loss_mul=1, **kwargs) :

        oProject = self.desktop.odesktop.SetActiveProject(self.desktop.project_list()[0])
        oDesign = oProject.SetActiveDesign(self.design.design_name)
        oModule = oDesign.GetModule("BoundarySetup")

        object_name = [item.name for item in objects]


        oModule.AssignEMLoss(
            [
                f'NAME:{name}',
                "Objects:=", object_name,
                "Project:=", "This Project*",
                "Product:=", "ElectronicsDesktop",
                "Design:=", f'{design.design_name}',
                "Soln:=", "Setup1 : LastAdaptive",
                self.design.variable._get_params_list(),
                "ForceSourceToSolve:=", False,
                "PreservePartnerSoln:=", False,
                "PathRelativeTo:=", "TargetProject",
                "Intrinsics:=", [f"{frequency}Hz"],
                "SurfaceOnly:=", [],
                "LossMultiplier:=", loss_mul
            ])

        


    def assign_icepak_source(self, assignment=[], thermal_condition=None, assignment_value=None, boundary_name=None) :
        
        # === parameter ===

        # assignment : object name or face number (didn't work) (list compatible)
        # thermal condition : "Total Power", "Surface Flux", "Fixed Temperature"
        # assignment_value : (example) "10W", "AmbientTemp", "30cel"
        # boundary name : assignment name

        # code example : icepak.excitation.assign_icepak_source(assignment=[i_LV_winding.name, i_HV_winding.name], thermal_condition="Fixed Temperature", assignment_value = "AmbientTemp", boundary_name = "cold_plate")

        # ==================
        
        if self.design.design_type != "Icepak" : return False # verify Icepak or not

        object_name = [obj if isinstance(obj, str) else obj.name for obj in assignment]

        setting = self.design.assign_source(
            assignment = object_name, 
            thermal_condition = thermal_condition, 
            assignment_value = assignment_value, 
            boundary_name = boundary_name
            )
        
        return setting