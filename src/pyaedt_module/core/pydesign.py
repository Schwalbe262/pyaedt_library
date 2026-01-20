from pyaedt_module.solver.maxwell3d import Maxwell3d
from pyaedt_module.solver.hfss import HFSS
from pyaedt_module.solver.circuit import Circuit
from pyaedt_module.solver.icepak import Icepak
from pyaedt_module.model3d import Model3d
from .post_processing import PostProcessing

import numpy as np

class pyDesign:
    def __init__(self, project, name=None, solver=None, solution=None, design=None):
        self.project = project
        self.NUM_CORE = 4


        if design is not None:
            self.design = design
            self.name = design.GetName()
            self.solver = design.GetDesignType()
            self.solution = design.GetSolutionType() if hasattr(design, "GetSolutionType") else None
        else :
            self.name = name
            self.solver = solver.lower() if solver is not None else None
            self.solution = solution
            self.solver_instance = None 

        self._store = {}

        

    
    def __getattr__(self, name):
        # First, try to get the attribute from the solver instance (e.g., methods like 'create_setup')
        if self.solver_instance:
            try:
                return getattr(self.solver_instance, name)
            except AttributeError:
                # If it's not a method/attribute on the solver, pass to check for it as a design variable
                pass

        # Second, try to get it as a design variable using __getitem__
        try:
            return self[name]
        except (KeyError, TypeError):
             # If it's not a variable either, raise the final error
            raise AttributeError(f"'pyDesign' object and its solver have no attribute or variable '{name}'")

    def __dir__(self):
        default_dir = super().__dir__()
        if self.solver_instance is not None:
            return list(set(default_dir + dir(self.solver_instance)))
        return default_dir
    
    def __getitem__(self, key):
        """변수 조회 - HFSS에 저장된 변수 또는 _store에서 가져오기"""
        if self.solver_instance and key in self.solver_instance.variable_manager.independent_variables:
            return self.solver_instance.variable_manager.independent_variables[key].value
        return self._store.get(key, None)  # HFSS가 없으면 _store에서 반환

    def __setitem__(self, key, value):
        """변수 저장 - HFSS에 직접 반영 또는 _store에 저장"""
        if self.solver_instance:
            self.solver_instance.variable_manager[key] = value  # HFSS 변수 시스템에 저장
        else:
            self._store[key] = value  # HFSS가 없으면 _store에 저장
            return value

    def __delitem__(self, key):
        """변수 삭제 - HFSS에서 삭제 또는 _store에서 삭제"""
        if self.solver_instance:
            if key in self.solver_instance.variable_manager.independent_variables:
                del self.solver_instance.variable_manager[key]
        elif key in self._store:
            del self._store[key]

    def __iter__(self):
        """변수 목록을 반환 (HFSS 또는 _store)"""
        if self.solver_instance:
            return iter(self.solver_instance.variable_manager.independent_variables)
        return iter(self._store)

    def __len__(self):
        """저장된 변수 개수 반환"""
        if self.solver_instance:
            return len(self.solver_instance.variable_manager.independent_variables)
        return len(self._store)

    def __repr__(self):
        return f"pyDesign(name={self.name}, solver={self.solver}, solution={self.solution}, store={self._store})"





    @classmethod
    def create_design(cls, project, name=None, solver=None, solution=None):
        design = cls(project, name=name, solver=solver, solution=solution)

        solver = solver.lower()
        if solver == "maxwell3d" or solver == "maxwell" :
            design._setup_maxwell()
        elif solver == "hfss":
            design._setup_hfss()
        elif solver == "circuit":
            design._setup_circuit()
        elif solver == "icepak":
            design._setup_icepak()
        
        return design
    

    def _setup_maxwell(self):
        if self.solution is None:
            self.solution = "EddyCurrent"

        self.project.desktop.odesktop.SetActiveProject(self.project.name)
        self.solver_instance = Maxwell3d(project=None, design=self.name, solution_type=self.solution)

        self.solver_instance.design = self

        self._get_module()
            
            
    def _setup_hfss(self):
        if self.solution is None:
            self.solution = "HFSS Terminal Network"
        # self.project.InsertDesign("HFSS", self.name, self.solution, "")
        # self.solver_instance = self.project.SetActiveDesign(self.name)

        self.project.desktop.odesktop.SetActiveProject(self.project.name)
        self.solver_instance = HFSS(project=None, design=self.name, solution_type=self.solution)

        self.solver_instance.design = self

        self._get_module()
        

    def _setup_circuit(self):
        
        self.project.desktop.odesktop.SetActiveProject(self.project.name)
        self.solver_instance = Circuit(project=None, design=self.name)

        self.solver_instance.design = self

        self._get_module()


    def _setup_icepak(self):
        self.project.desktop.odesktop.SetActiveProject(self.project.name)
        self.solver_instance = Icepak(project=None, design=self.name)

        self.solver_instance.design = self

        self._get_module()


    def _get_module(self):
        self.model3d = Model3d(self)
        self.post_processing = PostProcessing(self)


    def get_random_value(self, lower=None, upper=None, resolution=None):
        resolution_str = str(resolution)
        if '.' in resolution_str:
            precision = len(resolution_str.split('.')[1])
        else:
            precision = 0
        
        possible_values = np.arange(lower, upper + resolution, resolution)
        value = round(np.random.choice(possible_values), precision)

        if resolution == 1:
            value = int(value)
        else:
            value = float(value)
            
        return value


    def random_variable(self, variable_name=None, lower=None, upper=None, resolution=None, unit=""):
        
        value = self.get_random_value(lower, upper, resolution)

        if variable_name != None:
            self[variable_name] = f"{value}{unit}"
            self.variable_name = value

        return value



    def set_variable(self, variable_name=None, value=None, unit=""):

        if variable_name != None :
            self[variable_name] = f"{value}{unit}"
            self.variable_name = value

        return value
    


    def get_active_design(self) :

        design_name = self.project.desktop.active_design().GetName()
        design_type = self.project.desktop.active_design().GetDesignType()

        if design_type == "Icepak" :
            design_obj = pyDesign.create_design(self.project, name=design_name, solver="icepak")
        elif design_type == "Maxwell 3D" :
            design_obj = pyDesign.create_design(self.project, name=design_name, solver="maxwell3d")
        elif design_type == "HFSS" :
            design_obj = pyDesign.create_design(self.project, name=design_name, solver="hfss")
        else :
            return False

        return design_obj
    


    def delete_mesh(self, mesh_obj):
        
        # mesh : mesh object or mesh name(str)

        oModule = self.odesign.GetModule("MeshSetup")

        # mesh_obj가 리스트가 아닌 경우 리스트로 변환
        if not isinstance(mesh_obj, list):
            mesh_obj = [mesh_obj]

        for mesh in mesh_obj:
            if isinstance(mesh, str): # name case
                oModule.DeleteOp([mesh])
            elif isinstance(mesh.name, str): # obj case
                oModule.DeleteOp([mesh.name]) 
            else:
                raise ValueError("mesh_obj must be a mesh object or a mesh name(str)")
    



    def get_excitation(self, excitation_name=None):
        """
        Get excitation objects by name(s).
        
        Args:
            excitation_name (str or list): Name or list of names of excitations to get
            
        Returns:
            object or list: Single excitation object if str input, list of objects if list input
        """
        
        # Return empty list if no name provided
        if excitation_name is None:
            return []
            
        # Handle single name case
        if isinstance(excitation_name, str):
            if excitation_name in self.excitation_objects:
                return self.excitation_objects[excitation_name]
            else:
                raise ValueError(f"Excitation '{excitation_name}' not found")
                
        # Handle list of names case
        excitation_list = []
        for name in excitation_name:
            if name in self.excitation_objects:
                excitation_list.append(self.excitation_objects[name])
            else:
                raise ValueError(f"Excitation '{name}' not found")
                
        return excitation_list
