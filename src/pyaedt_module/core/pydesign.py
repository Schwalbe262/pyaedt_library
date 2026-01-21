from pyaedt_module.solver.maxwell3d import Maxwell3d
from pyaedt_module.solver.hfss import HFSS
from pyaedt_module.solver.circuit import Circuit
from pyaedt_module.solver.icepak import Icepak
from pyaedt_module.model3d import Model3d
from .post_processing import PostProcessing

import numpy as np
import re


class VariableWrapper(str):
    """
    문자열을 래핑하는 클래스로, 변수 값에서 숫자 부분만 추출할 수 있는 .value() 메서드를 제공합니다.
    
    Example:
        wrapper = VariableWrapper("1.6uH")
        wrapper.value()  # 1.6
        str(wrapper)     # "1.6uH"
    """
    def value(self):
        """
        Return the numeric part of the variable, with any units removed.
        E.g. '1.6uH' -> 1.6, '1k' -> 1, '2mm' -> 2, etc.
        If the numeric part cannot be parsed, returns the original string.
        """
        s = self.strip()
        m = re.match(r"^([-\d\.eE+]+)", s)
        if m:
            try:
                return float(m.group(1))
            except Exception:
                return self
        return self


class DesignList(list):
    """
    커스텀 리스트 클래스: 이름으로 design에 접근할 수 있게 함
    """
    def _get_design_name(self, design):
        """design 객체에서 이름을 안전하게 가져오기"""
        # solver_instance.design_name 우선 시도
        if hasattr(design, 'solver_instance') and design.solver_instance:
            if hasattr(design.solver_instance, 'design_name'):
                return design.solver_instance.design_name
        
        # name property 시도
        if hasattr(design, 'name'):
            return design.name
        
        return None
    
    def __getitem__(self, key):
        # 문자열이면 이름으로 검색
        if isinstance(key, str):
            for design in self:
                design_name = self._get_design_name(design)
                if design_name == key:
                    return design
            raise KeyError(f"Design '{key}' not found")
        
        # 정수면 일반 리스트처럼 인덱스로 접근
        return super().__getitem__(key)



class pyDesign:
    def __init__(self, project, name=None, solver=None, solution=None):
        self.project = project
        self.NUM_CORE = 4

        self._store = {}

        # 기본 design 생성 (AEDT design 객체)
        self.solver_instance = self._pydesign(project, name, solver, solution)
        
        # solver_instance가 None이면 에러 발생 (필수)
        if self.solver_instance is None:
            raise RuntimeError(
                f"Failed to create solver instance for design '{name}' with solver '{solver}'. "
                f"Please check if the solver type is valid and the project is properly initialized."
            )
        
        # solver_instance에 현재 pyDesign 인스턴스 연결 (다른 속성 이름 사용)
        # odesign은 PyAEDT의 property이므로 직접 설정하면 design 생성 시도가 발생함
        if not hasattr(self.solver_instance, '_py_design'):
            self.solver_instance._py_design = self
        
        # 모듈 초기화 (model3d, post_processing 등)
        self._get_module()
        


    
    def _pydesign(self, project, name, solver, solution):
        """인스턴스 메서드: design 생성 또는 가져오기"""
        solver = self._solver_name(solver)
        solution = self._solution_name(solver, solution)
        
        if solver == "HFSS":
            solver_instance = self._setup_hfss(name, solution)
        elif solver == "Maxwell 3D":
            solver_instance = self._setup_maxwell(name, solution)
        elif solver == "Icepak":
            solver_instance = self._setup_icepak(name, solution)
        elif solver == "Circuit Design":
            solver_instance = self._setup_circuit(name, solution)
        else:
            raise ValueError(f"Invalid solver: {solver}")

        return solver_instance

        



    def _solver_name(self, solver):

        if solver is None:
            return "Maxwell 3D"
        elif solver.lower().replace(" ", "") == "hfss":
            return "HFSS"
        elif solver.lower().replace(" ", "") == "maxwell3d":
            return "Maxwell 3D"
        elif solver.lower().replace(" ", "") == "maxwell2d":
            return "Maxwell 2D"
        elif solver.lower().replace(" ", "") == "icepak":
            return "Icepak"
        elif solver.lower().replace(" ", "") == "mechanical":
            return "Mechanical"
        elif solver.lower().replace(" ", "") == "circuitdesign" or solver.lower().replace(" ", "") == "circuit":
            return "Circuit Design"
        else:
            return solver



    def _solution_name(self, solver, solution):

        if solution is None:
            if solver == "HFSS":
                return "HFSS Terminal Network"
            elif solver == "Maxwell 3D":
                return "Magnetostatic"
            elif solver == "Maxwell 2D":
                return "Magnetostatic"
            elif solver == "Icepak":
                return "SteadyState TemperatureAndFlow"
            elif solver == "Mechanical":
                return ""
            elif solver == "Circuit Design":
                return "None"
            else:
                return None
        else:
            return solution




        

    
    def __getattr__(self, name):
        # First, try to get the attribute from the solver instance (e.g., methods like 'create_setup')
        if self.solver_instance:
            try:
                return getattr(self.solver_instance, name)
            except AttributeError:
                # If it's not found in solver_instance, try solver_instance.odesign (original AEDT design object)
                # odesign은 PyAEDT의 property이므로 직접 접근만 가능 (설정 불가)
                if hasattr(self.solver_instance, 'odesign'):
                    try:
                        odesign = self.solver_instance.odesign
                        if odesign:
                            return getattr(odesign, name)
                    except (AttributeError, TypeError):
                        pass
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
        """
        클래스 메서드: pyDesign 인스턴스를 생성합니다.
        __init__에서 이미 _setup_*가 호출되므로 여기서는 인스턴스만 생성하고 반환합니다.
        """
        return cls(project, name=name, solver=solver, solution=solution)
    

    def _setup_maxwell(self, name, solution):
        """Maxwell 3D solver 설정 및 인스턴스 생성"""
        self.project.desktop.odesktop.SetActiveProject(self.project.name)
        solver_instance = Maxwell3d(project=None, design=name, solution_type=solution)
        return solver_instance
            
    def _setup_hfss(self, name, solution):
        """HFSS solver 설정 및 인스턴스 생성"""
        self.project.desktop.odesktop.SetActiveProject(self.project.name)
        solver_instance = HFSS(project=None, design=name, solution_type=solution)
        return solver_instance

    def _setup_circuit(self, name, solution):
        """Circuit solver 설정 및 인스턴스 생성"""
        self.project.desktop.odesktop.SetActiveProject(self.project.name)
        solver_instance = Circuit(project=None, design=name)
        return solver_instance

    def _setup_icepak(self, name, solution):
        """Icepak solver 설정 및 인스턴스 생성"""
        self.project.desktop.odesktop.SetActiveProject(self.project.name)
        solver_instance = Icepak(project=None, design=name)
        return solver_instance



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

        if unit == None:
            unit = ""
        
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
    def variables(self) -> dict[str, VariableWrapper]:
        """
        Returns a dictionary where the keys are variable names, and the values are VariableWrapper objects,
        which behave like str, but have a `.value()` method to obtain the numeric part only.

        Example:
            design.variables["Ltx"]           # '1.6uH'
            design.variables["Ltx"].value()   # 1.6
        """
        variables = {
            var_name: VariableWrapper(self.solver_instance.odesign.GetVariableValue(var_name))
            for var_name in self.solver_instance.odesign.GetVariables()
        }
        return variables

    @property
    def name(self):
        return self.GetName()
    
    @property
    def solver(self):
        return self.GetDesignType()

    @property
    def solution(self):
        return self.GetSolutionType()

    




