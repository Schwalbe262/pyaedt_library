from pyaedt_module.solver.maxwell3d import Maxwell3d
from pyaedt_module.solver.hfss import HFSS
from pyaedt_module.solver.circuit import Circuit
from pyaedt_module.solver.icepak import Icepak
from pyaedt_module.model3d import Model3d
from .post_processing import PostProcessing

import numpy as np


class DesignList(list):
    """
    커스텀 리스트 클래스: 이름으로 design에 접근할 수 있게 함
    """
    def __getitem__(self, key):
        # 문자열이면 이름으로 검색
        if isinstance(key, str):
            for idx, design in enumerate(self):
                try:
                    # __dict__에서 직접 _name 속성 확인 (property 우회하여 크래시 방지)
                    design_name = None
                    
                    # 방법 1: __dict__에서 _name 직접 확인
                    if hasattr(design, '__dict__'):
                        design_name = design.__dict__.get('_name', None)
                    
                    # 방법 2: design 객체의 GetName() 메서드 직접 시도 (가장 안전)
                    if design_name is None:
                        if hasattr(design, 'design') and design.design is not None:
                            try:
                                if hasattr(design.design, 'GetName'):
                                    design_name = design.design.GetName()
                            except Exception:
                                pass
                    
                    # 방법 3: name property 시도 (마지막 수단)
                    if design_name is None:
                        try:
                            design_name = design.name
                        except Exception:
                            pass
                    
                    if design_name == key:
                        return design
                except Exception as e:
                    # 에러 발생하면 다음 design으로 넘어감
                    continue
            raise KeyError(f"Design '{key}' not found")
        # 정수면 일반 리스트처럼 인덱스로 접근
        return super().__getitem__(key)



class pyDesign:
    def __init__(self, project, name=None, solver=None, solution=None, design=None):
        self.project = project
        self.NUM_CORE = 4


        if design is not None:
            self.design = design
            self._name = design.GetName()
            self._solver = design.GetDesignType()
            self.solution = design.GetSolutionType() if hasattr(design, "GetSolutionType") else None
        else :
            self._name = name
            self._solver = solver.lower() if solver is not None else None
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


    
    @property
    def variables(self) -> dict[str, str]:
        """
        Returns a dictionary of all design variables.
        Automatically updates each time it's accessed.
        
        Returns:
            dict[str, str]: Dictionary mapping variable names to their values.
            
        Example:
            >>> design.variables
            {'Tx_outer_x': '2.5mm', 'Tx_ratio': '0.9', 'Tx_inner': '1.2mm', ...}
        """
        if self.solver_instance:
            var_dict = {}
            try:
                # variable_manager가 있는지 확인
                if hasattr(self.solver_instance, 'variable_manager'):
                    vm = self.solver_instance.variable_manager
                    # independent_variables가 있는지 확인
                    if hasattr(vm, 'independent_variables'):
                        for name, var_obj in vm.independent_variables.items():
                            # 변수 객체에서 값 가져오기
                            try:
                                var_dict[name] = var_obj.value
                            except (AttributeError, TypeError):
                                try:
                                    var_dict[name] = var_obj.expression
                                except (AttributeError, TypeError):
                                    var_dict[name] = str(var_obj)
            except Exception as e:
                # 에러 발생 시 빈 딕셔너리 반환
                print(f"Warning: Could not retrieve variables: {e}")
                return {}
            return var_dict
        return self._store.copy()


    @property
    def name(self):
        """Returns the design name. If solver_instance exists, returns its design_name, otherwise returns the stored name."""
        if self.solver_instance and hasattr(self.solver_instance, 'design_name'):
            return self.solver_instance.design_name
        return self._name
    
    @property
    def solver(self):
        """Returns the solver type. If solver_instance exists, returns its solver, otherwise returns the stored solver."""
        if self.solver_instance and hasattr(self.solver_instance, 'solver'):
            return self.solver_instance.solver
        return self._solver




