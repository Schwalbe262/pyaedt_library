import pyaedt
from pyaedt import Desktop, Maxwell3d, Icepak
import os
import shutil

from .model3D import Model3D
from .variable import Variable
from .excitation import Excitation
from .meshing import Meshing
from .result import Result
# from .material import Material

class Project:

    def __init__(self):

        self.version = None # ex> 2023.1
        self.non_graphical = False
        self.pid = None

        self.dir = os.path.expanduser('~/Documents/Ansoft')
        self.project_name = "script"


    # ==============================
    # launch ANSYS desktop app
    # ==============================
    def desktop(self) :

        self.desktop = Desktop(
            specified_version = self.version,
            non_graphical = self.non_graphical
        )

        self.desktop.disable_autosave() # disable auto save
        self.pid = self.desktop.aedt_process_id # get session pid number

        return self.desktop
    

        
    def create_project(self) :

        self.design_name = f'script1_{self.itr}'

        self.desktop.odesktop.NewProject(pyaedt.generate_unique_project_name())


    # ==============================
    # create new project on current desktop session
    # ==============================
    def new_design(self, design_name="Design1", design_type="Maxwell3D", solver="EddyCurrent") :

        design_obj = None # project object

        project_file = self.dir + f"\\{self.project_name}.aedt"

        # first project case
        if self.desktop.project_list() == [] :
            
            # folder check and make folder
            if os.path.exists(self.dir) == False :
                os.mkdir(self.dir)
    
            if os.path.isfile(project_file + ".lock") == True :
                os.remove(project_file + ".lock")


        # Maxwell3D
        if design_type == "Maxwell3D" :

            design_obj = Maxwell3d(
                projectname = project_file,
                designname = design_name,
                solution_type = solver,
                new_desktop_session = False
            )
            


        design_obj.model3D = Model3D(design_obj)
        design_obj.variable = Variable(design_obj, self.desktop)
        design_obj.excitation = Excitation(design_obj, self.desktop)
        design_obj.meshing = Meshing(design_obj, self.desktop)
        design_obj.result = Result(design_obj, self.dir)
        # design_obj.material = Material(design_obj)
        

        return design_obj
    

    def get_active_design(self) :

        icp_name = self.desktop.active_design().GetName()

        design_type = self.desktop.active_design().GetDesignType()

        design_obj = None

        if design_type == "Icepak" :
            design_obj = Icepak(design=icp_name)
        else :
            return False

        design_obj.model3D = Model3D(design_obj)
        design_obj.variable = Variable(design_obj, self.desktop)
        design_obj.excitation = Excitation(design_obj, self.desktop)
        design_obj.meshing = Meshing(design_obj, self.desktop)
        design_obj.result = Result(design_obj, self.dir)

        return design_obj



    

        

    


    # def new_design(self, obj_project, )





    # def make_new_project(self, dir=None, mod="delete", name_project="Project", name_design="Design", name_solver="EddyCurrent", desktop_version="2023.1"):

    #     self.solver = name_solver
        
    #     # folder delete and regenerate
    #     if mod == "delete" :
    #         if os.path.exists(dir) :
    #             shutil.rmtree(dir)

    #     # folder check and make folder
    #     if os.path.exists(dir) == False :
    #         os.mkdir(dir)

    #     # dir + aedt file name
    #     project_name = f'{dir}\\{name_project}.aedt'

    #     self.M3D = Maxwell3d(
    #         projectname = project_name,
    #         designname = name_design,
    #         solution_type = name_solver,
    #         specified_version = desktop_version,
    #         non_graphical = self.non_graphical,
    #         new_desktop_session = True
    #     )

    #     self.M3D.modeler.model_units = "mm"
    #     self.M3D.autosave_disable()  # for fast modeling

    #     self.meshing = Meshing(self.M3D)

    #     return self.M3D



