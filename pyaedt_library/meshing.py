import pyaedt
from pyaedt import Desktop
import os
import shutil
import math

from pyaedt import Maxwell3d

class Meshing :

    def __init__(self, design, desktop):
        self.design = design
        self.desktop = desktop



    def skin_depth_meshing(self, object=None, freq=30e+3, material="copper", name="skin_mesh") :

        mu = 0.999991 * 4 * 3.141592 * 1e-7 
        omega = 2 * 3.141592 * freq

        if material == "copper" : sigma = 58000000

        skindepth = math.sqrt(2/omega/mu/sigma) * 1e+3

        # obj_name = []
        # for obj in object :
        #     obj_name.append(self.design.modeler.get_object_from_name)

        # Tx = self.M3D.modeler.get_object_from_name(objname = "Tx_in")
        # Rx = self.M3D.modeler.get_object_from_name(objname = "Rx_in")

        object_name = [obj.name for obj in object]

        meshing =  self.design.mesh.assign_skin_depth(
            names = object_name,
            skin_depth = f"{skindepth}mm",
            triangulation_max_length = "30mm",
            maximum_elements = None,
            layers_number = "2",
            name = name
        )

        return meshing

        # self.M3D.mesh.assign_skin_depth(names=[Tx.name,Rx.name],skindepth=f"{skindepth}mm",maxelements = None,triangulation_max_length="30mm",numlayers="2",meshop_name="winding")


    

    def initial_mesh(self) :

        oProject = self.desktop.odesktop.SetActiveProject(self.desktop.project_list()[0])
        oDesign = oProject.SetActiveDesign(self.design.design_name)
        oModule = oDesign.GetModule("AnalysisSetup")
        oModule.RevertSetupToInitial("Setup1")

        return True